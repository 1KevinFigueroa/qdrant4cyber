#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import Dict, List, Any

try:
    import torch
    from sentence_transformers import SentenceTransformer
except ImportError:
    torch = None
    SentenceTransformer = None

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def parse_dirb_output_comprehensive(path: str) -> List[Dict[str, Any]]:
    entries: List[Dict[str, Any]] = []

    print(f"🔍 Reading ALL lines from: {path}")

    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for line_no, raw_line in enumerate(f, 1):
            line = raw_line.rstrip("\n").strip()
            if not line:
                continue

            entry = {
                "id": len(entries) + 1,
                "line_number": line_no,
                "raw_line": line,
                "type": "unknown"
            }

            # 1. DIRB HIT: + [url](url) (CODE:xxx|SIZE:xxx)
            if line.startswith("+ ["):
                try:
                    start1 = line.find("[") + 1
                    end1 = line.find("]", start1)
                    display_url = line[start1:end1] if end1 > 0 else ""

                    start2 = line.find("(", end1) + 1 if end1 > 0 else line.find("(") + 1
                    end2 = line.find(")", start2)
                    full_url = line[start2:end2] if end2 > 0 else ""

                    if "CODE:" in line and "SIZE:" in line:
                        code_start = line.find("CODE:") + 5
                        code_end = line.find("|", code_start)
                        size_start = line.find("SIZE:") + 5

                        code = line[code_start:code_end].strip()
                        size = line[size_start:].strip()

                        entry.update({
                            "type": "hit",
                            "url": display_url,
                            "full_url": full_url,
                            "status_code": code if code.isdigit() else None,
                            "size": size if size.isdigit() else None
                        })
                except:
                    pass

            # 2. DIRECTORY: ==> DIRECTORY: [url]
            elif "==> DIRECTORY:" in line:
                try:
                    start = line.find("[") + 1
                    end = line.find("]", start)
                    url = line[start:end] if end > 0 else ""
                    entry.update({
                        "type": "directory",
                        "url": url,
                        "full_url": url
                    })
                except:
                    pass

            # 3. METADATA lines
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

            # 4. SCAN SCOPE
            elif "---- Scanning URL:" in line or "---- Entering directory:" in line:
                try:
                    start = line.find("[") + 1
                    end = line.find("]", start)
                    url = line[start:end] if end > 0 else ""
                    entry.update({
                        "type": "scope",
                        "url": url
                    })
                except:
                    pass

            # 5. WARNINGS
            elif line.startswith("(!) WARNING:"):
                entry["type"] = "warning"

            # 6. Everything else gets captured as "info"
            else:
                entry["type"] = "info"

            entries.append(entry)

    print(f"✅ Captured {len(entries)} TOTAL entries")
    return entries


def build_embeddings(entries: List[Dict[str, Any]], model_name: str = DEFAULT_MODEL) -> List[List[float]]:
    if torch is None or SentenceTransformer is None:
        raise ImportError("Missing dependencies. Install with: pip install sentence-transformers torch")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = SentenceTransformer(model_name, device=device)

    # Use raw_line or url if available, otherwise empty
    texts = []
    for entry in entries:
        text = entry.get("url") or entry.get("full_url") or entry.get("raw_line", "")
        texts.append(text.strip()[:512])  # Truncate long lines for embedding

    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        batch_size=32,
        show_progress_bar=True,
    )
    return embeddings.tolist()


def write_json(entries: List[Dict[str, Any]], output_file: str):
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)

    hits = len([e for e in entries if e["type"] == "hit"])
    dirs = len([e for e in entries if e["type"] == "directory"])
    print(f"✅ SUCCESS: {output_file}")
    print(f"   📊 {len(entries)} total entries parsed!")
    print(f"   🎯 {hits} hits found")
    print(f"   📁 {dirs} directories")


def main():
    parser = argparse.ArgumentParser(
        prog="convert3r_dirbEmbed.py",
        description="Parse ALL dirb output to JSON with optional embeddings",
    )
    parser.add_argument("input_file", help="Dirb output file")
    parser.add_argument("-o", "--output-file", dest="output_file", help="Output JSON file")
    parser.add_argument("--embed", action="store_true", help="Add sentence-transformer embeddings to each record")

    args = parser.parse_args()

    try:
        entries = parse_dirb_output_comprehensive(args.input_file)

        if args.embed:
            print("Generating embeddings...")
            embeds = build_embeddings(entries)
            for entry, emb in zip(entries, embeds):
                entry["embed"] = emb

        output_file = args.output_file or str(Path(args.input_file).with_suffix(".json"))
        write_json(entries, output_file)

    except FileNotFoundError:
        print(f"❌ File '{args.input_file}' not found!")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()