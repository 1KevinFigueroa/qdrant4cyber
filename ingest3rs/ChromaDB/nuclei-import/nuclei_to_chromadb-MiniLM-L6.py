"""
Nuclei JSON to ChromaDB Importer
--------------------------------
This script imports Nuclei scan results from a JSON file into a ChromaDB collection.

Usage:
    python nuclei_to_chromadb.py <json_file_path>

Example:
    python nuclei_to_chromadb.py nuclei-results.json
"""

import sys
import json
import argparse
import os
from pathlib import Path
import chromadb


# =========================
# Utility Functions
# =========================

def print_usage():
    print("\n" + "="*70)
    print("Nuclei JSON to ChromaDB Importer")
    print("="*70)
    print("\nUsage:")
    print("    python nuclei_to_chromadb.py <json_file_path>")
    print("\nExample:")
    print("    python nuclei_to_chromadb.py nuclei-results.json")
    print("="*70 + "\n")


def validate_json_file(file_path):
    path = Path(file_path)

    if not path.exists():
        print(f"❌ File does not exist: {file_path}")
        return False

    if not path.is_file():
        print(f"❌ Not a file: {file_path}")
        return False

    return True


def load_json_data(file_path):
    try:
        with open(file_path, "r") as f:
            data = json.load(f)

        print(f"✓ Loaded JSON file: {file_path}")
        return data

    except Exception as e:
        print(f"❌ Failed to load JSON: {e}")
        return None


# =========================
# Nuclei Parsing Logic
# =========================

def extract_finding_info(entry):
    """Extract structured info from a Nuclei finding"""
    return {
        "id": entry.get("id"),
        "template": entry.get("template"),
        "severity": entry.get("severity"),
        "protocol": entry.get("protocol"),
        "target": entry.get("target"),
        "extra_info": entry.get("extra_info"),
        "entry_type": entry.get("entry_type")
    }


def create_document_text(finding):
    """Create searchable text blob"""
    parts = []

    parts.append(f"Target: {finding.get('target', 'unknown')}")
    parts.append(f"Template: {finding.get('template', 'unknown')}")
    parts.append(f"Severity: {finding.get('severity', 'unknown')}")
    parts.append(f"Protocol: {finding.get('protocol', 'unknown')}")

    if finding.get("entry_type"):
        parts.append(f"Type: {finding.get('entry_type')}")

    if finding.get("extra_info"):
        parts.append(f"Extra Info: {finding.get('extra_info')}")

    return "\n".join(parts)


# =========================
# ChromaDB Import
# =========================

def import_to_chromadb(data):
    try:
        chromadb_host = os.getenv("CHROMADB_HOST", "localhost")
        chromadb_port = int(os.getenv("CHROMADB_PORT", "9000"))

        client = chromadb.HttpClient(
            host=chromadb_host,
            port=chromadb_port,
            headers={"Authorization": "Bearer my-secret-token"}
        )

        collection_name = "nuclei-import"

        try:
            collection = client.get_collection(name=collection_name)
            print(f"✓ Using existing collection '{collection_name}'")
        except:
            collection = client.create_collection(name=collection_name)
            print(f"✓ Created collection '{collection_name}'")

        if not isinstance(data, list):
            print("❌ Expected JSON array of findings")
            return False

        print(f"\n📊 Processing {len(data)} findings...")

        documents = []
        metadatas = []
        ids = []

        for idx, entry in enumerate(data):
            finding = extract_finding_info(entry)

            # Document text
            doc_text = create_document_text(finding)
            documents.append(doc_text)

            # Metadata (flat only)
            metadata = {
                "severity": finding.get("severity", "unknown"),
                "template": finding.get("template", "unknown"),
                "protocol": finding.get("protocol", "unknown"),
                "target": finding.get("target", "unknown")
            }

            if finding.get("entry_type"):
                metadata["entry_type"] = finding["entry_type"]

            metadatas.append(metadata)

            # Unique ID
            safe_target = finding.get("target", "unknown").replace("http://", "").replace("https://", "").replace("/", "_")
            ids.append(f"finding_{idx}_{safe_target}")

        # Insert into ChromaDB
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )

        print(f"\n✅ Imported {len(documents)} findings into '{collection_name}'")

        # Summary
        print("\n" + "="*70)
        print("Import Summary")
        print("="*70)
        print(f"Collection: {collection_name}")
        print(f"Total findings: {len(documents)}")

        severities = {}
        for f in data:
            sev = f.get("severity", "unknown")
            severities[sev] = severities.get(sev, 0) + 1

        print("\nSeverity Breakdown:")
        for k, v in severities.items():
            print(f"  {k}: {v}")

        print(f"\nTotal documents in DB: {collection.count()}")
        print("="*70)

        print("\n💡 Example query:")
        print("results = collection.query(query_texts=['missing security headers'], n_results=5)")

        return True

    except Exception as e:
        print(f"\n❌ Error importing: {e}")
        import traceback
        traceback.print_exc()
        return False


# =========================
# Main
# =========================

def main():
    parser = argparse.ArgumentParser(
        description="Import Nuclei JSON results into ChromaDB"
    )
    parser.add_argument("json_file", nargs="?", help="Path to nuclei JSON file")

    args = parser.parse_args()

    if not args.json_file:
        print_usage()
        sys.exit(1)

    if not validate_json_file(args.json_file):
        sys.exit(1)

    data = load_json_data(args.json_file)
    if data is None:
        sys.exit(1)

    success = import_to_chromadb(data)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()