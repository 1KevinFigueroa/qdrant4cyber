# Nmap Milvus Hybrid Query Tool

`query_nmap_milvus-MiniLM-L6.py` performs hybrid search over Nmap host data stored in Milvus.

It combines:

- semantic vector search (natural-language query)
- optional metadata filter expressions (`--filter` or interactive `:f`)

## Purpose

The script makes Nmap data easier to explore by allowing intent-based queries such as `ssh servers` while still supporting precise constraints like `ip == "192.168.1.10"`.

## Requirements

- Python 3.8+
- `pymilvus`
- `sentence-transformers`
- Running Milvus instance (default `localhost:19530`)
- Loaded Milvus collection: `nmap_test`

Install dependencies:

```bash
pip install pymilvus sentence-transformers
```

## Architecture

1. **CLI layer (`main`)**
   - parses arguments (`question`, `--top-k`, `--filter`, `--interactive`)
2. **Model layer**
   - loads `all-MiniLM-L6-v2` using `SentenceTransformer`
3. **Data layer (`get_collection`)**
   - connects to Milvus and loads `nmap_test`
4. **Query layer (`query`)**
   - embeds query text, applies optional filter, runs vector search
5. **Interactive layer (`interactive`)**
   - REPL with commands to set `top-k`, set/clear filter, and run searches
6. **Output layer**
   - formatted headers and ranked host output

## Code Walkthrough

### `get_collection()`

Connects to Milvus with configured host/port and loads collection into memory.

### `fix_filter(expr)`

Normalizes some filter input before search. Current implementation auto-quotes unquoted IP equality values:

- input: `ip == 192.168.1.10`
- sent to Milvus: `ip == "192.168.1.10"`

### `query(question, model, collection, top_k, expr=None)`

1. Creates embedding from question text
2. Applies `fix_filter()`
3. Runs Milvus search on `embedding` field with COSINE metric
4. Returns top-k matches including `text`, `ip`, `hostname`, `os`
5. Prints formatted ranked results

### `interactive(model, collection, top_k)`

Supports commands:

- `:k <n>` set top-k
- `:f <expr>` set filter expression
- `:clear` clear filter
- `:quit` / `:q` / `:exit` exit session

Any non-command input is treated as a semantic query.

## Usage

Run from the same directory as `query_nmap_milvus-MiniLM-L6.py`.

### Basic semantic query

```bash
python query_nmap_milvus-MiniLM-L6.py "ssh servers"
```

### Hybrid query with filter

```bash
python query_nmap_milvus-MiniLM-L6.py "http" --filter 'ip == 192.168.47.110'
```

### Interactive mode

```bash
python query_nmap_milvus-MiniLM-L6.py --interactive
```

## Expected Output Examples

### Example 1: semantic query

```text
[INFO] Loading model: all-MiniLM-L6-v2
[INFO] Connecting to Milvus...

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
    22/tcp open ssh
```

### Example 2: semantic + filter

```text
================================================================================
  Query: http
  Results: 1
  Filter: ip == "192.168.47.110"
================================================================================

  [1] score: 0.8765
  ------------------------------------------------------------
    IP: 192.168.47.110
    OS: Linux
    80/tcp open http
```

### Example 3: interactive session

```text
nmap-query> :k 10
  top-k = 10

nmap-query> :f os == "Linux"
  filter set to: os == "Linux"

nmap-query> ssh

  [1] score: 0.9011
  ------------------------------------------------------------
    IP: 192.168.47.110
    OS: Linux
    22/tcp open ssh

nmap-query> :clear
  filter cleared

nmap-query> :q
Goodbye.
```

## Troubleshooting

- **No results**: verify data is ingested into `nmap_test` and embeddings were created with compatible model.
- **Milvus connection error**: check Milvus is running on `localhost:19530`.
- **Filter parse errors**: use valid Milvus expression syntax and quote string values.

## Notes

- Defaults are hardcoded in script constants:
  - host: `localhost`
  - port: `19530`
  - collection: `nmap_test`
  - model: `all-MiniLM-L6-v2`
  - top-k: `5`
