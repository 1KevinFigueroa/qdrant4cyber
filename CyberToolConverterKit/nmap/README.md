<table align="center">
  <tr>
    <td align="center" width="50%">
      <a href="https://github.com/nmap/nmap">
        <img src="https://img.shields.io/badge/Open%20Source-ff0000?style=flat&logo=github&logoColor=black" alt="Nmap open-source tool" width="100">
      </a>
    </td>
    <td align="center" width="50%">
      <a href="https://github.com/1KevinFigueroa/vector4cyber/blob/main/LICENSE">
        <img src="https://img.shields.io/badge/License-Apache%202.0-brightgreen?labelColor=gray&logo=github" alt="Apache 2.0">
    </a>
      </a>
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <a href="">
        <img src="https://github.com/1KevinFigueroa/vector4cyber/blob/main/RTFM-Knowledge/img/appLogos/nmap.png" width="150" alt="Nmap Logo">
      </a>
    </td>
    <td align="center" width="50%">
      <img src="https://github.com/1KevinFigueroa/vector4cyber/blob/main/RTFM-Knowledge/img/Vector4Cyber_extraSmalllogo.png" width="300" alt="Program Logo">
    </td>
  </tr>
</table>

# 🔄 Converter Nmap TXT file  → JSON file vectorized

[![GitHub Repo](https://img.shields.io/badge/GitHub-Repo-blue?logo=github)](https://github.com/1KevinFigueroa/vector4cyber/tree/main/CyberToolConverterKit/amass)
[![Qdrant](https://img.shields.io/badge/Qdrant-Compatible-brightgreen?logo=qdrant)](https://qdrant.tech/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)](https://python.org)

---

## 🎯 Brief:

Converting Nmap results from a plain text file to a structured JSON format makes a significant difference when the data is being vectorized. Properly structured JSON with unique IDs is extremely useful for aggregating and correlating complex data in a vectorized workflow. High-quality, fast, and accurate data is critical for red team pipelines, security dashboards, and vector databases.

The problem with amass' output text file is not parsed and structured in a way each subdomains within a list should be convertered for vectorization process. 

- ✅ Imports amass scan data into User Selection of VectorDB collection named "[NAME]"
- ✅ Extracts host information including IP addresses, hostnames, MAC addresses, vendors, OS detection
- ✅ Stores open ports and services information
- ✅ Creates searchable documents for each host
- ✅ Validates JSON file format
- ✅ Provides clear error messages and usage instructions

> **High-quality, structured data** is the foundation of **Red Team workflows**, **security dashboards**, and **AI-driven threat analysis**.

---

## Prerequisites

- Python 3.7+
- json
- xmltodict
- sys
- pathlib
- argparse
- re
- os
- sys
- typing
- uuid

### What Happens

**Raw Amass text output** → **Structured JSON** → **Vectorized Intelligence**

1. The script validates that the JSON file exists and is readable
2. Parses the text file data
3. Extracts relevant information from each host:
4. Creates unisque index point for named collection (or uses existing one)
5. Adds each host as a document with metadata

### Nmap TEXT file structure output example ❌
'''
ORT    STATE SERVICE   VERSION
80/tcp  open  http      Netlify
| fingerprint-strings:
|   DNSVersionBindReqTCP, GenericLines, Help, Kerberos, RPCCheck, RTSPRequest, SSLSessionReq, TLSSessionReq, TerminalServerCookie:
|     HTTP/1.1 400 Bad Request
|     Content-Type: text/plain; charset=utf-8
|     Connection: close
|     Request
|   FourOhFourRequest:
|     HTTP/1.0 400 Bad Request
|     Date: Fri, 16 Jan 2026 03:52:10 GMT
|     Server: Netlify
|     X-Nf-Request-Id: 01KF2EX6YJ13HBH5H645EQC8SP
|     Content-Length: 0
|   GetRequest:
|     HTTP/1.0 400 Bad Request
|     Date: Fri, 16 Jan 2026 03:52:05 GMT
|     Server: Netlify
|     X-Nf-Request-Id: 01KF2EX1RBFJ5DZN54NZR658CW
|     Content-Length: 0
|   HTTPOptions:
|     HTTP/1.0 400 Bad Request
|     Date: Fri, 16 Jan 2026 03:52:05 GMT
|     Server: Netlify
|     X-Nf-Request-Id: 01KF2EX1XTTWM1WZ7BS3A1A02X
|_Content-Length: 0
|_http-server-header: Netlify
443/tcp open  ssl/https Netlify
'''

### A JSON structure sample option to vectorized ✅

JSON file structure example:

<img src="https://github.com/1KevinFigueroa/vector4cyber/blob/main/RTFM-Knowledge/img/nmap_vectorizedStructure.png" width="500" alt="Nmap Logo">

With a plain text file, two important pieces of information are missing: the original input and the source from which the data was obtained. From a cybersecurity perspective, these small but crucial data points are essential for traceability, context, and confident decision-making during analysis.

---

## 📊 Vector Databases Supported

| **VectorDB** | **Supported** | **Status** |
|--------------|---------------|------------|
| ✅ **Qdrant** |  ✅ | <a href="https://github.com/1KevinFigueroa/vector4cyber/tree/main/ingest3rs/Qdrant/aMass"> ✅ Completed </a>  |
| ✅ **ChromaDB** |  ✅ | ⚡ In progress |
| ✅ **PineCone** |  ✅ | ⚡ In progress |
| ✅ **Weaviate** |  ✅ | ⚡ In progress |
| ✅ **Milvus** |  ✅ | ⚡ In progress |
---

## 💡 The Solution
> **usage: convert_nmapTXT.py [-h] [--pretty] input_file [output_file]

```bash
python convert3r_nmapTXT.py input_file.txt output_file.json
```
---

## Overview
From a high-level architecture perspective, the shift from flat-file ingestion to structured JSON isn't just a formatting preference; it’s the difference between a "data swamp" and a high-fidelity Cyber Threat Intelligence (CTI) pipeline.

In the world of vector databases—specifically Qdrant, Milvus, and Weaviate, context is the currency of accuracy. Here is the breakdown of why parsers is the "missing link" for these systems.

- Reads a text file containing subdomains
- Cleans and normalizes each line
- Assigns a unique, stable ID to every entry
- Serializes the result as JSON for downstream automation

Typical use cases:

- Ingesting into a **vector database** and user can select vector sizing (Qdrant, Milvus, Weaviate, more coming soon etc.) for semantic search and correlation made easier
- Powering recon dashboards or graphs (e.g., host → vuln → service relationships)
- Joining subdomains with WHOIS, DNS, HTTP fingerprinting, or vulnerability scan data