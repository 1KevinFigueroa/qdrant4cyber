# 🧠 Nmap → Milvus Hybrid Search (MiniLM-L6)

## 📌 Overview

This project provides a **semantic + structured search system** for Nmap scan data using:

* **Milvus** → vector database
* **Sentence Transformers (MiniLM-L6)** → embeddings
* **Hybrid search** → combines vector similarity + metadata filtering

The script:

```
query_nmap_milvus-MiniLM-L6.py
```

allows you to query Nmap results using **natural language** while optionally applying **precise filters** like IP or OS.

---

## 🎯 Purpose

Traditional Nmap analysis is:

* Manual
* Keyword-based
* Hard to scale

This script enables:

✅ Natural language search
✅ Fast similarity matching (vector search)
✅ Structured filtering (IP, OS, etc.)
✅ Interactive query console

👉 Result: A lightweight **AI-powered network search engine**

---

## ⚙️ Requirements

### Python Dependencies

```bash
pip install pymilvus sentence-transformers
```

---

### Infrastructure

* Milvus running locally:

```bash
docker run -d --name milvus \
  -p 19530:19530 -p 9091:9091 \
  milvusdb/milvus:v2.4.0
```

---

### Data Prerequisite

You must have already run the **ingest script** to populate:

```
Collection: nmap_test
```

---

## 🏗️ Architecture

```
                ┌────────────────────────┐
                │   Nmap JSON Results    │
                └──────────┬─────────────┘
                           │
                           ▼
                ┌────────────────────────┐
                │   Ingest Script        │
                │  (MiniLM embeddings)   │
                └──────────┬─────────────┘
                           │
                           ▼
                ┌────────────────────────┐
                │       Milvus           │
                │  (Vector + Metadata)   │
                └──────────┬─────────────┘
                           │
                           ▼
                ┌────────────────────────┐
                │   Query Script         │
                │ (Hybrid Search Engine) │
                └──────────┬─────────────┘
                           │
                           ▼
                ┌────────────────────────┐
                │  Ranked Search Results │
                └────────────────────────┘
```

---

## 🧩 How the Script Works

### 1. Connect to Milvus

```python
connections.connect("default", host="localhost", port="19530")
collection = Collection("nmap_test")
collection.load()
```

* Establishes connection
* Loads collection into memory for search

---

### 2. Convert Query → Embedding

```python
q_embedding = model.encode([question])[0].tolist()
```

* Uses **MiniLM-L6 (384-dim)**
* Same model used during ingestion → consistent search

---

### 3. Hybrid Search Execution

```python
collection.search(
    data=[q_embedding],
    anns_field="embedding",
    param={"metric_type": "COSINE", "params": {"nprobe": 10}},
    limit=top_k,
    expr=expr,
    output_fields=["text", "ip", "hostname", "os"]
)
```

#### Key Concepts:

| Component   | Purpose                    |
| ----------- | -------------------------- |
| `embedding` | Vector similarity search   |
| `expr`      | Structured filtering       |
| `COSINE`    | Semantic similarity metric |
| `nprobe`    | Search accuracy vs speed   |

---

### 4. Filter Auto-Fix Logic

```python
def fix_filter(expr):
```

Automatically corrects user input:

| Input               | Converted To          |
| ------------------- | --------------------- |
| `ip == 192.168.1.1` | `ip == "192.168.1.1"` |
| `os == Linux`       | `os == "Linux"`       |

👉 Prevents common Milvus parsing errors

---

### 5. Result Formatting

Each result includes:

* Score (similarity)
* IP address
* OS
* Parsed Nmap text

---

## 🔍 Supported Filters

### Basic Filters

```bash
ip == "192.168.1.10"
os == "Linux"
```

---

### Logical Filters

```bash
os == "Linux" && ip == "192.168.1.10"
```

---

### Multi-value Filters

```bash
ip in ["192.168.1.1", "10.0.0.5"]
```

---

## 🚀 Usage

---

### 🔹 Basic Semantic Search

```bash
python query_nmap_milvus-MiniLM-L6.py "ssh servers"
```

---

### 🔹 Hybrid Search (Semantic + Filter)

```bash
python query_nmap_milvus-MiniLM-L6.py "http" --filter 'ip == 192.168.47.110'
```

---

### 🔹 Interactive Mode

```bash
python query_nmap_milvus-MiniLM-L6.py --interactive
```

---

### Interactive Commands

| Command     | Description          |
| ----------- | -------------------- |
| `:k 10`     | Change top-k results |
| `:f <expr>` | Set filter           |
| `:clear`    | Clear filter         |
| `:quit`     | Exit                 |

---

## 📊 Example Outputs

---

### Example 1: Basic Query

```bash
python query_nmap_milvus-MiniLM-L6.py "ssh servers"
```

#### Output

```
================================================================================
  Query: ssh servers
  Results: 3
================================================================================

  [1] score: 0.9123
  ------------------------------------------------------------
    IP: 192.168.47.110
    OS: Linux
    Host 192.168.47.110
    Open ports:
    22 - ssh
```

---

### Example 2: Hybrid Query

```bash
python query_nmap_milvus-MiniLM-L6.py "http" --filter 'ip == 192.168.47.110'
```

#### Output

```
================================================================================
  Query: http
  Results: 1
  Filter: ip == "192.168.47.110"
================================================================================

  [1] score: 0.8765
  ------------------------------------------------------------
    IP: 192.168.47.110
    OS: Linux
    Host 192.168.47.110
    Open ports:
    80 - http
```

---

### Example 3: Interactive Session

```
nmap-query> :f os == Linux
nmap-query> ssh

[1] score: 0.91
IP: 192.168.47.110
OS: Linux
...
```

---

## ⚠️ Common Issues

### ❌ Invalid Expression Error

```
cannot parse expression: ip == 192.168.1.1
```

✔ Fixed automatically by `fix_filter()`

---

### ❌ No Results

* Check ingestion completed
* Verify collection name: `nmap_test`

---

### ⚠️ HuggingFace Warning

```
You are sending unauthenticated requests
```

Optional fix:

```bash
set HF_TOKEN=your_token_here
```

---

## 🔥 Key Features

* ✅ Semantic search over network data
* ✅ Hybrid filtering (vector + metadata)
* ✅ Auto-correct filter syntax
* ✅ Interactive CLI
* ✅ Fast (Milvus optimized)

---

## 🚀 Future Enhancements

* 🔍 Port-based filtering (`port == 22`)
* 🧠 NLP → automatic filter generation
* 🔗 Integration with Suricata / SIEM pipelines
* 📊 Visualization dashboards

---

## 🧠 Summary

This script transforms raw Nmap data into:

> 🔎 **An intelligent, searchable, AI-powered network dataset**

Instead of:

```
grep + manual analysis
```

You now have:

```
semantic + structured + scalable search
```
