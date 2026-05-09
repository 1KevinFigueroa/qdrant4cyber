# DIRB Weaviate Query (`query_dirb_weaviate-MiniLM-L6.py`)

This script queries the `DirbFinding` collection in Weaviate to retrieve and explore directories, files, and paths discovered by DIRB.

It supports two modes:

- **Canned queries** — six pre-built demonstrations that run automatically
- **Interactive mode** — a REPL with semantic search, property filters, and summary statistics

Semantic search is powered by `all-MiniLM-L6-v2` via Weaviate's `text2vec-transformers` module.

---

## Purpose

Once DIRB findings are ingested into Weaviate, you need a way to explore them beyond simple grep. This script lets you ask natural-language questions like:

- "SQL injection directories"
- "admin login panels"
- "file upload endpoints"
- "cross-site scripting vulnerabilities"

It also provides structured filters for drilling into specific hosts, HTTP status codes, or finding types.

---

## Requirements

### Python

- Python 3.10+
- Packages:

```bash
pip install weaviate-client
```

### Weaviate

A reachable Weaviate instance (default: `http://localhost:8080`) with gRPC on port `50051`, running the `text2vec-transformers` module with `all-MiniLM-L6-v2`.

### Data

The `DirbFinding` collection must already exist and be populated. Run the ingestor first:

```bash
python dirb_to_weaviate-MiniLM-L6.py dirb-results.json
```

---

## Architecture

```text
User Query (free text or command)
   │
   ▼
query_dirb_weaviate-MiniLM-L6.py
   │
   ├─ Semantic search ──► Weaviate near_text (text2vec-transformers)
   │                         │
   │                         ▼
   │                     all-MiniLM-L6-v2 (384-dim vectors)
   │
   └─ Property filters ──► Weaviate fetch_objects (exact match)
   │
   ▼
Formatted results to terminal
```

---

## How the Code Works

### 1. `main()` CLI

- Parses arguments (`-i`, `--host`, `--port`, `--grpc-port`, `--collection`)
- Connects to Weaviate via `connect_to_local()`
- Loads the collection and prints object count
- Routes to interactive mode or canned queries

### 2. Canned Queries (default mode)

Six pre-built queries run in sequence:

| Query | Method | Description |
|---|---|---|
| Query 1: Listable Directories | `fetch_objects` + filter | All findings with `finding_type == "directory"` |
| Query 2: Discovered Files | `fetch_objects` + filter | All findings with `finding_type == "file"` |
| Query 3: Non-200 HTTP Codes | `fetch_objects` + filter | Findings where `http_code != 200` and `http_code != 0` |
| Query 4: SQL Injection Paths | `near_text` | Semantic search for `"SQL injection database"` |
| Query 5: Admin/Config Paths | `near_text` | Semantic search for `"admin configuration setup management login"` |
| Query 6: Upload Paths | `near_text` | Semantic search for `"upload file upload image upload media"` |

### 3. `interactive_mode(collection)`

A REPL loop with prompt `dirb-query [k=5]>` supporting commands and free-text semantic search.

**Commands:**

| Command | Description |
|---|---|
| `<query>` | Semantic search via `near_text` (any free text) |
| `:k <number>` | Set number of results returned per query |
| `:dirs` | List all directories (up to 100) |
| `:files` | List all files with HTTP code and response size |
| `:host <host>` | Filter findings by host/IP |
| `:code <code>` | Filter findings by HTTP status code |
| `:count` | Show total number of findings |
| `:stats` | Summary: total, directories, files, unique hosts |
| `:help` | Show command reference |
| `:quit` / `:q` | Exit interactive mode |

**Semantic search results include:**

- URL and path
- Finding type (directory or file)
- HTTP status code and response size
- Whether the directory is listable
- Raw DIRB output line (shown when query terms match)

---

## Usage

### Run all canned queries

```bash
python query_dirb_weaviate-MiniLM-L6.py
```

### Launch interactive mode

```bash
python query_dirb_weaviate-MiniLM-L6.py -i
```

### Custom Weaviate connection

```bash
python query_dirb_weaviate-MiniLM-L6.py -i --host 10.0.0.5 --port 8080 --grpc-port 50051
```

### Custom collection name

```bash
python query_dirb_weaviate-MiniLM-L6.py -i --collection MyDirbFindings
```

---

## Example Interactive Session

```text
======================================================================
Interactive Query Mode
======================================================================
Collection: 'DirbFinding' (79 objects)

Commands:
  <query>           Semantic search for paths/directories
  :k <number>       Set number of results (default: 5)
  :dirs             List all directories
  :files            List all discovered files
  :host <host>      Filter findings by host
  :code <code>      Filter findings by HTTP status code
  :count            Show total finding count
  :stats            Show summary statistics
  :help             Show this help message
  :quit / :q        Exit interactive mode

dirb-query [k=5]> SQL injection

  Top 5 results for 'SQL injection':

  [1] http://192.168.0.252/vulnerabilities/sqli/help/
      Type: directory | HTTP 200 | Size: 0 | Listable: True
  [2] http://192.168.0.252/vulnerabilities/sqli/source/
      Type: directory | HTTP 200 | Size: 0 | Listable: True
  [3] http://192.168.0.252/vulnerabilities/sqli/
      Type: directory | HTTP 200 | Size: 0 | Listable: True
  [4] http://192.168.0.252/vulnerabilities/sqli_blind/
      Type: directory | HTTP 200 | Size: 0 | Listable: True
  [5] http://192.168.0.252/vulnerabilities/sqli_blind/help/
      Type: directory | HTTP 200 | Size: 0 | Listable: True

dirb-query [k=5]> :stats

  Total findings:  79
  Directories:     55
  Files:           24
  Unique hosts:    1
    - 192.168.0.252

dirb-query [k=5]> :code 403

  Findings with HTTP 403:

  [1] http://192.168.0.252/server-status
      Type: file | Size: 299

dirb-query [k=5]> :q
Exiting interactive mode.
```

---

## Expected Console Output (Canned Queries)

```text
======================================================================
Weaviate Query Script - DIRB Findings
======================================================================

Connecting to Weaviate at localhost:8080...
✓ Connected to Weaviate
✓ Collection 'DirbFinding' loaded (79 objects)

======================================================================
Query 1: Listable Directories
======================================================================

  Found 10 directories

  Path                                          Host
  -----------------------------------------------------------------
  /vulnerabilities/sqli/                        192.168.0.252
  /vulnerabilities/xss_r/                       192.168.0.252
  ...

======================================================================
Query demonstrations complete!
======================================================================

Tip: Run with -i or --interactive for interactive query mode
     Example: python query_dirb_weaviate.py -i
```

If Weaviate is unreachable or the collection is missing:

```text
❌ Error: Collection 'DirbFinding' does not exist.

Make sure you have:
  1. Weaviate running (docker compose up -d)
  2. Imported DIRB data with ingest_dirb_to_weaviate.py
```

---

## Companion Scripts

- **`dirb_to_weaviate-MiniLM-L6.py`** — Ingestor script that parses DIRB JSON and populates the `DirbFinding` collection.

---

## Notes

- Embedding model: `sentence-transformers/all-MiniLM-L6-v2`, served via the `t2v-transformers` Docker container.
- Vectorization and similarity search happen server-side — no local model needed.
- The `:stats` and `:dirs`/`:files` commands fetch up to 1000 objects. For very large scans, consider pagination.
- Free-text queries use Weaviate's `near_text` which converts your query into a vector and finds the closest findings by cosine similarity.
- Property filter commands (`:host`, `:code`) use exact-match filters, not semantic search.
