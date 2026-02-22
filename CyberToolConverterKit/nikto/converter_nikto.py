#!/usr/bin/env python3
import argparse
import json
import os

def parse_args():
    parser = argparse.ArgumentParser(description="Parse Nikto JSON and add sequential IDs")
    parser.add_argument("input_file", help="Input Nikto JSON file")
    parser.add_argument("output_file", help="Output JSON file with IDs")
    return parser.parse_args()

def parse_nikto_json(nikto_data):
    """Parse Nikto JSON structure and extract vulnerabilities with IDs"""
    parsed_findings = []
    
    # Nikto JSON typically has vulnerabilities as main array or under 'nikto'/'scans'
    vulns = nikto_data.get('vulnerabilities', [])
    if not vulns:
        # Fallback: direct array or other common structures
        if isinstance(nikto_data, list):
            vulns = nikto_data
        else:
            vulns = nikto_data.get('scans', [nikto_data])[0].get('vulnerabilities', [])
    
    for i, vuln in enumerate(vulns, 1):
        finding = {
            "id": i,
            "target": vuln.get("host", vuln.get("hostname", "unknown")),
            "url": vuln.get("url", ""),
            "method": vuln.get("method", ""),
            "message": vuln.get("msg", vuln.get("message", "")),
            "osvdb": vuln.get("osvdb", ""),
            "id_nikto": vuln.get("id", ""),  # Original Nikto ID
            "risk": vuln.get("risk", "medium"),
            "severity": vuln.get("severity", "")
        }
        parsed_findings.append(finding)
    
    return parsed_findings

def main():
    args = parse_args()
    
    # Check if input file exists
    if not os.path.exists(args.input_file):
        print(f"❌ Error: Input file '{args.input_file}' not found!")
        return
    
    # Read Nikto JSON
    try:
        with open(args.input_file, 'r') as f:
            nikto_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in '{args.input_file}': {e}")
        return
    
    # Parse and add IDs
    findings = parse_nikto_json(nikto_data)
    
    # Create output structure
    output = {
        "scan_info": {
            "target": nikto_data.get("host", "unknown"),
            "scanner": "Nikto",
            "total_findings": len(findings),
            "timestamp": nikto_data.get("scan_date", ""),
            "input_file": args.input_file
        },
        "findings": findings
    }
    
    # Write to output file
    try:
        with open(args.output_file, 'w') as f:
            json.dump(output, f, indent=2)
        print(f"✅ Parsed {len(findings)} findings from {args.input_file}")
        print(f"📄 Saved to {args.output_file}")
    except Exception as e:
        print(f"❌ Error writing to '{args.output_file}': {e}")

if __name__ == "__main__":
    main()