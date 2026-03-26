import re
import json
import argparse
import sys
from sentence_transformers import SentenceTransformer


def build_text(entry):
    """
    Build a text representation for embedding
    """
    if entry["entry_type"] == "finding":
        return f"{entry.get('template', '')} {entry.get('severity', '')} {entry.get('target', '')} {entry.get('extra_info', '')}"
    elif entry["entry_type"] == "log":
        return f"{entry.get('log_level', '')} {entry.get('message', '')}"
    return ""


def parse_nuclei_logs(input_path, output_path, model_name):
    parsed_results = []
    entry_id = 1

    # Load embedding model
    print(f"[+] Loading embedding model: {model_name}")
    model = SentenceTransformer(model_name)

    # Patterns
    finding_pattern = re.compile(
        r'^\[(?P<template>[^\]]+)\]\s\[(?P<protocol>[^\]]+)\]\s\[(?P<severity>[^\]]+)\]\s(?P<target>\S+)(?:\s+\[(?P<meta>.*)\])?'
    )

    status_pattern = re.compile(
        r'^\[(?P<type>INF|WRN)\]\s(?P<message>.*)'
    )

    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                entry = {"id": entry_id}

                # --- Findings ---
                finding_match = finding_pattern.match(line)
                if finding_match:
                    entry.update({
                        "entry_type": "finding",
                        "template": finding_match.group('template'),
                        "protocol": finding_match.group('protocol'),
                        "severity": finding_match.group('severity'),
                        "target": finding_match.group('target'),
                        "extra_info": finding_match.group('meta').strip() if finding_match.group('meta') else None
                    })

                # --- Logs ---
                else:
                    status_match = status_pattern.match(line)
                    if status_match:
                        entry.update({
                            "entry_type": "log",
                            "log_level": "info" if status_match.group('type') == "INF" else "warning",
                            "message": status_match.group('message')
                        })
                    else:
                        continue

                # --- Build embedding ---
                text = build_text(entry)
                vector = model.encode(text).tolist()

                entry["text"] = text
                entry["vector"] = vector

                parsed_results.append(entry)
                entry_id += 1

        # Save JSON
        with open(output_path, 'w', encoding='utf-8') as out_f:
            json.dump(parsed_results, out_f, indent=4)

        print(f"[+] Successfully parsed {len(parsed_results)} entries.")
        print(f"[+] Output saved to: {output_path}")

    except FileNotFoundError:
        print(f"[-] Error: File '{input_path}' not found.")
        sys.exit(1)
    except Exception as e:
        print(f"[-] Unexpected error: {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Convert Nuclei TXT output into Milvus-compatible JSON with embeddings."
    )

    parser.add_argument(
        "-i", "--input",
        required=True,
        help="Path to raw Nuclei TXT file"
    )

    parser.add_argument(
        "-o", "--output",
        required=True,
        help="Path to output JSON file"
    )

    parser.add_argument(
        "-m", "--model",
        default="all-MiniLM-L6-v2",
        help="Embedding model (default: all-MiniLM-L6-v2)"
    )

    args = parser.parse_args()

    parse_nuclei_logs(args.input, args.output, args.model)


if __name__ == "__main__":
    main()