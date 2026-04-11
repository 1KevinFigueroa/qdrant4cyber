#!/usr/bin/env python3
"""
Convert text file of domains/subdomains into structured JSON format.

Input: one domain per line
Output:
[
  {"id": 1, "hostname": "example.com", "embed": [...]},
  {"id": 2, "hostname": "sub.example.com", "embed": [...]}
]

Usage:
  python convert3r_subfinderTxt.py [-h] [--embed] [-o OUTPUT_FILE] input_file
"""

import argparse
import json
import os
from typing import List, Dict, Any

try:
    import torch
    from sentence_transformers import SentenceTransformer
except ImportError:
    torch = None
    SentenceTransformer = None


DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def read_domains(input_file: str) -> List[str]:
    with open(input_file, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def build_records(domains: List[str], embed: bool = False, model_name: str = DEFAULT_MODEL) -> List[Dict[str, Any]]:
    records = [{"id": i, "hostname": domain} for i, domain in enumerate(domains, start=1)]

    if embed:
        if torch is None or SentenceTransformer is None:
            raise ImportError(
                "Missing dependencies. Install with: pip install sentence-transformers torch"
            )

        model = SentenceTransformer(model_name)
        embeddings = model.encode(
            domains,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True
        )

        for record, emb in zip(records, embeddings):
            record["embed"] = emb.tolist()

    return records


def write_json(records: List[Dict[str, Any]], output_file: str) -> None:
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(
        prog="convert3r_subfinderTxt.py",
        description="Convert domains/subdomains text file to JSON, optionally with embeddings."
    )
    parser.add_argument("input_file", help="Input text file with one domain per line")
    parser.add_argument("-o", "--output-file", dest="output_file", help="Output JSON file")
    parser.add_argument(
        "--embed",
        action="store_true",
        help="Add sentence-transformer embeddings to each record"
    )

    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        raise FileNotFoundError(f"File not found: {args.input_file}")

    domains = read_domains(args.input_file)

    if args.output_file:
        output_file = args.output_file
    else:
        base_name = os.path.splitext(args.input_file)[0]
        output_file = f"{base_name}.json"

    records = build_records(domains, embed=args.embed)
    write_json(records, output_file)

    print(f"Created {len(records)} records -> {output_file}")


if __name__ == "__main__":
    main()