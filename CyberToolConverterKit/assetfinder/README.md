<table align="center">
  <tr>
    <td align="center" width="50%">
      <a href="https://github.com/tomnomnom/assetfinder">
        <img src="https://img.shields.io/badge/Open%20Source-10000000?style=flat&logo=github&logoColor=black" alt="Assetfinder" width="100">
      </a>
    </td>
    <td align="center" width="50%">
      <a href="https://github.com/1KevinFigueroa/vector4cyber/blob/main/LICENSE">
        <img src="https://img.shields.io/badge/License-Apache%202.0-brightgreen?labelColor=gray&logo=github" alt="Apache 2.0 License">
      </a>
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <a href="">
        <img src="https://github.com/1KevinFigueroa/vector4cyber/blob/main/RTFM-Knowledge/img/appLogos/assetfinder.png" width="300" alt="Assetfinder Logo">
      </a>
    </td>
    <td align="center" width="50%">
      <img src="https://github.com/1KevinFigueroa/vector4cyber/blob/main/RTFM-Knowledge/img/Vector4Cyber_extraSmalllogo.png" width="300" alt="Program Logo">
    </td>
  </tr>
</table>

# 🔄 Convert Assetfinder Results → JSON (Vectorized)

[![GitHub Repo](https://img.shields.io/badge/GitHub-Repo-blue?logo=github)](https://github.com/1KevinFigueroa/vector4cyber/tree/main/CyberToolConverterKit/assetfinder)
[![Qdrant](https://img.shields.io/badge/Qdrant-Compatible-brightgreen?logo=qdrant)](https://qdrant.tech/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)](https://python.org)

---

# 🎯 Brief:

Converting Amass results from a plain text file to a structured JSON format makes a significant difference when the data is being vectorized. Properly structured JSON with unique IDs is extremely useful for aggregating and correlating complex data in a vectorized workflow. High-quality, fast, and accurate data is critical for red team pipelines, security dashboards, and vector databases.

The problem with amass' output text file is not parsed and structured in a way each subdomains within a list should be convertered for vectorization process. 

- ✅ Imports amass scan data into User Selection of VectorDB collection named "[NAME]"
- ✅ Extracts host information including IP addresses, hostnames, MAC addresses, vendors, OS detection
- ✅ Stores open ports and services information
- ✅ Creates searchable documents for each host
- ✅ Validates JSON file format
- ✅ Provides clear error messages and usage instructions

> **High-quality, structured data** is the foundation of **Red Team workflows**, **security dashboards**, and **AI-driven threat analysis**.



## Prerequisites

- Python 3.7+
- argparse
- json

### What Happens

**Raw Assetfinder text output** → **Structured JSON** → **Vectorized Intelligence**

1. The script validates that the JSON file exists and is readable
2. Parses the text file data
3. Extracts relevant information from each host:
4. Creates unisque index point for named collection (or uses existing one)
5. Adds each host as a document with metadata

---

## 🚨 The Problem

| **Format** | **Example** | **Issues** |
|------------|-------------|------------|
| ❌ **Text File** | `example.com` | ❌ No context<br>❌ No source tracking<br>❌ No unique IDs |
| ✅ **Vectorized JSON** | `{"id": 1, "host": "example.com", "input": "example.com", "source": "reconeer"}` | ✅ Full context<br>✅ Traceability<br>✅ Vectorization-ready |

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
> **usage: convert3r_amassTXT.py [-h] input_file output_file**

```bash
python convert3r_amassTXT.py input_file.txt output_file.json
```
---

## 🎯 Overview and Why This Matters

In the world of vector databases—specifically, information context is the currency of accuracy. Here is the breakdown of why parsers is the "missing link" for these systems. From a high-level architecture perspective, the shift from flat-file ingestion to structured JSON isn't just a formatting preference; it’s the difference between a "data swamp" and a high-fidelity Cyber Threat Intelligence (CTI) pipeline. Converting Amass results from a plain text file to a structured **JSON format** makes a significant difference when the data is being vectorized. Properly structured JSON with unique IDs is extremely useful for aggregating and correlating complex data in a vectorized workflow. High-quality, fast, and accurate data is critical for red team pipelines, security dashboards, and vector databases. 


## Architecture

```
┌──────────────┐     ┌────────────────────┐     ┌──────────────────┐
│              │     │   Ingest Scripts   │     │                  │
│      JSON    │────▶│  (embed + upsert)  │────▶│  (Docker :8000)  │
│  log file    │     │                    │     │                  │
└──────────────┘     └────────────────────┘     └────────┬─────────┘
                                                         │
                     ┌────────────────────┐              │  similarity
                     │  Query Scripts     │◀─────────────┘  search
                     │  (interactive)     │
                     └────────┬───────────┘
                              │ (optional)
                              ▼
                     ┌────────────────────┐
                     │                    │
                     │                    │
                     │  LLM analysis      │
                     └────────────────────┘
```

---
In the world of vector databases—specifically, context is the currency of accuracy. Here is the breakdown of why parsers is the "missing link" for these systems.

From a high-level architecture perspective, the shift from flat-file ingestion to structured JSON isn't just a formatting preference; it’s the difference between a "data swamp" and a high-fidelity Cyber Threat Intelligence (CTI) pipeline. Converting Assetfinder results from a plain text file to a structured **JSON format** makes a significant difference when the data is being vectorized. Properly structured JSON with unique IDs is extremely useful for aggregating and correlating complex data in a vectorized workflow. High-quality, fast, and accurate data is critical for red team pipelines, security dashboards, and vector databases.

From a high-level architecture perspective, the shift from flat-file ingestion to structured JSON isn't just a formatting preference; it’s the difference between a "data swamp" and a high-fidelity Cyber Threat Intelligence.

- Reads a text file containing subdomains
- Cleans and normalizes each line
- Assigns a unique, stable ID to every entry
- Serializes the result as JSON for downstream automation

Typical use cases:

- Ingesting into a **vector database** and user can select vector sizing (Qdrant, Milvus, Weaviate, more coming soon etc.) for semantic search and correlation made easier
- Powering recon dashboards or graphs (e.g., host → vuln → service relationships)
- Joining subdomains with WHOIS, DNS, HTTP fingerprinting, or vulnerability scan data