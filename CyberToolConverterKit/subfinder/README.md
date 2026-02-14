# Subdomain Subfinder  → JSON Converter

Convert subdomains from a plain text file into structured JSON with IDs for use in red team pipelines, dashboards, or vector databases.

---

## Overview

As a Red Team operator, most recon tools (`nuclei`, `nmap`, `amass`, etc.) become exponentially more valuable once their raw output is normalized and made machine‑readable. This repository provides a lightweight Python parser that:

- Reads a text file containing subdomains (e.g., from `subfinder -silent -o subs.txt`)
- Cleans and normalizes each line
- Assigns a unique, stable ID to every entry
- Serializes the result as JSON for downstream automation

Typical use cases:

- Ingesting subdomains into a **vector database** (Qdrant, Milvus, etc.) for semantic search and correlation
- Powering recon dashboards or graphs (e.g., host → vuln → service relationships)
- Joining subdomains with WHOIS, DNS, HTTP fingerprinting, or vulnerability scan data

---

## Input Format

The script expects a text file with **one subdomain per line**, for example:

```text
