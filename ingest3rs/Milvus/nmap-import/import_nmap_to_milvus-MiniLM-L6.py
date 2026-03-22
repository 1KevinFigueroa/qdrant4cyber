#!/usr/bin/env python3
"""
nmap_ingest_milvus.py — Production-ready Nmap → Milvus ingestion

Requirements:
    pip install pymilvus sentence-transformers

Run:
    python nmap_ingest_milvus.py scan.json --reset
"""

from __future__ import annotations

import argparse
import json
import sys

from sentence_transformers import SentenceTransformer
from pymilvus import (
    connections,
    FieldSchema,
    CollectionSchema,
    DataType,
    Collection,
    utility,
)

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
MILVUS_HOST = "localhost"
MILVUS_PORT = "19530"
COLLECTION_NAME = "nmap_test"

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

BATCH_SIZE = 64


# ─────────────────────────────────────────────
# CONNECTION
# ─────────────────────────────────────────────
def connect():
    connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT)


# ─────────────────────────────────────────────
# COLLECTION SETUP
# ─────────────────────────────────────────────
def create_collection(reset=False):
    if utility.has_collection(COLLECTION_NAME):
        if reset:
            print(f"[INFO] Dropping existing collection: {COLLECTION_NAME}")
            utility.drop_collection(COLLECTION_NAME)
        else:
            return Collection(COLLECTION_NAME)

    print(f"[INFO] Creating collection: {COLLECTION_NAME}")

    fields = [
        FieldSchema(
            name="id",
            dtype=DataType.INT64,
            is_primary=True,
            auto_id=True
        ),
        FieldSchema(
            name="embedding",
            dtype=DataType.FLOAT_VECTOR,
            dim=EMBEDDING_DIM
        ),
        FieldSchema(
            name="text",
            dtype=DataType.VARCHAR,
            max_length=2048
        ),
        FieldSchema(
            name="ip",
            dtype=DataType.VARCHAR,
            max_length=50
        ),
        FieldSchema(
            name="hostname",
            dtype=DataType.VARCHAR,
            max_length=255
        ),
        FieldSchema(
            name="os",
            dtype=DataType.VARCHAR,
            max_length=255
        ),
    ]

    schema = CollectionSchema(fields, description="Nmap scan results")

    collection = Collection(name=COLLECTION_NAME, schema=schema)

    index_params = {
        "index_type": "IVF_FLAT",
        "metric_type": "COSINE",
        "params": {"nlist": 1024},
    }

    collection.create_index(field_name="embedding", index_params=index_params)

    return collection


# ─────────────────────────────────────────────
# NMAP PARSING
# ─────────────────────────────────────────────
def parse_nmap_json(path: str):
    with open(path) as f:
        data = json.load(f)

    hosts_raw = data.get("nmaprun", {}).get("host", [])

    if isinstance(hosts_raw, dict):
        hosts_raw = [hosts_raw]

    hosts = []

    for host in hosts_raw:
        if host.get("status", {}).get("@state") != "up":
            continue

        addresses = host.get("address", [])
        if isinstance(addresses, dict):
            addresses = [addresses]

        ip = None
        for a in addresses:
            if a.get("@addrtype") == "ipv4":
                ip = a["@addr"]

        if not ip:
            continue

        ports_raw = host.get("ports", {}).get("port", [])
        if isinstance(ports_raw, dict):
            ports_raw = [ports_raw]

        ports = []
        for p in ports_raw:
            if p.get("state", {}).get("@state") == "open":
                ports.append({
                    "port": p.get("@portid"),
                    "service": p.get("service", {}).get("@name", ""),
                })

        hosts.append({
            "ip": ip,
            "ports": ports,
            "hostname": "",
            "os": "unknown",
        })

    return hosts


def host_to_text(h):
    lines = [f"Host {h['ip']}"]

    if h["ports"]:
        lines.append("Open ports:")
        for p in h["ports"]:
            lines.append(f"{p['port']} - {p['service']}")

    return "\n".join(lines)


# ─────────────────────────────────────────────
# INGEST
# ─────────────────────────────────────────────
def ingest(json_path: str, reset=False):
    connect()

    collection = create_collection(reset=reset)

    hosts = parse_nmap_json(json_path)
    if not hosts:
        sys.exit("No valid hosts found.")

    print(f"[INFO] Parsed {len(hosts)} hosts")

    model = SentenceTransformer(EMBEDDING_MODEL)

    texts = [host_to_text(h) for h in hosts]

    print("[INFO] Generating embeddings...")
    embeddings = model.encode(texts).tolist()

    ips = [h["ip"] for h in hosts]
    hostnames = [h["hostname"] for h in hosts]
    os_list = [h["os"] for h in hosts]

    total = 0

    print("[INFO] Inserting into Milvus...")

    for i in range(0, len(texts), BATCH_SIZE):
        batch_embeddings = embeddings[i:i+BATCH_SIZE]
        batch_texts = texts[i:i+BATCH_SIZE]
        batch_ips = ips[i:i+BATCH_SIZE]
        batch_hostnames = hostnames[i:i+BATCH_SIZE]
        batch_os = os_list[i:i+BATCH_SIZE]

        collection.insert([
            batch_embeddings,
            batch_texts,
            batch_ips,
            batch_hostnames,
            batch_os
        ])

        total += len(batch_texts)
        print(f"  inserted {total}/{len(texts)}")

    collection.flush()
    collection.load()

    print(f"\n✅ Done: {total} records inserted into '{COLLECTION_NAME}'")


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("json_file", help="Path to Nmap JSON file")
    parser.add_argument("--reset", action="store_true", help="Drop & recreate collection")

    args = parser.parse_args()

    ingest(args.json_file, reset=args.reset)


if __name__ == "__main__":
    main()