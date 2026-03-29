#!/usr/bin/env python3
"""
nmap_ingest_weaviate.py — Production-ready Nmap → Weaviate ingestion

Features:
- MiniLM embeddings
- Hybrid search ready (BM25 + vector)
- Tag enrichment
- CLI interface
- Reset schema option

Requirements:
    pip install weaviate-client sentence-transformers tqdm
"""

import argparse
import json
import sys
from urllib.parse import urlparse

import weaviate
import weaviate.classes as wvc
from sentence_transformers import SentenceTransformer
from tqdm import tqdm
from weaviate.classes.config import Configure, DataType, Property
from weaviate.exceptions import WeaviateGRPCUnavailableError

# -----------------------------
# CONFIG
# -----------------------------
WEAVIATE_URL = "http://localhost:8080"
CLASS_NAME = "NmapHost"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
BATCH_SIZE = 64


# -----------------------------
# CONNECT
# -----------------------------
def connect():
    parsed = urlparse(WEAVIATE_URL)
    host = parsed.hostname or "localhost"
    http_secure = parsed.scheme == "https"
    http_port = parsed.port or (443 if http_secure else 80)
    grpc_port = 50051 if http_port == 8080 else http_port

    try:
        return weaviate.connect_to_custom(
            http_host=host,
            http_port=http_port,
            http_secure=http_secure,
            grpc_host=host,
            grpc_port=grpc_port,
            grpc_secure=http_secure,
            additional_config=wvc.init.AdditionalConfig(
                timeout=wvc.init.Timeout(init=30)
            ),
        )
    except WeaviateGRPCUnavailableError as exc:
        raise SystemExit(
            f"Could not connect to Weaviate gRPC at {host}:{grpc_port}. "
            "Ensure Weaviate is running and the gRPC port is exposed."
        ) from exc


# -----------------------------
# SCHEMA
# -----------------------------
def create_schema(client, reset=False):
    if client.collections.exists(CLASS_NAME):
        if reset:
            print(f"[INFO] Dropping schema: {CLASS_NAME}")
            client.collections.delete(CLASS_NAME)
        else:
            return

    print(f"[INFO] Creating schema: {CLASS_NAME}")

    client.collections.create(
        CLASS_NAME,
        vector_config=Configure.Vectors.self_provided(),
        properties=[
            Property(name="text", data_type=DataType.TEXT, index_searchable=True),
            Property(name="ip", data_type=DataType.TEXT, index_searchable=True),
            Property(name="hostname", data_type=DataType.TEXT, index_searchable=True),
            Property(name="os", data_type=DataType.TEXT, index_searchable=True),
            Property(name="tags", data_type=DataType.TEXT_ARRAY, index_filterable=True),
        ],
    )


# -----------------------------
# TAG GENERATION
# -----------------------------
def generate_tags(ports, os_name):
    tags = []

    for p in ports:
        service = p["service"].lower()

        if "kubernetes" in service:
            tags += ["kubernetes", "orchestration"]

        if "docker" in service:
            tags.append("container")

        if any(x in service for x in ["mysql", "postgres"]):
            tags.append("database")

        if "redis" in service:
            tags.append("cache")

        if "kafka" in service:
            tags.append("streaming")

        if "prometheus" in service:
            tags.append("monitoring")

        if "grafana" in service:
            tags.append("dashboard")

        if "nginx" in service or "apache" in service:
            tags.append("web_server")

        if "traefik" in service:
            tags.append("reverse_proxy")

        if p["port"] == "6443":
            tags.append("k8s_api")

        if p["port"] in ["9200", "9300"]:
            tags.append("exposed_search")

    if "linux" in os_name.lower():
        tags.append("linux")

    if "windows" in os_name.lower():
        tags.append("windows")

    return list(set(tags))


# -----------------------------
# PARSE NMAP
# -----------------------------
def parse_nmap_json(path):
    with open(path) as f:
        data = json.load(f)

    hosts_raw = data.get("nmaprun", {}).get("host", [])

    if isinstance(hosts_raw, dict):
        hosts_raw = [hosts_raw]

    hosts = []

    for host in hosts_raw:
        if host.get("status", {}).get("@state") != "up":
            continue

        # IP
        ip = None
        for addr in host.get("address", []):
            if addr.get("@addrtype") == "ipv4":
                ip = addr.get("@addr")

        if not ip:
            continue

        # OS
        os_name = host.get("os", {}).get("osmatch", {}).get("@name", "unknown")

        # Ports
        ports_raw = host.get("ports", {}).get("port", [])
        if isinstance(ports_raw, dict):
            ports_raw = [ports_raw]

        ports = []
        for p in ports_raw:
            if p.get("state", {}).get("@state") == "open":
                ports.append({
                    "port": p.get("@portid"),
                    "service": p.get("service", {}).get("@product", "")
                })

        hosts.append({
            "ip": ip,
            "hostname": "",
            "os": os_name,
            "ports": ports
        })

    return hosts


# -----------------------------
# TEXT BUILDER
# -----------------------------
def host_to_text(host):
    lines = [f"Host {host['ip']} running {host['os']}"]

    if host["ports"]:
        lines.append("Open services:")
        for p in host["ports"]:
            lines.append(f"{p['port']} {p['service']}")

    return "\n".join(lines)


# -----------------------------
# INGEST
# -----------------------------
def ingest(json_path, reset=False):
    client = connect()
    try:
        create_schema(client, reset=reset)
        collection = client.collections.get(CLASS_NAME)

        hosts = parse_nmap_json(json_path)

        if not hosts:
            sys.exit("No valid hosts found")

        print(f"[INFO] Parsed {len(hosts)} hosts")

        model = SentenceTransformer(MODEL_NAME)

        texts = []
        tags_list = []

        for h in hosts:
            tags = generate_tags(h["ports"], h["os"])
            text = host_to_text(h) + f"\nTags: {' '.join(tags)}"

            texts.append(text)
            tags_list.append(tags)

        print("[INFO] Generating embeddings...")
        vectors = model.encode(texts).tolist()

        print("[INFO] Inserting into Weaviate...")

        total = 0
        with collection.batch.dynamic() as batch:
            for i in tqdm(range(len(texts))):
                batch.add_object(
                    properties={
                        "text": texts[i],
                        "ip": hosts[i]["ip"],
                        "hostname": hosts[i]["hostname"],
                        "os": hosts[i]["os"],
                        "tags": tags_list[i],
                    },
                    vector=vectors[i],
                )
                total += 1

        print(f"\n✅ Done: {total} hosts ingested into '{CLASS_NAME}'")
    finally:
        client.close()


# -----------------------------
# CLI
# -----------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("json_file", help="Path to Nmap JSON file")
    parser.add_argument("--reset", action="store_true", help="Drop schema first")

    args = parser.parse_args()

    ingest(args.json_file, reset=args.reset)


if __name__ == "__main__":
    main()