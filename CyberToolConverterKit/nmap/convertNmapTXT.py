#!/usr/bin/env python3
import json
import argparse
import re
import os
import sys
from typing import List, Dict, Any, Optional
from collections import defaultdict
import uuid

class RobustNmapParser:
    def __init__(self):
        self.results = {
            "scan_info": {
                "nmap_version": "",
                "start_time": "",
                "end_time": "",
                "total_hosts": 0,
                "hosts_up": 0,
                "scan_duration": ""
            },
            "hosts": [],
            "progress_stats": [],
            "nse_scripts": [],
            "service_fingerprints": [],
            "raw_lines": []
        }
        self.current_host = None
        self.current_port = None
        self.current_script_section = None
        self.lines = []
        self.host_id_counter = 0
    
    def parse(self, input_file: str) -> Dict[str, Any]:
        """Parse ALL Nmap text output into comprehensive structured JSON."""
        with open(input_file, 'r', encoding='utf-8') as f:
            self.lines = f.readlines()
        
        self._parse_all_lines()
        self._finalize_results()
        return self.results
    
    def _parse_all_lines(self):
        """Parse every line with maximum robustness."""
        for i, line in enumerate(self.lines):
            line_stripped = line.strip()
            self.results["raw_lines"].append({
                "line_num": i + 1,
                "content": line_stripped
            })
            
            self._parse_scan_header(line_stripped)
            self._parse_progress_stats(line_stripped)
            self._parse_nse_start_finish(line_stripped)
            self._parse_host_report(line_stripped)
            self._parse_host_metadata(line_stripped)
            self._parse_port_table(line_stripped)
            self._parse_port_scripts(line_stripped)
            self._parse_service_fingerprints(line_stripped)
    
    def _parse_scan_header(self, line: str):
        """Parse Nmap version and start time."""
        if "Starting Nmap" in line:
            version_match = re.search(r'Starting Nmap ([\d.]+)', line)
            time_match = re.search(r'at (.+?)$', line)
            if version_match:
                self.results["scan_info"]["nmap_version"] = version_match.group(1)
            if time_match:
                self.results["scan_info"]["start_time"] = time_match.group(1)
    
    def _parse_progress_stats(self, line: str):
        """Capture all progress statistics."""
        if line.startswith("Stats:"):
            self.results["progress_stats"].append({
                "type": "stats",
                "content": line
            })
        elif line.startswith("NSE:"):
            self.results["progress_stats"].append({
                "type": "nse",
                "content": line
            })
    
    def _parse_nse_start_finish(self, line: str):
        """Parse NSE script start/finish and individual results."""
        if "Starting" in line and "against" in line:
            self.results["nse_scripts"].append({
                "type": "start",
                "script": line.split()[1],
                "target": line
            })
        elif "Finished" in line and "against" in line:
            self.results["nse_scripts"].append({
                "type": "finish",
                "script": line.split()[1],
                "target": line
            })
        elif "[http-enum" in line and "Found a valid page!" in line:
            path_match = re.search(r'Found a valid page!\s+(.+?):\s*(.+)', line)
            if path_match:
                self.results["nse_scripts"].append({
                    "type": "http-enum-path",
                    "script": "http-enum",
                    "path": path_match.group(1).strip(),
                    "title": path_match.group(2).strip(),
                    "full_line": line
                })
    
    def _parse_host_report(self, line: str):
        """Parse host scan report start."""
        host_match = re.search(r'Nmap scan report for\s+(.+?)\s*\((.+?)\)', line)
        if host_match and not self.current_host:
            self.host_id_counter += 1
            self.current_host = {
                "id": f"host_{self.host_id_counter}",
                "hostname": host_match.group(1).strip(),
                "ip": host_match.group(2).strip(),
                "ports": [],
                "metadata": {},
                "scripts": {},
                "raw_section": []
            }
            self.results["hosts"].append(self.current_host)
    
    def _parse_host_metadata(self, line: str):
        """Parse host metadata (rDNS, latency, timing)."""
        if not self.current_host:
            return
        
        self.current_host["raw_section"].append(line)
        
        # rDNS
        rdns_match = re.search(r'rDNS record for \S+:\s*(.+)', line)
        if rdns_match:
            self.current_host["metadata"]["rdns"] = rdns_match.group(1).strip()
        
        # Latency
        latency_match = re.search(r'Host is up \(([^)]+)s latency\)', line)
        if latency_match:
            self.current_host["metadata"]["latency"] = latency_match.group(1) + 's'
        
        # Scan timing
        scan_match = re.search(r'Scanned at (.+?) for (\d+)s', line)
        if scan_match:
            self.current_host["metadata"]["scan_start"] = scan_match.group(1)
            self.current_host["metadata"]["scan_duration"] = scan_match.group(2) + 's'
    
    def _parse_port_table(self, line: str):
        """Parse PORT STATE SERVICE VERSION table."""
        if not self.current_host:
            return
        
        port_match = re.match(r'^(\d+)/([a-z]+)\s+(open|closed|filtered)\s+(.+?)(?:\s+(.+))?$', line)
        if port_match:
            self.current_port = {
                "port": int(port_match.group(1)),
                "protocol": port_match.group(2),
                "state": port_match.group(3),
                "service": port_match.group(4).strip(),
                "version": port_match.group(5).strip() if port_match.group(5) else "",
                "scripts": {},
                "raw_output": line,
                "script_lines": []
            }
            self.current_host["ports"].append(self.current_port)
    
    def _parse_port_scripts(self, line: str):
        """Parse ALL port-specific NSE script output."""
        if not self.current_host or not self.current_port:
            return
        
        self.current_port["script_lines"].append(line)
        
        # http-enum paths
        enum_match = re.search(r'Found a valid page!\s+(.+?):\s*(.+)', line)
        if enum_match:
            self.current_port["scripts"].setdefault("http-enum", {"paths": []})
            self.current_port["scripts"]["http-enum"]["paths"].append({
                "path": enum_match.group(1).strip(),
                "title": enum_match.group(2).strip()
            })
        
        # http-server-header
        header_match = re.search(r'_http-server-header:\s*(.+)', line)
        if header_match:
            self.current_port["scripts"]["http-server-header"] = header_match.group(1).strip()
        
        # Script section headers (fingerprint-strings, etc.)
        if line.startswith('|') and ':' in line and not line.startswith('|_'):
            script_name = line.split(':', 1)[0].replace('|', '').strip()
            if script_name not in self.current_port["scripts"]:
                self.current_port["scripts"][script_name] = []
    
    def _parse_service_fingerprints(self, line: str):
        """Capture service fingerprints."""
        if "NEXT SERVICE FINGERPRINT" in line:
            self.results["service_fingerprints"].append({
                "type": "service_fingerprint",
                "content": line
            })
    
    def _finalize_results(self):
        """Finalize scan summary from Nmap done line."""
        done_match = re.search(r'Nmap done:.*?(\d+) IP address.*\((\d+) hosts up\).*scanned in ([\d.]+) seconds?', 
                             ' '.join(self.lines))
        if done_match:
            self.results["scan_info"].update({
                "total_hosts": int(done_match.group(1)),
                "hosts_up": int(done_match.group(2)),
                "scan_duration": f"{done_match.group(3)}s"
            })


def main():
    parser = argparse.ArgumentParser(description="Parse ALL Nmap text output to comprehensive JSON")
    parser.add_argument("input_file", help="Path to Nmap text output file")
    parser.add_argument("output_file", nargs='?', default=None, help="Output JSON file")
    parser.add_argument("--pretty", action="store_true", help="Pretty print JSON")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input_file):
        print(f"❌ File '{args.input_file}' not found.")
        sys.exit(1)
    
    if args.output_file is None:
        base = os.path.splitext(args.input_file)[0]
        args.output_file = f"{base}_complete.json"
    
    try:
        parser_obj = RobustNmapParser()
        results = parser_obj.parse(args.input_file)
        
        indent = 2 if args.pretty else None
        with open(args.output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=indent, ensure_ascii=False)
        
        # Summary stats
        hosts = len(results["hosts"])
        ports = sum(len(h["ports"]) for h in results["hosts"])
        nse_paths = sum(len(h["ports"][i]["scripts"].get("http-enum", {}).get("paths", [])) 
                      for h in results["hosts"] for i in range(len(h["ports"])))
        
        print(f"✅ COMPLETE PARSE SUCCESS")
        print(f"   Hosts: {hosts}")
        print(f"   Ports: {ports}")
        print(f"   NSE Paths: {nse_paths}")
        print(f"   Progress Stats: {len(results['progress_stats'])}")
        print(f"   NSE Scripts: {len(results['nse_scripts'])}")
        print(f"   Saved: {args.output_file}")
        
    except Exception as e:
        print(f"❌ Parse error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()