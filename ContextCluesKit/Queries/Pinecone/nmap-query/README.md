# Nmap Pinecone Query Tool

`query-nmap-pinecone-MiniLM-L6.py` provides semantic search over Nmap scan data stored in a local Pinecone index.

It encodes natural-language questions with `all-MiniLM-L6-v2` and returns relevant hosts using cosine similarity.

## Purpose

The script enables fast, intent-based querying of Nmap data without manual grep-style filtering.

Example questions:

- `hosts running Redis`
- `Windows servers with SQL Server`
- `web servers on port 443`

## Requirements

- Python 3.9+
- `pinecone[grpc]`
- `sentence-transformers`
- Local Pinecone index running in Docker
- Ingested Nmap data (for example with `nmap_ingest.py`)

Install dependencies:

```bash
pip install pinecone[grpc] sentence-transformers
```

Optional environment variable:

- `PINECONE_HOST` (default: `http://localhost:5081`)

## Architecture

1. **CLI layer (`main`)**
   - Parses `question`, `--top-k`, and `--interactive`.
2. **Model layer**
   - Loads `all-MiniLM-L6-v2` once.
3. **Connection layer (`get_index`)**
   - Connects to local Pinecone index.
4. **Query layer (`query`)**
   - Embeds query and performs similarity search.
5. **Display layer**
   - Prints ranked results and metadata.
6. **Interactive layer (`interactive`)**
   - REPL loop for multiple queries with runtime `top-k` updates.

## Code Walkthrough

### `get_index()`

Creates a Pinecone client and returns an index handle using `PINECONE_HOST`.

### `query(question, model, index, top_k)`

1. Encodes question to vector.
2. Calls `index.query(vector=..., top_k=..., include_metadata=True)`.
3. Reads `matches`.
4. Prints results with score and metadata fields (`ip`, `hostname`, `os`, `services`, `products`, `text`).

### `interactive(model, index, top_k)`

Supports:

- `:k <n>` change result count
- `:quit`, `:q`, `:exit` exit
- any other input runs semantic search

### `main()`

- Validates arguments
- Loads embedding model
- Connects to Pinecone
- Runs one-shot mode or interactive mode

## Usage

Run from the same directory as `query-nmap-pinecone-MiniLM-L6.py`.

### One-shot query

```bash
python query-nmap-pinecone-MiniLM-L6.py "hosts running Redis"
```

### One-shot query with custom top-k

```bash
python query-nmap-pinecone-MiniLM-L6.py "Windows servers" --top-k 10
```

### Interactive mode

```bash
python query-nmap-pinecone-MiniLM-L6.py --interactive
```

## Expected Output Examples

### One-shot query

```text
Loading embedding model 'all-MiniLM-L6-v2' …
Connecting to local Pinecone index at http://localhost:5081 …

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
```

### Interactive session

```text
================================================================================
  nmap Query Console  —  local Pinecone
  Index: http://localhost:5081  |  Model: all-MiniLM-L6-v2  |  top-k: 5
================================================================================

nmap-query> :k 10
  top-k set to 10

nmap-query> web servers on port 443
... ranked results ...

nmap-query> :q
Goodbye.
```

## Troubleshooting

- **No results**: verify data was ingested and metadata exists.
- **Connection error**: verify local Pinecone is running and `PINECONE_HOST` is correct.
- **Slow first run**: model download/caching may take time initially.

## Notes

- Use the same embedding model for ingest and query: `all-MiniLM-L6-v2`.
- Default `top-k` is `5`.
