#!/usr/bin/env python3
"""
query-nmap-pinecone-MiniLM-L6.py — Semantic search over nmap scan data stored in a local
Pinecone index (Docker).

Uses the same 'all-MiniLM-L6-v2' embedding model as nmap_ingest.py to
encode your question, then returns the most relevant hosts via cosine
similarity.

Requirements:
    pip install pinecone[grpc] sentence-transformers

Prerequisites:
    1. Local Pinecone Docker container running (DIMENSION=384, METRIC=cosine)
    2. Data already ingested via nmap_ingest.py

Environment variables (optional):
    PINECONE_HOST  – local index URL (default: "http://localhost:5081")

Usage:
    # One-shot query
    python query-nmap-pinecone-MiniLM-L6.py "hosts running Redis"

    # Return more results
    python query-nmap-pinecone-MiniLM-L6.py "Windows servers" --top-k 10

    # Interactive mode — ask multiple questions in a session
    python query-nmap-pinecone-MiniLM-L6.py --interactive

    Inside the interactive session you can type :k 10 to change the number of results or :quit to exit.
"""

from __future__ import annotations

import argparse
import os
import sys

from sentence_transformers import SentenceTransformer
from pinecone import Pinecone

# ──────────────────────────────────────────────────────────────────────
# Configuration  (must match nmap_ingest.py)
# ──────────────────────────────────────────────────────────────────────
PINECONE_HOST = os.environ.get("PINECONE_HOST", "http://localhost:5081")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"  # 384 dimensions
TOP_K_DEFAULT = 5


# ──────────────────────────────────────────────────────────────────────
# Pinecone connection (local Docker — pinecone-index image)
# ──────────────────────────────────────────────────────────────────────
def get_index():
    """Return a handle to the local Pinecone index."""
    pc = Pinecone(api_key="pclocal")
    return pc.Index(host=PINECONE_HOST)


# ──────────────────────────────────────────────────────────────────────
# Display helpers
# ──────────────────────────────────────────────────────────────────────
SEPARATOR = "=" * 80
THIN_SEP = "-" * 60


def print_header(question: str, count: int):
    print(f"\n{SEPARATOR}")
    print(f"  Query: {question}")
    print(f"  Results: {count}")
    print(SEPARATOR)


def print_result(rank: int, match: dict):
    meta = match.get("metadata", {})
    score = match.get("score", 0.0)

    ip = meta.get("ip", "?")
    hostname = meta.get("hostname", "")
    os_name = meta.get("os", "unknown")
    port_count = meta.get("port_count", 0)
    services = meta.get("services", [])
    products = meta.get("products", [])

    label = f"{ip} ({hostname})" if hostname else ip

    print(f"\n  [{rank}]  {label}   —   score: {score:.4f}")
    print(f"  {THIN_SEP}")
    print(f"  OS          : {os_name}")
    print(f"  Open ports  : {port_count}")
    if services:
        print(f"  Services    : {', '.join(services)}")
    if products:
        print(f"  Products    : {', '.join(products)}")

    # Show full text description if available
    text = meta.get("text", "")
    if text:
        print()
        for line in text.split("\n"):
            print(f"    {line}")
    print()


def print_no_results():
    print("\n  No matching hosts found.\n")


# ──────────────────────────────────────────────────────────────────────
# Query logic
# ──────────────────────────────────────────────────────────────────────
def query(question: str, model: SentenceTransformer, index, top_k: int = TOP_K_DEFAULT):
    """Embed a question and return the closest host records from Pinecone."""
    q_embedding = model.encode([question])[0].tolist()

    results = index.query(
        vector=q_embedding,
        top_k=top_k,
        include_metadata=True,
    )

    matches = results.get("matches", [])
    if not matches:
        print_no_results()
        return

    print_header(question, len(matches))
    for i, match in enumerate(matches, 1):
        print_result(i, match)


# ──────────────────────────────────────────────────────────────────────
# Interactive REPL
# ──────────────────────────────────────────────────────────────────────
def interactive(model: SentenceTransformer, index, top_k: int):
    """Run an interactive query loop."""
    print(SEPARATOR)
    print("  nmap Query Console  —  local Pinecone")
    print(f"  Index: {PINECONE_HOST}  |  Model: {EMBEDDING_MODEL}  |  top-k: {top_k}")
    print(f"  Type a question and press Enter. Commands:")
    print(f"    :k <n>    change top-k    (e.g.  :k 10)")
    print(f"    :quit     exit")
    print(SEPARATOR)

    current_top_k = top_k

    while True:
        try:
            user_input = input("\nnmap-query> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if not user_input:
            continue

        # Commands
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
            except (ValueError, IndexError):
                print("  Usage: :k <number>  (e.g. :k 10)")
            continue

        query(user_input, model, index, top_k=current_top_k)


# ──────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(
        description="Semantic search over nmap scan data in a local Pinecone index.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  python query-nmap-pinecone-MiniLM-L6.py "hosts running Redis"
  python query-nmap-pinecone-MiniLM-L6.py "databases exposed on the network"
  python query-nmap-pinecone-MiniLM-L6.py "Windows servers with SQL Server" --top-k 10
  python query-nmap-pinecone-MiniLM-L6.py "web servers on port 443"
  python query-nmap-pinecone-MiniLM-L6.py "hosts with Kubernetes or Docker"
  python query-nmap-pinecone-MiniLM-L6.py --interactive
  python query-nmap-pinecone-MiniLM-L6.py --interactive --top-k 3
  python query-nmap-pinecone-MiniLM-L6.py -i
    [Inside the interactive session you can type the following ] 
    [ :k 10 to change the number of results ]
    [ :quit to exit ]
""",
    )
    parser.add_argument(
        "question",
        nargs="?",
        default=None,
        help="Natural-language query (omit for interactive mode)",
    )
    parser.add_argument(
        "--top-k", "-k",
        type=int,
        default=TOP_K_DEFAULT,
        help=f"Number of results to return (default: {TOP_K_DEFAULT})",
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Start an interactive query session",
    )

    args = parser.parse_args()

    if not args.question and not args.interactive:
        parser.print_help()
        sys.exit(0)

    # Load model once
    print(f"Loading embedding model '{EMBEDDING_MODEL}' …")
    model = SentenceTransformer(EMBEDDING_MODEL)

    # Connect to local Pinecone
    print(f"Connecting to local Pinecone index at {PINECONE_HOST} …")
    index = get_index()

    if args.interactive:
        interactive(model, index, top_k=args.top_k)
    else:
        query(args.question, model, index, top_k=args.top_k)


if __name__ == "__main__":
    main()
