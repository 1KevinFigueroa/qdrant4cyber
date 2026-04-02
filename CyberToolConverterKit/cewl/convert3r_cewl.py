#!/usr/bin/env python3
"""
convert_cewl.py - Convert CeWL wordlist text file to enriched JSON with embeddings

CeWL outputs one word per line. This script converts it to a JSON array 
with incremental IDs, metadata, and semantic embeddings using all-MiniLM-L6-v2.

Usage:
    python convert_cewl.py input.txt output.json
"""

import argparse
import json
import sys
from typing import List, Dict, Any
from collections import OrderedDict

# ✅ Import only after checking dependencies (safe runtime fallback)
try:
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    print(
        "❌ Missing required dependency: 'sentence-transformers'. "
        "Install with: pip install sentence-transformers",
        file=sys.stderr,
    )
    sys.exit(1)


def load_embedding_model(model_name: str = "all-MiniLM-L6-v2") -> "SentenceTransformer":
    """
    Safely loads the embedding model once. Validates model name and handles network issues.
    Uses caching via SentenceTransformer's default cache directory.
    """
    try:
        print(f"📂 Loading embedding model '{model_name}' (first run may download)...")
        model = SentenceTransformer(model_name)
        # 🔒 Optional: verify model output dimension = 384
        dummy_embed = model.encode(["test"], convert_to_numpy=False)[0]
        assert len(dummy_embed) == 384, f"Model '{model_name}' produced {len(dummy_embed)} dims (expected 384)"
        print("✅ Model loaded and validated.")
        return model
    except Exception as e:
        raise RuntimeError(
            f"Failed to load embedding model '{model_name}'. "
            "Check internet connectivity or try a different model."
        ) from e


def convert_cewl_to_json(input_path: str, model: "SentenceTransformer") -> List[OrderedDict]:
    """
    Read CeWL wordlist (one word per line) and convert to JSON array.
    Each word gets an ID, length, lowercase version, and 384-dim embedding.

    Args:
        input_path: Path to CeWL .txt file
        model: Preloaded SentenceTransformer instance

    Returns:
        List[OrderedDict]: Enriched word records
    """
    words: List[OrderedDict] = []
    word_id = 1
    line_num = 0

    print(f"📖 Reading CeWL wordlist from {input_path}...")

    # ✅ Input validation
    if not isinstance(input_path, str) or not input_path.strip():
        raise ValueError("❌ Invalid input file path.")

    with open(input_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            word = line.strip()
            
            # Skip empty lines
            if not word:
                continue

            # ✅ Sanitize: reject non-printable/control chars (prevent injection risk)
            if any(not c.isprintable() for c in word):
                print(f"⚠️ Skipping unsafe/non-printable line {line_num}: '{word!r}'")
                continue

            try:
                embedding = model.encode(
                    [word],
                    convert_to_numpy=False,
                    show_progress_bar=False
                )[0]

                # Convert to serializable float list (avoids numpy type issues)
                embedding_list = [float(x.item()) for x in embedding]

            except Exception as e:
                print(f"⚠️ Embedding failed for word '{word}' at line {line_num}: {e}")
                continue  # skip problematic entries

            record = OrderedDict([
                ("id", word_id),
                ("word", word),
                ("length", len(word)),
                ("lowercase", word.lower()),
                ("line_number", line_num),
                ("embedding", embedding_list)
            ])

            words.append(record)
            word_id += 1

    print(f"✅ Processed {len(words)} valid words (skipped {line_num - len(words)} lines).")
    return words


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert CeWL wordlist text to JSON with sentence embeddings."
    )
    parser.add_argument("input_file", help="CeWL wordlist text file (one word per line)")
    parser.add_argument("output_file", help="Output JSON file (includes embeddings)")
    args = parser.parse_args()

    try:
        # 1️⃣ Load embedding model ONCE
        model = load_embedding_model("all-MiniLM-L6-v2")

        # 2️⃣ Convert wordlist → structured data + embeddings
        records = convert_cewl_to_json(args.input_file, model)

        # 3️⃣ Write JSON output
        with open(args.output_file, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Saved {len(records)} words to {args.output_file}")

        # 📊 Show statistics
        if not records:
            print("⚠️ No valid entries found!")
            return

        lengths = [r["length"] for r in records]
        print(
            f"📊 Stats: avg={sum(lengths)/len(lengths):.1f} chars, "
            f"min={min(lengths)}, max={max(lengths)}"
        )

        # 📋 Sample preview (first 5)
        print("\n📋 First 5 entries:")
        for r in records[:5]:
            emb_preview = "[{}]".format(", ".join(f"{x:.3f}" for x in r["embedding"][:2])) + "..."
            print(
                f"  ID={r['id']:3d} | {r['word']:<15} | len={r['length']} | emb[0,1]≈{emb_preview}"
            )

    except FileNotFoundError:
        print(f"❌ '{args.input_file}' not found", file=sys.stderr)
        sys.exit(1)
    except ValueError as ve:
        print(f"❌ Invalid input: {ve}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Critical error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
