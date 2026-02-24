# Nmap ChromaDB Query Tool

A command-line tool for querying Nmap scan data stored in a [ChromaDB](https://www.trychroma.com/) vector database. It provides both a set of pre-built demo queries and a fully interactive REPL for exploring hosts, ports, and services using semantic search.

## Overview

After importing Nmap XML scan results into ChromaDB (via a companion `nmap_to_chromadb-MiniLM-L6.py` script), this tool lets you search that data using natural language. ChromaDB's vector embeddings mean you don't need exact keyword matches — a query like `"web server"` will surface results containing `http`, `nginx`, `apache`, and similar terms.

The tool operates in two modes:

- **Demo mode** (default) — runs seven pre-built queries that showcase different query techniques.
- **Interactive mode** (`-i`) — drops you into a live prompt where you can run free-form searches and control result count on the fly.

## Prerequisites

- **Python 3.8+**
- **ChromaDB** — `pip install chromadb`
- **A running ChromaDB server** — the script connects to `localhost:8000` by default (e.g. via Docker).
- **Imported Nmap data** — run `nmap_to_chromadb-MiniLM-L6` first to populate the `nmaptest` collection.

## Quick Start

```bash
# Install dependencies
pip install chromadb

# Run the pre-built demo queries
python query-nmap-chromadb-MiniLM-L6.py

# Or launch interactive mode
python query-nmap-chromadb-MiniLM-L6.py -i
```

## Usage

```
usage: query-nmap-chromadb-MiniLM-L6.py [-h] [-i]

ChromaDB Query Examples for Nmap Data

options:
  -h, --help         show this help message and exit
  -i, --interactive  Launch interactive query mode
```

### Demo Mode (default)

Running the script with no flags executes seven built-in queries that demonstrate different ways to search the collection:

```bash
python query-nmap-chromadb-MiniLM-L6.py
```

| Query | Description | Technique |
|-------|-------------|-----------|
| 1 — HTTP Services | Finds web servers | Semantic search (`query_texts`) |
| 2 — SSH Services | Finds SSH endpoints | Semantic search |
| 3 — High Port Count | Hosts with > 3 open ports | Metadata filter (`where` clause) |
| 4 — SMB Services | Finds SMB/CIFS on port 445 | Semantic search |
| 5 — Active Hosts | Summary table of all live hosts | Metadata filter (`state = "up"`) |
| 6 — Database Services | MySQL, PostgreSQL, MongoDB, Redis | Semantic search |
| 7 — SMTP Services | Simple single-keyword search | Semantic search |

### Interactive Mode

```bash
python query-nmap-chromadb-MiniLM-L6.py -i
```

This launches a REPL with a prompt that shows the current result limit:

```
nmap-query [k=5]>
```

#### Interactive Commands

| Command | Description | Example |
|---------|-------------|---------|
| `<any text>` | Semantic search for services/hosts | `http`, `ssh`, `database`, `windows rdp` |
| `:k <number>` | Set how many results to return | `:k 10` |
| `:all` | List all active (state=up) hosts | `:all` |
| `:ports <n>` | Show hosts with more than `n` open ports | `:ports 5` |
| `:count` | Display total documents in the collection | `:count` |
| `:help` | Print the command reference | `:help` |
| `:quit` / `:q` | Exit interactive mode | `:q` |

#### Interactive Session Example

```
nmap-query [k=5]> ssh
  Top 5 results for 'ssh':

  [1] 192.168.1.10 (fileserver.local) - 8 open ports  [score: 0.4312]
      22/tcp open ssh: OpenSSH 8.9p1
  [2] 10.0.0.5 (gateway.local) - 4 open ports  [score: 0.5107]
      22/tcp open ssh: OpenSSH 7.6p1
  ...

nmap-query [k=5]> :k 20
  ✓ Results per query set to 20

nmap-query [k=20]> mysql
  Top 3 results for 'mysql':

  [1] 192.168.1.50 (db-primary.local) - 5 open ports  [score: 0.3201]
      3306/tcp open mysql: MySQL 8.0.32
  ...

nmap-query [k=20]> :ports 10
  Hosts with more than 10 open ports:

  [1] 192.168.1.1 (router.local) - 14 open ports
      22/tcp open ssh: OpenSSH 8.2
      80/tcp open http: nginx 1.18
      443/tcp open https: nginx 1.18
      ...

nmap-query [k=20]> :all
  Found 42 active hosts

  IP Address         Hostname                  Ports
  -------------------------------------------------------
  192.168.1.1        router.local              14
  192.168.1.10       fileserver.local           8
  ...

nmap-query [k=20]> :q
Exiting interactive mode.
```

## How It Works

### Data Model

Each document in the `nmaptest` ChromaDB collection represents a single host from an Nmap scan. The document text contains the raw port/service information, while structured fields are stored as metadata:

| Metadata Field | Type | Description |
|----------------|------|-------------|
| `ip_address` | string | Host IP address |
| `hostname` | string | Resolved hostname |
| `state` | string | Host state (`up` / `down`) |
| `open_port_count` | int | Number of open ports detected |
| `vendor` | string | OS or hardware vendor (when detected) |

### Query Techniques

The script demonstrates two core ChromaDB query patterns:

**Semantic search** via `collection.query(query_texts=["..."])` — ChromaDB converts the query into a vector embedding and finds the most similar documents. This is why `"HTTP web server"` can match documents containing `nginx` or `apache` even without those exact words in the query.

**Metadata filtering** via `collection.get(where={...})` — retrieves documents based on exact metadata conditions (e.g., `state == "up"` or `open_port_count > 3`). This is useful for structured filtering that doesn't depend on text similarity.

### ChromaDB Connection

The script connects to a ChromaDB HTTP server by default:

```python
client = chromadb.HttpClient(
    host="localhost",
    port=8000,
    headers={"Authorization": "Bearer my-secret-token"}
)
```

To use an in-memory or persistent local client instead, uncomment the alternative `chromadb.Client(...)` block in the source and comment out the `HttpClient` section.

## Customization

- **Change the collection name** — replace `"nmaptest"` in the `client.get_collection()` call.
- **Adjust the ChromaDB host/port** — modify the `HttpClient` parameters.
- **Change the auth token** — update the `Authorization` header value.
- **Add your own demo queries** — define a new function following the pattern of the existing ones and call it from `main()`.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `Connection refused` on port 8000 | Make sure the ChromaDB Docker container is running |
| `Collection 'nmaptest' not found` | Run `nmap_to_chromadb-MiniLM-L6` first to import data |
| `ModuleNotFoundError: chromadb` | Install with `pip install chromadb` |
| No results returned | Verify data was imported — run `:count` in interactive mode |

