# 🧪 Milvus Vector Database Demo (test-connect.py)

## 📌 Overview

This script  demonstrates a **minimal end-to-end workflow** using Milvus:

* Connect to a Milvus instance
* Create a collection (vector table)
* Insert sample vector data
* Build an index
* Perform a similarity search
* Return nearest results

👉 It’s essentially a **hello-world for vector databases with Milvus**

---

## 🎯 Purpose

The goal of this script is to:

* Show how Milvus works at a basic level
* Demonstrate vector insertion and similarity search
* Provide a simple test environment for validating your setup

This is useful for:

* Learning Milvus fundamentals
* Testing connectivity
* Understanding vector similarity search mechanics

---

## ⚙️ Requirements

### Python Dependencies

```bash
pip install pymilvus
```

---

### Milvus Server

Run Milvus locally using Docker:

```bash
docker run -d --name milvus \
  -p 19530:19530 -p 9091:9091 \
  milvusdb/milvus:v2.4.0
```

---

## 🏗️ Architecture

```text
        Python Script
             │
             ▼
     Milvus Client (pymilvus)
             │
             ▼
        Milvus Server
             │
     ┌───────┴────────┐
     │                │
 Insert Vectors   Search Query
     │                │
     ▼                ▼
  Stored Data   Similar Results
```

---

## 🧩 Code Walkthrough

---

### 1. Connect to Milvus

```python
connections.connect("default", host="localhost", port="19530")
```

* Establishes a connection to the Milvus server
* Uses default alias `"default"`

---

### 2. Define Collection Schema

```python
fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=4)
]
```

* `id` → auto-generated primary key
* `embedding` → vector field (dimension = 4)

---

### 3. Create Collection

```python
collection = Collection(name="demo_collection", schema=schema)
```

* Creates a new collection (similar to a table in SQL)

---

### 4. Insert Sample Data

```python
data = [[
    [random.random() for _ in range(4)]
    for _ in range(10)
]]
```

* Generates 10 random vectors (dimension = 4)
* Inserts them into Milvus:

```python
collection.insert(data)
```

---

### 5. Create Index

```python
collection.create_index(
    field_name="embedding",
    index_params={
        "index_type": "IVF_FLAT",
        "metric_type": "L2",
        "params": {"nlist": 128}
    }
)
```

* Improves search performance
* Uses:

  * `IVF_FLAT` → indexing algorithm
  * `L2` → Euclidean distance

---

### 6. Load Collection

```python
collection.load()
```

* Loads data into memory for querying
* Required before search

---

### 7. Perform Search

```python
results = collection.search(
    data=query_vectors,
    anns_field="embedding",
    param={"metric_type": "L2", "params": {"nprobe": 10}},
    limit=3
)
```

* Searches for nearest vectors
* Returns top 3 matches

---

### 8. Display Results

```python
for hits in results:
    for hit in hits:
        print(f"ID: {hit.id}, Distance: {hit.distance}")
```

* Prints:

  * Vector ID
  * Distance (similarity score)

---

## 🚀 How to Run

```bash
python test-connect.py
```

---

## 📊 Example Output

```text
ID: 7, Distance: 0.2134
ID: 2, Distance: 0.2871
ID: 9, Distance: 0.3019
```

### 🧠 Interpretation

* Lower distance = more similar vector
* ID corresponds to inserted vector
* Results are ranked by similarity

---

## 🔍 Key Concepts Explained

| Concept    | Meaning                            |
| ---------- | ---------------------------------- |
| Vector     | Numerical representation of data   |
| Embedding  | Vector representation of content   |
| Collection | Table of vectors                   |
| Index      | Structure for fast search          |
| Distance   | Similarity metric (lower = closer) |

---

## ⚠️ Common Issues

### ❌ Connection Error

```text
failed to connect to server
```

✔ Ensure Milvus is running on port `19530`

---

### ❌ Collection Already Exists

If rerunning script:

```python
Collection(name="demo_collection", schema=schema)
```

may fail.

✔ Fix by dropping first:

```python
from pymilvus import utility
utility.drop_collection("demo_collection")
```

---

### ❌ Dimension Mismatch

* All vectors must match defined dimension (4)

---

## 🔥 Key Takeaways

* Milvus stores and searches vectors efficiently
* Similarity is based on distance (L2 here)
* Indexing is critical for performance
* Schema must match inserted data exactly

---

## 🚀 Next Steps

Once comfortable, you can:

* Increase vector dimension (e.g., 384 for embeddings)
* Use real data (text embeddings, Nmap results)
* Switch to COSINE similarity
* Add metadata fields (IP, OS, etc.)
* Build hybrid search systems

---

## 🧠 Summary

This script is a **minimal working example** of:

> Vector insertion → indexing → similarity search

It provides a strong foundation for building:

* Semantic search systems
* AI-powered applications
* Security analytics pipelines

---

✅ You now understand the core Milvus workflow end-to-end.
