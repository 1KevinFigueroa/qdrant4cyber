import re
import json
import argparse
from datetime import datetime


def parse_metadata(meta_str):
    """
    Parse metadata like:
    ["7.0.30"] [paths="/phpinfo.php"]
    """
    if not meta_str:
        return {}

    metadata = {}

    # Extract key="value"
    kv_pairs = re.findall(r'(\w+)="([^"]+)"', meta_str)
    for k, v in kv_pairs:
        metadata[k] = v

    # Extract arrays ["a","b"]
    array_match = re.findall(r'\[([^\]]+)\]', meta_str)
    for arr in array_match:
        values = [v.strip().strip('"') for v in arr.split(",")]
        metadata.setdefault("values", []).extend(values)

    return metadata


def build_description(template, protocol, severity, target, metadata):
    """
    Create a searchable text field for embeddings
    """
    meta_text = " ".join(
        [f"{k}:{v}" if not isinstance(v, list) else f"{k}:{','.join(v)}"
         for k, v in metadata.items()]
    )

    return f"{template} {protocol} {severity} {target} {meta_text}".strip()


def parse_nuclei_txt(input_file):
    pattern = re.compile(
        r'^\[(?P<template>[^\]]+)\]\s'
        r'\[(?P<protocol>[^\]]+)\]\s'
        r'\[(?P<severity>[^\]]+)\]\s'
        r'(?P<target>\S+)'
        r'(?:\s+(?P<meta>.*))?'
    )

    results = []

    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            match = pattern.match(line)
            if not match:
                continue

            template = match.group("template")
            protocol = match.group("protocol")
            severity = match.group("severity")
            target = match.group("target")
            raw_meta = match.group("meta")

            metadata = parse_metadata(raw_meta)

            description = build_description(
                template, protocol, severity, target, metadata
            )

            result = {
                "class": "NucleiFinding",
                "properties": {
                    "template": template,
                    "protocol": protocol,
                    "severity": severity,
                    "target": target,
                    "metadata": metadata,
                    "description": description,
                    "raw": line,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }

            results.append(result)

    return results


def main():
    parser = argparse.ArgumentParser(
        description="Convert Nuclei TXT output to Weaviate-ready JSON"
    )
    parser.add_argument("-i", "--input", required=True)
    parser.add_argument("-o", "--output", required=True)

    args = parser.parse_args()

    data = parse_nuclei_txt(args.input)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

    print(f"[+] Parsed {len(data)} findings")
    print(f"[+] Output written to {args.output}")


if __name__ == "__main__":
    main()