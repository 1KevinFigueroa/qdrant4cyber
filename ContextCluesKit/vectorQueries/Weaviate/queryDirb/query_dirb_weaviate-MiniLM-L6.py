#!/usr/bin/env python3
"""
Weaviate Query Script for DIRB Findings
----------------------------------------
This script queries the 'DirbFinding' collection in Weaviate
and retrieves directories, files, and paths discovered by DIRB.

Prerequisites:
- Run ingest_dirb_to_weaviate.py first to import your DIRB data
- Weaviate must be running (default: localhost:8080)
"""

import argparse
import sys

import weaviate
from weaviate.classes.query import Filter


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


# =========================================================
# CANNED QUERIES
# =========================================================

def query_directories(collection):
    """Query for discovered directories."""
    print_section("Query 1: Listable Directories")

    results = collection.query.fetch_objects(
        filters=Filter.by_property("finding_type").equal("directory"),
        limit=10
    )

    if results.objects:
        print(f"\n  Found {len(results.objects)} directories\n")
        print(f"  {'Path':<45} {'Host'}")
        print(f"  {'-' * 65}")
        for obj in results.objects:
            p = obj.properties
            print(f"  {p.get('path', 'N/A'):<45} {p.get('host', 'N/A')}")
    else:
        print("  No directories found")


def query_files(collection):
    """Query for discovered files."""
    print_section("Query 2: Discovered Files")

    results = collection.query.fetch_objects(
        filters=Filter.by_property("finding_type").equal("file"),
        limit=10
    )

    if results.objects:
        print(f"\n  Found {len(results.objects)} files\n")
        print(f"  {'Path':<40} {'Code':<6} {'Size':<8} {'Host'}")
        print(f"  {'-' * 75}")
        for obj in results.objects:
            p = obj.properties
            print(
                f"  {p.get('path', 'N/A'):<40} "
                f"{p.get('http_code', 'N/A'):<6} "
                f"{p.get('response_size', 'N/A'):<8} "
                f"{p.get('host', 'N/A')}"
            )
    else:
        print("  No files found")


def query_interesting_codes(collection):
    """Query for non-200 HTTP response codes."""
    print_section("Query 3: Non-200 HTTP Response Codes")

    results = collection.query.fetch_objects(
        filters=(
            Filter.by_property("http_code").not_equal(200)
            & Filter.by_property("http_code").not_equal(0)
        ),
        limit=10
    )

    if results.objects:
        for i, obj in enumerate(results.objects, 1):
            p = obj.properties
            print(f"\n  [{i}] {p.get('url', 'N/A')}")
            print(f"      HTTP {p.get('http_code', '?')} | Size: {p.get('response_size', '?')}")
    else:
        print("  All findings returned HTTP 200")


def query_sql_paths(collection):
    """Semantic search for SQL injection related paths."""
    print_section("Query 4: SQL Injection Related Paths")

    results = collection.query.near_text(
        query="SQL injection database",
        limit=5
    )

    if results.objects:
        for i, obj in enumerate(results.objects, 1):
            p = obj.properties
            print(f"\n  [{i}] {p.get('url', 'N/A')}")
            print(f"      Type: {p.get('finding_type', '?')} | HTTP {p.get('http_code', '?')}")
    else:
        print("  No SQL-related paths found")


def query_admin_paths(collection):
    """Semantic search for admin/config paths."""
    print_section("Query 5: Admin and Configuration Paths")

    results = collection.query.near_text(
        query="admin configuration setup management login",
        limit=5
    )

    if results.objects:
        for i, obj in enumerate(results.objects, 1):
            p = obj.properties
            print(f"\n  [{i}] {p.get('url', 'N/A')}")
            print(f"      Type: {p.get('finding_type', '?')} | HTTP {p.get('http_code', '?')}")
    else:
        print("  No admin/config paths found")


def query_upload_paths(collection):
    """Semantic search for upload/file upload paths."""
    print_section("Query 6: Upload and File Handling Paths")

    results = collection.query.near_text(
        query="upload file upload image upload media",
        limit=5
    )

    if results.objects:
        for i, obj in enumerate(results.objects, 1):
            p = obj.properties
            print(f"\n  [{i}] {p.get('url', 'N/A')}")
            print(f"      Type: {p.get('finding_type', '?')} | HTTP {p.get('http_code', '?')}")
    else:
        print("  No upload paths found")


# =========================================================
# INTERACTIVE MODE
# =========================================================

def interactive_mode(collection):
    """Run an interactive query session against the DIRB collection."""
    print_section("Interactive Query Mode")

    total = collection.aggregate.over_all(total_count=True).total_count
    print(f"Collection: 'DirbFinding' ({total} objects)")

    print("\nCommands:")
    print("  <query>           Semantic search for paths/directories")
    print("  :k <number>       Set number of results (default: 5)")
    print("  :dirs             List all directories")
    print("  :files            List all discovered files")
    print("  :host <host>      Filter findings by host")
    print("  :code <code>      Filter findings by HTTP status code")
    print("  :count            Show total finding count")
    print("  :stats            Show summary statistics")
    print("  :help             Show this help message")
    print("  :quit / :q        Exit interactive mode")
    print()

    n_results = 5

    while True:
        try:
            user_input = input(f"dirb-query [k={n_results}]> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting interactive mode.")
            break

        if not user_input:
            continue

        # --- :quit ---
        if user_input.lower() in (":quit", ":q", ":exit"):
            print("Exiting interactive mode.")
            break

        # --- :help ---
        if user_input.lower() == ":help":
            print("\nCommands:")
            print(f"  <query>           Semantic search for paths/directories")
            print(f"  :k <number>       Set number of results (current: {n_results})")
            print(f"  :dirs             List all directories")
            print(f"  :files            List all discovered files")
            print(f"  :host <host>      Filter findings by host")
            print(f"  :code <code>      Filter findings by HTTP status code")
            print(f"  :count            Show total finding count")
            print(f"  :stats            Show summary statistics")
            print(f"  :help             Show this help message")
            print(f"  :quit / :q        Exit interactive mode")
            continue

        # --- :k ---
        if user_input.lower().startswith(":k "):
            try:
                new_k = int(user_input.split()[1])
                if new_k < 1:
                    print("  ⚠ Number of results must be at least 1")
                    continue
                n_results = new_k
                print(f"  ✓ Results per query set to {n_results}")
            except (ValueError, IndexError):
                print("  ⚠ Usage: :k <number>  (e.g. :k 10)")
            continue

        # --- :count ---
        if user_input.lower() == ":count":
            total = collection.aggregate.over_all(total_count=True).total_count
            print(f"  Total findings: {total}")
            continue

        # --- :stats ---
        if user_input.lower() == ":stats":
            total = collection.aggregate.over_all(total_count=True).total_count

            dirs = collection.query.fetch_objects(
                filters=Filter.by_property("finding_type").equal("directory"),
                limit=1000
            )
            files = collection.query.fetch_objects(
                filters=Filter.by_property("finding_type").equal("file"),
                limit=1000
            )

            dir_count = len(dirs.objects)
            file_count = len(files.objects)

            # Collect unique hosts
            hosts = set()
            all_results = collection.query.fetch_objects(limit=1000)
            for obj in all_results.objects:
                h = obj.properties.get("host", "")
                if h:
                    hosts.add(h)

            print(f"\n  Total findings:  {total}")
            print(f"  Directories:     {dir_count}")
            print(f"  Files:           {file_count}")
            print(f"  Unique hosts:    {len(hosts)}")
            if hosts:
                for h in sorted(hosts):
                    print(f"    - {h}")
            continue

        # --- :dirs ---
        if user_input.lower() == ":dirs":
            results = collection.query.fetch_objects(
                filters=Filter.by_property("finding_type").equal("directory"),
                limit=100
            )
            if results.objects:
                print(f"\n  Found {len(results.objects)} directories\n")
                print(f"  {'Path':<50} {'Host'}")
                print(f"  {'-' * 70}")
                for obj in results.objects:
                    p = obj.properties
                    print(f"  {p.get('path', 'N/A'):<50} {p.get('host', 'N/A')}")
            else:
                print("  No directories found")
            continue

        # --- :files ---
        if user_input.lower() == ":files":
            results = collection.query.fetch_objects(
                filters=Filter.by_property("finding_type").equal("file"),
                limit=100
            )
            if results.objects:
                print(f"\n  Found {len(results.objects)} files\n")
                print(f"  {'Path':<40} {'Code':<6} {'Size':<8} {'Host'}")
                print(f"  {'-' * 75}")
                for obj in results.objects:
                    p = obj.properties
                    print(
                        f"  {p.get('path', 'N/A'):<40} "
                        f"{p.get('http_code', '?'):<6} "
                        f"{p.get('response_size', '?'):<8} "
                        f"{p.get('host', 'N/A')}"
                    )
            else:
                print("  No files found")
            continue

        # --- :host <host> ---
        if user_input.lower().startswith(":host"):
            parts = user_input.split(maxsplit=1)
            if len(parts) < 2:
                print("  ⚠ Usage: :host <hostname_or_ip>  (e.g. :host 192.168.0.252)")
                continue
            host_filter = parts[1].strip()
            results = collection.query.fetch_objects(
                filters=Filter.by_property("host").equal(host_filter),
                limit=n_results
            )
            if results.objects:
                print(f"\n  Findings for host '{host_filter}':\n")
                for i, obj in enumerate(results.objects, 1):
                    p = obj.properties
                    print(
                        f"  [{i}] {p.get('url', 'N/A')}"
                    )
                    print(
                        f"      Type: {p.get('finding_type', '?')} | "
                        f"HTTP {p.get('http_code', '?')} | "
                        f"Size: {p.get('response_size', '?')}"
                    )
            else:
                print(f"  No findings for host '{host_filter}'")
            continue

        # --- :code <code> ---
        if user_input.lower().startswith(":code"):
            parts = user_input.split()
            if len(parts) < 2:
                print("  ⚠ Usage: :code <http_code>  (e.g. :code 403)")
                continue
            try:
                code_filter = int(parts[1])
            except ValueError:
                print("  ⚠ HTTP code must be a number")
                continue
            results = collection.query.fetch_objects(
                filters=Filter.by_property("http_code").equal(code_filter),
                limit=n_results
            )
            if results.objects:
                print(f"\n  Findings with HTTP {code_filter}:\n")
                for i, obj in enumerate(results.objects, 1):
                    p = obj.properties
                    print(f"  [{i}] {p.get('url', 'N/A')}")
                    print(
                        f"      Type: {p.get('finding_type', '?')} | "
                        f"Size: {p.get('response_size', '?')}"
                    )
            else:
                print(f"  No findings with HTTP {code_filter}")
            continue

        # --- Default: semantic search ---
        results = collection.query.near_text(
            query=user_input,
            limit=n_results
        )

        if results.objects:
            print(f"\n  Top {len(results.objects)} results for '{user_input}':\n")
            for i, obj in enumerate(results.objects, 1):
                p = obj.properties
                print(
                    f"  [{i}] {p.get('url', 'N/A')}"
                )
                print(
                    f"      Type: {p.get('finding_type', '?')} | "
                    f"HTTP {p.get('http_code', '?')} | "
                    f"Size: {p.get('response_size', '?')} | "
                    f"Listable: {p.get('directory_listable', False)}"
                )

                # Highlight matching lines from raw_line
                raw = p.get("raw_line", "")
                query_terms = user_input.lower().split()
                if any(term in raw.lower() for term in query_terms):
                    print(f"      Raw: {raw.strip()}")
            print()
        else:
            print(f"  No results found for '{user_input}'")


# =========================================================
# MAIN
# =========================================================

def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Weaviate Query Script for DIRB Findings"
    )
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Launch interactive query mode"
    )
    parser.add_argument(
        "--host", default="localhost",
        help="Weaviate host (default: localhost)"
    )
    parser.add_argument(
        "--port", type=int, default=8080,
        help="Weaviate HTTP port (default: 8080)"
    )
    parser.add_argument(
        "--grpc-port", type=int, default=50051,
        help="Weaviate gRPC port (default: 50051)"
    )
    parser.add_argument(
        "--collection", default="DirbFinding",
        help="Weaviate collection name (default: DirbFinding)"
    )
    args = parser.parse_args()

    print("\n" + "=" * 70)
    print("Weaviate Query Script - DIRB Findings")
    print("=" * 70)
    print(f"\nConnecting to Weaviate at {args.host}:{args.port}...")

    try:
        client = weaviate.connect_to_local(
            host=args.host,
            port=args.port,
            grpc_port=args.grpc_port,
        )

        collection = client.collections.get(args.collection)
        total = collection.aggregate.over_all(total_count=True).total_count

        print(f"✓ Connected to Weaviate")
        print(f"✓ Collection '{args.collection}' loaded ({total} objects)")

        if args.interactive:
            interactive_mode(collection)
        else:
            # Run all canned queries
            query_directories(collection)
            query_files(collection)
            query_interesting_codes(collection)
            query_sql_paths(collection)
            query_admin_paths(collection)
            query_upload_paths(collection)

            print("\n" + "=" * 70)
            print("Query demonstrations complete!")
            print("=" * 70)
            print("\nTip: Run with -i or --interactive for interactive query mode")
            print("     Example: python query_dirb_weaviate.py -i")
            print()

        client.close()

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nMake sure you have:")
        print("  1. Weaviate running (docker compose up -d)")
        print("  2. Imported DIRB data with ingest_dirb_to_weaviate.py")
        print()


if __name__ == "__main__":
    main()
