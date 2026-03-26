#!/usr/bin/env python3
"""
nuclei_to_weaviate.py — Parse Nuclei JSON results and upsert into Weaviate
using MiniLM embeddings (v4 client).

Features:
- Removes null metadata values
- Normalizes metadata types
- Uses MiniLM embeddings
- Batch ingestion (like Pinecone script)
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any

import weaviate
from sentence_transformers import SentenceTransformer
from weaviate.classes.config import Property, DataType


# ──────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────
WEAVIATE_URL = "http://localhost:8080"

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

CLASS_NAME = "NucleiFinding"


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────
def embed_texts(texts: list[str], model: SentenceTransformer) -> list[list[float]]:
    embeddings = model.encode(texts, show_progress_bar=True)
    return embeddings.tolist()


def clean_metadata(d: dict) -> dict:
    """
    Ensure metadata is Weaviate-safe:
    - No None values
    - Only primitive types or list[str]
    """
    cleaned = {}

    for k, v in d.items():
        if v is None:
            continue

        if isinstance(v, (str, int, float, bool)):
            cleaned[k] = v
        elif isinstance(v, list):
            cleaned[k] = [str(x) for x in v if x is not None]
        else:
            cleaned[k] = str(v)

    return cleaned


# ──────────────────────────────────────────────────────────────────────
# Nuclei Parsing (MATCHES YOUR STYLE)
# ──────────────────────────────────────────────────────────────────────
def _finding_to_text(f: dict) -> str:
    """
    Convert finding into semantic string for embeddings.
    """
    props = f.get("properties", {})
    metadata = props.get("metadata", {})

    meta_text = " ".join(
        f"{k}:{','.join(v) if isinstance(v, list) else v}"
        for k, v in metadata.items()
    )

    return (
        f"{props.get('severity', 'unknown')} severity finding | "
        f"template {props.get('template', '')} | "
        f"target {props.get('target', '')} | "
        f"protocol {props.get('protocol', '')} | "
        f"{meta_text}"
    )


def _finding_to_metadata(f: dict) -> dict:
    props = f.get("properties", {})

    raw_meta = {
        "template": props.get("template"),
        "severity": props.get("severity"),
        "target": props.get("target"),
        "protocol": props.get("protocol"),
    }

    return clean_metadata(raw_meta)


def parse_nuclei_json(path: str) -> list[dict]:
    with open(path, "r") as f:
        return json.load(f)


# ──────────────────────────────────────────────────────────────────────
# Weaviate
# ──────────────────────────────────────────────────────────────────────
def get_client():
    return weaviate.connect_to_local()


def ensure_collection(client):
    existing = client.collections.list_all()

    if CLASS_NAME in existing:
        print(f"[+] Collection '{CLASS_NAME}' already exists")
        return

    print(f"[+] Creating collection '{CLASS_NAME}'...")

    client.collections.create(
        name=CLASS_NAME,
        vectorizer_config=None,
        properties=[
            Property(name="template", data_type=DataType.TEXT),
            Property(name="protocol", data_type=DataType.TEXT),
            Property(name="severity", data_type=DataType.TEXT),
            Property(name="target", data_type=DataType.TEXT),
            Property(name="description", data_type=DataType.TEXT),
            Property(name="raw", data_type=DataType.TEXT),
            Property(name="timestamp", data_type=DataType.TEXT),
            Property(name="metadata", data_type=DataType.TEXT),
        ],
    )


def ingest(json_path: str):
    findings = parse_nuclei_json(json_path)

    if not findings:
        sys.exit("No findings found in JSON.")

    print(f"Parsed {len(findings)} findings from {json_path}")

    print(f"Loading embedding model '{EMBEDDING_MODEL}' …")
    model = SentenceTransformer(EMBEDDING_MODEL)

    print(f"Connecting to Weaviate at {WEAVIATE_URL} …")
    client = get_client()

    ensure_collection(client)

    collection = client.collections.get(CLASS_NAME)

    texts = [_finding_to_text(f) for f in findings]
    metas = [_finding_to_metadata(f) for f in findings]

    BATCH = 100
    total = 0

    for i in range(0, len(texts), BATCH):
        batch_texts = texts[i:i+BATCH]
        batch_objs = findings[i:i+BATCH]
        batch_metas = metas[i:i+BATCH]

        embeddings = embed_texts(batch_texts, model)

        with collection.batch.dynamic() as batch:
            for obj, emb, meta, text in zip(batch_objs, embeddings, batch_metas, batch_texts):
                props = obj.get("properties", {})

                batch.add_object(
                    properties={
                        "template": props.get("template"),
                        "protocol": props.get("protocol"),
                        "severity": props.get("severity"),
                        "target": props.get("target"),
                        "description": text,
                        "raw": props.get("raw"),
                        "timestamp": props.get("timestamp"),
                        "metadata": json.dumps(meta),
                    },
                    vector=emb
                )

        total += len(batch_texts)
        print(f"  upserted {total}/{len(texts)} findings")

    client.close()

    print(f"\nDone — {total} findings stored in Weaviate.")


# ──────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Ingest Nuclei JSON results into Weaviate."
    )
    parser.add_argument("json_file", help="Path to Nuclei JSON file")

    args = parser.parse_args()
    ingest(args.json_file)


if __name__ == "__main__":
    main()