# Nuclei Semantic Query for Milvus (`MiniLM-L6`)

Script: `query-nuclei-milvus-MiniLM-L6.py`

## Purpose

This script performs semantic search over Nuclei findings stored in Milvus.

It converts a natural-language question into an embedding using `all-MiniLM-L6-v2`, searches the `nuclei_findings` collection, and prints ranked matches with metadata (`template`, `severity`, `target`, `protocol`, `extra_info`).

---

## Requirements

- Python `3.10+`
- Python packages:
  - `sentence-transformers`
  - `pymilvus`
- Milvus running and accessible at `localhost:19530`
- A populated `nuclei_findings` collection (for example via `nuclei_to_milvus-MiniLM-L6.py`)

Install dependencies:

```bash
pip install sentence-transformers pymilvus
```

Run Milvus locally (example):

```bash
docker run -d --name milvus \
  -p 19530:19530 -p 9091:9091 \
  milvusdb/milvus:v2.4.0
```

---

## Architecture

The script is organized into four parts:

1. **Configuration**
   - Milvus host/port, collection name, embedding model, default `top-k`.

2. **Connection Layer**
   - `get_collection()` connects to Milvus, loads the collection into memory, and returns a handle.

3. **Query + Render Layer**
   - `query(...)` encodes text and runs vector search.
   - `print_header(...)`, `print_result(...)`, `print_no_results()` handle terminal output formatting.

4. **CLI / Interactive Layer**
   - `main()` handles one-shot mode or interactive mode.
   - `interactive(...)` provides a REPL-style query console with commands.

---

## Code Walkthrough

### Constants

- `MILVUS_HOST = "localhost"`
- `MILVUS_PORT = "19530"`
- `COLLECTION_NAME = "nuclei_findings"`
- `EMBEDDING_MODEL = "all-MiniLM-L6-v2"`
- `TOP_K_DEFAULT = 5`

### `get_collection()`

- Connects to Milvus with timeout.
- Opens the `nuclei_findings` collection.
- Calls `collection.load()` so the collection is query-ready.

### Display Helpers

- `print_header(question, count)`: prints query summary.
- `print_result(rank, hit)`: prints each result and metadata fields.
- `print_no_results()`: shown when no matches are returned.

### `query(question, model, collection, top_k=TOP_K_DEFAULT)`

Core query flow:

1. Encode question into embedding vector.
2. Call `collection.search(...)` with:
   - `anns_field="vector"`
   - `metric_type="COSINE"`
   - `nprobe=10`
   - `limit=top_k`
   - selected metadata output fields
3. Print ranked results.

### `interactive(model, collection, top_k)`

Starts an interactive prompt.

Commands:
- `:k <n>` update top-k
- `:quit`, `:exit`, `:q` exit

It also handles `Ctrl+C` and `Ctrl+D` gracefully.

### `main()`

- Parses args:
  - optional positional `question`
  - `--top-k` / `-k`
  - `--interactive` / `-i`
- Loads embedding model.
- Connects to Milvus.
- Runs one-shot query or interactive console.

---

## Usage

Run the following commands from the same directory as `query-nuclei-milvus-MiniLM-L6.py`.

### One-shot query

```bash
python query-nuclei-milvus-MiniLM-L6.py "critical vulnerabilities"
```

### One-shot query with custom top-k

```bash
python query-nuclei-milvus-MiniLM-L6.py "apache misconfigurations" --top-k 10
```

### Interactive mode

```bash
python query-nuclei-milvus-MiniLM-L6.py --interactive
```

---

## Expected Output

### Example one-shot success output

```text
Loading embedding model 'all-MiniLM-L6-v2' …
Connecting to Milvus at localhost:19530 …

================================================================================
  Query: critical vulnerabilities
  Results: 2
================================================================================

  [1]  cve-2023-example   —   score: 0.8921
  ------------------------------------------------------------
  Severity  : critical
  Target    : https://example.com
  Protocol  : http
  Details   : vulnerable endpoint detected


  [2]  ssl-weak-cipher   —   score: 0.8413
  ------------------------------------------------------------
  Severity  : high
  Target    : 10.10.10.20:443
  Protocol  : tcp
```

### Example when no matches are found

```text
Loading embedding model 'all-MiniLM-L6-v2' …
Connecting to Milvus at localhost:19530 …

  No matching findings found.
```

### Example interactive session

```text
================================================================================
  Nuclei Query Console  —  Milvus
  Collection: nuclei_findings  |  Model: all-MiniLM-L6-v2  |  top-k: 5
  Commands:
    :k <n>    change top-k
    :quit     exit
================================================================================

nuclei-query> misconfigured headers
...results shown...

nuclei-query> :k 10
  top-k set to 10

nuclei-query> :quit
Goodbye.
```

---

## Notes

- Use the same embedding model for ingestion and query (`all-MiniLM-L6-v2`) so vectors remain compatible.
- First run may be slower while model files are downloaded/cached.
- Similarity scores are ranking values; higher generally means more relevant semantic matches.
