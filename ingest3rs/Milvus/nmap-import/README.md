# 🚀 Nmap → Milvus Ingestion Pipeline (MiniLM-L6)

## 📌 Overview

This script  ingests **Nmap JSON scan results** into a **Milvus vector database** using semantic embeddings.

It transforms raw scan data into:

* 🧠 **Vector embeddings** (semantic representation)
* 📊 **Structured metadata** (IP, OS, hostname)
* 🔎 **Searchable dataset** (for hybrid semantic queries)

---

## 🎯 Purpose

Nmap produces detailed scan data, but:

* It’s difficult to search semantically
* Keyword-based search is limited
* Large scans become hard to analyze

This script enables:

* ✅ Semantic search over hosts/services
* ✅ Structured filtering (IP, OS, etc.)
* ✅ Fast retrieval using Milvus
* ✅ Scalable ingestion of large scan datasets

👉 Result: A foundation for **AI-powered network analysis**

---

## ⚙️ Requirements

### Python Dependencies

```bash
pip install pymilvus sentence-transformers
```

---

### Milvus (Required)

Run Milvus locally:

```bash
docker run -d --name milvus \
  -p 19530:19530 -p 9091:9091 \
  milvusdb/milvus:v2.4.0
```

---

## 🏗️ Architecture

```text
        Nmap JSON File
               │
               ▼
        Parsing Logic
     (extract hosts/ports)
               │
               ▼
     Text Representation
 ("Host X running Y...")
               │
               ▼
   SentenceTransformer Model
      (MiniLM-L6 embeddings)
               │
               ▼
          Milvus DB
   (vector + metadata storage)
```

---

## 🧩 How the Script Works

---

### 1. Connect to Milvus

```python
connections.connect("default", host="localhost", port="19530")
```

* Establishes connection to Milvus server

---

### 2. Create or Reset Collection

```python
create_collection(reset=False)
```

* If `--reset` is used:

  * Drops existing collection
  * Recreates schema

#### Schema:

| Field     | Type              | Description                |
| --------- | ----------------- | -------------------------- |
| id        | INT64             | Auto-generated primary key |
| embedding | FLOAT_VECTOR(384) | Semantic vector            |
| text      | VARCHAR           | Human-readable summary     |
| ip        | VARCHAR           | Host IP                    |
| hostname  | VARCHAR           | Hostname                   |
| os        | VARCHAR           | Operating system           |

---

### 3. Parse Nmap JSON

```python
parse_nmap_json(path)
```

Extracts:

* Live hosts only (`status == up`)
* IPv4 addresses
* Open ports and services

Example output:

```json
{
  "ip": "192.168.1.10",
  "ports": [
    {"port": "22", "service": "ssh"}
  ]
}
```

---

### 4. Convert Host → Text

```python
host_to_text(h)
```

Example:

```text
Host 192.168.1.10
Open ports:
22 - ssh
80 - http
```

👉 This becomes the **semantic representation input**

---

### 5. Generate Embeddings

```python
model = SentenceTransformer("all-MiniLM-L6-v2")
embeddings = model.encode(texts)
```

* Converts text → 384-dimensional vectors
* Same model used later for querying

---

### 6. Batch Insert into Milvus

```python
collection.insert([
    embeddings,
    texts,
    ips,
    hostnames,
    os_list
])
```

* Inserts data in batches (`BATCH_SIZE = 64`)
* Ensures scalability for large datasets

---

### 7. Create Index

```python
collection.create_index(
    field_name="embedding",
    index_params={
        "index_type": "IVF_FLAT",
        "metric_type": "COSINE",
        "params": {"nlist": 1024}
    }
)
```

* Enables fast similarity search
* Uses **COSINE similarity** (best for embeddings)

---

### 8. Finalize

```python
collection.flush()
collection.load()
```

* Persists data
* Loads collection into memory

---

## 🚀 Usage

---

### 🔹 Basic Ingestion

```bash
python import_nmap_to_milvus-MiniLM-L6.py scan.json
```

---

### 🔹 Reset & Recreate Collection

```bash
python import_nmap_to_milvus-MiniLM-L6.py scan.json --reset
```

---

## 📊 Example Output

```text
[INFO] Creating collection: nmap_test
[INFO] Parsed 5 hosts
[INFO] Generating embeddings...
[INFO] Inserting into Milvus...
  inserted 5/5

✅ Done: 5 records inserted into 'nmap_test'
```

---

## 🔍 Example Input (Nmap JSON)

```json
{
  "nmaprun": {
    "host": {
      "status": {"@state": "up"},
      "address": {"@addr": "192.168.1.10", "@addrtype": "ipv4"},
      "ports": {
        "port": {
          "@portid": "22",
          "state": {"@state": "open"},
          "service": {"@name": "ssh"}
        }
      }
    }
  }
}
```

---

## ⚠️ Common Issues

---

### ❌ No Hosts Found

```text
No valid hosts found.
```

✔ Ensure:

* JSON structure is valid
* Hosts are marked `"@state": "up"`

---

### ❌ Connection Error

```text
failed to connect to server
```

✔ Ensure Milvus is running on port `19530`

---

### ❌ Dimension Mismatch

* Embeddings must be **384-dim**
* Must match schema exactly

---

### ❌ Collection Schema Conflict

If schema changed:

```bash
--reset
```

---

## 🔥 Key Features

* ✅ Converts Nmap → semantic vectors
* ✅ Batch ingestion (scalable)
* ✅ Hybrid-ready schema (metadata + vectors)
* ✅ COSINE similarity optimized
* ✅ CLI-friendly

---

## 🚀 Next Steps

After ingestion, you can:

* 🔎 Run hybrid queries (semantic + filters)
* 🧠 Build AI-driven search tools
* 🔐 Integrate with SIEM pipelines
* 📊 Analyze network attack surfaces

---

## 🧠 Summary

This script transforms:

```text
Raw Nmap JSON
```

Into:

```text
Searchable vector intelligence dataset
```

👉 Enabling:

* Faster analysis
* Smarter querying
* Scalable security workflows

