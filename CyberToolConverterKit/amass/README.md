# 🔄 Convert Amass Results → JSON (Vectorized)

[![GitHub Repo](https://img.shields.io/badge/GitHub-Repo-blue?logo=github)](https://github.com/1KevinFigueroa/vector4cyber/tree/main/CyberToolConverterKit/amass)
[![Qdrant](https://img.shields.io/badge/Qdrant-Compatible-brightgreen?logo=qdrant)](https://qdrant.tech/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python)](https://python.org)

---

## 🎯 Why This Matters

**Raw Amass text output** → **Structured JSON** → **Vectorized Intelligence**

Converting Amass results into **JSON format** with **unique IDs** unlocks powerful capabilities for **vector databases** and **automation pipelines**.

> **High-quality, structured data** is the foundation of **Red Team workflows**, **security dashboards**, and **AI-driven threat analysis**.

---

## 🚨 The Problem

| **Format** | **Example** | **Issues** |
|------------|-------------|------------|
| ❌ **Text File** | `example.com` | ❌ No context<br>❌ No source tracking<br>❌ No unique IDs |
| ❌ **Native JSON** | `{"host": " ", "input": " ", "source": "reconeer"}` | ❌ Incomplete fields<br>❌ Missing IDs |
| ✅ **Vectorized JSON** | `{"id": 1, "host": "example.com", "input": "example.com", "source": "reconeer"}` | ✅ Full context<br>✅ Traceability<br>✅ Vectorization-ready |

---

## 💡 The Solution

```bash
convert_AmassTXT2JSON.py input_file.txt output_file.json
