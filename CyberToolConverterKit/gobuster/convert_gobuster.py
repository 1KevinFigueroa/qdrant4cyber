#!/usr/bin/env python3
"""
Gobuster text output → JSON converter

Usage: python gobuster_to_json.py gobuster_output.txt --vector-size 384 output.json
"""

import argparse
import os
import re
import json
from typing import List, Dict, Any

DEFAULT_VECTOR_SIZE = 384


def parse_gobuster_line(line: str) -> Dict[str, Any] | None:
    """Parse single gobuster output line into structured data."""
    # Pattern: /path                  (Status: 302)   [Size: 43]  [--> redirect_url]
    pattern = r'^(\S+)\s+\(Status:\s*(\d+)\)\s+\[Size:\s*([^\]]+)\](?:\s+\[--> ([^\]]+)\])?'
    
    match = re.match(pattern, line.strip())
    if not match:
        return None
    
    path, status, size, redirect = match.groups()
    
    return {
        "id": None,  # Will be assigned sequentially
        "path": path,
        "status": int(status),
        "size": size.strip(),
        "redirect_url": redirect.strip() if redirect else None,
        "line_number": None,  # Will be assigned
        "raw_line": line.strip()
    }


def gobuster_txt_to_json(txt_file: str, output_file: str, vector_size: int = DEFAULT_VECTOR_SIZE) -> None:
    """Parse gobuster text file and save as structured JSON."""
    if not os.path.exists(txt_file):
        raise FileNotFoundError(f"❌ Text file not found: {txt_file}")
    
    entries = []
    line_number = 1
    
    print(f"📖 Reading gobuster output: {txt_file}")
    
    with open(txt_file, 'r', encoding='utf-8') as f:
        for line in f:
            parsed = parse_gobuster_line(line)
            if parsed:
                parsed["line_number"] = line_number
                parsed["vector_size"] = vector_size  # Store chosen dimension
                entries.append(parsed)
            line_number += 1
    
    print(f"✓ Parsed {len(entries)} valid gobuster entries")
    
    # Save as JSON array
    output_data = {
        "vector_size": vector_size,
        "total_entries": len(entries),
        "entries": entries
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Converted to JSON: {output_file}")
    
    # Quick stats
    status_counts = {}
    for entry in entries:
        status = entry["status"]
        status_counts[status] = status_counts.get(status, 0) + 1
    
    print("📊 Status breakdown:")
    for status, count in sorted(status_counts.items()):
        print(f"   {status}: {count}")
    
    print(f"\n🔢 Vector size recorded: {vector_size}")


def main():
    parser = argparse.ArgumentParser(
        description="Convert gobuster text output to structured JSON"
    )
    parser.add_argument(
        "txt_path",
        help="Path to gobuster text output file",
    )
    parser.add_argument(
        "output_json",
        help="Output JSON file path",
    )
    parser.add_argument(
        "--vector-size",
        type=int,
        default=DEFAULT_VECTOR_SIZE,
        help=f"Vector dimension size to record (default: {DEFAULT_VECTOR_SIZE})",
    )
    
    args = parser.parse_args()
    
    gobuster_txt_to_json(
        txt_file=args.txt_path,
        output_file=args.output_json,
        vector_size=args.vector_size
    )


if __name__ == "__main__":
    main()