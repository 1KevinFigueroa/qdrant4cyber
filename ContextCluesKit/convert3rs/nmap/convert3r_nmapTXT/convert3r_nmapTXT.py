#!/usr/bin/env python3
"""
convert3r_nmapTXT.py - Convert Nmap scan results to structured JSON with optional sentence embeddings

Usage: convert3r_nmapTXT.py [-h] [--embed] [-o OUTPUT_FILE] input_file
"""

import argparse
import json
import os
import re
import sys
from typing import List, Dict, Any, Optional

try:
    import torch
    from sentence_transformers import SentenceTransformer
except ImportError:
    torch = None
    SentenceTransformer = None

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


def safe_dict_get(obj, key, default=None):
    return obj.get(key, default) if isinstance(obj, dict) else default


def safe_list(obj):
    if isinstance(obj, list):
        return obj
    if obj is None:
        return []
    return [obj]


class RobustNmapParser:
    def __init__(self):
        self.results: Dict[str, Any] = {
            "scan_info": {},
            "hosts": [],
            "progress_stats": [],
            "nse_scripts": [],
            "service_fingerprints": [],
            "raw_lines": []
        }
        self.lines: List[str] = []
        self.current_host: Optional[Dict[str, Any]] = None
        self.current_port: Optional[Dict[str, Any]] = None
        self.host_id_counter = 0

    def parse(self, input_file: str) -> Dict[str, Any]:
        try:
            with open(input_file, "r", encoding="utf-8") as f:
                self.lines = f.readlines()
        except OSError as e:
            raise RuntimeError(f"Failed to read {input_file}: {e}")

        self._parse_all_lines()
        self._finalize_results()
        return self.results

    def _parse_all_lines(self):
        for i, line in enumerate(self.lines):
            line_stripped = line.strip()
            self.results["raw_lines"].append({"line_num": i + 1, "content": line_stripped})
            self._parse_scan_header(line_stripped)
            self._parse_progress_stats(line_stripped)
            self._parse_nse_start_finish(line_stripped)
            self._parse_host_report(line_stripped)
            self._parse_host_metadata(line_stripped)
            self._parse_port_table(line_stripped)
            self._parse_port_scripts(line_stripped)
            self._parse_service_fingerprints(line_stripped)

    def _parse_scan_header(self, line: str):
        if "Starting Nmap" in line:
            version_match = re.search(r"Starting Nmap ([\d.]+)", line)
            time_match = re.search(r"at (.+?)$", line)
            if version_match:
                self.results["scan_info"]["nmap_version"] = version_match.group(1)
            if time_match:
                self.results["scan_info"]["start_time"] = time_match.group(1)

    def _parse_progress_stats(self, line: str):
        if line.startswith("Stats:"):
            self.results["progress_stats"].append({"type": "stats", "content": line})
        elif line.startswith("NSE:"):
            self.results["progress_stats"].append({"type": "nse", "content": line})

    def _parse_nse_start_finish(self, line: str):
        if "Starting" in line and "against" in line:
            parts = line.split()
            if len(parts) > 1:
                self.results["nse_scripts"].append({"type": "start", "script": parts[1], "target": line})
        elif "Finished" in line and "against" in line:
            parts = line.split()
            if len(parts) > 1:
                self.results["nse_scripts"].append({"type": "finish", "script": parts[1], "target": line})

    def _parse_host_report(self, line: str):
        host_match = re.search(r"Nmap scan report for\s+(.+?)\s*\((.+?)\)", line)
        if host_match and not self.current_host:
            self.host_id_counter += 1
            self.current_host = {
                "id": self.host_id_counter,
                "hostname": host_match.group(1).strip(),
                "ip": host_match.group(2).strip(),
                "ports": [],
                "metadata": {},
                "scripts": {},
                "raw_section": []
            }
            self.results["hosts"].append(self.current_host)

    def _parse_host_metadata(self, line: str):
        if not self.current_host:
            return
        self.current_host["raw_section"].append(line)
        rdns_match = re.search(r"rDNS record for \S+:\s*(.+)", line)
        if rdns_match:
            self.current_host["metadata"]["rdns"] = rdns_match.group(1).strip()
        latency_match = re.search(r"Host is up \(([^)]+)s latency\)", line)
        if latency_match:
            self.current_host["metadata"]["latency"] = latency_match.group(1) + "s"
        scan_match = re.search(r"Scanned at (.+?) for (\d+)s", line)
        if scan_match:
            self.current_host["metadata"]["scan_start"] = scan_match.group(1)
            self.current_host["metadata"]["scan_duration"] = scan_match.group(2) + "s"

    def _parse_port_table(self, line: str):
        if not self.current_host:
            return
        port_match = re.match(r"^(\d+)/([a-z]+)\s+(open|closed|filtered)\s+(.+?)(?:\s+(.+))?$", line)
        if port_match:
            version_part = port_match.group(5).strip() if port_match.group(5) else ""
            self.current_port = {
                "port": int(port_match.group(1)),
                "protocol": port_match.group(2),
                "state": port_match.group(3),
                "service": port_match.group(4).strip(),
                "version": version_part,
                "scripts": {},
                "raw_output": line,
                "script_lines": []
            }
            self.current_host["ports"].append(self.current_port)

    def _parse_port_scripts(self, line: str):
        if not self.current_host or not self.current_port:
            return
        self.current_port["script_lines"].append(line)

        enum_match = re.search(r"Found a valid page!\s+(.+?):\s*(.+)", line)
        if enum_match:
            path = enum_match.group(1).strip()
            title = enum_match.group(2).strip()
            self.current_port["scripts"].setdefault("http-enum", {"paths": []})
            self.current_port["scripts"]["http-enum"]["paths"].append({"path": path, "title": title})

        header_match = re.search(r"_http-server-header:\s*(.+)", line)
        if header_match:
            self.current_port["scripts"]["http-server-header"] = header_match.group(1).strip()

        if line.startswith("|") and ":" in line and not line.startswith("|_"):
            script_name = line.split(":", 1)[0].replace("|", "").strip()
            self.current_port["scripts"].setdefault(script_name, [])

    def _parse_service_fingerprints(self, line: str):
        if "NEXT SERVICE FINGERPRINT" in line:
            self.results["service_fingerprints"].append({"type": "service_fingerprint", "content": line})

    def _finalize_results(self):
        done_match = re.search(
            r"Nmap done:\s+(\d+)\s+IP address.*\((\d+)\s+hosts up\).*scanned in\s+([\d.]+)\s+seconds?",
            " ".join(self.lines)
        )
        if done_match:
            self.results["scan_info"].update({
                "total_hosts": int(done_match.group(1)),
                "hosts_up": int(done_match.group(2)),
                "scan_duration_seconds": float(done_match.group(3))
            })

    def add_embeddings(self, embedding_model: str = DEFAULT_MODEL) -> None:
        if SentenceTransformer is None:
            raise RuntimeError("sentence-transformers package not installed. Install with `pip install sentence-transformers`.")

        model = SentenceTransformer(embedding_model)
        total_items = 0

        for host in self.results["hosts"]:
            host_text = f"{host.get('hostname', '')} {host.get('ip', '')}".strip()
            if host_text:
                try:
                    host["embed"] = model.encode([host_text], show_progress_bar=False, convert_to_numpy=True)[0].tolist()
                except Exception:
                    pass

            for port in safe_list(host.get("ports")):
                if not isinstance(port, dict):
                    continue
                scripts = safe_dict_get(port, "scripts", {})
                http_enum = safe_dict_get(scripts, "http-enum", {})
                paths = safe_list(safe_dict_get(http_enum, "paths", []))

                for path_entry in paths:
                    if not isinstance(path_entry, dict):
                        continue
                    text = f"{path_entry.get('title', '')} {path_entry.get('path', '')}".strip()
                    if text:
                        try:
                            path_entry["embed"] = model.encode([text], show_progress_bar=False, convert_to_numpy=True)[0].tolist()
                            total_items += 1
                        except Exception:
                            continue

        print(f"✅ Generated embeddings for {total_items} textual items.", file=sys.stderr)


def parse_file(input_file: str, output_file: str, embed: bool = False):
    parser_obj = RobustNmapParser()
    data = parser_obj.parse(input_file)

    if embed:
        try:
            parser_obj.add_embeddings()
        except Exception as e:
            print(f"⚠️ Embedding failed: {e}", file=sys.stderr)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def main():
    parser = argparse.ArgumentParser(
        prog="convert3r_nmapTXT.py",
        description="Convert Nmap scan results to structured JSON with optional sentence embeddings."
    )
    parser.add_argument("input_file", help="Path to input file (e.g., nmap output)")
    parser.add_argument("-o", "--output-file", dest="output_file", help="Output JSON file")
    parser.add_argument("--embed", action="store_true",
                        help="Generate SentenceTransformer embeddings for host info and HTTP paths")

    args = parser.parse_args()

    if not os.path.isfile(args.input_file):
        print(f"❌ Error: Input file '{args.input_file}' does not exist.", file=sys.stderr)
        sys.exit(1)

    try:
        output_file = args.output_file or os.path.splitext(args.input_file)[0] + ".json"
        parse_file(args.input_file, output_file, embed=args.embed)
        print(f"✅ Successfully parsed → {output_file}", file=sys.stderr)
    except Exception as e:
        print(f"❌ Fatal error: {e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()