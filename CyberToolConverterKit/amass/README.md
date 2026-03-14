<table align="center">
  <tr>
    <td align="center" width="50%">
      <a href="https://owasp.org/projects/">
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
