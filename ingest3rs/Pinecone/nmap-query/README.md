# Semantic Search for Nmap Scan Data with Pinecone

This project provides a **natural-language semantic search interface for Nmap scan results** stored in a **local Pinecone vector database**.

The script encodes user queries using a **sentence-transformer embedding model** and retrieves the most relevant hosts from the vector index based on **cosine similarity**.

The goal is to allow security analysts, red teamers, and network engineers to **query network scan data using natural language instead of manual filtering**.

Example queries:

```
hosts running Redis
Windows servers with SQL Server
databases exposed on the network
web servers on port 443
```

The system converts these questions into embeddings and finds hosts with similar semantic descriptions stored in the vector index.

The script being documented:

****

---

# Table of Contents

* Overview
* Architecture
* Requirements
* Installation
* Configuration
* Usage
* Interactive Mode
* Example Queries
* Expected Output
* Code Walkthrough
* How Semantic Search Works
* Troubleshooting

---

# Overview

Traditional Nmap output is difficult to query programmatically once scans become large. Analysts often rely on tools like:

* grep
* jq
* manual filtering
* spreadsheets

This project solves that problem by converting scan results into **vector embeddings**, enabling **semantic queries**.

Instead of searching exact strings like:

```
redis
port 6379
```

You can ask:

```
hosts running Redis
```

The script:

1. Encodes the user question using a **SentenceTransformer model**
2. Queries a **Pinecone vector index**
3. Returns the **most semantically similar hosts**

---

# Architecture

```
                ┌───────────────────────┐
                │      Nmap Scans       │
                │ (XML / parsed data)  │
                └──────────┬────────────┘
                           │
                           ▼
                ┌───────────────────────┐
                │  nmap_ingest.py       │
                │  (data ingestion)     │
                └──────────┬────────────┘
                           │
                           ▼
                 ┌─────────────────────┐
                 │   SentenceTransformer│
                 │   all-MiniLM-L6-v2   │
                 └──────────┬───────────┘
                            │ embeddings
                            ▼
                   ┌─────────────────┐
                   │ Pinecone Index  │
                   │ (Docker local)  │
                   └────────┬────────┘
                            │
                            ▼
              query-nmap-pinecone-MiniLM-L6.py
                            │
                            ▼
                 Natural Language Queries
```

---

# Requirements

Python dependencies:

```
pinecone[grpc]
sentence-transformers
```

Install:

```bash
pip install pinecone[grpc] sentence-transformers
```

System requirements:

* Python 3.9+
* Docker
* Local Pinecone container
* Previously ingested Nmap data

---

# Pinecone Configuration

This script assumes a **local Pinecone container**.

Example environment configuration:

```
DIMENSION=384
METRIC=cosine
```

Default connection:

```
http://localhost:5081
```

You can override this using:

```
PINECONE_HOST
```

Example:

```
export PINECONE_HOST=http://localhost:5081
```

---

# Embedding Model

The system uses:

```
all-MiniLM-L6-v2
```

Properties:

| Property   | Value                    |
| ---------- | ------------------------ |
| Dimensions | 384                      |
| Model Type | Sentence Transformer     |
| Speed      | Fast                     |
| Accuracy   | Good semantic similarity |

The embedding model converts text into **384-dimension vectors** used for similarity search.

---

# Usage

Basic syntax:

```bash
python query-nmap-pinecone-MiniLM-L6.py "<query>"
```

Example:

```bash
python query-nmap-pinecone-MiniLM-L6.py "hosts running Redis"
```

Return more results:

```bash
python query-nmap-pinecone-MiniLM-L6.py "Windows servers" --top-k 10
```

---

# Interactive Mode

Interactive mode allows multiple queries in a single session.

Start:

```bash
python query-nmap-pinecone-MiniLM-L6.py --interactive
```

Example console:

```
================================================================================
nmap Query Console — local Pinecone
Index: http://localhost:5081 | Model: all-MiniLM-L6-v2 | top-k: 5
================================================================================

nmap-query>
```

Commands available inside the console:

| Command | Description              |
| ------- | ------------------------ |
| `:k 10` | Change number of results |
| `:quit` | Exit                     |
| `:exit` | Exit                     |
| `:q`    | Exit                     |

---

# Example Queries

Example useful questions:

```
hosts running Redis
Windows servers with SQL Server
databases exposed on the network
hosts running Kubernetes
servers with Docker installed
web servers on port 443
Linux machines running SSH
hosts exposing MongoDB
```

---

# Example Output

Example query:

```
python query-nmap-pinecone-MiniLM-L6.py "hosts running Redis"
```

Output:

```
================================================================================
Query: hosts running Redis
Results: 3
================================================================================

[1]  10.0.1.23 (redis-prod-01)   —   score: 0.9214
------------------------------------------------------------
OS          : Linux
Open ports  : 5
Services    : redis, ssh
Products    : Redis 6.2

    Redis server on port 6379
    SSH service running on port 22
```

Another example:

```
[2]  10.0.1.17
------------------------------------------------------------
OS          : Linux
Open ports  : 3
Services    : redis
Products    : Redis 5.0
```

---

# Code Walkthrough

## Configuration

The script defines core configuration parameters:

```python
PINECONE_HOST = os.environ.get("PINECONE_HOST", "http://localhost:5081")
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
TOP_K_DEFAULT = 5
```

These determine:

* Pinecone connection
* embedding model
* number of results returned

---

## Connecting to Pinecone

Function:

```python
def get_index():
    pc = Pinecone(api_key="pclocal")
    return pc.Index(host=PINECONE_HOST)
```

This connects to the **local Pinecone index running in Docker**.

---

## Query Process

The main search logic:

```python
def query(question, model, index, top_k):
```

Steps performed:

1. Convert question to embedding

```
model.encode(question)
```

2. Query Pinecone index

```
index.query(...)
```

3. Retrieve top matches

4. Display results

---

## Embedding Generation

Example:

```python
q_embedding = model.encode([question])[0].tolist()
```

This produces a **384-dimension vector representation** of the query.

---

## Pinecone Search

Query sent to Pinecone:

```python
results = index.query(
    vector=q_embedding,
    top_k=top_k,
    include_metadata=True,
)
```

Returned matches include:

* similarity score
* metadata
* host information

---

## Result Display

The script extracts metadata fields such as:

* IP address
* hostname
* OS
* open ports
* services
* detected products

Example:

```
IP: 10.0.1.23
Hostname: redis-prod-01
OS: Linux
Services: redis, ssh
```

---

## Interactive REPL

Interactive mode runs a simple **read-eval-print loop**:

```
while True:
    user_input = input("nmap-query>")
```

This allows repeated queries without restarting the script.

Special commands are handled:

```
:k 10
:quit
```

---

# How Semantic Search Works

Traditional search:

```
grep redis scan.txt
```

Requires exact matches.

Semantic search instead:

1. Converts text → vector
2. Measures **cosine similarity**
3. Returns closest matches

Example:

```
Query: "databases exposed on the network"
```

May match:

```
PostgreSQL
MongoDB
MySQL
Redis
```

Because the embeddings capture **semantic meaning**, not just keywords.

---

# Troubleshooting

### Model download slow

First run downloads the embedding model (~90MB).

Solution:

```
Allow model download to complete
```

---

### Pinecone connection error

Check container:

```
docker ps
```

Verify port:

```
localhost:5081
```

---

### No results returned

Possible causes:

* index is empty
* ingestion script not run
* incorrect metadata format

---

# Future Improvements

Possible enhancements:

* filtering by subnet
* time-based scan filtering
* web UI
* LLM-assisted network analysis
* automatic vulnerability tagging
* graph visualization of hosts

---

If you'd like, I can also generate an **architecture diagram for the README** or a **much stronger GitHub-style README (with badges, screenshots, and diagrams)**.
