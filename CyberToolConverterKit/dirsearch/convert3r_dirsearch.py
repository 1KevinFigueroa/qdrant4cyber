#!/usr/bin/env python3
"""
convert_dirsearch.py - Ensures ID is FIRST in each JSON object + adds semantic embeddings

Usage:
    python convert_dirsearch.py input.txt output.json [--device cpu|cuda]
"""

import argparse
import json
import re
import sys
from typing import List, Dict, Any, Optional
from collections import OrderedDict
from pathlib import Path

# Embedding dependencies (optional; fails gracefully if not installed)
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    SentenceTransformer = None  # type: ignore[misc,assignment]
    EMBEDDINGS_AVAILABLE = False


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
    """Clean [url](link) markdown to plain URL."""
    m = re.match(r'\[([^\]]+)\]\(([^)]+)\)', raw)
    if m:
        return m.group(2)
    m2 = re.match(r'\[([^\]]+)\]', raw)
    if m2:
        return m2.group(1)
    return raw


def parse_dirsearch_line(line: str) -> Optional[Dict[str, Any]]:
    """Parse dirsearch line or return None."""
    match = LINE_RE.match(line)
    if not match:
        return None

    return {
        "status": int(match.group("status")),
        "size": match.group("size"),
        "url": clean_markdown_url(match.group("url")),
        "redirect_to": clean_markdown_url(match.group("redirect"))
                     if match.group("redirect") else None,
    }


def _get_embedding_input(parsed: Dict[str, Any], full_line: str) -> str:
    """Prepare text for embedding: prioritize URL + metadata."""
    parts = [parsed.get("url", "")]
    status = parsed.get("status")
    size = parsed.get("size")
    redirect = parsed.get("redirect_to")

    if status and status != 200:
        parts.append(f"HTTP {status}")
    if size not in ["-"] and size is not None:
        parts.append(f"{size}b response")
    if redirect and "REDIRECTS" not in full_line.upper():
        # Avoid redundancy: if redirect already visible in full line, skip
        parts.append(f"→ redirects to {redirect}")

    return "; ".join(parts) if parts else full_line.strip()


def generate_embeddings(
    records: List[OrderedDict],
    device: Optional[str] = None,
    batch_size: int = 32
) -> List[OrderedDict]:
    """
    Generate semantic embeddings for each record and attach them as 'embedding' field.
    
    Returns updated list with new 'embedding' key (list of floats).
    """
    if not EMBEDDINGS_AVAILABLE or SentenceTransformer is None:
        print("⚠️  Skipping embeddings: sentence-transformers not installed.", file=sys.stderr)
        return records

    try:
        print(f"🚀 Loading all-MiniLM-L6-v2 model on device '{device or 'auto'}'...")
        model_kwargs = {"device": device} if device else {}
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", **model_kwargs)
        print(f"✅ Model loaded (dimension: {model.get_sentence_embedding_dimension()})")
    except Exception as e:
        print(f"⚠️ Failed to load embedding model: {e}", file=sys.stderr)
        return records

    # Prepare texts for embedding
    texts = []
    for record in records:
        full_line_text = str(record).strip()  # Fallback
        parsed = {
            "url": record.get("url"),
            "status": record.get("status"),
            "size": record.get("size"),
            "redirect_to": record.get("redirect_to")
        }
        text_for_embed = _get_embedding_input(parsed, full_line_text)
        texts.append(text_for_embed)

    try:
        print(f"📊 Generating embeddings for {len(records)} records...")
        embeddings = model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=True,
            convert_to_tensor=False
        ).tolist()

        # Attach embeddings to records (as list of floats)
        for record, emb in zip(records, embeddings):
            record["embedding"] = emb
    except Exception as e:
        print(f"⚠️ Embedding generation failed: {e}", file=sys.stderr)

    return records


def convert_dirsearch_to_json(
    input_path: str,
    device: Optional[str] = None
) -> List[OrderedDict]:
    """Convert dirsearch file to list of OrderedDicts with 'id' FIRST + embeddings."""
    results = []
    current_id = 1

    # Ensure input exists
    input_file = Path(input_path)
    if not input_file.is_file():
        raise FileNotFoundError(f"'{input_path}' does not exist")

    with open(input_file, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line_cleaned = line.strip()
            if (
                not line_cleaned or
                line_cleaned.startswith("# Dirsearch") or
                line_cleaned.startswith("HTTP code")
            ):
                continue

            parsed = parse_dirsearch_line(line_cleaned)
            if parsed:
                # **ID FIRST** - using OrderedDict
                ordered = OrderedDict([("id", current_id)])
                # Add other fields AFTER id (preserves insertion order in Python 3.7+)
                ordered.update(parsed)
                results.append(ordered)
                current_id += 1

    # Apply embeddings if possible
    return generate_embeddings(results, device=device)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert Dirsearch output to JSON (ID first + semantic embeddings)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python convert_dirsearch.py input.txt output.json
  python convert_dirsearch.py input.txt output.json --device cuda
        """
    )
    parser.add_argument("input_file", help="Dirsearch text file")
    parser.add_argument("output_file", help="Output JSON file (supports .json/.jsonl)")
    parser.add_argument(
        "-d", "--device",
        choices=["cpu", "cuda"],
        default=None,
        help="Device to run embedding model on (auto-selects if omitted)"
    )
    args = parser.parse_args()

    try:
        records = convert_dirsearch_to_json(args.input_file, device=args.device)
        
        # Handle output format (.jsonl vs .json)
        ext = Path(args.output_file).suffix.lower()
        with open(args.output_file, "w", encoding="utf-8") as out:
            if ext == ".jsonl":
                for record in records:
                    json.dump(record, out, ensure_ascii=False)
                    out.write("\n")
            else:  # Default to pretty-printed JSON
                json.dump(records, out, indent=2, ensure_ascii=False)

        print(f"✅ Converted {len(records)} entries → {args.output_file}")
        if records:
            sample = {
                k: ("[embedding]" if k == "embedding" else v) 
                for k, v in records[0].items()
            }
            print("\n📝 Sample JSON structure (embeddings hidden):")
            print(json.dumps(sample, indent=2))
    except FileNotFoundError as e:
        print(f"❌ Input file not found: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
