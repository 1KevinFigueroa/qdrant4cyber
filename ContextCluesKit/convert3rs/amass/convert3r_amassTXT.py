#!/usr/bin/env python3
import argparse
import json
import os
from typing import List, Dict, Any

from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"


def parse_file(input_file: str) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    entry_id = 1

    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            domain = line.strip()
            if not domain:
                continue
            if domain.startswith("-"):
                domain = domain.lstrip("-").strip()
            if not domain:
                continue

            records.append({
                "id": entry_id,
                "domain": domain,
            })
            entry_id += 1

    return records


def embed_records(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    model = SentenceTransformer(MODEL_NAME)
    for record in records:
        text = record["domain"]
        record["embedding_text"] = text
        record["vector"] = model.encode(text, normalize_embeddings=True).tolist()
    return records


def main():
    parser = argparse.ArgumentParser(
        prog="convert3r_amass.py",
        description="Convert Amass domain output into JSON.",
    )
    parser.add_argument(
        "-o",
        "--output-file",
        default=None,
        help="Path to the output JSON file. Defaults to <input_file>.json",
    )
    parser.add_argument(
        "--embed",
        action="store_true",
        help="Generate vector embeddings for each domain using all-MiniLM-L6-v2",
    )
    parser.add_argument(
        "input_file",
        help="Path to the Amass output text file.",
    )

    args = parser.parse_args()

    output_file = args.output_file
    if output_file is None:
        base, _ = os.path.splitext(args.input_file)
        output_file = f"{base}.json"

    records = parse_file(args.input_file)
    if args.embed:
        records = embed_records(records)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=4)

    print(f"✓ Parsed {len(records)} domains")
    print(f"✓ Wrote JSON to {output_file}")


if __name__ == "__main__":
    main()