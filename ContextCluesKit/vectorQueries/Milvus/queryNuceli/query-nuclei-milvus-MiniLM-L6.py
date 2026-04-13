#!/usr/bin/env python3
"""
query-nuclei-milvus-MiniLM-L6.py — Semantic search over Nuclei findings
stored in Milvus.

Uses MiniLM embeddings (same as ingestion script).

Usage:
    python query-nuclei-milvus-MiniLM-L6.py "critical vulnerabilities"
    python query-nuclei-milvus-MiniLM-L6.py "apache misconfigurations" --top-k 10
    python query-nuclei-milvus-MiniLM-L6.py --interactive
"""

from __future__ import annotations

import argparse
import sys

from sentence_transformers import SentenceTransformer
from pymilvus import connections, Collection


# ──────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────
MILVUS_HOST = "localhost"
MILVUS_PORT = "19530"

COLLECTION_NAME = "nuclei_findings"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
TOP_K_DEFAULT = 5


# ──────────────────────────────────────────────────────────────────────
# Milvus
# ──────────────────────────────────────────────────────────────────────
def get_collection():
    connections.connect(host=MILVUS_HOST, port=MILVUS_PORT, timeout=5)
    collection = Collection(COLLECTION_NAME)
    collection.load()
    return collection


# ──────────────────────────────────────────────────────────────────────
# Display helpers (same as your Pinecone script)
# ──────────────────────────────────────────────────────────────────────
SEPARATOR = "=" * 80
THIN_SEP = "-" * 60


def print_header(question: str, count: int):
    print(f"\n{SEPARATOR}")
    print(f"  Query: {question}")
    print(f"  Results: {count}")
    print(SEPARATOR)


def print_result(rank: int, hit):
    entity = hit.entity
    score = hit.score

    template = entity.get("template")
    severity = entity.get("severity")
    target = entity.get("target")
    protocol = entity.get("protocol")
    extra = entity.get("extra_info")

    print(f"\n  [{rank}]  {template}   —   score: {score:.4f}")
    print(f"  {THIN_SEP}")
    print(f"  Severity  : {severity}")
    print(f"  Target    : {target}")
    print(f"  Protocol  : {protocol}")

    if extra:
        print(f"  Details   : {extra}")

    print()


def print_no_results():
    print("\n  No matching findings found.\n")


# ──────────────────────────────────────────────────────────────────────
# Query logic
# ──────────────────────────────────────────────────────────────────────
def query(question: str, model: SentenceTransformer, collection, top_k: int = TOP_K_DEFAULT):
    q_embedding = model.encode([question])[0].tolist()

    results = collection.search(
        data=[q_embedding],
        anns_field="vector",
        param={
            "metric_type": "COSINE",
            "params": {"nprobe": 10}
        },
        limit=top_k,
        output_fields=["template", "severity", "target", "protocol", "extra_info"]
    )

    hits = results[0]

    if not hits:
        print_no_results()
        return

    print_header(question, len(hits))

    for i, hit in enumerate(hits, 1):
        print_result(i, hit)


# ──────────────────────────────────────────────────────────────────────
# Interactive mode (same UX as Pinecone script)
# ──────────────────────────────────────────────────────────────────────
def interactive(model: SentenceTransformer, collection, top_k: int):
    print(SEPARATOR)
    print("  Nuclei Query Console  —  Milvus")
    print(f"  Collection: {COLLECTION_NAME}  |  Model: {EMBEDDING_MODEL}  |  top-k: {top_k}")
    print("  Commands:")
    print("    :k <n>    change top-k")
    print("    :quit     exit")
    print(SEPARATOR)

    current_top_k = top_k

    while True:
        try:
            user_input = input("\nnuclei-query> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not user_input:
            continue

        if user_input.lower() in (":quit", ":exit", ":q"):
            print("Goodbye.")
            break

        if user_input.lower().startswith(":k "):
            try:
                new_k = int(user_input.split()[1])
                if new_k < 1:
                    raise ValueError
                current_top_k = new_k
                print(f"  top-k set to {current_top_k}")
            except:
                print("  Usage: :k <number>")
            continue

        query(user_input, model, collection, top_k=current_top_k)


# ──────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Semantic search over Nuclei findings in Milvus."
    )

    parser.add_argument(
        "question",
        nargs="?",
        help="Search query (omit for interactive mode)",
    )

    parser.add_argument(
        "--top-k", "-k",
        type=int,
        default=TOP_K_DEFAULT,
        help="Number of results",
    )

    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Interactive mode",
    )

    args = parser.parse_args()

    if not args.question and not args.interactive:
        parser.print_help()
        sys.exit(0)

    print(f"Loading embedding model '{EMBEDDING_MODEL}' …")
    model = SentenceTransformer(EMBEDDING_MODEL)

    print(f"Connecting to Milvus at {MILVUS_HOST}:{MILVUS_PORT} …")
    collection = get_collection()

    if args.interactive:
        interactive(model, collection, args.top_k)
    else:
        query(args.question, model, collection, args.top_k)


if __name__ == "__main__":
    main()