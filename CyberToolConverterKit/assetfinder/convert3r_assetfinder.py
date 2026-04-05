#!/usr/bin/env python3
import argparse
import json
from pathlib import Path
from typing import List, Dict, Any

try:
    import torch
    from sentence_transformers import SentenceTransformer
except ImportError:
    torch = None
    SentenceTransformer = None

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def parse_assetfinder_file(input_file: str) -> List[Dict[str, Any]]:
    entries = []

    with open(input_file, "r", encoding="utf-8", errors="ignore") as f:
        for line_num, line in enumerate(f, 1):
            raw_line = line.rstrip("\n")
            domain = raw_line.strip()

            if not domain or domain.startswith("#"):
                continue

            entries.append({
                "id": len(entries) + 1,
                "line_number": line_num,
                "domain": domain,
                "raw_line": raw_line
            })

    return entries


def build_embeddings(texts: List[str], model_name: str = DEFAULT_MODEL) -> List[List[float]]:
    if torch is None or SentenceTransformer is None:
        raise ImportError("Missing dependencies. Install with: pip install sentence-transformers torch")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = SentenceTransformer(model_name, device=device)
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
    print(f"✅ Saved {len(entries)} assetfinder domains to {output_file}")


def main():
    parser = argparse.ArgumentParser(
        prog="convert3r_assetfinderEmbed.py",
        description="Parse assetfinder output into structured JSON with IDs and optional embeddings",
    )
    parser.add_argument("input_file", help="Assetfinder output text file (one domain per line)")
    parser.add_argument("-o", "--output-file", dest="output_file", help="Output JSON file")
    parser.add_argument("--embed", action="store_true", help="Add sentence-transformer embeddings to each record")

    args = parser.parse_args()

    entries = parse_assetfinder_file(args.input_file)

    if not entries:
        print("❌ No valid domains found")
        return

    if args.embed:
        texts = [entry["domain"] for entry in entries]
        embeds = build_embeddings(texts)
        for entry, emb in zip(entries, embeds):
            entry["embed"] = emb

    output_file = args.output_file or str(Path(args.input_file).with_suffix(".json"))
    write_json(entries, output_file)


if __name__ == "__main__":
    main()