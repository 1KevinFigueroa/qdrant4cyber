#!/usr/bin/env python3
"""
convert3r_subfinderTXT.py - Convert subdomain text file to JSON with guaranteed embeddings

Usage:
  python convert3r_subfinderTXT.py [-h] [--embed] [-o OUTPUT_FILE] input_file
"""

import argparse
import json
import os
import sys
from collections import OrderedDict
from pathlib import Path
from typing import List, Dict, Any

# Guaranteed sentence-transformers + torch import
try:
    import torch
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    print("❌ Need 'pip install sentence-transformers torch'", file=sys.stderr)
    sys.exit(1)

def load_and_sanitize_domains(input_file: str) -> List[str]:
    """Load clean domains from TXT file."""
    if not os.path.isfile(input_file):
        raise FileNotFoundError(f"File not found: {input_file}")

    domains = []
    try:
        with open(input_file, 'r', encoding='utf-8', errors='replace') as f:
            for line in f:
                stripped = line.strip()
                if stripped and not stripped.startswith('#'):
                    # Quick security filter
                    if any(c in stripped for c in r'/\?;&|'):
                        continue
                    domains.append(stripped)
    except Exception as e:
        raise IOError(f"Read error: {e}")

    if not domains:
        raise ValueError("No valid domains found!")
    return domains

def generate_embeddings(domains: List[str]) -> List[List[float]]:
    """Generate 384-dim embeddings for ALL domains."""
    print("🧠 Loading all-MiniLM-L6-v2...")
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2', device='cpu')
    
    print(f"📊 Embedding {len(domains)} domains...")
    embeddings = model.encode(
        domains,
        batch_size=32,  # Conservative batch size
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True
    )
    
    # Convert ALL to list-of-lists (guaranteed)
    result = [emb.tolist() for emb in embeddings]
    
    # Verify consistency
    expected_dim = 384
    for i, emb in enumerate(result):
        if len(emb) != expected_dim:
            print(f"⚠️ Fixing dim {len(emb)} → {expected_dim} at {i}")
            # Pad/truncate to exact size
            if len(emb) < expected_dim:
                emb += [0.0] * (expected_dim - len(emb))
            else:
                emb = emb[:expected_dim]
            result[i] = emb[:expected_dim]
    
    print(f"✅ {len(result)} embeddings (all {expected_dim} dims)")
    return result

def safe_write_json(data: List[Dict], output_file: str) -> None:
    """Atomic JSON write."""
    os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
    tmp = output_file + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    os.replace(tmp, output_file)

def main():
    parser = argparse.ArgumentParser(description="TXT → JSON w/ guaranteed embeddings")
    parser.add_argument("input_file", help="Domains TXT file")
    parser.add_argument("--embed", action="store_true", 
                       help="Generate text_embedding for each ID")
    parser.add_argument("-o", "--output-file", dest="output_file", 
                       help="Output JSON (default: enriched_<input>.json)")

    args = parser.parse_args()

    try:
        print(f"📖 Loading: {args.input_file}")
        domains = load_and_sanitize_domains(args.input_file)
        print(f"✅ Found {len(domains)} domains")

        # Output path
        if not args.output_file:
            base = Path(args.input_file).stem
            args.output_file = f"enriched_{base}.json"

        # ALWAYS generate embeddings if --embed (guaranteed per ID)
        records = []
        if args.embed:
            embeddings = generate_embeddings(domains)
            for i, (domain, embedding) in enumerate(zip(domains, embeddings), 1):
                record = OrderedDict({
                    "id": i,
                    "hostname": domain,
                    "text_embedding": embedding  # GUARANTEED 384-dim
                })
                records.append(record)
        else:
            # No embeddings
            for i, domain in enumerate(domains, 1):
                record = OrderedDict({
                    "id": i,
                    "hostname": domain
                })
                records.append(record)

        safe_write_json(records, args.output_file)
        print(f"💾 Saved {len(records)} records to {args.output_file}")

        # Safe preview
        sample = records[0].copy()
        if "text_embedding" in sample:
            emb = sample["text_embedding"]
            sample["text_embedding"] = f"[{len(emb)} dims]"
        print("\n📋 Preview:")
        print(json.dumps(sample, indent=2))

    except Exception as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()