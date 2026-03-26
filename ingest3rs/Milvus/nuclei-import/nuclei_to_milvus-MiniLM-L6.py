#!/usr/bin/env python3
"""
nuclei_to_milvus.py — Parse Nuclei JSON results and insert into Milvus.

Features:
- Uses precomputed embeddings (no re-embedding needed)
- Creates collection if not exists
- Inserts findings with metadata
- Batch ingestion
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from pymilvus import (
    connections,
    FieldSchema,
    CollectionSchema,
    DataType,
    utility,
    Collection
)


# ──────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────
MILVUS_HOST = "localhost"
MILVUS_PORT = "19530"

COLLECTION_NAME = "nuclei_findings"
VECTOR_DIM = 384   # Must match your embedding size


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────
def clean_metadata(d: dict) -> dict:
    """
    Ensure metadata is Milvus-safe:
    - No None values
    - Convert complex types to string
    """
    cleaned = {}

    for k, v in d.items():
        if v is None:
            continue

        if isinstance(v, (str, int, float, bool)):
            cleaned[k] = v
        else:
            cleaned[k] = str(v)

    return cleaned


def parse_nuclei_json(path: str) -> list[dict]:
    with open(path, "r") as f:
        data = json.load(f)

    findings = []
    for entry in data:
        if entry.get("entry_type") == "finding":
            findings.append(entry)

    return findings


# ──────────────────────────────────────────────────────────────────────
# Milvus Setup
# ──────────────────────────────────────────────────────────────────────
def connect_milvus():
    print(f"[+] Connecting to Milvus at {MILVUS_HOST}:{MILVUS_PORT} ...")
    connections.connect(host=MILVUS_HOST, port=MILVUS_PORT)


def create_collection():
    if COLLECTION_NAME in utility.list_collections():
        print(f"[+] Collection '{COLLECTION_NAME}' already exists.")
        return Collection(COLLECTION_NAME)

    print(f"[+] Creating collection '{COLLECTION_NAME}' ...")

    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=False),
        FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=VECTOR_DIM),
        FieldSchema(name="template", dtype=DataType.VARCHAR, max_length=256),
        FieldSchema(name="severity", dtype=DataType.VARCHAR, max_length=32),
        FieldSchema(name="target", dtype=DataType.VARCHAR, max_length=512),
        FieldSchema(name="protocol", dtype=DataType.VARCHAR, max_length=32),
        FieldSchema(name="extra_info", dtype=DataType.VARCHAR, max_length=1024),
    ]

    schema = CollectionSchema(fields, description="Nuclei scan findings")

    collection = Collection(name=COLLECTION_NAME, schema=schema)

    print("[+] Creating index on vector field ...")
    collection.create_index(
        field_name="vector",
        index_params={
            "metric_type": "COSINE",
            "index_type": "IVF_FLAT",
            "params": {"nlist": 128}
        }
    )

    return collection


# ──────────────────────────────────────────────────────────────────────
# Ingest
# ──────────────────────────────────────────────────────────────────────
def ingest(json_path: str):
    findings = parse_nuclei_json(json_path)

    if not findings:
        sys.exit("No findings found in JSON.")

    print(f"[+] Parsed {len(findings)} findings from {json_path}")

    connect_milvus()
    collection = create_collection()

    BATCH = 100
    total = 0

    for i in range(0, len(findings), BATCH):
        batch = findings[i:i+BATCH]

        ids = []
        vectors = []
        templates = []
        severities = []
        targets = []
        protocols = []
        extra_infos = []

        for f in batch:
            ids.append(int(f["id"]))
            vectors.append(f["vector"])
            templates.append(str(f.get("template", "")))
            severities.append(str(f.get("severity", "")))
            targets.append(str(f.get("target", "")))
            protocols.append(str(f.get("protocol", "")))
            extra_infos.append(str(f.get("extra_info", "")))

        collection.insert([
            ids,
            vectors,
            templates,
            severities,
            targets,
            protocols,
            extra_infos
        ])

        total += len(batch)
        print(f"  inserted {total}/{len(findings)} findings")

    collection.flush()

    print(f"\n[+] Done — {total} findings stored in Milvus.")


# ──────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Ingest Nuclei JSON results into Milvus."
    )

    parser.add_argument(
        "json_file",
        help="Path to Milvus-ready Nuclei JSON file"
    )

    args = parser.parse_args()

    ingest(args.json_file)


if __name__ == "__main__":
    main()