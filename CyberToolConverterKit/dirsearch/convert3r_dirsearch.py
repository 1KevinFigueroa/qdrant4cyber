#!/usr/bin/env python3
"""
convert3r_dirsearch.py - Convert dirsearch to JSON with ID first and optional embeddings

Usage: convert3r_dirsearch.py [-h] [--embed] [-o OUTPUT_FILE] input_file
"""

import argparse
import json
import re
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Dict, Any, List

try:
    import torch
    from sentence_transformers import SentenceTransformer
except ImportError:
    torch = None
    SentenceTransformer = None

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

LINE_RE = re.compile(
    r"""
    ^\s*
    (?P<status>\d{3})
    \s+
    (?P<size>\S+)
    \s+
    (?P<url>\S+)
    (?:\s*->\s*REDIRECTS\s+TO:\s*(?P<redirect>\S+))?
    """,
    re.VERBOSE,
)


def clean_markdown_url(raw: str) -> str:
    m = re.match(r'\[([^\]]+)\]\(([^)]+)\)', raw)
    if m:
        return m.group(2)
    m2 = re.match(r'\[([^\]]+)\]', raw)
    if m2:
        return m2.group(1)
    return raw


def parse_dirsearch_line(line: str) -> Dict[str, Any] | None:
    match = LINE_RE.match(line)
    if not match:
        return None

    return {
        "status": int(match.group("status")),
        "size": match.group("size"),
        "url": clean_markdown_url(match.group("url")),
        "redirect_to": clean_markdown_url(match.group("redirect")) if match.group("redirect") else None,
    }


def convert_dirsearch_to_json(input_path: str) -> List[OrderedDict]:
    results = []
    current_id = 1

    with open(input_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("# Dirsearch") or line.startswith("HTTP code"):
                continue

            parsed = parse_dirsearch_line(line)
            if parsed:
                ordered = OrderedDict([("id", current_id)])
                ordered.update(parsed)
                results.append(ordered)
                current_id += 1

    return results


def build_embeddings(records: List[OrderedDict], model_name: str = DEFAULT_MODEL):
    if torch is None or SentenceTransformer is None:
        raise ImportError("Missing dependencies. Install with: pip install sentence-transformers torch")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = SentenceTransformer(model_name, device=device)

    texts = [record["url"] for record in records]
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
        prog="convert3r_dirsearch.py",
        description="Convert Dirsearch to JSON (ID first) with optional embeddings"
    )
    parser.add_argument("input_file", help="Dirsearch text file")
    parser.add_argument("-o", "--output-file", dest="output_file", help="Output JSON file")
    parser.add_argument("--embed", action="store_true", help="Add sentence-transformer embeddings to each record")

    args = parser.parse_args()

    try:
        records = convert_dirsearch_to_json(args.input_file)

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