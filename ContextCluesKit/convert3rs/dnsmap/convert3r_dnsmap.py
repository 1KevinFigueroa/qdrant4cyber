#!/usr/bin/env python3
"""
convert3r_dnsmap.py - Parse dnsmap-style text output to JSON with optional embeddings

Usage: convert3r_dnsmap.py [-h] [--embed] [-o OUTPUT_FILE] input_file
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, Any, List

try:
    import torch
    from sentence_transformers import SentenceTransformer
except ImportError:
    torch = None
    SentenceTransformer = None

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


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


def parse_dnsmap_line(line: str) -> Dict[str, Any] | None:
    line = line.strip()
    if not line:
        return None

    # Domain line
    if re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9.\-]*\.[a-z]{2,}", line):
        candidate = line.lower()
        if is_valid_domain(candidate):
            return {"type": "domain", "domain": candidate}
        return None

    # IP line
    ip_match = re.fullmatch(r"IP\s+address\s+#\d+:\s*(.+)", line)
    if ip_match:
        raw_ip = ip_match.group(1).strip()
        if is_valid_ipv4(raw_ip):
            return {"type": "ip", "ip": raw_ip}
        return None

    return None


def convert_dnsmap_to_json(input_path: str) -> List[Dict[str, Any]]:
    results = []
    current_id = 1
    pending_domain = None

    with open(input_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            parsed = parse_dnsmap_line(line)
            if parsed:
                if parsed["type"] == "domain":
                    pending_domain = parsed["domain"]
                elif parsed["type"] == "ip" and pending_domain:
                    record = {
                        "id": current_id,
                        "line_number": line_num,
                        "domain": pending_domain,
                        "ip": parsed["ip"],
                        "raw_line": line.strip()
                    }
                    results.append(record)
                    current_id += 1
                    pending_domain = None

    return results


def build_embeddings(records: List[Dict[str, Any]], model_name: str = DEFAULT_MODEL):
    if torch is None or SentenceTransformer is None:
        raise ImportError("Missing dependencies. Install with: pip install sentence-transformers torch")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = SentenceTransformer(model_name, device=device)

    texts = [record["domain"] for record in records]
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
        prog="convert3r_dnsmap.py",
        description="Convert dnsmap to JSON with ID first and optional embeddings"
    )
    parser.add_argument("input_file", help="dnsmap text file")
    parser.add_argument("-o", "--output-file", dest="output_file", help="Output JSON file")
    parser.add_argument("--embed", action="store_true", help="Add sentence-transformer embeddings to each record")

    args = parser.parse_args()

    try:
        records = convert_dnsmap_to_json(args.input_file)

        if args.embed:
            print("Generating embeddings...")
            embeds = build_embeddings(records)
            for record, emb in zip(records, embeds):
                record["embed"] = emb

        output_file = args.output_file or str(Path(args.input_file).with_suffix(".json"))

        with open(output_file, "w", encoding="utf-8") as out:
            json.dump(records, out, indent=2, ensure_ascii=False)

        print(f"✓ Converted {len(records)} entries → {output_file}")
        if records:
            print("Sample JSON structure:")
            print(json.dumps(records[0], indent=2))

    except FileNotFoundError:
        print(f"❌ '{args.input_file}' not found", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()