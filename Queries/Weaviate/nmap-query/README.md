# Nmap Hybrid Query Tool for Weaviate (`query-nmap-weaviate-MiniLM-L6.py`)

## Purpose

`query-nmap-weaviate-MiniLM-L6.py` is a command-line and interactive query tool for searching Nmap scan data stored in Weaviate.

It combines:

- **Semantic search** (MiniLM embeddings)
- **Keyword relevance** (hybrid search)
- **Structured filtering** (`ip`, `os`, `tags`)

This allows natural language queries like:

- `ssh servers`
- `linux web hosts`
- `kubernetes` with `tags contains k8s_api`

---

## Requirements

### Python

- Python 3.9+

### Dependencies

Install:

```bash
pip install weaviate-client sentence-transformers
```

### Runtime Services

- Weaviate running locally (default: `http://localhost:8080`)
- Weaviate gRPC available (default expected: `localhost:50051`)
- Existing class/collection: `NmapHost`
- Data already ingested (for example via `nmap_to_weaviate-MiniLM-L6.py`)

---

## Architecture

```text
User Query
   │
   ▼
SentenceTransformer (all-MiniLM-L6-v2)
   │
   ▼
Query Vector (384 dims)
   │
   ▼
Weaviate Hybrid Search (BM25 + vector, alpha=0.5)
   │
   ├── Optional Filter Parsing
   │     ├── ip == "x.x.x.x"
   │     ├── os == "Linux"
   │     └── tags contains <tag>
   │
   ▼
Ranked Results (score + host properties)
```

---

## Script Configuration

The script currently uses:

- `WEAVIATE_URL = "http://localhost:8080"`
- `CLASS_NAME = "NmapHost"`
- `MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"`
- `TOP_K_DEFAULT = 5`

---

## Code Walkthrough

### `connect()`

- Parses host/port from `WEAVIATE_URL`
- Connects to Weaviate using custom HTTP + gRPC settings
- Raises a clear error if gRPC is unavailable

### `fix_filter(expr)`

- Normalizes filter input
- Auto-quotes unquoted IPv4 values
  - Example: `ip == 192.168.1.10` → `ip == "192.168.1.10"`

### `build_where_filter(expr)`

Parses user filter expressions into Weaviate filters.

Supported formats:

- `ip == "192.168.1.10"`
- `os == "Linux"`
- `tags contains k8s_api`

Unsupported syntax prints:

- `[WARN] Unsupported filter format`

### `query(client, model, question, top_k, expr=None)`

Core query execution:

1. Build optional filter
2. Encode question with MiniLM
3. Run `collection.query.hybrid(...)`
4. Return top results with score and selected fields

Requested fields:

- `ip`
- `hostname`
- `os`
- `tags`
- `text`

### `interactive(client, model, top_k)`

Interactive REPL with commands:

- `:k <n>` change top-k
- `:f <expr>` set filter
- `:clear` clear filter
- `:quit` / `:exit` / `:q` exit

### `main()`

- Parses CLI arguments
- Connects to Weaviate
- Loads MiniLM model
- Runs either one-shot query or interactive mode
- Always closes client in `finally`

---

## Usage

Run commands from the same directory as `query-nmap-weaviate-MiniLM-L6.py`.

### Basic query

```bash
python query-nmap-weaviate-MiniLM-L6.py "ssh servers"
```

### Query with filter

```bash
python query-nmap-weaviate-MiniLM-L6.py "kubernetes" --filter 'tags contains k8s_api'
```

### Query with custom top-k

```bash
python query-nmap-weaviate-MiniLM-L6.py "linux hosts" --top-k 10
```

### Interactive mode

```bash
python query-nmap-weaviate-MiniLM-L6.py --interactive
```

---

## Example Commands and Expected Output

### 1) Basic semantic query

Command:

```bash
python query-nmap-weaviate-MiniLM-L6.py "ssh servers"
```

Expected output shape:

```text
[INFO] Connecting to Weaviate...
[INFO] Loading MiniLM model...

================================================================================
  Query: ssh servers
  Results: 2
================================================================================

  [1] score: 0.8210
  ------------------------------------------------------------
    IP: 192.168.47.110
    OS: Linux
    Tags: linux, web_server
    Host 192.168.47.110 running Linux
    Open services:
    22 OpenSSH
```

### 2) Filtered hybrid query

Command:

```bash
python query-nmap-weaviate-MiniLM-L6.py "kubernetes" --filter 'tags contains k8s_api'
```

Expected output shape:

```text
================================================================================
  Query: kubernetes
  Results: 1
  Filter: tags contains k8s_api
================================================================================

  [1] score: 0.9032
  ------------------------------------------------------------
    IP: 10.10.10.12
    OS: Linux
    Tags: kubernetes, k8s_api, linux
```

### 3) No results case

```text
No matching hosts found.
```

### 4) Unsupported filter format

```text
[WARN] Unsupported filter format
```

### 5) Connection failure case

```text
Could not connect to Weaviate gRPC at localhost:50051. Ensure Weaviate is running and the gRPC port is exposed.
```

---

## Notes / Limitations

- Filter parser is intentionally simple and string-based.
- Complex boolean expressions are not supported in current implementation.
- `alpha` is fixed at `0.5` (equal balance between semantic and keyword signals).
- First run may take longer while the sentence-transformer model is loaded/downloaded.
