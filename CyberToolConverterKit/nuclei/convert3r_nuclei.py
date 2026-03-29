import re
import json
import argparse
import sys

def parse_nuclei_logs(input_path, output_path):
    parsed_results = []
    entry_id = 1

    # Pattern for findings: [template-id] [protocol] [severity] target [metadata]
    finding_pattern = re.compile(r'^\[(?P<template>[^\]]+)\]\s\[(?P<protocol>[^\]]+)\]\s\[(?P<severity>[^\]]+)\]\s(?P<target>\S+)(?:\s+\[(?P<meta>.*)\])?')
    
    # Pattern for system status/logs: [INF] or [WRN] Message
    status_pattern = re.compile(r'^\[(?P<type>INF|WRN)\]\s(?P<message>.*)')

    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                entry = {"id": entry_id}
                
                # Check for vulnerability/tech findings
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
                    parsed_results.append(entry)
                    entry_id += 1
                    continue

                # Check for INF/WRN log messages
                status_match = status_pattern.match(line)
                if status_match:
                    entry.update({
                        "entry_type": "log",
                        "log_level": "info" if status_match.group('type') == "INF" else "warning",
                        "message": status_match.group('message')
                    })
                    parsed_results.append(entry)
                    entry_id += 1
                    continue

        # Save to JSON
        with open(output_path, 'w', encoding='utf-8') as out_f:
            json.dump(parsed_results, out_f, indent=4)
        
        print(f"[+] Successfully parsed {len(parsed_results)} entries.")
        print(f"[+] Output saved to: {output_path}")

    except FileNotFoundError:
        print(f"[-] Error: The file '{input_path}' was not found.")
        sys.exit(1)
    except Exception as e:
        print(f"[-] An unexpected error occurred: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Parse Nuclei CLI output into a structured JSON file.")
    
    # Positional arguments or flagged arguments
    parser.add_argument("-i", "--input", required=True, help="Path to the raw Nuclei log file (.txt)")
    parser.add_argument("-o", "--output", required=True, help="Path for the resulting JSON file (.json)")

    args = parser.parse_args()

    parse_nuclei_logs(args.input, args.output)

if __name__ == "__main__":
    main()