#!/usr/bin/env python3
import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

import whois

try:
    import torch
    from sentence_transformers import SentenceTransformer
except ImportError:
    torch = None
    SentenceTransformer = None

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def load_domains(input_file):
    with open(input_file, "r", encoding="utf-8") as f:
        return [line.strip().lower() for line in f if line.strip()]


def build_embeddings(texts, model_name=DEFAULT_MODEL):
    if torch is None or SentenceTransformer is None:
        raise ImportError("Missing dependencies. Install with: pip install sentence-transformers torch")

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = SentenceTransformer(model_name, device=device)
    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        normalize_embeddings=True,
        batch_size=32,
        show_progress_bar=True
    )
    return embeddings.tolist()


def whois_to_json(domain, entry_id, embed=None):
    try:
        w = whois.whois(domain)

        result = {
            "id": entry_id,
            "domain": domain,
            "timestamp": datetime.now().isoformat(),
            "whois_data": {
                "domain_name": getattr(w, "domain", None),
                "registrar": getattr(w, "registrar", None),
                "creation_date": str(getattr(w, "creation_date", None)),
                "expiration_date": str(getattr(w, "expiration_date", None)),
                "updated_date": str(getattr(w, "updated_date", None)),
                "name_servers": getattr(w, "name_servers", None),
                "status": getattr(w, "status", None),
                "emails": getattr(w, "emails", None),
                "country": getattr(w, "country", None),
                "state": getattr(w, "state", None),
                "city": getattr(w, "city", None),
                "organization": getattr(w, "org", None),
                "registrant": {
                    "name": getattr(w, "name", None),
                    "organization": getattr(w, "registrant_organization", None),
                    "street": getattr(w, "address", None),
                    "city": getattr(w, "city", None),
                    "state": getattr(w, "state", None),
                    "postal_code": getattr(w, "postal_code", None),
                    "country": getattr(w, "country", None),
                },
            },
            "raw_whois": getattr(w, "text", None),
        }

        if embed is not None:
            result["embed"] = embed

        return result

    except Exception as e:
        result = {
            "id": entry_id,
            "domain": domain,
            "timestamp": datetime.now().isoformat(),
            "error": str(e),
            "whois_data": None,
            "raw_whois": None,
        }

        if embed is not None:
            result["embed"] = embed

        return result


def main():
    parser = argparse.ArgumentParser(
        prog="convert3r_whois.py",
        description="WHOIS Lookup to JSON with IDs and optional embeddings",
    )
    parser.add_argument("input_file", help="Input file containing one domain per line")
    parser.add_argument("-o", "--output-file", dest="output_file", help="Output JSON file")
    parser.add_argument("--embed", action="store_true", help="Add sentence-transformer embeddings to each record")

    args = parser.parse_args()

    input_path = Path(args.input_file)
    if not input_path.exists():
        print(f"Error: File '{input_path}' not found!", file=sys.stderr)
        sys.exit(1)

    domains = load_domains(str(input_path))
    print(f"Loaded {len(domains)} domains")

    embeddings = None
    if args.embed:
        print("Generating embeddings...")
        embeddings = build_embeddings(domains)
        print("Embeddings generated")

    all_results = []
    for entry_id, domain in enumerate(domains, start=1):
        print(f"[{entry_id}] Looking up {domain}...")
        embed = embeddings[entry_id - 1] if embeddings is not None else None
        all_results.append(whois_to_json(domain, entry_id, embed=embed))

    output_path = Path(args.output_file) if args.output_file else input_path.with_suffix(".json")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False, default=str)

    print(f"Results saved to: {output_path.resolve()}")
    print(f"Processed {len(all_results)} domains with IDs 1-{len(all_results)}")


if __name__ == "__main__":
    main()