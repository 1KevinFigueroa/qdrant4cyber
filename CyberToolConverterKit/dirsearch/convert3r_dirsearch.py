#!/usr/bin/env python3
"""
convert_dirsearch.py - Ensures ID is FIRST in each JSON object

Usage: python convert_dirsearch.py input.txt output.json
"""

import argparse
import json
import re
import sys
from typing import List, Dict, Any
from collections import OrderedDict


LINE_RE = re.compile(
    r"""
    ^\s*
    (?P<status>\d{3})
    \s+
    (?P<size>\S+)
    \s+
    (?P<url>\S+)
    (?:\s*->\s*REDIRECTS\s+TO:\s*(?P<redirect>\S+))?
    """,
    re.VERBOSE,
)


def clean_markdown_url(raw: str) -> str:
    """Clean [url](link) markdown to plain URL."""
    m = re.match(r'\[([^\]]+)\]\(([^)]+)\)', raw)
    if m:
        return m.group(2)
    m2 = re.match(r'\[([^\]]+)\]', raw)
    if m2:
        return m2.group(1)
    return raw


def parse_dirsearch_line(line: str) -> Dict[str, Any] | None:
    """Parse dirsearch line or return None."""
    match = LINE_RE.match(line)
    if not match:
        return None

    return {
        "status": int(match.group("status")),
        "size": match.group("size"),
        "url": clean_markdown_url(match.group("url")),
        "redirect_to": clean_markdown_url(match.group("redirect")) if match.group("redirect") else None,
    }


def convert_dirsearch_to_json(input_path: str) -> List[OrderedDict]:
    """Convert dirsearch file to list of OrderedDicts with 'id' FIRST."""
    results = []
    current_id = 1

    with open(input_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith("# Dirsearch") or line.startswith("HTTP code"):
                continue

            parsed = parse_dirsearch_line(line)
            if parsed:
                # **ID FIRST** - using OrderedDict
                ordered = OrderedDict([
                    ("id", current_id),
                ])
                # Add other fields AFTER id
                ordered.update(parsed)
                results.append(ordered)
                current_id += 1

    return results


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert Dirsearch to JSON (ID first)")
    parser.add_argument("input_file", help="Dirsearch text file")
    parser.add_argument("output_file", help="Output JSON file")
    args = parser.parse_args()

    try:
        records = convert_dirsearch_to_json(args.input_file)
        with open(args.output_file, "w", encoding="utf-8") as out:
            json.dump(records, out, indent=2, ensure_ascii=False)

        print(f"✓ Converted {len(records)} entries → {args.output_file}")
        if records:
            print("Sample JSON structure:")
            print(json.dumps(records[0], indent=2))
    except FileNotFoundError:
        print(f"❌ '{args.input_file}' not found", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
