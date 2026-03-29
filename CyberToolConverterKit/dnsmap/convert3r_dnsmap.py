#!/usr/bin/env python3
import argparse
import csv
import json
import re
import sys
import os


def parse_csv_row(hostname: str, ip_addresses: str) -> list:
    """Parse a single CSV row into multiple DNS records."""
    records = []
    
    # Clean hostname (remove markdown links like [www.example.com](https://...))
    hostname = re.sub(r'\[([^\]]+)\].*', r'\1', hostname.strip())
    
    # Split IPs by comma
    ips = [ip.strip() for ip in ip_addresses.split(',') if ip.strip()]
    
    # Create one record per IP
    for ip in ips:
        record = {
            "host": hostname,
            "address": ip,
            "type": "A" if ":" not in ip else "AAAA",
            "source": "csv_import",
            "timestamp": "2026-02-24"
        }
        records.append(record)
    
    return records


def convert_csv_to_dnsrecon(input_file: str, output_file: str) -> None:
    """Convert CSV to DNSRecon JSON format."""
    all_records = []
    
    print(f"📖 Reading {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        row_num = 0
        
        for row in reader:
            if not row or len(row) < 2:
                print(f"⚠️  Skipping empty row {row_num}")
                continue
                
            hostname = row[0]
            ip_list = ','.join(row[1:])  # Join all remaining columns as IPs
            
            records = parse_csv_row(hostname, ip_list)
            all_records.extend(records)
            
            print(f"  → {hostname}: {len(records)} IPs")
            row_num += 1
    
    print(f"\n💾 Writing {len(all_records)} records to {output_file}...")
    
    with open(output_file, 'w', encoding='utf-8') as jsonfile:
        json.dump(all_records, jsonfile, indent=2, ensure_ascii=False)
    
    print(f"✅ Complete! Generated {len(all_records)} records")
    print(f"\n📋 Sample:")
    for i, record in enumerate(all_records[:3]):
        print(f"  {i+1}. {record['host']} → {record['address']} ({record['type']})")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert CSV (subdomain,IP1,IP2...) to DNSRecon JSON",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("input_file", help="Input CSV file")
    parser.add_argument("output_file", nargs="?", 
                       help="Output JSON file (default: input_file.json)")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_file):
        print(f"Error: '{args.input_file}' not found", file=sys.stderr)
        sys.exit(1)
    
    # Auto-generate output filename if not provided
    if args.output_file is None:
        args.output_file = args.input_file.rsplit('.', 1)[0] + '.json'
    
    try:
        convert_csv_to_dnsrecon(args.input_file, args.output_file)
        print(f"\n🎉 Ready for Qdrant: python ingest3r_dnsrecon.py {args.output_file}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
