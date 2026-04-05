#!/usr/bin/env python3
"""
convert3r_dnsmap.py - Parse dnsmap-style text output to JSON with optional embeddings

Usage: convert3r_dnsmap.py [-h] [--embed] [-o OUTPUT_FILE] input_file
"""

import argparse
import json
import logging
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

try:
    import torch
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    print(
        "Error: Required package 'sentence-transformers' not found.\n"
        "Install with: pip install sentence-transformers torch transformers\n"
        f"Details: {e}",
        file=sys.stderr
    )
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)
_MODEL_CACHE = None
DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def get_model() -> SentenceTransformer:
    global _MODEL_CACHE
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE

    logger.info("Loading '%s' model (cpu)...", DEFAULT_MODEL)
    model = SentenceTransformer(DEFAULT_MODEL, device="cpu")
    _MODEL_CACHE = model
    return model


def is_valid_ipv4(ip: str) -> bool:
    parts = ip.split(".")
    if len(parts) != 4:
        return False
    for part in parts:
        if not part.isdigit() or not 0 <= int(part) <= 255:
            return False
        if len(part) > 1 and part[0] == "0":
            return False
    return True


def is_valid_domain(domain: str) -> bool:
    if not domain or len(domain) > 253:
        return False
    domain = domain.lower()
    labels = domain.split(".")
    if len(labels) < 2:
        return False
    for label in labels:
        if not label or len(label) > 63:
            return False
        if not re.fullmatch(r"[a-z0-9](?:[a-z0-9\-]*[a-z0-9])?", label):
            return False
    return True


def compute_embedding(model: SentenceTransformer, text: str) -> list[float]:
    cleaned = re.sub(r"\s+", " ", text.strip())
    embedding = model.encode([cleaned], convert_to_numpy=True, show_progress_bar=False, normalize_embeddings=True)
    return embedding[0].tolist()


def parse_dnsmap_output(input_path: str, output_path: str, embed: bool = False) -> None:
    if not Path(input_path).is_file():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    model = get_model() if embed else None
    records = []
    domain = None
    line_count = 0
    error_count = 0

    logger.info("Parsing input%s...", " and generating embeddings" if embed else "")

    with open(input_path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line_count += 1
            line = raw_line.strip()
            if not line:
                continue

            if re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9.\-]*\.[a-z]{2,}", line):
                candidate = line.lower()
                if is_valid_domain(candidate):
                    domain = candidate
                else:
                    error_count += 1
                    logger.warning("Invalid domain at line %d: '%s'", line_count, line)
                continue

            ip_match = re.fullmatch(r"IP\s+address\s+#\d+:\s*(.+)", line)
            if ip_match and domain:
                raw_ip = ip_match.group(1).strip()
                if is_valid_ipv4(raw_ip):
                    try:
                        record = {
                            "id": len(records) + 1,
                            "domain": domain,
                            "ip": raw_ip,
                        }
                        if embed and model is not None:
                            record["embed"] = compute_embedding(model, domain)
                        records.append(record)
                    except Exception as e:
                        error_count += 1
                        logger.error("Failed to process record: domain='%s', ip='%s' — %s", domain, raw_ip, str(e))
                else:
                    error_count += 1
                    logger.warning("Invalid IP at line %d for '%s': %s", line_count, domain, raw_ip)

                domain = None

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(records, f, indent=2, ensure_ascii=False)

    logger.info("✅ Wrote %d records to %s", len(records), output_path)
    if error_count > 0:
        logger.warning("⚠️ Skipped %d invalid entries", error_count)


def main():
    parser = argparse.ArgumentParser(
        prog="convert3r_dnsmap.py",
        description="Convert dnsmap-style domain/IP pairs to JSON with optional embeddings",
    )
    parser.add_argument("input_file", help="Input file with domain/IP pairs")
    parser.add_argument("-o", "--output-file", dest="output_file", help="Output JSON file")
    parser.add_argument("--embed", action="store_true", help="Generate sentence embeddings for each record")

    args = parser.parse_args()

    try:
        output_file = args.output_file or str(Path(args.input_file).with_suffix(".json"))
        parse_dnsmap_output(args.input_file, output_file, embed=args.embed)
    except Exception as e:
        logger.critical("Fatal error: %s", str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()