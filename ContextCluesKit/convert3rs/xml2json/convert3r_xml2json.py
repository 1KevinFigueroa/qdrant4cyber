#!/usr/bin/env python3
"""
convert3r_XML2JSON.py - Convert XML to JSON with sequential IDs, no @ prefixes, and optional embeddings

Usage:
  python convert3r_XML2JSON.py [-h] [--embed] [-o OUTPUT_FILE] input_file
"""

import argparse
import json
import os
import sys
import xmltodict

try:
    import torch
    from sentence_transformers import SentenceTransformer
except ImportError:
    torch = None
    SentenceTransformer = None

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def rename_text_key(node):
    if isinstance(node, dict):
        new_node = {}
        for k, v in node.items():
            new_key = "IP" if k == "#text" else k
            new_node[new_key] = rename_text_key(v)
        return new_node
    if isinstance(node, list):
        return [rename_text_key(i) for i in node]
    return node


def flatten_xml(node):
    if isinstance(node, dict):
        return {k: flatten_xml(v) for k, v in node.items()}
    if isinstance(node, list):
        return [flatten_xml(i) for i in node]
    return node


def extract_entries(parsed):
    if not isinstance(parsed, dict) or not parsed:
        return []

    root_key = next(iter(parsed.keys()))
    root_val = parsed[root_key]

    if isinstance(root_val, list):
        return root_val

    if isinstance(root_val, dict):
        for v in root_val.values():
            if isinstance(v, list):
                return v

    return [root_val]


def entry_to_text(entry):
    return json.dumps(entry, ensure_ascii=False, sort_keys=True, default=str)


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
        show_progress_bar=True,
    )
    return embeddings.tolist()


def xml_file_to_json(input_file, output_file=None, embed=False):
    if output_file is None:
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}.json"

    try:
        print(f"Reading XML from: {input_file}")
        with open(input_file, "r", encoding="utf-8") as xml_file:
            xml_content = xml_file.read()

        print("Parsing XML to dictionary...")
        data_dict = xmltodict.parse(xml_content, attr_prefix="")
        data_dict = rename_text_key(data_dict)

        entries = extract_entries(data_dict)

        embeds = None
        if embed:
            print("Generating embeddings...")
            texts = [entry_to_text(e) for e in entries]
            embeds = build_embeddings(texts)
            print("Embeddings generated")

        results = []
        for idx, entry in enumerate(entries, start=1):
            record = {
                "id": idx,
                "data": flatten_xml(entry),
            }
            if embeds is not None:
                record["embed"] = embeds[idx - 1]
            results.append(record)

        json_str = json.dumps(results, indent=2, ensure_ascii=False, default=str)

        print(f"Writing JSON to: {output_file}")
        with open(output_file, "w", encoding="utf-8") as json_file:
            json_file.write(json_str)

        print(f"✓ Successfully converted {input_file} → {output_file}")
        print("\nPreview (first 500 chars):")
        print(json_str[:500] + "..." if len(json_str) > 500 else json_str)

    except FileNotFoundError:
        print(f"Error: XML file '{input_file}' not found.", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error processing XML: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        prog="convert3r_XML2JSON.py",
        description="Convert XML to JSON with sequential IDs, IP field rename, and optional embeddings",
    )
    parser.add_argument("input_file", help="Input XML file")
    parser.add_argument("-o", "--output-file", dest="output_file", help="Output JSON file")
    parser.add_argument("--embed", action="store_true", help="Add sentence-transformer embeddings to each record")

    args = parser.parse_args()
    xml_file_to_json(args.input_file, args.output_file, embed=args.embed)


if __name__ == "__main__":
    main()