#!/usr/bin/env python3
"""
query_weaviate_nmap_hybrid.py — Hybrid semantic + filter search (Weaviate)

Examples:
    python query_weaviate_nmap_hybrid.py "ssh servers"
    python query_weaviate_nmap_hybrid.py "kubernetes" --filter 'tags contains k8s_api'
    python query_weaviate_nmap_hybrid.py --interactive
"""

import argparse
import sys
import re
from urllib.parse import urlparse

import weaviate
import weaviate.classes as wvc
from sentence_transformers import SentenceTransformer
from weaviate.classes.query import Filter
from weaviate.exceptions import WeaviateGRPCUnavailableError

# -----------------------------
# CONFIG
# -----------------------------
WEAVIATE_URL = "http://localhost:8080"
CLASS_NAME = "NmapHost"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
TOP_K_DEFAULT = 5

SEPARATOR = "=" * 80
THIN_SEP = "-" * 60


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
# FILTER PARSER
# -----------------------------
def fix_filter(expr):
    if not expr:
        return None

    # Auto-quote IPs
    expr = re.sub(
        r'ip\s*==\s*([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)',
        r'ip == "\1"',
        expr
    )

    return expr


def build_where_filter(expr):
    """
    Convert simple filter syntax → Weaviate filter
    Supported:
        ip == "x.x.x.x"
        tags contains tagname
        os == "Linux"
    """
    if not expr:
        return None

    expr = fix_filter(expr)

    # ip filter
    if "ip ==" in expr:
        value = expr.split("==")[1].strip().strip('"')
        return Filter.by_property("ip").equal(value)

    # os filter
    if "os ==" in expr:
        value = expr.split("==")[1].strip().strip('"')
        return Filter.by_property("os").equal(value)

    # tag filter
    if "tags contains" in expr:
        value = expr.split("contains")[1].strip()
        return Filter.by_property("tags").contains_any([value])

    print("[WARN] Unsupported filter format")
    return None


# -----------------------------
# DISPLAY
# -----------------------------
def print_header(question, count, expr):
    print(f"\n{SEPARATOR}")
    print(f"  Query: {question}")
    print(f"  Results: {count}")
    if expr:
        print(f"  Filter: {expr}")
    print(SEPARATOR)


def print_result(rank, obj):
    score = obj.metadata.score if obj.metadata and obj.metadata.score is not None else 0
    props = obj.properties or {}

    print(f"\n  [{rank}] score: {score:.4f}")
    print(f"  {THIN_SEP}")

    print(f"    IP: {props.get('ip')}")
    print(f"    OS: {props.get('os')}")
    print(f"    Tags: {', '.join(props.get('tags', []))}")

    text = props.get("text", "")
    if text:
        for line in text.split("\n"):
            print(f"    {line}")

    print()


def print_no_results():
    print("\n  No matching hosts found.\n")


# -----------------------------
# QUERY (HYBRID)
# -----------------------------
def query(client, model, question, top_k, expr=None):
    where_filter = build_where_filter(expr)
    collection = client.collections.get(CLASS_NAME)
    query_vector = model.encode(question).tolist()

    result = collection.query.hybrid(
        query=question,
        vector=query_vector,
        alpha=0.5,
        limit=top_k,
        filters=where_filter,
        return_properties=["ip", "hostname", "os", "tags", "text"],
        return_metadata=wvc.query.MetadataQuery(score=True),
    )

    hits = result.objects

    if not hits:
        print_no_results()
        return

    print_header(question, len(hits), expr)

    for i, hit in enumerate(hits, 1):
        print_result(i, hit)


# -----------------------------
# INTERACTIVE MODE
# -----------------------------
def interactive(client, model, top_k):
    print(SEPARATOR)
    print("  Nmap Hybrid Search — Weaviate")
    print(f"  Class: {CLASS_NAME}")
    print(f"  top-k: {top_k}")
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

        query(client, model, user_input, current_top_k, expr=current_filter)


# -----------------------------
# CLI
# -----------------------------
def main():
    parser = argparse.ArgumentParser(
        description="Hybrid semantic + filter search in Weaviate"
    )

    parser.add_argument("question", nargs="?", default=None)
    parser.add_argument("--top-k", "-k", type=int, default=TOP_K_DEFAULT)
    parser.add_argument("--filter", "-f", type=str, default=None)
    parser.add_argument("--interactive", "-i", action="store_true")

    args = parser.parse_args()

    if not args.question and not args.interactive:
        parser.print_help()
        sys.exit(0)

    print("[INFO] Connecting to Weaviate...")
    client = connect()
    print("[INFO] Loading MiniLM model...")
    model = SentenceTransformer(MODEL_NAME)

    try:
        if args.interactive:
            interactive(client, model, args.top_k)
        else:
            query(client, model, args.question, args.top_k, expr=args.filter)
    finally:
        client.close()


if __name__ == "__main__":
    main()