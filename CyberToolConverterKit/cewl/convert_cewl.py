#!/usr/bin/env python3
"""
convert_cewl.py - Convert CeWL wordlist text file to JSON

CeWL outputs one word per line. This script converts it to a JSON array 
with incremental IDs and metadata.

Usage: 
    python convert_cewl.py input.txt output.json
"""

import argparse
import json
import sys
from typing import List, Dict, Any
from collections import OrderedDict


def convert_cewl_to_json(input_path: str) -> List[OrderedDict]:
    """
    Read CeWL wordlist (one word per line) and convert to JSON array.
    Each word gets an ID, length, and lowercase version.
    """
    words: List[OrderedDict] = []
    word_id = 1
    
    print(f"📖 Reading CeWL wordlist from {input_path}...")
    
    with open(input_path, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            word = line.strip()
            if not word:
                continue
            
            # Create record with ID FIRST
            record = OrderedDict([
                ("id", word_id),
                ("word", word),
                ("length", len(word)),
                ("lowercase", word.lower()),
                ("line_number", line_num)
            ])
            
            words.append(record)
            word_id += 1
    
    print(f"✓ Processed {len(words)} unique words")
    return words


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert CeWL wordlist text to JSON"
    )
    parser.add_argument("input_file", help="CeWL wordlist text file")
    parser.add_argument("output_file", help="Output JSON file")
    args = parser.parse_args()

    try:
        records = convert_cewl_to_json(args.input_file)
        
        with open(args.output_file, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Saved {len(records)} words to {args.output_file}")
        
        # Show stats and sample
        lengths = [r["length"] for r in records]
        print(f"📊 Stats: avg={sum(lengths)/len(lengths):.1f} chars, "
              f"min={min(lengths)}, max={max(lengths)}")
        
        if records:
            print("\n📋 Sample:")
            for r in records[:5]:
                print(f"  ID={r['id']:3d} | {r['word']:<15} | len={r['length']}")
                
    except FileNotFoundError:
        print(f"❌ '{args.input_file}' not found", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
