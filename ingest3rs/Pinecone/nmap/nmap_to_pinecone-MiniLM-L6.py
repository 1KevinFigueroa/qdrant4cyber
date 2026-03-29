#!/usr/bin/env python3
"""
nmap_ingest.py — Parse nmap JSON scan results and upsert them into a local
Pinecone index (Docker).

Uses the local 'all-MiniLM-L6-v2' model from sentence-transformers for
embeddings — no OpenAI API key required.

Requirements:
    pip install pinecone[grpc] sentence-transformers

Docker setup (run before this script):
    docker run -d --name nmap-index \
        -e PORT=5081 \
        -e INDEX_TYPE=serverless \
        -e VECTOR_TYPE=dense \
        -e DIMENSION=384 \
        -e METRIC=cosine \
        -p 5081:5081 \
        --platform linux/amd64 \
        ghcr.io/pinecone-io/pinecone-index:latest

Environment variables (optional):
    PINECONE_HOST  – local index URL (default: "http://localhost:5081")

Usage:
    python nmap_ingest.py fake_nmap_results.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

from sentence_transformers import SentenceTransformer

# ──────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────
PINECONE_HOST = os.environ.get("PINECONE_HOST", "http://localhost:5081")

EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # 384 dimensions
EMBEDDING_DIM = 384


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────
def embed_texts(texts: list[str], model: SentenceTransformer) -> list[list[float]]:
    embeddings = model.encode(texts, show_progress_bar=True)
    return embeddings.tolist()


# ──────────────────────────────────────────────────────────────────────
# Parsing nmap JSON → documents
# ──────────────────────────────────────────────────────────────────────
def _normalize_host(host: dict) -> dict | None:
    if host.get("status", {}).get("@state", "unknown") != "up":
        return None

    addresses = host.get("address", [])
    if isinstance(addresses, dict):
        addresses = [addresses]
    ip = mac = None
    for a in addresses:
        if a.get("@addrtype") == "ipv4":
            ip = a["@addr"]
        elif a.get("@addrtype") == "mac":
            mac = a["@addr"]

    hn_block = host.get("hostnames", {})
    hostname_entry = hn_block.get("hostname", {})
    if isinstance(hostname_entry, list):
        hostname = hostname_entry[0].get("@name", "") if hostname_entry else ""
    else:
        hostname = hostname_entry.get("@name", "")

    port_list = host.get("ports", {}).get("port", [])
    if isinstance(port_list, dict):
        port_list = [port_list]

    ports: list[dict[str, Any]] = []
    for p in port_list:
        svc = p.get("service", {})
        ports.append({
            "port": p.get("@portid", ""),
            "protocol": p.get("@protocol", ""),
            "state": p.get("state", {}).get("@state", ""),
            "service_name": svc.get("@name", ""),
            "product": svc.get("@product", ""),
            "version": svc.get("@version", ""),
            "extra": svc.get("@extrainfo", ""),
        })

    os_match = host.get("os", {}).get("osmatch", {})
    if isinstance(os_match, list):
        os_match = os_match[0] if os_match else {}
    os_name = os_match.get("@name", "unknown")
    os_accuracy = os_match.get("@accuracy", "")

    uptime_sec = host.get("uptime", {}).get("@seconds", "")
    last_boot = host.get("uptime", {}).get("@lastboot", "")

    return {
        "ip": ip,
        "mac": mac,
        "hostname": hostname,
        "os": os_name,
        "os_accuracy": os_accuracy,
        "uptime_seconds": uptime_sec,
        "last_boot": last_boot,
        "ports": ports,
    }


def _host_to_text(h: dict) -> str:
    lines = [f"Host {h['ip']}"]
    if h["hostname"]:
        lines[0] += f" ({h['hostname']})"
    if h["mac"]:
        lines.append(f"MAC address: {h['mac']}")
    lines.append(f"Operating system: {h['os']} (accuracy {h['os_accuracy']}%)")
    if h["last_boot"]:
        lines.append(f"Last boot: {h['last_boot']} (uptime {h['uptime_seconds']}s)")

    open_ports = [p for p in h["ports"] if p["state"] == "open"]
    if open_ports:
        lines.append(f"Open ports ({len(open_ports)}):")
        for p in open_ports:
            desc = f"  {p['port']}/{p['protocol']} — {p['service_name']}"
            if p["product"]:
                desc += f" ({p['product']}"
                if p["version"]:
                    desc += f" {p['version']}"
                if p["extra"]:
                    desc += f", {p['extra']}"
                desc += ")"
            lines.append(desc)

    return "\n".join(lines)


def _host_to_metadata(h: dict) -> dict:
    open_ports = [p for p in h["ports"] if p["state"] == "open"]
    return {
        "ip": h["ip"] or "",
        "hostname": h["hostname"] or "",
        "mac": h["mac"] or "",
        "os": h["os"],
        "os_accuracy": h["os_accuracy"],
        "last_boot": h["last_boot"],
        "uptime_seconds": h["uptime_seconds"],
        "open_port_numbers": [p["port"] for p in open_ports],
        "services": [p["service_name"] for p in open_ports],
        "products": [p["product"] for p in open_ports if p["product"]],
        "port_count": len(open_ports),
        "text": _host_to_text(h),
    }


def parse_nmap_json(path: str) -> list[dict]:
    with open(path) as f:
        data = json.load(f)

    hosts_raw = data.get("nmaprun", {}).get("host", [])
    if isinstance(hosts_raw, dict):
        hosts_raw = [hosts_raw]

    hosts = []
    for raw in hosts_raw:
        h = _normalize_host(raw)
        if h and h["ip"]:
            hosts.append(h)
    return hosts


# ──────────────────────────────────────────────────────────────────────
# Pinecone operations (local Docker — pinecone-index image)
#
# The pinecone-index Docker image exposes a single index on a port.
# There is no control-plane API (no list/create/delete index).
# We connect directly to the index host.
# ──────────────────────────────────────────────────────────────────────
def get_index():
    """Return a handle to the local Pinecone index."""
    from pinecone import Pinecone
    pc = Pinecone(api_key="pclocal")
    return pc.Index(host=PINECONE_HOST)


def ingest(json_path: str):
    hosts = parse_nmap_json(json_path)
    if not hosts:
        sys.exit("No hosts found in the scan file.")
    print(f"Parsed {len(hosts)} live hosts from {json_path}")

    print(f"Loading embedding model '{EMBEDDING_MODEL}' …")
    model = SentenceTransformer(EMBEDDING_MODEL)

    print(f"Connecting to local Pinecone index at {PINECONE_HOST} …")
    index = get_index()

    texts = [_host_to_text(h) for h in hosts]
    metas = [_host_to_metadata(h) for h in hosts]
    ids = [f"host-{h['ip'].replace('.', '_')}" for h in hosts]

    BATCH = 100
    total = 0
    for i in range(0, len(texts), BATCH):
        batch_texts = texts[i : i + BATCH]
        batch_ids = ids[i : i + BATCH]
        batch_metas = metas[i : i + BATCH]

        embeddings = embed_texts(batch_texts, model)
        vectors = [
            {"id": vid, "values": emb, "metadata": meta}
            for vid, emb, meta in zip(batch_ids, embeddings, batch_metas)
        ]
        index.upsert(vectors=vectors)
        total += len(vectors)
        print(f"  upserted {total}/{len(texts)} vectors")

    print(f"\nDone — {total} host records stored in Pinecone index at {PINECONE_HOST}.")


# ──────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Ingest nmap JSON scan results into a Pinecone vector database.",
    )
    parser.add_argument("json_file", help="Path to the nmap JSON results file")
    args = parser.parse_args()
    ingest(args.json_file)


if __name__ == "__main__":
    main()
