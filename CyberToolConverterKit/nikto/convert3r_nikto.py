#!/usr/bin/env python3
"""
convert3r_niktoEmbed.py - Nikto text output → JSON converter with embeddings

Usage: convert3r_niktoEmbed.py [-h] [--embed] [-o OUTPUT_FILE] input_file
"""

import argparse
import json
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import torch
    from sentence_transformers import SentenceTransformer
except ImportError:
    torch = None
    SentenceTransformer = None

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_VECTOR_SIZE = 384


def parse_nikto_line(line: str) -> Dict[str, Any] | None:
    line = line.strip()
    if not line:
        return None

    # Primary pattern
    pattern = r'^\+\s+(?P<method>[A-Z]+)\s+(?P<path>\S+)\s*:\s*(?P<desc>.+?)\s*(?:See:\s*(?P<url>https?://\S+))?'
    match = re.match(pattern, line)
    if not match:
        # Fallback pattern
        pattern2 = r'^\+\s+(?P<method>\S+)\s+(?P<path>\S+)?\s*:\s*(?P<desc>.+)'
        match = re.match(pattern2, line)

    if not match:
        return None

    d = match.groupdict()
    path = d.get('path') or ''
    method = d.get('method', 'GET')
    desc = (d.get('desc') or '').strip()
    url = (d.get('url') or '').strip()

    return {
        "method": method.upper(),
        "path": path.strip('/'),
        "description": desc,
        "reference_url": url if url.startswith("http") else "",
        "line_number": None,
        "raw_line": line.strip()
    }


def nikto_txt_to_json(txt_file: str, output_file: str, embed: bool = False):
    if not os.path.exists(txt_file):
        raise FileNotFoundError(f"❌ Text file not found: {txt_file}")

    entries = []
    line_number = 1

    print(f"📖 Reading nikto output: {txt_file}")

    with open(txt_file, "r", encoding="utf-8") as f:
        for line in f:
            parsed = parse_nikto_line(line)
            if parsed:
                parsed["line_number"] = line_number
                entries.append(parsed)
            line_number += 1

    # Add sequential IDs
    for idx, entry in enumerate(entries, start=1):
        entry["id"] = idx

    print(f"✓ Parsed {len(entries)} valid nikto entries")

    if embed:
        print("Generating embeddings...")
        texts = [entry["path"] for entry in entries]  # Embed path names (same as gobuster)
        embeds = build_embeddings(texts)
        for entry, emb in zip(entries, embeds):
            entry["embed"] = emb
        print("Embeddings added")

    output_data = {
        "vector_size": DEFAULT_VECTOR_SIZE,
        "total_entries": len(entries),
        "entries": entries
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Converted to JSON: {output_file}")

    # Status breakdown (method counts instead of HTTP status)
    method_counts = {}
    for entry in entries:
        method = entry["method"]
        method_counts[method] = method_counts.get(method, 0) + 1

    print("📊 Method breakdown:")
    for method, count in sorted(method_counts.items()):
        print(f"   {method}: {count}")


def build_embeddings(texts: List[str], model_name: str = DEFAULT_MODEL):
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


def main():
    parser = argparse.ArgumentParser(
        prog="convert3r_niktoEmbed.py",
        description="Convert nikto text output to structured JSON with optional embeddings"
    )
    parser.add_argument("input_file", help="Path to nikto text output file")
    parser.add_argument("-o", "--output-file", dest="output_file", help="Output JSON file")
    parser.add_argument("--embed", action="store_true", help="Add sentence-transformer embeddings to each record")

    args = parser.parse_args()

    try:
        output_file = args.output_file or str(Path(args.input_file).with_suffix(".json"))
        nikto_txt_to_json(args.input_file, output_file, embed=args.embed)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()