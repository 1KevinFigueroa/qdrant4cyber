# Nuclei Semantic Query for Weaviate (`MiniLM-L6`)

Script: `query-nuclei-weaviate-MiniLM-L6.py`

## Purpose

This script performs semantic search over Nuclei findings stored in Weaviate.

It converts a natural-language query into an embedding with `all-MiniLM-L6-v2`, runs vector similarity search against the `NucleiFinding` collection, and prints ranked findings with metadata.

---

## Requirements

### Python
- Python `3.10+`

### Packages
```bash
pip install weaviate-client sentence-transformers
```

### Weaviate
- Local Weaviate instance running and populated with Nuclei findings.
- Default endpoint shown by the script: `http://localhost:8082`.

Example Docker run:
```bash
docker run -d --name weaviate \
  -p 8082:8080 -p 50051:50051 \
  semitechnologies/weaviate:latest
```

---

## Architecture

```text
User query text
      │
      ▼
SentenceTransformer(all-MiniLM-L6-v2)
      │
      ▼
query.near_vector() on Weaviate
(collection: NucleiFinding)
      │
      ▼
Result objects + distance metadata
      │
      ▼
Formatted CLI output
(one-shot or interactive mode)
```

---

## Code Walkthrough

### Configuration constants
- `WEAVIATE_URL = "http://localhost:8082"`
- `CLASS_NAME = "NucleiFinding"`
- `EMBEDDING_MODEL = "all-MiniLM-L6-v2"`
- `TOP_K_DEFAULT = 5`

### `get_client()`
Connects to local Weaviate via `weaviate.connect_to_local()`.

### Display helpers
- `print_header(question, count)`: prints query summary.
- `print_result(rank, obj)`: prints each result with score and fields.
- `print_no_results()`: shown when no objects are returned.

`print_result` also parses `metadata` from JSON string (if present in stored properties).

### `query(question, model, client, top_k=TOP_K_DEFAULT)`
Core query logic:
1. Encode question into vector (`model.encode(question)`).
2. Fetch collection handle (`NucleiFinding`).
3. Search with `collection.query.near_vector(...)` using:
   - `near_vector`: query embedding
   - `limit`: top-k
   - `return_metadata=["distance"]`
4. Print results in ranked format.

### `interactive(model, client, top_k)`
Starts a REPL-like query console.

Commands:
- `:k <n>` change top-k
- `:quit`, `:exit`, `:q` exit

Handles `Ctrl+C` and `Ctrl+D` gracefully.

### `main()`
- Parses CLI args:
  - optional positional `question`
  - `--top-k` / `-k`
  - `--interactive` / `-i`
- Loads embedding model
- Connects to Weaviate
- Runs one-shot or interactive mode
- Closes client at the end

---

## Usage

Run commands from the same directory as `query-nuclei-weaviate-MiniLM-L6.py`.

### One-shot query

```bash
python query-nuclei-weaviate-MiniLM-L6.py "critical vulnerabilities"
```

### One-shot query with custom top-k

```bash
python query-nuclei-weaviate-MiniLM-L6.py "apache misconfigurations" --top-k 10
```

### Interactive mode

```bash
python query-nuclei-weaviate-MiniLM-L6.py --interactive
```

---

## Expected Output

### Example one-shot success output

```text
Loading embedding model 'all-MiniLM-L6-v2' …
Connecting to Weaviate at http://localhost:8082 …

================================================================================
  Query: critical vulnerabilities
  Results: 2
================================================================================

  [1]  cve-2023-example   —   score: 0.1074
  ------------------------------------------------------------
  Severity  : critical
  Target    : http://dvwa
  Protocol  : http
  Metadata  : {'template': 'cve-2023-example', 'severity': 'critical', 'target': 'http://dvwa', 'protocol': 'http'}


  [2]  apache-detect   —   score: 0.1889
  ------------------------------------------------------------
  Severity  : info
  Target    : http://dvwa
  Protocol  : http
```

### Example when no matches are found

```text
Loading embedding model 'all-MiniLM-L6-v2' …
Connecting to Weaviate at http://localhost:8082 …

  No matching findings found.
```

### Example interactive session

```text
================================================================================
  Nuclei Query Console  —  local Weaviate
  Endpoint: http://localhost:8082  |  Model: all-MiniLM-L6-v2  |  top-k: 5
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

- Use the same embedding model for ingestion and querying to keep vector space consistent.
- Weaviate `distance` is shown as `score`; lower distance usually means closer semantic match.
- First run may be slower due to model download/caching.
