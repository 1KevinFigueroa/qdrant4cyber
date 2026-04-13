#!/usr/bin/env python3
"""
Convert DNS CSV to JSON with sequential IDs and semantic embeddings using all-MiniLM-L6-v2.

Security & Reliability Features:
• Input validation (file existence, encoding)
• Control character sanitization before embedding
• CPU-only inference enforced
• Graceful error handling + user-friendly messages
• No shell commands / no eval/exec
"""

import argparse
import csv
import json
import os
import re

# Optional import — handled gracefully if missing
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDING_AVAILABLE = True
except ImportError:
    EMBEDDING_AVAILABLE = False

try:
    import torch
except ImportError:
    torch = None


def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert DNS CSV to JSON with sequential IDs and embeddings (optional)"
    )
    parser.add_argument("input_csv", help="Input DNS CSV file")
    parser.add_argument("output_json", help="Output JSON file")
    parser.add_argument(
        "--embed",
        action="store_true",
        help="Enable sentence-transformer embedding of 'name' + 'address' fields"
    )
    return parser.parse_args()


def sanitize_for_embedding(text: str) -> str:
    """Remove control characters that may break embedding models."""
    if not isinstance(text, str):
        return ""
    # Keep only printable & whitespace (space, tab, newline)
    return re.sub(r'[\x00-\x1F\x7F]', '', text)


def add_embeddings(records: list, model: "SentenceTransformer") -> None:
    """
    In-place: Adds 'embedding' to each record using all-MiniLM-L6-v2.
    
    Embeds: "<name> <address>"
    """
    texts = []
    for rec in records:
        name = sanitize_for_embedding(rec.get("name", "") or "")
        addr = sanitize_for_embedding(rec.get("address", "") or "")
        combined = f"{name} {addr}".strip()
        if not combined:
            combined = "[empty]"  # prevent empty input from breaking model
        texts.append(combined)

    if not EMBEDDING_AVAILABLE or torch is None:
        raise RuntimeError("sentence-transformers and/or torch are required for embedding")

    try:
        with torch.no_grad():  # ✅ Correct context manager for inference
            embeddings = model.encode(
                texts,
                convert_to_tensor=True,   # PyTorch tensor
                show_progress_bar=False,
                device="cpu"             # 🔒 Force CPU for security & portability
            )
        
        # Detach from graph, move to CPU (defensive), then to list-of-lists
        emb_list = embeddings.detach().cpu().tolist()

        for rec, emb in zip(records, emb_list):
            rec["embedding"] = emb  # list of 384 floats for all-MiniLM-L6-v2

    except Exception as e:
        raise RuntimeError(f"Failed to generate embeddings: {e}") from e


def csv_to_dns_json(csv_file: str, json_file: str, embed: bool = False) -> None:
    """Convert DNS CSV to structured JSON with optional embeddings."""
    # Validate input file
    if not os.path.exists(csv_file):
        print(f"❌ Error: Input file '{csv_file}' not found!")
        return

    records = []
    id_counter = 1

    try:
        with open(csv_file, 'r', newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            # Read header
            try:
                header = next(reader)
            except StopIteration:
                print("❌ Error: CSV is empty or has no header row.")
                return

            if not header:
                print("❌ Error: No headers found in CSV.")
                return

            print(f"📋 Headers found: {header}")

            # Process each row
            for row in reader:
                # Pad short rows with empty strings (defensive)
                while len(row) < len(header):
                    row.append('')

                record = {
                    "id": id_counter,
                    "type": row[0].strip() if row[0] else "",
                    "name": row[1].strip() if row[1] else "",
                    "address": row[2].strip() if row[2] else "",
                    "target": row[3].strip() if row[3] else "",
                    "port": row[4].strip() if row[4] else "",
                    "string": row[5].strip() if len(row) > 5 and row[5] else ""
                }

                # Only include records with at least one meaningful field
                if record["name"] or record["address"] or record.get("type") or record.get("target"):
                    records.append(record)
                    id_counter += 1

    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        return

    # Embed (if requested & available)
    model = None
    if embed:
        if not EMBEDDING_AVAILABLE or torch is None:
            print("⚠️  Skipping embedding: sentence-transformers/torch not installed.")
            print("   Install with: pip install sentence-transformers torch --index-url https://download.pytorch.org/whl/cpu")
        else:
            try:
                print("🧠 Loading all-MiniLM-L6-v2 model (first run may download)...")
                model = SentenceTransformer('all-MiniLM-L6-v2')
                add_embeddings(records, model)
                print(f"✅ Generated embeddings for {len(records)} records.")
            except Exception as e:
                print(f"⚠️  Embedding skipped due to error: {e}")
    else:
        print("ℹ️  Embeddings disabled (--embed not specified).")

    # Prepare output
    output = {
        "scan_info": {
            "input_file": csv_file,
            "total_records": len(records),
            "headers": header,
            "embedding_enabled": embed and model is not None
        },
        "records": records
    }

    # Write JSON safely
    try:
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"✅ Converted {len(records)} DNS records from '{csv_file}'")
        print(f"📄 Saved to: {json_file}")
    except PermissionError:
        print(f"❌ Permission denied writing to '{json_file}'. Check file permissions.")
    except OSError as e:
        print(f"❌ OS error while writing JSON: {e}")


def main():
    args = parse_args()
    csv_to_dns_json(args.input_csv, args.output_json, embed=args.embed)


if __name__ == "__main__":
    main()
