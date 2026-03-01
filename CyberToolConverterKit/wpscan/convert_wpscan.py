#!/usr/bin/env python3
"""
convert_wpscan.py - Read WPScan JSON and add ID as FIRST field in each record

Usage: python convert_wpscan.py input.json output.json
"""

import argparse
import json
import sys
from typing import List, Dict, Any
from collections import OrderedDict


def add_id_first_wpscan(data: List[Dict[str, Any]]) -> List[OrderedDict]:
    """
    Add incremental ID as FIRST field to each WPScan record.
    """
    results = []
    
    for i, record in enumerate(data):
        # Create OrderedDict with ID FIRST
        ordered = OrderedDict([
            ("id", i + 1)
        ])
        
        # Add all original WPScan fields AFTER ID
        for key, value in record.items():
            ordered[key] = value
            
        results.append(ordered)
    
    return results


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Add ID (first field) to WPScan JSON records"
    )
    parser.add_argument("input_file", help="Input WPScan JSON file")
    parser.add_argument("output_file", help="Output JSON file")
    args = parser.parse_args()

    try:
        # Read WPScan JSON
        with open(args.input_file, 'r', encoding='utf-8') as f:
            wpscan_data = json.load(f)

        # Handle both single scan and list of scans
        if isinstance(wpscan_data, list):
            records = wpscan_data
        elif isinstance(wpscan_data, dict) and 'scan' in wpscan_data:
            # WPScan typically has 'scan' as root key
            records = [wpscan_data]
        else:
            records = [wpscan_data]

        # Add ID first to each record
        records_with_id = add_id_first_wpscan(records)

        # Write ordered JSON
        with open(args.output_file, 'w', encoding='utf-8') as f:
            json.dump(records_with_id, f, indent=2, ensure_ascii=False)

        print(f"✓ Processed {len(records_with_id)} records")
        print(f"  Input:  {args.input_file}")
        print(f"  Output: {args.output_file}")
        
        # Show sample structure
        if records_with_id:
            print("\nSample (first record):")
            print(json.dumps(records_with_id[0], indent=2))
            
    except FileNotFoundError:
        print(f"❌ Error: '{args.input_file}' not found", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in '{args.input_file}': {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
