<table align="center">
  <tr>
    <td align="center" width="50%">
      <a href="https://github.com/v0re/dirb">
        <img src="https://img.shields.io/badge/Open%20Source-10000000?style=flat&logo=github&logoColor=black" alt="DIRB open-source tool" width="100">
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
        <img src="https://github.com/1KevinFigueroa/vector4cyber/blob/main/RTFM-Knowledge/img/appLogos/dirb.png" width="150" alt="Amass Logo">
      </a>
    </td>
    <td align="center" width="50%">
      <img src="https://github.com/1KevinFigueroa/vector4cyber/blob/main/RTFM-Knowledge/img/Vector4Cyber_extraSmalllogo.png" width="300" alt="Program Logo">
    </td>
  </tr>
</table>

# 🔄 Convert Dirb Results → JSON (Vectorized)

[![GitHub Repo](https://img.shields.io/badge/GitHub-Repo-blue?logo=github)](https://github.com/1KevinFigueroa/vector4cyber/tree/main/CyberToolConverterKit/dirb)
[![Qdrant](https://img.shields.io/badge/Qdrant-Compatible-brightgreen?logo=qdrant)](https://qdrant.tech/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)](https://python.org)

---

## 🎯 Overveiw and Why This Matters
In the world of vector databases—specifically, context is the currency of accuracy. Here is the breakdown of why parsers is the "missing link" for these systems.

From a high-level architecture perspective, the shift from flat-file ingestion to structured JSON isn't just a formatting preference; it’s the difference between a "data swamp" and a high-fidelity Cyber Threat Intelligence (CTI) pipeline. Converting Assetfinder results from a plain text file to a structured **JSON format** makes a significant difference when the data is being vectorized. Properly structured JSON with unique IDs is extremely useful for aggregating and correlating complex data in a vectorized workflow. High-quality, fast, and accurate data is critical for red team pipelines, security dashboards, and vector databases.
> **High-quality, structured data** is the foundation of **Red Team workflows**, **security dashboards**, and **AI-driven threat analysis**.

**Raw dirb text output** → **Structured JSON** → **Vectorized Intelligence**

---

## 🚨 The Problem

| **Format** | **Example** | **Issues** |
|------------|-------------|------------|
| ❌ **Text File** | `example.com` | ❌ No context<br>❌ No source tracking<br>❌ No unique IDs |
| ✅ **Vectorized JSON** | `{"id": 1, "host": "example.com"}` | ✅ Full context<br>✅ Traceability<br>✅ Vectorization-ready |

---

## 📊 Vector Databases Supported

| **VectorDB** | **Supported** | **Status** |
|--------------|---------------|------------|
| ✅ **Qdrant** |  ✅ | <a href="https://github.com/1KevinFigueroa/vector4cyber/tree/main/ingest3rs/Qdrant/dirb" target="_blank" rel="noopener noreferrer">✅ Completed</a> |
| ✅ **ChromaDB** |  ✅ | ⚡ In progress |
| ✅ **PineCone** |  ✅ | ⚡ In progress |
| ✅ **Weaviate** |  ✅ | ⚡ In progress |
| ✅ **Milvus** |  ✅ | ⚡ In progress |
---

## 💡 The Solution
> **Usage: usage: convert_dirb2JSON_v0.2.py [-h] [-o output_file] input_file**

```bash
convert_dirb2JSON.py input_file.txt output_file.json


