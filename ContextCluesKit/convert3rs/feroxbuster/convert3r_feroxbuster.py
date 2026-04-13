#!/usr/bin/env python3
"""
convert3r_feroxbuster.py - Convert feroxbuster JSON to JSON with ID first and optional embeddings

Usage: convert3r_feroxbuster.py [-h] [--embed] [-o OUTPUT_FILE] input_file
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Any, List

try:
    import torch
    from sentence_transformers import SentenceTransformer
except ImportError:
    torch = None
    SentenceTransformer = None

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def parse_feroxbuster_line(line: str) -> Dict[str, Any] | None:
    line = line.strip()
    if not line:
        return None
    
    try:
        entry = json.loads(line)
        # Only process "response" type entries
        if isinstance(entry.get("type"), str) and entry["type"].lower() == "response":
            return entry
        return None
    except json.JSONDecodeError:
        return None


def convert_feroxbuster_to_json(input_path: str) -> List[Dict[str, Any]]:
    results = []
    current_id = 1

    with open(input_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            parsed = parse_feroxbuster_line(line)
            if parsed:
                record = {
                    "id": current_id,
                    "line_number": line_num,
                    **parsed  # unpack original fields
                }
                results.append(record)
                current_id += 1

    return results


def build_embeddings(records: List[Dict[str, Any]], model_name: str = DEFAULT_MODEL):
    if torch is None or SentenceTransformer is None:
        raise ImportError("Missing dependencies. Install with: pip install sentence-transformers torch")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = SentenceTransformer(model_name, device=device)

    # Use url, path, or title fields for embedding
    texts = []
    for record in records:
        text_parts = []
        for key in ["url", "path", "title"]:
            val = record.get(key)
            if isinstance(val, str) and val.strip():
                text_parts.append(val.strip())
        texts.append(" ".join(text_parts) or record.get("url", ""))

    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        batch_size=32,
        show_progress_bar=True,
    )
    return embeddings.tolist()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="convert3r_feroxbuster.py",
        description="Convert Feroxbuster to JSON (ID first) with optional embeddings"
    )
    parser.add_argument("input_file", help="Feroxbuster JSON text file")
    parser.add_argument("-o", "--output-file", dest="output_file", help="Output JSON file")
    parser.add_argument("--embed", action="store_true", help="Add sentence-transformer embeddings to each record")

    args = parser.parse_args()

    try:
        records = convert_feroxbuster_to_json(args.input_file)

        if args.embed:
            print("Generating embeddings...")
            embeds = build_embeddings(records)
            for record, emb in zip(records, embeds):
                record["embed"] = emb

        output_file = args.output_file or str(Path(args.input_file).with_suffix(".json"))

        with open(output_file, "w", encoding="utf-8") as out:
            json.dump(records, out, indent=2, ensure_ascii=False)

        print(f"✓ Converted {len(records)} entries → {output_file}")
        if records:
            print("Sample JSON structure:")
            print(json.dumps(records[0], indent=2))

    except FileNotFoundError:
        print(f"❌ '{args.input_file}' not found", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()