#!/usr/bin/env python3
import json
import argparse
from typing import Dict, List, Any, Optional
import sys

try:
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    raise RuntimeError(
        "❌ Missing dependency: 'sentence-transformers'. Install with:\n"
        "   pip install -U sentence-transformers"
    ) from e


def _get_embedding_text(entry: Dict[str, Any]) -> str:
    """
    Return the most semantically meaningful text string for embedding.
    Prioritizes fields likely to contain high-value content (e.g., URLs, descriptions).
    Falls back to raw_line if nothing else is present or useful.
    """
    # Try these fields in order of priority
    candidates = [
        entry.get("full_url") or entry.get("url"),
        entry.get("raw_line", "").strip(),
        entry.get("description"),
        entry.get("value"),  # metadata
        entry.get("key"),   # metadata
    ]
    for text in candidates:
        if isinstance(text, str) and len(text.strip()) > 0:
            return text.strip()
    return ""  # last resort: empty string → zero embedding


def encode_entries_with_embeddings(entries: List[Dict[str, Any]], model: SentenceTransformer) -> None:
    """
    In-place: adds 'embedding' field to each entry.
    Uses batching for efficiency and handles empty/invalid entries gracefully.
    """
    print(f"📊 Generating embeddings for {len(entries)} entries...")
    texts = [_get_embedding_text(e) for e in entries]
    
    # Filter out truly empty strings (to avoid unnecessary encoding)
    non_empty_indices = [i for i, t in enumerate(texts) if t]
    non_empty_texts = [texts[i] for i in non_empty_indices]

    if not non_empty_texts:
        print("⚠️ No meaningful content found — embeddings will be zeros.")
        empty_emb = [0.0] * 384  # all-MiniLM-L6-v2 dimension
        for e in entries:
            e["embedding"] = empty_emb
        return

    # Encode non-empty texts in batches (GPU/CPU)
    try:
        embeddings_list = model.encode(
            non_empty_texts,
            convert_to_numpy=False,
            batch_size=32,  # optimal default; adjust if OOM on large models
            show_progress_bar=True,
            normalize_embeddings=True  # cosine similarity-friendly
        )
    except Exception as enc_err:
        print(f"⚠️ Embedding failed: {enc_err}. Using zero vectors.")
        for i in non_empty_indices:
            entries[i]["embedding"] = [0.0] * 384
        return

    # Assign embeddings back to original positions
    emb_idx = 0
    for i, entry in enumerate(entries):
        if texts[i]:
            entry["embedding"] = [float(x.item()) for x in embeddings_list[emb_idx]]
            emb_idx += 1
        else:
            # Empty text → zero vector (dimensionally consistent)
            entry["embedding"] = [0.0] * 384


def parse_dirb_output_comprehensive(path: str) -> Dict[str, Any]:
    entries: List[Dict[str, Any]] = []
    print(f"🔍 Reading ALL lines from: {path}")
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line_no, raw_line in enumerate(f, 1):
            line = raw_line.rstrip("\n").strip()
            if not line:  # Skip empty lines
                continue

            entry = {
                "id": len(entries) + 1,
                "line_number": line_no,
                "raw_line": line,
                "type": "unknown"
            }

            try:
                # 1. DIRB HIT: + [display_url] (CODE:xxx|SIZE:xxx)
                if line.startswith("+ ["):
                    start1 = line.find("[") + 1
                    end1 = line.find("]", start1)
                    display_url = line[start1:end1] if end1 > 0 else ""
                    
                    # Extract full URL: (http://...)
                    start2 = line.find("(", end1) + 1 if end1 > 0 else line.find("(") + 1
                    end2 = line.find(")", start2)
                    full_url = line[start2:end2] if end2 > 0 else ""
                    
                    # Extract status & size
                    status_code = None
                    size_str = None
                    if "CODE:" in line and "|" in line:
                        try:
                            parts = line.split("|")
                            for p in parts:
                                if p.strip().startswith("CODE:"):
                                    code_val = p.replace("CODE:", "").strip()
                                    status_code = int(code_val) if code_val.isdigit() else None
                                elif p.strip().startswith("SIZE:"):
                                    size_str = p.replace("SIZE:", "").strip()
                        except Exception:
                            pass

                    entry.update({
                        "type": "hit",
                        "url": display_url,
                        "full_url": full_url,
                        "status_code": status_code,
                        "size": size_str
                    })

                # 2. DIRECTORY: ==> DIRECTORY: [url]
                elif "==> DIRECTORY:" in line:
                    start = line.find("[") + 1
                    end = line.find("]", start)
                    url = line[start:end] if end > 0 else ""
                    entry.update({
                        "type": "directory",
                        "url": url,
                        "full_url": url
                    })

                # 3. METADATA lines (key: value)
                elif ":" in line and not line.startswith("----"):
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip()
                        entry.update({
                            "type": "metadata",
                            "key": key,
                            "value": value
                        })

                # 4. SCAN SCOPE: ---- Scanning URL: [url]
                elif "---- Scanning URL:" in line or "---- Entering directory:" in line:
                    start = line.find("[") + 1
                    end = line.find("]", start)
                    url = line[start:end] if end > 0 else ""
                    entry.update({
                        "type": "scope",
                        "url": url
                    })

                # 5. WARNINGS: (!) WARNING: ...
                elif line.startswith("(!) WARNING:"):
                    entry["type"] = "warning"

                # 6. Fallback: generic info
                else:
                    entry["type"] = "info"
            except Exception as parse_err:
                print(f"⚠️ Parse warning at line {line_no}: {parse_err}")

            entries.append(entry)

    print(f"✅ Captured {len(entries)} TOTAL entries (every meaningful line)")
    return {
        "total_entries": len(entries),
        "results": entries
    }


def main():
    parser = argparse.ArgumentParser(
        description="Parse dirb output to JSON + add semantic embeddings."
    )
    parser.add_argument("input", help="Dirb output file")
    parser.add_argument("-o", "--output", default="dirb_complete_embedded.json")
    parser.add_argument(
        "-d", "--device",
        choices=["cpu", "cuda"],
        default=None,
        help="Device to run embedding model on (auto-detects if omitted)"
    )
    
    args = parser.parse_args()

    # Load model ONCE at startup
    try:
        print("🚀 Loading all-MiniLM-L6-v2 model...")
        model_kwargs = {"device": args.device} if args.device else {}
        model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2", **model_kwargs)
        print(f"✅ Model loaded successfully (dimension: {model.get_sentence_embedding_dimension()})")
    except Exception as e:
        print(f"❌ Failed to load embedding model: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        # 1. Parse dirb output
        data = parse_dirb_output_comprehensive(args.input)

        # 2. Add embeddings in-place for all entries
        encode_entries_with_embeddings(data["results"], model)

        # 3. Write result to JSON
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        print(f"✅ Embedded JSON saved: {args.output}")

    except FileNotFoundError as e:
        print(f"❌ Input file not found: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
