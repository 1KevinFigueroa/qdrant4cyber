#!/usr/bin/env python3
"""
Parse dnsmap-style text output → JSON with sentence-transformer embeddings.
Uses all-MiniLM-L6-v2 for embedding domain names.

Security: Input validation, safe model loading, no eval/exec/dynamic imports.
"""

import argparse
import json
import logging
import re
import sys
from pathlib import Path

try:
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    print(
        "Error: Required package 'sentence-transformers' not found.\n"
        "Install with: pip install sentence-transformers torch transformers\n"
        f"Details: {e}",
        file=sys.stderr
    )
    sys.exit(1)


# Configure logging for production safety (no sensitive data)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Global model cache to avoid repeated downloads
_MODEL_CACHE = None


def get_model() -> SentenceTransformer:
    """Load all-MiniLM-L6-v2 once, with fallback and caching."""
    global _MODEL_CACHE
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE

    logging.info("Loading 'all-MiniLM-L6-v2' model (may download on first run)...")
    try:
        # Force CPU to avoid CUDA OOM in headless environments
        model = SentenceTransformer(
            "sentence-transformers/all-MiniLM-L6-v2",
            device="cpu"  # Explicitly use CPU for safety & portability
        )
        _MODEL_CACHE = model
        logging.info("Model loaded successfully.")
        return model
    except Exception as e:
        logging.error("Failed to load embedding model: %s", str(e))
        raise


def is_valid_ipv4(ip: str) -> bool:
    """Validate IPv4 address (strict, no leading zeros)."""
    parts = ip.split(".")
    if len(parts) != 4:
        return False
    for part in parts:
        if not part.isdigit() or not 0 <= int(part) <= 255:
            return False
        if len(part) > 1 and part[0] == '0':
            return False
    return True


def is_valid_domain(domain: str) -> bool:
    """
    Validate domain name per RFC 1035/1123 (case-insensitive, normalized).
    - Max 253 chars total
    - Labels separated by dots; each label alphanumeric/hyphen (not start/end hyphen)
    - TLD at least 2 letters
    """
    if not domain or len(domain) > 253:
        return False

    domain = domain.lower()
    labels = domain.split(".")
    if len(labels) < 2:
        return False

    for label in labels:
        if not label or len(label) > 63:
            return False
        # Regex: start/end with alphanum, middle may include hyphens
        if not re.fullmatch(r"[a-z0-9](?:[a-z0-9\-]*[a-z0-9])?", label):
            return False

    return True


def compute_embedding(model: SentenceTransformer, text: str) -> list[float]:
    """Compute embedding for a single string. Returns flat list of floats."""
    try:
        # Ensure input is clean string (no newlines/special chars)
        cleaned = re.sub(r"\s+", " ", text.strip())
        embedding = model.encode([cleaned], convert_to_tensor=False, show_progress_bar=False)
        # Convert numpy array → Python list for JSON compatibility
        return embedding[0].tolist()
    except Exception as e:
        logging.error("Embedding failed for '%s': %s", text[:50], str(e))
        raise


def parse_dnsmap_output(input_path: str, output_path: str) -> None:
    """
    Parse dnsmap-style input (domain + "IP address #N: x.x.x.x" lines) → JSON array.
    Each record: {"id": int, "domain": str, "ip": str, "embedding": list[float]}
    """
    if not Path(input_path).is_file():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    model = get_model()
    records = []
    domain = None

    logging.info("Parsing input and generating embeddings...")
    line_count = 0
    error_count = 0

    with open(input_path, "r", encoding="utf-8") as f:
        for raw_line in f:
            line_count += 1
            line = raw_line.strip()
            if not line:
                continue

            # Match domain pattern (e.g., "www.yandex.ru")
            if re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9.\-]*\.[a-z]{2,}", line):
                candidate = line.lower()
                if is_valid_domain(candidate):
                    domain = candidate
                else:
                    error_count += 1
                    logging.warning("Invalid domain at line %d: '%s'", line_count, line)
                continue

            # Match IP line (e.g., "IP address #1: 87.250.254.79")
            ip_match = re.fullmatch(r"IP\s+address\s+#\d+:\s*(.+)", line)
            if ip_match and domain:
                raw_ip = ip_match.group(1).strip()
                if is_valid_ipv4(raw_ip):
                    try:
                        # Compute embedding only for clean domain
                        embed = compute_embedding(model, domain)

                        record = {
                            "id": len(records) + 1,
                            "domain": domain,
                            "ip": raw_ip,
                            "embedding": embed  # e.g., [0.123, -0.456, ...] (384 floats)
                        }
                        records.append(record)

                    except Exception as e:
                        error_count += 1
                        logging.error(
                            "Failed to process record: domain='%s', ip='%s' — %s",
                            domain, raw_ip, str(e)
                        )
                else:
                    error_count += 1
                    logging.warning("Invalid IP at line %d for '%s': %s", line_count, domain, raw_ip)

                # Reset domain after use (prevents duplicate bindings)
                domain = None

    # Write output JSON with proper formatting
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
        logging.info(f"✅ Wrote {len(records)} records (with embeddings) to {output_path}")
        if error_count > 0:
            logging.warning(f"⚠️ Skipped {error_count} invalid entries")
    except OSError as e:
        raise IOError(f"Failed to write output file: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert dnsmap-style domain/IP pairs → JSON with sentence-transformer embeddings.",
        epilog="""
Input format (text lines):
  www.yandex.ru
  IP address #1: 77.88.55.88

Output (JSON):
  [
    {
      "id": 1,
      "domain": "www.yandex.ru",
      "ip": "77.88.55.88",
      "embedding": [0.23, -0.45, ...]  // 384 floats
    },
    ...
  ]

Notes:
- Embeddings use all-MiniLM-L6-v2 (384-dimensional).
- Fails safely if sentence-transformers not installed.
        """
    )
    parser.add_argument("input_file", help="Input file with domain/IP pairs")
    parser.add_argument("output_file", help="Output JSON path")

    args = parser.parse_args()
    
    try:
        parse_dnsmap_output(args.input_file, args.output_file)
    except Exception as e:
        logging.critical("Fatal error: %s", str(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
