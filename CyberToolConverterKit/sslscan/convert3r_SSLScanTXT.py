#!/usr/bin/env python3

import argparse
import json
import re
from pathlib import Path

# Try importing sentence-transformers at top-level (fail fast if missing)
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDING_AVAILABLE = True
except ImportError as e:
    EMBEDDING_AVAILABLE = False


def generate_embeddings(entries: list[dict]) -> None:
    """
    Adds a new key 'embedding' to each entry in-place using all-MiniLM-L6-v2.
    Embedding is computed from:
      - target (hostname/IP)
      - port
      - supported protocols (enabled only)
      - heartbleed status per protocol

    Falls back gracefully if model not available or embedding fails.
    """
    if not EMBEDDING_AVAILABLE:
        for entry in entries:
            entry['_embedding_error'] = "sentence-transformers package missing"
        return

    try:
        model = SentenceTransformer('all-MiniLM-L6-v2')
    except Exception as e:
        for entry in entries:
            entry['_embedding_error'] = f"Model loading failed: {e}"
        return

    texts_to_embed = []
    for entry in entries:
        parts = [
            entry.get("target", "N/A"),
            str(entry.get("port", 443)),
            ",".join(k for k, v in entry.get("protocols", {}).items() if v == "enabled"),
            ",".join(f"{k}:{v}" for k, v in entry.get("heartbleed", {}).items()),
        ]
        text = " ".join(filter(None, parts))
        texts_to_embed.append(text)

    try:
        embeddings = model.encode(texts_to_embed, convert_to_tensor=False, show_progress_bar=False).tolist()
        if len(embeddings) == len(entries):
            for idx, emb in enumerate(embeddings):
                entries[idx]["embedding"] = emb
        else:
            # Mismatch: mark all as failed
            for entry in entries:
                entry['_embedding_error'] = "Embedding length mismatch"
    except Exception as e:
        for entry in entries:
            entry['_embedding_error'] = f"Embedding computation failed: {e}"


def parse_sslscan_file(input_file: str, output_file: str, embed: bool = False) -> None:
    """Parse sslscan text file into structured JSON, optionally with embeddings."""
    
    # Input validation
    input_path = Path(input_file)
    if not input_path.is_file():
        raise FileNotFoundError(f"Input file does not exist or is not a file: {input_file}")

    try:
        with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except OSError as e:
        raise IOError(f"Failed to read input file '{input_file}': {e}") from e

    # Split blocks by "Connected to" pattern (look-ahead keeps full match)
    blocks = re.split(r'(?=Connected to \S+)', content)
    
    results = []
    entry_id = 1
    non_empty_blocks = [b for b in blocks if b.strip()]
    print(f"DEBUG: Found {len(non_empty_blocks)} raw blocks")

    for block_idx, block_text in enumerate(blocks, start=1):
        block_text = block_text.strip()
        if not block_text or not block_text.startswith('Connected to'):
            continue

        try:
            parsed = parse_single_sslscan_block(block_text, entry_id)
        except Exception as e:
            print(f"⚠️  Block {block_idx} failed parsing: {e}")
            entry_id += 1
            continue

        # Only add valid entries (must have target)
        if parsed.get('target'):
            results.append(parsed)
            ip = parsed.get('ip', 'N/A')
            print(f"✅ [{entry_id}] {parsed['target']} (IP: {ip})")
        else:
            print(f"⚠️  Block {block_idx} skipped (no target found)")

        entry_id += 1

    # Embed if requested
    if embed and results:
        print("🔐 Generating embeddings...")
        generate_embeddings(results)

    # Write JSON
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
    except OSError as e:
        raise IOError(f"Failed to write output file '{output_file}': {e}") from e

    print(f"\n🎉 SUCCESS: Parsed {len(results)}/{entry_id-1} entries")
    print(f"📁 Saved to: {output_path}")


def parse_single_sslscan_block(block_text: str, entry_id: int) -> dict:
    """Parse ONE complete sslscan block with Heartbleed support."""
    result = {
        "id": entry_id,
        "ip": None,
        "target": None,
        "port": 443,
        "sni": None,
        "protocols": {},
        "heartbleed": {},
        "ciphers": [],
        "certificate": {}
    }

    # 1. IP from "Connected to 87.250.250.16"
    ip_match = re.search(r'Connected to\s+(\S+)', block_text)
    result["ip"] = ip_match.group(1) if ip_match else None

    # 2. Target/Port/SNI from header
    header_pattern = r'Testing SSL server\s+(.+?)\s+on port\s+(\d+)\s+using SNI name\s+(.+?)(?=\n|$)'
    header_match = re.search(header_pattern, block_text, re.DOTALL)
    if header_match:
        result["target"] = header_match.group(1).strip()
        result["port"] = int(header_match.group(2))
        result["sni"] = header_match.group(3).strip()

    # 3. Protocols (SSLv2, TLSv1.0, etc.)
    proto_matches = re.findall(r'^(\w+(?:v?\d+\.?\d*))\s+(enabled|disabled)', block_text, re.MULTILINE)
    for proto, status in proto_matches:
        result["protocols"][proto] = status

    # 4. HEARTBLEED SECTION
    heartbleed_pattern = r'(\w+(?:v?\d+\.?\d*))\s+(not vulnerable to heartbleed|vulnerable to heartbleed)'
    for match in re.finditer(heartbleed_pattern, block_text, re.MULTILINE):
        proto = match.group(1)
        status = match.group(2).strip()
        result["heartbleed"][proto] = status

    # 5. Ciphers
    cipher_lines = []
    for line in block_text.splitlines():
        if 'bits' in line and ('Preferred' in line or 'Accepted' in line):
            cipher_line_match = re.match(
                r'^(Preferred|Accepted)\s+(\w+(?:v\d+\.\d+))\s+\d+\s+bits\s+(.+?)(?:\s+Curve|$)',
                line.strip()
            )
            if cipher_line_match:
                status, proto, cipher = cipher_line_match.groups()
                cipher_lines.append({
                    "status": status.strip(),
                    "protocol": proto.strip(),
                    "cipher": cipher.strip()
                })
    result["ciphers"] = cipher_lines

    # 6. Certificate details
    cert_patterns = {
        'signature_algorithm': r'Signature Algorithm:\s+(.+)',
        'rsa_key_strength': r'RSA Key Strength:\s+(.+)',
        'ecc_curve_name': r'ECC Curve Name:\s+(.+)',
        'ecc_key_strength': r'ECC Key Strength:\s+(.+)',
        'subject': r'Subject:\s+(.+)',
        'issuer': r'Issuer:\s+(.+)',
        'not_valid_before': r'Not valid before:\s+(.+)',
        'not_valid_after': r'Not valid after:\s+(.+)'
    }
    for key, pattern in cert_patterns.items():
        match = re.search(pattern, block_text)
        if match:
            result["certificate"][key] = match.group(1).strip()

    # 7. Altnames (subjectAltName / DNS names)
    altnames_pattern = r'Altnames:\s+(.+?)(?:\n\nIssuer:|\n\nNot valid before|$)'
    altnames_match = re.search(altnames_pattern, block_text, re.DOTALL)
    if altnames_match:
        altnames = [name.strip() for name in altnames_match.group(1).split(',') if name.strip()]
        result["certificate"]["altnames"] = altnames

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Parse sslscan multi-entry text file into structured JSON."
    )
    parser.add_argument("input_file", help="Path to input sslscan .txt file")
    parser.add_argument("output_file", help="Output JSON file path")
    parser.add_argument(
        "--embed",
        action="store_true",
        help="Generate embeddings using all-MiniLM-L6-v2 for each entry"
    )
    args = parser.parse_args()

    if args.embed and not EMBEDDING_AVAILABLE:
        raise ImportError(
            "⚠️  --embed requires sentence-transformers. "
            "Install with: pip install sentence-transformers"
        )

    parse_sslscan_file(args.input_file, args.output_file, embed=args.embed)


if __name__ == "__main__":
    main()
