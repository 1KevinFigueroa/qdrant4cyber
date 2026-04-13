#!/usr/bin/env python3
"""
query_nmap_milvus_hybrid.py — Hybrid semantic + filter search

Examples:
    python query_nmap_milvus_hybrid.py "ssh servers"
    python query_nmap_milvus_hybrid.py "ssh servers" --filter 'os == "Linux"'
    python query_nmap_milvus_hybrid.py --interactive
"""

from __future__ import annotations

import argparse
import sys

from sentence_transformers import SentenceTransformer
from pymilvus import connections, Collection

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
MILVUS_HOST = "localhost"
MILVUS_PORT = "19530"
COLLECTION_NAME = "nmap_test"

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
TOP_K_DEFAULT = 5


# ─────────────────────────────────────────────
# CONNECTION
# ─────────────────────────────────────────────
def get_collection():
    connections.connect("default", host=MILVUS_HOST, port=MILVUS_PORT)
    collection = Collection(COLLECTION_NAME)
    collection.load()
    return collection


# ─────────────────────────────────────────────
# DISPLAY
# ─────────────────────────────────────────────
SEPARATOR = "=" * 80
THIN_SEP = "-" * 60


def print_header(question: str, count: int, expr: str | None):
    print(f"\n{SEPARATOR}")
    print(f"  Query: {question}")
    print(f"  Results: {count}")
    if expr:
        print(f"  Filter: {expr}")
    print(SEPARATOR)


def print_result(rank: int, hit):
    entity = hit.entity
    score = hit.distance

    print(f"\n  [{rank}] score: {score:.4f}")
    print(f"  {THIN_SEP}")

    print(f"    IP: {entity.get('ip')}")
    print(f"    OS: {entity.get('os')}")

    text = entity.get("text")
    if text:
        for line in text.split("\n"):
            print(f"    {line}")

    print()


def print_no_results():
    print("\n  No matching hosts found.\n")


# ─────────────────────────────────────────────
# QUERY (HYBRID)
# ─────────────────────────────────────────────
import re

def fix_filter(expr: str | None) -> str | None:
    if not expr:
        return expr

    # Auto-quote IP addresses if missing quotes
    expr = re.sub(
        r'ip\s*==\s*([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)',
        r'ip == "\1"',
        expr
    )

    return expr

def query(question, model, collection, top_k, expr=None):
    q_embedding = model.encode([question])[0].tolist()

    # 🔥 APPLY FIX HERE
    expr = fix_filter(expr)

    search_params = {
        "metric_type": "COSINE",
        "params": {"nprobe": 10}
    }

    results = collection.search(
        data=[q_embedding],
        anns_field="embedding",
        param=search_params,
        limit=top_k,
        expr=expr,
        output_fields=["text", "ip", "hostname", "os"]
    )

    hits = results[0]

    if not hits:
        print_no_results()
        return

    print_header(question, len(hits), expr)

    for i, hit in enumerate(hits, 1):
        print_result(i, hit)


# ─────────────────────────────────────────────
# INTERACTIVE MODE (WITH FILTERS)
# ─────────────────────────────────────────────
def interactive(model, collection, top_k):
    print(SEPARATOR)
    print("  Nmap Hybrid Search — Milvus")
    print(f"  Collection: {COLLECTION_NAME}")
    print(f"  Model: {EMBEDDING_MODEL} | top-k: {top_k}")
    print("  Commands:")
    print("    :k <n>        change top-k")
    print("    :f <expr>     set filter")
    print("    :clear        clear filter")
    print("    :quit         exit")
    print(SEPARATOR)

    current_top_k = top_k
    current_filter = None

    while True:
        try:
            user_input = input("\nnmap-query> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not user_input:
            continue

        if user_input.lower() in (":quit", ":exit", ":q"):
            print("Goodbye.")
            break

        if user_input.startswith(":k "):
            try:
                current_top_k = int(user_input.split()[1])
                print(f"  top-k = {current_top_k}")
            except:
                print("  Usage: :k <number>")
            continue

        if user_input.startswith(":f "):
            current_filter = user_input[3:].strip()
            print(f"  filter set to: {current_filter}")
            continue

        if user_input == ":clear":
            current_filter = None
            print("  filter cleared")
            continue

        query(user_input, model, collection, current_top_k, expr=current_filter)


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Hybrid semantic + filter search in Milvus"
    )

    parser.add_argument("question", nargs="?", default=None)
    parser.add_argument("--top-k", "-k", type=int, default=TOP_K_DEFAULT)
    parser.add_argument("--filter", "-f", type=str, default=None)
    parser.add_argument("--interactive", "-i", action="store_true")

    args = parser.parse_args()

    if not args.question and not args.interactive:
        parser.print_help()
        sys.exit(0)

    print(f"[INFO] Loading model: {EMBEDDING_MODEL}")
    model = SentenceTransformer(EMBEDDING_MODEL)

    print(f"[INFO] Connecting to Milvus...")
    collection = get_collection()

    if args.interactive:
        interactive(model, collection, args.top_k)
    else:
        query(args.question, model, collection, args.top_k, expr=args.filter)


if __name__ == "__main__":
    main()