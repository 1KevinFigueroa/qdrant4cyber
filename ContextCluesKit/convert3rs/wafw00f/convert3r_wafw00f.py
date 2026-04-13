#!/usr/bin/env python3
"""
convert3r_wafw00fEmbed.py - Convert Wafw00f JSON to enriched JSON with IDs and optional embeddings

Usage:
  python convert3r_wafw00fEmbed.py [-h] [--embed] [-o OUTPUT_FILE] input_file
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
except ImportError:
    torch = None
    SentenceTransformer = None

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
_MODEL_CACHE = None


def load_embedding_model() -> Optional[Any]:
    if torch is None or SentenceTransformer is None:
        return None

    global _MODEL_CACHE
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE

    try:
        print(f"📂 Loading embedding model '{DEFAULT_MODEL}' (first run may download)...")
        model = SentenceTransformer(DEFAULT_MODEL, device="cpu")
        dummy_embed = model.encode(["test"], convert_to_numpy=True)[0]
        assert len(dummy_embed) == 384, f"Model '{DEFAULT_MODEL}' produced {len(dummy_embed)} dims (expected 384)"
        print("✅ Model loaded and validated.")
        _MODEL_CACHE = model
        return model
    except Exception as e:
        print(f"⚠️ Embedding disabled: Failed to load model '{DEFAULT_MODEL}': {e}", file=sys.stderr)
        return None


def encode_with_safety(text: str, model) -> Optional[List[float]]:
    try:
        if not isinstance(text, str):
            text = str(text)

        text = text.strip()
        if not text:
            return None

        embedding = model.encode(
            [text],
            convert_to_numpy=True,
            show_progress_bar=False,
            normalize_embeddings=True
        )[0]

        return embedding.tolist() if hasattr(embedding, "tolist") else [float(x) for x in embedding]
    except Exception as e:
        print(f"⚠️ Embedding failed for '{text[:30]}...': {e}", file=sys.stderr)
        return None


def sanitize_value(val):
    if isinstance(val, list):
        return [sanitize_value(v) for v in val]
    if hasattr(val, "item") and callable(getattr(val, "item")):
        try:
            return float(val.item()) if getattr(val, "ndim", 0) == 0 else [float(x) for x in val.flatten()]
        except Exception:
            return str(val)
    if isinstance(val, dict):
        return {str(k): sanitize_value(v) for k, v in val.items()}
    if isinstance(val, set):
        return {str(k): sanitize_value(v) for k, v in val.items()}
    if isinstance(val, bool):
        return val
    if isinstance(val, (int, float)):
        try:
            return int(val) if float(val).is_integer() else float(val)
        except Exception:
            return str(val)
    if isinstance(val, bytes):
        return val.decode("utf-8", errors="replace")
    if val is None:
        return None
    return str(val)


def parse_wafw00f_json(wafw00f_data, model=None) -> List[OrderedDict]:
    parsed_findings = []

    results = wafw00f_data if isinstance(wafw00f_data, list) else [wafw00f_data]

    for i, result in enumerate(results, 1):
        finding = OrderedDict()
        finding["id"] = i
        finding["url"] = result.get("url", "unknown")
        finding["detected"] = result.get("detected", False)
        finding["firewall"] = result.get("firewall", "")
        finding["manufacturer"] = result.get("manufacturer", "")
        finding["confidence"] = result.get("confidence", 0)
        finding["scan_date"] = result.get("timestamp", "")

        for key, value in list(finding.items()):
            if key != "id":
                finding[key] = sanitize_value(value)

        if model:
            text_parts = []
            for key in ["url", "firewall", "manufacturer", "scan_date"]:
                v = finding.get(key)
                if isinstance(v, str) and v.strip():
                    text_parts.append(v.strip())
            combined = " ".join(text_parts) or "[empty]"
            emb = encode_with_safety(combined, model)
            if emb is not None:
                finding["embed"] = emb

        parsed_findings.append(finding)

    return parsed_findings


def main():
    parser = argparse.ArgumentParser(
        prog="convert3r_wafw00fEmbed.py",
        description="Parse Wafw00f JSON output and add IDs with optional embeddings.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python convert3r_wafw00fEmbed.py wafw00f.json
  python convert3r_wafw00fEmbed.py --embed -o enriched.json wafw00f.json
        """
    )
    parser.add_argument("input_file", help="Input Wafw00f JSON file")
    parser.add_argument("-o", "--output-file", dest="output_file", help="Output JSON file")
    parser.add_argument("--embed", action="store_true", help="Add sentence-transformer embeddings to each record")

    args = parser.parse_args()

    if not os.path.isfile(args.input_file):
        print(f"❌ Error: Input file '{args.input_file}' not found!", file=sys.stderr)
        sys.exit(1)

    try:
        with open(args.input_file, "r", encoding="utf-8") as f:
            wafw00f_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in '{args.input_file}': {e}", file=sys.stderr)
        sys.exit(1)

    model = load_embedding_model() if args.embed else None
    if args.embed and model is None:
        print("⚠️ Embedding requested but model failed to load. Continuing without embeddings.", file=sys.stderr)

    findings = parse_wafw00f_json(wafw00f_data, model=model)

    output = {
        "scan_info": {
            "scanner": "Wafw00f",
            "total_findings": len(findings),
            "input_file": args.input_file,
            "embedding_enabled": bool(model),
        },
        "findings": findings
    }

    output_file = args.output_file or str(Path(args.input_file).with_suffix(".json"))

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"✅ Parsed {len(findings)} WAF findings from {args.input_file}")
        print(f"📄 Saved to {output_file}")
    except Exception as e:
        print(f"❌ Error writing to '{output_file}': {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()