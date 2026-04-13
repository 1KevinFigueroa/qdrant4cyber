#!/usr/bin/env python3
"""
nuclei_to_milvus.py — Parse Nuclei JSON results and insert into Milvus.

Features:
- Generates embeddings at ingest time using sentence-transformers (MiniLM-L6-v2)
- Creates collection if not exists
- Inserts findings with metadata
- Batch ingestion
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

from sentence_transformers import SentenceTransformer

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
EMBED_MODEL = "all-MiniLM-L6-v2"


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────
def build_embed_text(entry: dict) -> str:
    """
    Build a single string from the finding fields to embed.
    """
    parts = [
        f"template:{entry.get('template', '')}",
        f"severity:{entry.get('severity', '')}",
        f"target:{entry.get('target', '')}",
        f"protocol:{entry.get('protocol', '')}",
    ]
    extra = entry.get("extra_info")
    if extra:
        parts.append(f"extra_info:{extra}")
    return " | ".join(parts)


def embed_findings(findings: list[dict]) -> list[list[float]]:
    """
    Generate embeddings for a list of findings using MiniLM-L6-v2.
    """
    print(f"[+] Loading embedding model '{EMBED_MODEL}' ...")
    model = SentenceTransformer(EMBED_MODEL)
    texts = [build_embed_text(f) for f in findings]
    print(f"[+] Embedding {len(texts)} findings ...")
    vectors = model.encode(texts, show_progress_bar=True)
    return [v.tolist() for v in vectors]
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

    # Generate embeddings for all findings
    all_vectors = embed_findings(findings)

    connect_milvus()
    collection = create_collection()

    BATCH = 100
    total = 0

    for i in range(0, len(findings), BATCH):
        batch = findings[i:i+BATCH]
        batch_vectors = all_vectors[i:i+BATCH]

        ids = []
        vectors = []
        templates = []
        severities = []
        targets = []
        protocols = []
        extra_infos = []

        for idx, f in enumerate(batch):
            ids.append(int(f["id"]))
            vectors.append(batch_vectors[idx])
            templates.append(str(f.get("template", "")))
            severities.append(str(f.get("severity", "")))
            targets.append(str(f.get("target", "")))
            protocols.append(str(f.get("protocol", "")))
            extra_infos.append(str(f.get("extra_info") or ""))

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