#!/usr/bin/env python3
"""
convert3r_cewkEmbed.py - Convert CeWL wordlist text file to JSON with optional embeddings

Usage:
  python convert3r_cewkEmbed.py [-h] [--embed] [-o OUTPUT_FILE] input_file
"""

import argparse
import json
import sys
from collections import OrderedDict
from pathlib import Path
from typing import List

try:
    import torch
    from sentence_transformers import SentenceTransformer
except ImportError:
    torch = None
    SentenceTransformer = None

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def convert_cewl_to_json(input_path: str) -> List[OrderedDict]:
    words: List[OrderedDict] = []
    word_id = 1

    print(f"📖 Reading CeWL wordlist from {input_path}...")

    with open(input_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            word = line.strip()
            if not word:
                continue

            record = OrderedDict([
                ("id", word_id),
                ("word", word),
                ("length", len(word)),
                ("lowercase", word.lower()),
                ("line_number", line_num)
            ])

            words.append(record)
            word_id += 1

    print(f"✓ Processed {len(words)} words")
    return words


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


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="convert3r_cewkEmbed.py",
        description="Convert CeWL wordlist text to JSON with IDs and optional embeddings"
    )
    parser.add_argument("input_file", help="CeWL wordlist text file")
    parser.add_argument("-o", "--output-file", dest="output_file", help="Output JSON file")
    parser.add_argument("--embed", action="store_true", help="Add sentence-transformer embeddings to each record")

    args = parser.parse_args()

    try:
        records = convert_cewl_to_json(args.input_file)

        if args.embed:
            print("Generating embeddings...")
            texts = [r["word"] for r in records]
            embeds = build_embeddings(texts)
            for r, emb in zip(records, embeds):
                r["embed"] = emb
            print("Embeddings generated")

        output_file = args.output_file or str(Path(args.input_file).with_suffix(".json"))

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)

        print(f"✅ Saved {len(records)} words to {output_file}")

        lengths = [r["length"] for r in records]
        print(f"📊 Stats: avg={sum(lengths)/len(lengths):.1f} chars, "
              f"min={min(lengths)}, max={max(lengths)}")

        if records:
            print("\n📋 Sample:")
            for r in records[:5]:
                print(f"  ID={r['id']:3d} | {r['word']:<15} | len={r['length']}")

    except FileNotFoundError:
        print(f"❌ '{args.input_file}' not found", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()