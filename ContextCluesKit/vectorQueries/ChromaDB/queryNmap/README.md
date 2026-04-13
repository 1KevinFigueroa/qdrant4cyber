# Nmap ChromaDB Query Tool

`query-nmap-chromadb-MiniLM-L6.py` is a command-line query utility for exploring Nmap scan data that has already been indexed in a ChromaDB collection.

It supports:

- demo mode (7 built-in query examples)
- interactive mode (REPL-style semantic and metadata queries)

---

## Purpose

The script helps you quickly answer questions like:

- Which hosts are running HTTP/SSH/SMB?
- Which hosts expose many open ports?
- Which active hosts are currently in the dataset?
- Which systems look like database servers?

Because it uses ChromaDB semantic search, you can query in natural language (for example, `web server`) and still match related services (`http`, `nginx`, `apache`, etc.).

---

## Location and File Names

This README describes:

- `query-nmap-chromadb-MiniLM-L6.py`

Run commands from the same directory as the script.

---

## Requirements

- Python 3.8+
- `chromadb` Python package
- A running ChromaDB server (default host/port: `localhost:9000`)
- A populated ChromaDB collection named `nmaptest` with host documents and metadata

Install dependency:

```bash
pip install chromadb
```

---

## Quick Start

From the script directory:

```bash
# Demo mode
python query-nmap-chromadb-MiniLM-L6.py

# Interactive mode
python query-nmap-chromadb-MiniLM-L6.py -i
```

Optional environment variables:

```bash
set CHROMADB_HOST=localhost
set CHROMADB_PORT=9000
```

---

## Script Architecture

The script is organized into five parts:

1. **CLI entrypoint (`main`)**
   - parses `-i/--interactive`
   - initializes ChromaDB HTTP client
   - loads `nmaptest` collection
   - routes to demo or interactive mode

2. **Display helper**
   - `print_section(title)` for consistent console section formatting

3. **Demo query functions**
   - `query_http_services`
   - `query_ssh_services`
   - `query_by_port_count`
   - `query_smb_services`
   - `get_all_active_hosts`
   - `custom_query_example`
   - `simple_query_example`

4. **Interactive REPL (`interactive_mode`)**
   - semantic free-text search
   - command handlers (`:k`, `:all`, `:ports`, `:count`, `:help`, `:q`)

5. **Error handling**
   - catches connection/runtime errors
   - prints troubleshooting guidance

---

## How the Code Works

### 1) Connection and collection load

`main()` builds a `chromadb.HttpClient` and connects to:

- host from `CHROMADB_HOST` (default `localhost`)
- port from `CHROMADB_PORT` (default `9000`)
- auth header `Authorization: Bearer my-secret-token`

It then loads `client.get_collection("nmaptest")`.

### 2) Two query strategies

- **Semantic search** (`collection.query`) for fuzzy intent-based matching
- **Metadata filtering** (`collection.get(where=...)`) for exact filters like:
  - `state == "up"`
  - `open_port_count > N`

### 3) Result rendering

Each result prints key metadata (IP, hostname, port count), then extracts service lines from the document body to keep output readable.

### 4) Interactive behavior

In interactive mode, user input is either:

- a control command (starts with `:`), or
- treated as semantic query text

The result count is adjustable live via `:k <number>`.

---

## Usage

```text
usage: query-nmap-chromadb-MiniLM-L6.py [-h] [-i]

ChromaDB Query Examples for Nmap Data

options:
  -h, --help         show this help message and exit
  -i, --interactive  Launch interactive query mode
```

---

## Interactive Commands

| Command | Description |
|---|---|
| `<text>` | Semantic search across host/service documents |
| `:k <number>` | Set max results for semantic and `:ports` queries |
| `:all` | List hosts where `state = up` |
| `:ports <n>` | Hosts where `open_port_count > n` |
| `:count` | Print collection document count |
| `:help` | Show command help |
| `:quit` / `:q` | Exit interactive mode |

---

## Expected Output Examples

### Demo mode (abridged)

```text
======================================================================
ChromaDB Query Examples - Nmap Data
======================================================================

Connecting to ChromaDB and loading 'nmaptest' collection...
✓ Successfully loaded collection 'nmaptest'
✓ Total documents in collection: 42

======================================================================
Query 1: Search for HTTP Services
======================================================================

Result 1:
  IP Address: 192.168.1.10
  80/tcp open http: nginx 1.24.0
```

### Interactive mode sample

```text
nmap-query [k=5]> ssh
  Top 5 results for 'ssh':

  [1] 192.168.1.10 (fileserver.local) - 8 open ports  [score: 0.4312]
      22/tcp open ssh: OpenSSH 8.9p1

nmap-query [k=5]> :k 10
  ✓ Results per query set to 10

nmap-query [k=10]> :count
  Total documents: 42

nmap-query [k=10]> :q
Exiting interactive mode.
```

---

## Metadata Model Assumed by the Script

Each host document is expected to include metadata like:

- `ip_address` (string)
- `hostname` (string)
- `state` (string, typically `up`/`down`)
- `open_port_count` (integer)
- `vendor` (string, optional)

---

## Troubleshooting

| Problem | Likely Cause | Fix |
|---|---|---|
| Connection refused | ChromaDB server not running | Start server/container on configured host/port |
| Collection not found | `nmaptest` missing | Import Nmap data into that collection |
| `ModuleNotFoundError: chromadb` | Dependency missing | `pip install chromadb` |
| No semantic matches | Empty or low-quality indexed data | Verify ingest process and use `:count` |

---

## Notes

- Default collection name is hardcoded as `nmaptest`.
- Default auth header uses a placeholder token (`my-secret-token`); update if your server enforces different auth.
- The script includes a commented local `chromadb.Client(Settings(...))` example if you want non-HTTP client usage.

