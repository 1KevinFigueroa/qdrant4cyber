# Nuclei Semantic Query for Pinecone (`MiniLM-L6`)

Script: `query_nuclei-pinecone-MiniLM-L6.py`

## Purpose

This script performs semantic search over Nuclei findings stored in a local Pinecone index.

It converts your natural-language query into an embedding using `all-MiniLM-L6-v2`, then retrieves the most similar findings from Pinecone with metadata like template, severity, target, and protocol.

---

## Requirements

- Python 3.10+
- Python packages:
  - `sentence-transformers`
  - `pinecone`
- Local Pinecone index running and populated with Nuclei vectors (for example via `ingest3rs/Pinecone/nuclei-import/nuclei_to_pinecone-MiniLM-L6.py`)

Install dependencies:

```bash
pip install sentence-transformers pinecone
```

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `PINECONE_HOST` | `http://localhost:5081` | URL for the local Pinecone index |

---

## Architecture

The script is organized into four layers:

1. **Configuration**
   - Defines host, embedding model, and default top-k.

2. **Connection Layer**
   - `get_index()` initializes the Pinecone client and returns an index handle.

3. **Query + Rendering Layer**
   - `query(...)` embeds the question and sends vector search requests.
   - `print_header(...)`, `print_result(...)`, and `print_no_results()` format output.

4. **Interactive CLI Layer**
   - `interactive(...)` runs a REPL-like console for repeated querying.
   - Supports `:k <n>` to change result count and `:quit` to exit.

---

## Code Walkthrough

### Constants

- `PINECONE_HOST`: connection target (from env var)
- `EMBEDDING_MODEL`: `all-MiniLM-L6-v2`
- `TOP_K_DEFAULT`: default number of results (`5`)

### `get_index()`

Creates a Pinecone client with local key (`pclocal`) and binds to the configured host.

### Display Functions

- `print_header(question, count)`: prints query summary
- `print_result(rank, match)`: prints each match with score + metadata
- `print_no_results()`: message when no matches are returned

### `query(question, model, index, top_k=TOP_K_DEFAULT)`

Core query flow:

1. Encode the question into a dense vector.
2. Call `index.query(...)` with:
   - `vector`
   - `top_k`
   - `include_metadata=True`
3. Display results (or no-results message).

### `interactive(model, index, top_k)`

Starts a query console where users can run repeated searches.

Commands:

- `:k <n>` set top-k dynamically
- `:quit`, `:exit`, `:q` leave console

Handles `Ctrl+C` / `Ctrl+D` gracefully.

### `main()`

- Parses CLI args:
  - optional positional `question`
  - `--top-k` / `-k`
  - `--interactive` / `-i`
- Loads embedding model
- Connects to Pinecone
- Executes one-shot query or interactive mode

---

## Usage

### One-shot query

```bash
python query_nuclei-pinecone-MiniLM-L6.py "critical vulnerabilities"
```

### One-shot query with custom result count

```bash
python query_nuclei-pinecone-MiniLM-L6.py "apache misconfigurations" --top-k 10
```

### Interactive mode

```bash
python query_nuclei-pinecone-MiniLM-L6.py --interactive
```

---

## Expected Output

### Example one-shot success output

```text
Loading embedding model 'all-MiniLM-L6-v2' …
Connecting to Pinecone at http://localhost:5081 …

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
Connecting to Pinecone at http://localhost:5081 …

  No matching findings found.
```

### Example interactive session

```text
================================================================================
  Nuclei Query Console  —  local Pinecone
  Index: http://localhost:5081  |  Model: all-MiniLM-L6-v2  |  top-k: 5
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

- Use the same embedding model for ingestion and query (`all-MiniLM-L6-v2`) to keep vectors compatible.
- First run may be slower while model files are downloaded/cached.
- Returned scores are similarity scores; higher usually means more relevant semantic matches.
