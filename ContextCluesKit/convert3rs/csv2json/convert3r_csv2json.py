#!/usr/bin/env python3
"""
convert3r_csv2jsonEmbed.py - Convert CSV to JSON with optional sentence embeddings

Usage: convert3r_csv2jsonEmbed.py [-h] [-o OUTPUT_FILE] [--embed] input_file
"""

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

try:
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    raise ImportError("sentence-transformers not installed. Install via: pip install sentence-transformers") from e


def load_embedding_model(model_name: str = "all-MiniLM-L6-v2") -> SentenceTransformer:
    model = SentenceTransformer(model_name)
    dummy_vec = model.encode(["test"], convert_to_numpy=False)[0]
    if len(dummy_vec) != 384:
        raise RuntimeError(f"Expected 384-dim, got {len(dummy_vec)} for '{model_name}'")
    return model


def extract_text_fields(row: Dict[str, str]) -> List[str]:
    text_fields = []
    for key, value in row.items():
        if not isinstance(value, str):
            continue
        stripped = value.strip()
        if not stripped or any(not c.isprintable() for c in stripped):
            continue
        text_fields.append(stripped)
    return text_fields


def csv_to_json_with_embeddings(
    csv_path: str,
    json_path: str,
    embed: bool = False,
    batch_size: int = 64
) -> None:
    csv_file = Path(csv_path)
    if not csv_file.is_file():
        raise FileNotFoundError(f"CSV file not found: {csv_file}")

    model = load_embedding_model() if embed else None

    try:
        records: List[Dict[str, Any]] = []
        all_texts: List[str] = []

        with csv_file.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)

            if not reader.fieldnames:
                raise ValueError("CSV file has no header row.")

            for idx, row in enumerate(reader, start=1):
                texts = extract_text_fields(row)
                combined_text = " ".join(texts) if texts else ""

                all_texts.append(combined_text)

                obj: Dict[str, Any] = {"id": idx}
                obj.update({k: v.strip() if isinstance(v, str) else v for k, v in row.items()})
                records.append(obj)

        print(f"ℹ️  Found {len(records)} rows")

        if embed and model:
            print("Generating embeddings...")
            embeddings = model.encode(
                all_texts,
                convert_to_numpy=False,
                batch_size=batch_size,
                show_progress_bar=True
            )
            for i, rec in enumerate(records):
                embedding_list = [float(x.item()) for x in embeddings[i]]
                rec["embedding"] = embedding_list

        out_file = Path(json_path)
        with out_file.open("w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)

        print(f"✅ Wrote {len(records)} records to {out_file}")

    finally:
        if model:
            del model


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="convert3r_csv2jsonEmbed.py",
        description="Convert CSV to JSON with IDs and optional sentence embeddings"
    )
    parser.add_argument("input_file", help="Input CSV file")
    parser.add_argument("-o", "--output-file", dest="output_file", help="Output JSON file")
    parser.add_argument("--embed", action="store_true", help="Add sentence-transformer embeddings to each record")

    args = parser.parse_args()

    try:
        output_file = args.output_file or str(Path(args.input_file).with_suffix(".json"))
        csv_to_json_with_embeddings(args.input_file, output_file, embed=args.embed)
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ Input error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()