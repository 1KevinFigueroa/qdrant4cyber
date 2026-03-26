#!/usr/bin/env python3
"""
query-nuclei-weaviate-MiniLM-L6.py — Semantic search over Nuclei findings
stored in a local Weaviate instance.

Uses MiniLM embeddings (same as ingestion script).

Usage:
    python query-nuclei-weaviate-MiniLM-L6.py "critical vulnerabilities"
    python query-nuclei-weaviate-MiniLM-L6.py "apache misconfigurations" --top-k 10
    python query-nuclei-weaviate-MiniLM-L6.py --interactive
"""

from __future__ import annotations

import argparse
import json
import sys

import weaviate
from sentence_transformers import SentenceTransformer


# ──────────────────────────────────────────────────────────────────────
# Configuration
# ──────────────────────────────────────────────────────────────────────
WEAVIATE_URL = "http://localhost:8080"
CLASS_NAME = "NucleiFinding"

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
TOP_K_DEFAULT = 5


# ──────────────────────────────────────────────────────────────────────
# Weaviate
# ──────────────────────────────────────────────────────────────────────
def get_client():
    return weaviate.connect_to_local()


# ──────────────────────────────────────────────────────────────────────
# Display helpers (IDENTICAL STYLE)
# ──────────────────────────────────────────────────────────────────────
SEPARATOR = "=" * 80
THIN_SEP = "-" * 60


def print_header(question: str, count: int):
    print(f"\n{SEPARATOR}")
    print(f"  Query: {question}")
    print(f"  Results: {count}")
    print(SEPARATOR)


def print_result(rank: int, obj):
    props = obj.properties
    score = obj.metadata.distance if obj.metadata else 0.0

    # metadata stored as JSON string
    metadata = {}
    if props.get("metadata"):
        try:
            metadata = json.loads(props.get("metadata"))
        except:
            pass

    template = props.get("template", "unknown")
    severity = props.get("severity", "unknown")
    target = props.get("target", "?")
    protocol = props.get("protocol", "")

    print(f"\n  [{rank}]  {template}   —   score: {score:.4f}")
    print(f"  {THIN_SEP}")
    print(f"  Severity  : {severity}")
    print(f"  Target    : {target}")
    print(f"  Protocol  : {protocol}")

    if metadata:
        print(f"  Metadata  : {metadata}")

    print()


def print_no_results():
    print("\n  No matching findings found.\n")


# ──────────────────────────────────────────────────────────────────────
# Query logic
# ──────────────────────────────────────────────────────────────────────
def query(question: str, model: SentenceTransformer, client, top_k: int = TOP_K_DEFAULT):
    q_embedding = model.encode(question).tolist()

    collection = client.collections.get(CLASS_NAME)

    results = collection.query.near_vector(
        near_vector=q_embedding,
        limit=top_k,
        return_metadata=["distance"]
    )

    objects = results.objects

    if not objects:
        print_no_results()
        return

    print_header(question, len(objects))

    for i, obj in enumerate(objects, 1):
        print_result(i, obj)


# ──────────────────────────────────────────────────────────────────────
# Interactive mode (IDENTICAL UX)
# ──────────────────────────────────────────────────────────────────────
def interactive(model: SentenceTransformer, client, top_k: int):
    print(SEPARATOR)
    print("  Nuclei Query Console  —  local Weaviate")
    print(f"  Endpoint: {WEAVIATE_URL}  |  Model: {EMBEDDING_MODEL}  |  top-k: {top_k}")
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

        query(user_input, model, client, top_k=current_top_k)


# ──────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Semantic search over Nuclei findings in Weaviate."
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

    print(f"Connecting to Weaviate at {WEAVIATE_URL} …")
    client = get_client()

    if args.interactive:
        interactive(model, client, args.top_k)
    else:
        query(args.question, model, client, args.top_k)

    client.close()


if __name__ == "__main__":
    main()