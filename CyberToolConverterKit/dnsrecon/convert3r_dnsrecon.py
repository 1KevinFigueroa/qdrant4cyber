#!/usr/bin/env python3
import argparse
import csv
import json
import os

def parse_args():
    parser = argparse.ArgumentParser(description="Convert DNS CSV to JSON with sequential IDs")
    parser.add_argument("input_csv", help="Input DNS CSV file")
    parser.add_argument("output_json", help="Output JSON file")
    return parser.parse_args()

def csv_to_dns_json(csv_file, json_file):
    """Convert DNS CSV to structured JSON with IDs"""
    
    # Check if input file exists
    if not os.path.exists(csv_file):
        print(f"❌ Error: Input file '{csv_file}' not found!")
        return
    
    records = []
    id_counter = 1
    
    # Read CSV with proper handling of quoted fields and commas
    with open(csv_file, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        
        # Read header
        header = next(reader)
        print(f"📋 Headers found: {header}")
        
        # Process each row
        for row in reader:
            # Pad short rows with empty strings
            while len(row) < len(header):
                row.append('')
            
            record = {
                "id": id_counter,
                "type": row[0].strip() if row[0] else "",
                "name": row[1].strip() if row[1] else "",
                "address": row[2].strip() if row[2] else "",
                "target": row[3].strip() if row[3] else "",
                "port": row[4].strip() if row[4] else "",
                "string": row[5].strip() if len(row) > 5 and row[5] else ""
            }
            
            # Clean up empty records
            if record["name"] or record["address"] or record["string"]:
                records.append(record)
                id_counter += 1
    
    # Create output structure
    output = {
        "scan_info": {
            "input_file": csv_file,
            "total_records": len(records),
            "headers": header
        },
        "records": records
    }
    
    # Write JSON
    try:
        with open(json_file, 'w') as f:
            json.dump(output, f, indent=2)
        print(f"✅ Converted {len(records)} DNS records from {csv_file}")
        print(f"📄 Saved to {json_file}")
    except Exception as e:
        print(f"❌ Error writing JSON: {e}")

def main():
    args = parse_args()
    csv_to_dns_json(args.input_csv, args.output_json)

if __name__ == "__main__":
    main()