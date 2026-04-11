#!/usr/bin/env python3
"""
convert3r_wpscan.py - Read WPScan JSON and add ID as FIRST field in each record,
with optional sentence embeddings.

Usage:
  python convert3r_wpscan.py [-h] [--embed] [-o OUTPUT_FILE] input_file
"""

import argparse
import json
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any, Dict, List

try:
    import torch
    from sentence_transformers import SentenceTransformer
except ImportError:
    torch = None
    SentenceTransformer = None

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def load_records(input_file: str) -> List[Dict[str, Any]]:
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        return data
    return [data]


def build_embeddings(texts: List[str], model_name: str = DEFAULT_MODEL) -> List[List[float]]:
    if torch is None or SentenceTransformer is None:
        raise ImportError("Missing dependencies. Install with: pip install sentence-transformers torch")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = SentenceTransformer(model_name, device=device)
    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        batch_size=32,
        show_progress_bar=True,
    )
    return embeddings.tolist()


def record_to_text(record: Dict[str, Any]) -> str:
    return json.dumps(record, ensure_ascii=False, sort_keys=True, default=str)


def add_id_first_wpscan(data: List[Dict[str, Any]], embeds: List[List[float]] | None = None) -> List[OrderedDict]:
    results = []

    for i, record in enumerate(data):
        ordered = OrderedDict([("id", i + 1)])

        for key, value in record.items():
            ordered[key] = value

        if embeds is not None:
            ordered["embed"] = embeds[i]

        results.append(ordered)

    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="convert3r_wpscan.py",
        description="Add ID (first field) to WPScan JSON records with optional embeddings",
    )
    parser.add_argument("input_file", help="Input WPScan JSON file")
    parser.add_argument("-o", "--output-file", dest="output_file", help="Output JSON file")
    parser.add_argument("--embed", action="store_true", help="Add sentence-transformer embeddings to each record")

    args = parser.parse_args()

    try:
        records = load_records(args.input_file)

        embeds = None
        if args.embed:
            texts = [record_to_text(r) for r in records]
            embeds = build_embeddings(texts)

        records_with_id = add_id_first_wpscan(records, embeds=embeds)

        output_path = Path(args.output_file) if args.output_file else Path(args.input_file).with_suffix(".json")
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(records_with_id, f, indent=2, ensure_ascii=False, default=str)

        print(f"✓ Processed {len(records_with_id)} records")
        print(f"  Input:  {args.input_file}")
        print(f"  Output: {output_path}")

        if records_with_id:
            print("\nSample (first record):")
            print(json.dumps(records_with_id[0], indent=2, ensure_ascii=False, default=str))

    except FileNotFoundError:
        print(f"❌ Error: '{args.input_file}' not found", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in '{args.input_file}': {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()