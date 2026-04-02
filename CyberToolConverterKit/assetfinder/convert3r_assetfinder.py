#!/usr/bin/env python3
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    raise ImportError(
        "❌ This script requires 'sentence-transformers'. Install it with:\n"
        "   pip install sentence-transformers"
    )


def parse_assetfinder_file(input_file: str) -> List[Dict[str, Any]]:
    """
    Parse assetfinder output file — one domain/subdomain per line.
    Identical format to assetfinder text file output.
    """
    entries = []
    with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
        for line_num, line in enumerate(f, 1):
            raw_line = line.rstrip('\n')
            domain = raw_line.strip()
            # Skip empty lines and comments
            if not domain or domain.startswith('#'):
                continue
            entries.append({
                "id": len(entries) + 1,
                "line_number": line_num,
                "domain": domain,
                "raw_line": raw_line,
                "text": f"domain {domain}",  # For embedding context (helps model)
            })
    return entries


def generate_embeddings(entries: List[Dict[str, Any]], model_name: str = 'all-MiniLM-L6-v2') -> List[Dict[str, Any]]:
    """
    Generate SentenceTransformer embeddings for each entry's `text` field.
    Updates entries in-place with `"embedding"` key (list of floats).
    """
    print(f"🔧 Loading embedding model: {model_name} ...", end=" ", flush=True)
    try:
        model = SentenceTransformer(model_name)
        print("✅ loaded.")
    except Exception as e:
        raise RuntimeError(f"Failed to load {model_name}. Error: {e}")

    texts = [entry["text"] for entry in entries]
    if not texts:
        return entries

    # Generate embeddings (CPU-friendly by default; use .to('cuda') if GPU available)
    print(f"⚡ Generating {len(texts)} embeddings...", flush=True)
    try:
        embeddings = model.encode(
            texts,
            batch_size=64,         # Adjust based on memory
            show_progress_bar=True,  # Shows progress bar in terminal
            convert_to_tensor=False,  # Returns numpy arrays (→ list of floats)
            normalize_embeddings=True  # L2-normalized for cosine similarity
        )
    except Exception as e:
        raise RuntimeError(f"Embedding generation failed: {e}")

    # Attach embeddings back to entries
    for i, embedding in enumerate(embeddings):
        entries[i]["embedding"] = embedding.tolist()  # Convert numpy array → Python list

    return entries


def write_json(entries: List[Dict[str, Any]], output_file: str):
    """Write parsed & embedded entries to JSON file."""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)
    print(f"✅ Saved {len(entries)} domains (with embeddings) to {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Parse assetfinder output → structured JSON with embeddings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python embed_assetfinder.py domains.txt
  python embed_assetfinder.py domains.txt -o yandex_embedded.json
        """
    )
    parser.add_argument("input", help="Assetfinder output text file (one domain per line)")
    parser.add_argument("-o", "--output", default="assetfinder_embedded.json",
                        help="Output JSON file (default: assetfinder_embedded.json)")
    args = parser.parse_args()

    # Input validation
    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"❌ Input file not found: {args.input}")

    # Parse domains
    entries = parse_assetfinder_file(args.input)
    print(f"📊 Parsed {len(entries)} domains from {args.input}")

    if not entries:
        print("⚠️  No valid domains found.")
        return

    # Generate embeddings (in-place update of `entries`)
    entries_with_embeddings = generate_embeddings(entries)

    # Save to JSON
    write_json(entries_with_embeddings, args.output)


if __name__ == "__main__":
    main()
