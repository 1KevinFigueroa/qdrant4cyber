#!/usr/bin/env python3
"""

Usage:
  python convert3r_subfinder.py [-h] [--embed] [-o OUTPUT_FILE] input_file
"""

import argparse
import json
import os
import sys
from collections import OrderedDict
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import torch
    from sentence_transformers import SentenceTransformer
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
_MODEL_CACHE = None

def load_embedding_model() -> Optional[Any]:
    """Load and validate sentence-transformer model"""
    global _MODEL_CACHE
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE

    if not TORCH_AVAILABLE:
        print("⚠️ Torch/sentence-transformers not available", file=sys.stderr)
        return None

    print(f"📂 Loading embedding model '{DEFAULT_MODEL}' (first run may download)...")
    try:
        model = SentenceTransformer(DEFAULT_MODEL, device="cpu")
        # Validate model produces expected 384-dim embeddings
        dummy_embed = model.encode(["test"], convert_to_numpy=True)[0]
        assert len(dummy_embed) == 384, f"Expected 384 dims, got {len(dummy_embed)}"
        print("✅ Model loaded and validated (384 dims).")
        _MODEL_CACHE = model
        return model
    except Exception as e:
        print(f"❌ Failed to load model: {e}", file=sys.stderr)
        return None

def create_text_for_embedding(record: Dict[str, Any]) -> str:
    """Create rich text representation for embedding from any record"""
    text_parts = []
    
    # Priority fields for key content
    priority_fields = ["word", "target", "subdomain", "domain", "hostname", "url", "name", "path"]
    for field in priority_fields:
        value = record.get(field)
        if isinstance(value, str) and value.strip():
            text_parts.append(value.strip())
    
    # Add status/method/content info
    if isinstance(record.get("status"), (int, str)):
        text_parts.append(f"status:{record['status']}")
    if isinstance(record.get("method"), str):
        text_parts.append(f"method:{record['method']}")
    if isinstance(record.get("content_length"), (int, str)):
        text_parts.append(f"size:{record['content_length']}")
    
    # Response body preview if available
    if "response" in str(record.get("type", "")):
        body_preview = record.get("body", "") or record.get("content", "")
        if isinstance(body_preview, str) and len(body_preview) > 10:
            text_parts.append(body_preview[:200])
    
    return " ".join(text_parts)[:512]  # Cap length for consistent embeddings

def encode_text(text: str, model) -> List[float]:
    """Safely encode text to embedding with fallback"""
    if not isinstance(text, str) or not text.strip():
        return model.encode(["empty_record"], convert_to_numpy=True, show_progress_bar=False)[0].tolist()
    
    try:
        embedding = model.encode(
            [text.strip()],
            convert_to_numpy=True,
            show_progress_bar=False,
            normalize_embeddings=True
        )[0]
        return embedding.tolist()
    except Exception as e:
        print(f"⚠️ Embedding failed for '{text[:50]}...': {e}", file=sys.stderr)
        return model.encode(["fallback"], convert_to_numpy=True, show_progress_bar=False)[0].tolist()

def sanitize_value(val):
    """Clean values for JSON serialization"""
    if isinstance(val, list):
        return [sanitize_value(v) for v in val]
    if hasattr(val, "item") and callable(getattr(val, "item")):
        return float(val.item()) if getattr(val, "ndim", 0) == 0 else [float(x) for x in val.flatten()]
    if isinstance(val, dict):
        return {str(k): sanitize_value(v) for k, v in val.items()}
    if isinstance(val, set):
        return list(val)
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        return int(val) if float(val).is_integer() else float(val)
    if isinstance(val, bytes):
        return val.decode("utf-8", errors="replace")
    if val is None:
        return None
    return str(val)

def process_input(input_path: str, model) -> List[OrderedDict]:
    """Process JSONL input, add embeddings if model available"""
    results = []
    skipped_lines = 0
    next_id = 1

    print(f"📖 Reading from {input_path}...")
    
    with open(input_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                skipped_lines += 1
                continue

            try:
                obj = json.loads(line)
                if not isinstance(obj, dict):
                    skipped_lines += 1
                    continue
            except json.JSONDecodeError:
                skipped_lines += 1
                continue

            # Create new record with sequential ID
            new_record = OrderedDict()
            new_record["id"] = next_id

            # Copy all original fields (skip existing embeddings)
            for key, value in obj.items():
                if not key.endswith(("_embed", "_embedding")):
                    new_record[key] = sanitize_value(value)

            # Add embedding if model available
            if model is not None:
                text_for_embed = create_text_for_embedding(new_record)
                embedding = encode_text(text_for_embed, model)
                new_record["text_embedding"] = embedding

            results.append(new_record)
            next_id += 1

            if next_id % 100 == 0:
                print(f"  Processed {next_id-1} records...")

    print(f"✅ Processed {len(results)} records (skipped {skipped_lines} lines)")
    if model is not None:
        print(f"📊 Each record has 'text_embedding' (384 dims) + original metadata")
    else:
        print("📊 Records have metadata only (no embeddings)")
    return results

def main():
    parser = argparse.ArgumentParser(
        prog="convert3r_subfinder.py",
        description="Convert JSONL to enriched format with optional embeddings per ID",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python convert3r_subfinder.py domains.jsonl                    # No embeddings
  python convert3r_subfinder.py --embed domains.jsonl            # With embeddings  
  python convert3r_subfinder.py --embed -o output.json input.jsonl
        """
    )
    parser.add_argument("input_file", help="Input JSON lines file")
    parser.add_argument("--embed", action="store_true", default=False, 
                       help="Add semantic embeddings using all-MiniLM-L6-v2 (requires torch)")
    parser.add_argument("-o", "--output-file", dest="output_file", 
                       help="Output file (default: enriched_<input>.json)")

    args = parser.parse_args()

    if not os.path.isfile(args.input_file):
        print(f"❌ Input file not found: {args.input_file}", file=sys.stderr)
        sys.exit(1)

    # Load model only if --embed requested
    model = load_embedding_model() if args.embed else None
    if args.embed and model is None:
        print("⚠️ Embeddings requested but unavailable. Continuing without.", file=sys.stderr)

    if args.output_file is None:
        base = Path(args.input_file).stem
        args.output_file = f"enriched_{base}.json"

    try:
        records = process_input(args.input_file, model)

        with open(args.output_file, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)

        print(f"💾 Saved {len(records)} enriched records to {args.output_file}")
        
        # Preview first record
        if records:
            first = records[0]
            print(f"\n📋 Sample record structure:")
            print(f"  ID: {first['id']}")
            print(f"  Keys: {list(first.keys())}")
            if "text_embedding" in first:
                print(f"  Embedding preview: [{first['text_embedding'][:3]}...{first['text_embedding'][-3:]}]")
            
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 