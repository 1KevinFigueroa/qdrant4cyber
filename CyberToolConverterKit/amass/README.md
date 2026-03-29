<table align="center">
  <tr>
    <td align="center" width="50%">
      <a href="https://github.com/owasp-amass/amass">
        <img src="https://img.shields.io/badge/OWASP-Flagship-00589d?logo=owasp&logoColor=white" alt="OWASP Flagship" width="100">
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
        <img src="https://github.com/1KevinFigueroa/vector4cyber/blob/main/RTFM-Knowledge/img/appLogos/Amass.png" width="300" alt="Amass Logo">
      </a>
    </td>
    <td align="center" width="50%">
      <img src="https://github.com/1KevinFigueroa/vector4cyber/blob/main/RTFM-Knowledge/img/Vector4Cyber_extraSmalllogo.png" width="300" alt="Program Logo">
    </td>
  </tr>
</table>

# 🔄 Convert Amass Results → JSON (Vectorized)

[![GitHub Repo](https://img.shields.io/badge/GitHub-Repo-blue?logo=github)](https://github.com/1KevinFigueroa/vector4cyber/tree/main/CyberToolConverterKit/amass)
[![Qdrant](https://img.shields.io/badge/Qdrant-Compatible-brightgreen?logo=qdrant)](https://qdrant.tech/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)](https://python.org)

---

## 🎯 Overview and Why This Matters
In the world of vector databases—specifically, context is the currency of accuracy. Here is the breakdown of why parsers is the "missing link" for these systems.

From a high-level architecture perspective, the shift from flat-file ingestion to structured JSON isn't just a formatting preference; it’s the difference between a "data swamp" and a high-fidelity Cyber Threat Intelligence (CTI) pipeline. Converting Amass results from a plain text file to a structured **JSON format** makes a significant difference when the data is being vectorized. Properly structured JSON with unique IDs is extremely useful for aggregating and correlating complex data in a vectorized workflow. High-quality, fast, and accurate data is critical for red team pipelines, security dashboards, and vector databases.

- ✅ Imports amass scan data into User Selection of VectorDB collection named "<NAME>"
- ✅ Extracts host information including IP addresses, hostnames, MAC addresses, vendors, OS detection
- ✅ Stores open ports and services information
- ✅ Creates searchable documents for each host
- ✅ Validates JSON file format
- ✅ Provides clear error messages and usage instructions

> **High-quality, structured data** is the foundation of **Red Team workflows**, **security dashboards**, and **AI-driven threat analysis**.

## Prerequisites

- Python 3.7+


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

**Raw Amass text output** → **Structured JSON** → **Vectorized Intelligence**

---

## 🚨 The Problem

| **Format** | **Example** | **Issues** |
|------------|-------------|------------|
| ❌ **Text File** | `example.com` | ❌ No context<br>❌ No source tracking<br>❌ No unique IDs |
| ❌ **Native JSON** | `{"host": " ", "input": " ", "source": "reconeer"}` | ❌ Incomplete fields<br>❌ Missing IDs |
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
> **usage: convertAmassTXT2JSON.py [-h] input_file output_file**

```bash
convert_AmassTXT2JSON.py input_file.txt output_file.json