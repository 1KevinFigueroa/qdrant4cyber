#!/usr/bin/env python3
"""
ChromaDB Query Examples for Nuclei Data
---------------------------------------
Query the 'nuclei-import' collection for findings.

Prerequisites:
- Run nuclei_to_chromadb.py first
- pip install chromadb
"""

import argparse
import os
import chromadb


# =========================
# Helpers
# =========================

def print_section(title):
    print("\n" + "="*70)
    print(title)
    print("="*70)


# =========================
# Query Functions
# =========================

def query_high_severity(collection):
    print_section("Query 1: High Severity Findings")

    results = collection.get(
        where={"severity": "high"},
        limit=5
    )

    if results["documents"]:
        for i, (doc, meta) in enumerate(zip(results["documents"], results["metadatas"]), 1):
            print(f"\n[{i}] {meta.get('target')}")
            print(f"  Severity: {meta.get('severity')}")
            print(f"  Template: {meta.get('template')}")
    else:
        print("No high severity findings found")


def query_web_vulns(collection):
    print_section("Query 2: Web Vulnerabilities")

    results = collection.query(
        query_texts=["web vulnerability http misconfiguration"],
        n_results=5
    )

    if results["documents"] and results["documents"][0]:
        for i, (doc, meta) in enumerate(zip(results["documents"][0], results["metadatas"][0]), 1):
            print(f"\n[{i}] {meta.get('target')}")
            print(f"  Severity: {meta.get('severity')}")
            print(f"  Template: {meta.get('template')}")
    else:
        print("No results found")


def query_specific_template(collection):
    print_section("Query 3: Specific Template Search")

    results = collection.query(
        query_texts=["phpinfo exposed"],
        n_results=5
    )

    if results["documents"][0]:
        for i, (doc, meta) in enumerate(zip(results["documents"][0], results["metadatas"][0]), 1):
            print(f"\n[{i}] {meta.get('target')}")
            print(f"  Template: {meta.get('template')}")
    else:
        print("No matches found")


def query_targets(collection):
    print_section("Query 4: All Targets Summary")

    results = collection.get(limit=20)

    if results["documents"]:
        print(f"\n{'Target':<30} {'Severity':<10} {'Template'}")
        print("-"*70)

        for meta in results["metadatas"]:
            target = meta.get("target", "N/A")[:28]
            severity = meta.get("severity", "N/A")
            template = meta.get("template", "N/A")[:25]

            print(f"{target:<30} {severity:<10} {template}")
    else:
        print("No results")


def query_by_severity(collection):
    print_section("Query 5: Medium Severity Findings")

    results = collection.get(
        where={"severity": "medium"},
        limit=5
    )

    if results["documents"]:
        for i, (doc, meta) in enumerate(zip(results["documents"], results["metadatas"]), 1):
            print(f"\n[{i}] {meta.get('target')}")
            print(f"  Template: {meta.get('template')}")
    else:
        print("No medium findings")


def custom_query(collection):
    print_section("Query 6: Custom - Security Headers")

    results = collection.query(
        query_texts=["missing security headers"],
        n_results=5
    )

    if results["documents"][0]:
        for i, (doc, meta) in enumerate(zip(results["documents"][0], results["metadatas"][0]), 1):
            print(f"\n[{i}] {meta.get('target')}")
            print(f"  Severity: {meta.get('severity')}")
            print(f"  Template: {meta.get('template')}")
    else:
        print("No results")


# =========================
# Interactive Mode
# =========================

def interactive_mode(collection):
    print_section("Interactive Query Mode")
    print(f"Collection: nuclei-import ({collection.count()} docs)\n")

    n_results = 5

    while True:
        try:
            q = input(f"nuclei-query [k={n_results}]> ").strip()
        except:
            break

        if not q:
            continue

        if q in [":q", ":quit"]:
            break

        if q.startswith(":k"):
            try:
                n_results = int(q.split()[1])
                print(f"✓ Results set to {n_results}")
            except:
                print("Usage: :k <number>")
            continue

        if q == ":count":
            print(f"Total: {collection.count()}")
            continue

        if q.startswith(":severity"):
            try:
                sev = q.split()[1]
                results = collection.get(where={"severity": sev}, limit=n_results)

                for meta in results["metadatas"]:
                    print(f"{meta.get('target')} [{meta.get('severity')}]")
            except:
                print("Usage: :severity <low|medium|high|info>")
            continue

        # default semantic query
        results = collection.query(
            query_texts=[q],
            n_results=n_results
        )

        if results["documents"][0]:
            for i, (doc, meta, dist) in enumerate(
                zip(results["documents"][0], results["metadatas"][0], results["distances"][0]), 1
            ):
                print(f"\n[{i}] {meta.get('target')} ({meta.get('severity')}) [score={dist:.4f}]")
                print(f"  Template: {meta.get('template')}")

        else:
            print("No results")


# =========================
# Main
# =========================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--interactive", action="store_true")
    args = parser.parse_args()

    print("\nConnecting to ChromaDB...")

    client = chromadb.HttpClient(
        host=os.getenv("CHROMADB_HOST", "localhost"),
        port=int(os.getenv("CHROMADB_PORT", "9000")),
        headers={"Authorization": "Bearer my-secret-token"}
    )

    collection = client.get_collection("nuclei-import")

    print(f"✓ Loaded collection 'nuclei-import'")
    print(f"✓ Documents: {collection.count()}")

    if args.interactive:
        interactive_mode(collection)
    else:
        query_high_severity(collection)
        query_web_vulns(collection)
        query_specific_template(collection)
        query_targets(collection)
        query_by_severity(collection)
        custom_query(collection)

        print("\nDone. Use -i for interactive mode.\n")


if __name__ == "__main__":
    main()