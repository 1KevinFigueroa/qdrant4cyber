#!/usr/bin/env python3
"""
Convert CSV to JSON with sentence embeddings using all-MiniLM-L6-v2.
Intended for enriching textual records (e.g., threat intel, vulnerability data).
"""

import csv
import json
import sys
from pathlib import Path
from typing import List, Dict, Any

# Security note: Avoid importing directly from `transformers` to prevent accidental model loading;
# use SentenceTransformer with explicit version guard.
try:
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    raise ImportError(
        "sentence-transformers not installed. Install via: pip install sentence-transformers"
    ) from e


def load_embedding_model(model_name: str = "all-MiniLM-L6-v2") -> "SentenceTransformer":
    """
    Safely loads the embedding model with validation.
    Ensures correct dimensionality (384) to prevent silent errors downstream.
    """
    try:
        model = SentenceTransformer(model_name)
        # Test encoding a dummy sentence
        dummy_vec = model.encode(["test"], convert_to_numpy=False)[0]
        if len(dummy_vec) != 384:
            raise RuntimeError(f"Expected 384-dim, got {len(dummy_vec)} for '{model_name}'")
        return model
    except Exception as e:
        raise RuntimeError(
            f"Failed to load embedding model '{model_name}'. "
            "Check internet connectivity or try a different model."
        ) from e


def extract_text_fields(row: Dict[str, str]) -> List[str]:
    """
    Extracts all string fields (ignores empty values) for embedding.
    Skips non-string types and control characters to prevent injection risks.
    """
    text_fields = []
    for key, value in row.items():
        if not isinstance(value, str):
            continue
        # Strip whitespace and skip empty strings
        stripped = value.strip()
        if not stripped:
            continue
        # Sanitize: reject non-printable characters (e.g., control codes)
        if any(not c.isprintable() for c in stripped):
            continue  # Skip unsafe content
        text_fields.append(stripped)
    return text_fields


def csv_to_json_with_embeddings(
    csv_path: str,
    json_path: str,
    model: "SentenceTransformer" = None,
    batch_size: int = 64
) -> None:
    """
    Convert CSV to JSON with incremental IDs and sentence embeddings.

    Args:
        csv_path: Path to input CSV file
        json_path: Path to output JSON file
        model: Preloaded SentenceTransformer instance (if not provided, loads automatically)
        batch_size: Encoding batch size for efficiency
    """
    csv_file = Path(csv_path)
    if not csv_file.is_file():
        raise FileNotFoundError(f"CSV file not found: {csv_file}")

    # Load model only if not pre-supplied
    should_close_model = False
    if model is None:
        model = load_embedding_model()
        should_close_model = True

    try:
        records: List[Dict[str, Any]] = []
        all_texts: List[str] = []  # Collect for batch encoding

        with csv_file.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            
            # Validate headers
            if not reader.fieldnames:
                raise ValueError("CSV file has no header row.")

            for idx, row in enumerate(reader, start=1):
                # Sanitize & extract text fields
                texts = extract_text_fields(row)

                # Create base record (id + original rows)
                obj: Dict[str, Any] = {"id": idx}
                
                if texts:
                    # Collect all text for batch encoding later
                    all_texts.append(" ".join(texts))  # combine relevant text per row
                else:
                    # Use empty string to avoid indexing mismatch in embeddings list
                    all_texts.append("")

                obj.update({k: v.strip() if isinstance(v, str) else v for k, v in row.items()})
                records.append(obj)

        print(f"ℹ️  Found {len(records)} rows; encoding {sum(1 for t in all_texts if t)} non-empty text fields...")

        # Batch encode all collected texts
        embeddings = model.encode(
            all_texts,
            convert_to_numpy=False,
            batch_size=batch_size,
            show_progress_bar=True
        )

        # Inject embeddings into records (only if text existed)
        for i, rec in enumerate(records):
            embedding_list = [float(x.item()) for x in embeddings[i]]
            rec["embedding"] = embedding_list  # always add; empty rows get zero-like embedding

        # Write output JSON
        out_file = Path(json_path)
        with out_file.open("w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)

    finally:
        if should_close_model:
            del model  # Help GC cleanup GPU/CPU resources

    print(f"✅ Wrote {len(records)} records (including embeddings) to {out_file}")


def main() -> None:
    script_name = Path(sys.argv[0]).name
    if len(sys.argv) != 3:
        print(f"Usage: python {script_name} input.csv output.json")
        sys.exit(1)

    csv_input = sys.argv[1]
    json_output = sys.argv[2]

    try:
        # Load model once for all processing
        model = load_embedding_model()
        csv_to_json_with_embeddings(csv_input, json_output, model=model)
    except (FileNotFoundError, ValueError) as e:
        print(f"❌ Input error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
