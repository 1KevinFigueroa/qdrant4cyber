#!/usr/bin/env python3
"""
nuclei_to_pinecone.py — Parse Nuclei JSON results and upsert into a local
Pinecone index using MiniLM embeddings.

Fixes applied:
- Removes null metadata values (Pinecone requirement)
- Normalizes metadata types
- Improves semantic embedding text
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

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384


# ──────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────
def embed_texts(texts: list[str], model: SentenceTransformer) -> list[list[float]]:
    embeddings = model.encode(texts, show_progress_bar=True)
    return embeddings.tolist()


def clean_metadata(d: dict) -> dict:
    """
    Ensure metadata is Pinecone-safe:
    - No None values
    - Only primitive types or list[str]
    """
    cleaned = {}

    for k, v in d.items():
        if v is None:
            continue  # remove nulls

        if isinstance(v, (str, int, float, bool)):
            cleaned[k] = v
        elif isinstance(v, list):
            cleaned[k] = [str(x) for x in v if x is not None]
        else:
            cleaned[k] = str(v)

    return cleaned


# ──────────────────────────────────────────────────────────────────────
# Nuclei Parsing
# ──────────────────────────────────────────────────────────────────────
def _finding_to_text(f: dict) -> str:
    """
    Convert finding into semantic string for embeddings.
    """
    return (
        f"{f.get('severity', 'unknown')} severity finding | "
        f"template {f.get('template', '')} | "
        f"target {f.get('target', '')} | "
        f"protocol {f.get('protocol', '')} | "
        f"extra {f.get('extra_info') or 'none'}"
    )


def _finding_to_metadata(f: dict) -> dict:
    raw_meta = {
        "id": f.get("id"),
        "entry_type": f.get("entry_type"),
        "template": f.get("template"),
        "severity": f.get("severity"),
        "target": f.get("target"),
        "protocol": f.get("protocol"),
        "extra_info": f.get("extra_info"),
    }

    return clean_metadata(raw_meta)


def parse_nuclei_json(path: str) -> list[dict]:
    with open(path, "r") as f:
        data = json.load(f)

    findings = []
    for entry in data:
        if entry.get("entry_type") == "finding":
            findings.append(entry)

    return findings


# ──────────────────────────────────────────────────────────────────────
# Pinecone
# ──────────────────────────────────────────────────────────────────────
def get_index():
    from pinecone import Pinecone
    pc = Pinecone(api_key="pclocal")
    return pc.Index(host=PINECONE_HOST)


def ingest(json_path: str):
    findings = parse_nuclei_json(json_path)

    if not findings:
        sys.exit("No findings found in JSON.")

    print(f"Parsed {len(findings)} findings from {json_path}")

    print(f"Loading embedding model '{EMBEDDING_MODEL}' …")
    model = SentenceTransformer(EMBEDDING_MODEL)

    print(f"Connecting to Pinecone at {PINECONE_HOST} …")
    index = get_index()

    texts = [_finding_to_text(f) for f in findings]
    metas = [_finding_to_metadata(f) for f in findings]
    ids = [f"finding-{f['id']}" for f in findings]

    BATCH = 100
    total = 0

    for i in range(0, len(texts), BATCH):
        batch_texts = texts[i:i+BATCH]
        batch_ids = ids[i:i+BATCH]
        batch_metas = metas[i:i+BATCH]

        embeddings = embed_texts(batch_texts, model)

        vectors = [
            {
                "id": vid,
                "values": emb,
                "metadata": meta
            }
            for vid, emb, meta in zip(batch_ids, embeddings, batch_metas)
        ]

        index.upsert(vectors=vectors)
        total += len(vectors)

        print(f"  upserted {total}/{len(texts)} findings")

    print(f"\nDone — {total} findings stored in Pinecone.")


# ──────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Ingest Nuclei JSON results into Pinecone."
    )
    parser.add_argument("json_file", help="Path to Nuclei JSON file")

    args = parser.parse_args()
    ingest(args.json_file)


if __name__ == "__main__":
    main()