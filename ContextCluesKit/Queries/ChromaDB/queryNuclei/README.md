# Nuclei ChromaDB Query Tool

Script: `query-nuclei-chromadb-MiniLM-L6.py`

## Purpose

`query-nuclei-chromadb-MiniLM-L6.py` queries Nuclei findings stored in a ChromaDB collection named `nuclei-import`.

It supports:
- **Demo mode** (default): runs a set of built-in query examples.
- **Interactive mode** (`-i`): provides a REPL for ad-hoc semantic and metadata queries.

## Requirements

- Python 3.8+
- `chromadb` package
  - Install: `pip install chromadb`
- Running ChromaDB server reachable from this script
- Existing collection: `nuclei-import`
  - Populate it first with `nuclei_to_chromadb-MiniLM-L6.py`

### Environment Variables

Connection settings are read from:

- `CHROMADB_HOST` (default: `localhost`)
- `CHROMADB_PORT` (default: `9000`)

Auth header used:

- `Authorization: Bearer my-secret-token`

## Architecture

The script is organized into four logical layers:

1. **Presentation helpers**
   - `print_section()` for consistent console formatting.

2. **Pre-built query functions**
   - `query_high_severity()`
   - `query_web_vulns()`
   - `query_specific_template()`
   - `query_targets()`
   - `query_by_severity()`
   - `custom_query()`

3. **Interactive query loop**
   - `interactive_mode()` supports command-driven filtering and semantic search.

4. **Bootstrap / wiring**
   - `main()` parses CLI args, connects to ChromaDB, loads collection, and runs chosen mode.

## Code Walkthrough

### `print_section(title)`
Prints a header block for readable terminal output.

### Query functions

#### `query_high_severity(collection)`
Uses metadata filter:
- `collection.get(where={"severity": "high"}, limit=5)`

#### `query_web_vulns(collection)`
Uses semantic search:
- Query text: `"web vulnerability http misconfiguration"`

#### `query_specific_template(collection)`
Semantic query aimed at template-like terms:
- Query text: `"phpinfo exposed"`

#### `query_targets(collection)`
Lists a summary table of targets/severity/template using:
- `collection.get(limit=20)`

#### `query_by_severity(collection)`
Metadata filter for medium severity findings:
- `where={"severity": "medium"}`

#### `custom_query(collection)`
Semantic example for missing security headers:
- Query text: `"missing security headers"`

### `interactive_mode(collection)`
Starts a prompt:

`nuclei-query [k=5]>`

Supported commands:
- `:q` / `:quit` — exit
- `:k <number>` — set result count
- `:count` — show collection count
- `:severity <low|medium|high|info>` — metadata filter by severity
- any other text — semantic search query

### `main()`
- Parses `-i/--interactive`
- Connects via `chromadb.HttpClient(...)`
- Loads `nuclei-import`
- Runs interactive mode or demo query sequence

## Usage

Run these commands from the same directory as `query-nuclei-chromadb-MiniLM-L6.py`.

### Demo mode

```bash
python query-nuclei-chromadb-MiniLM-L6.py
```

### Interactive mode

```bash
python query-nuclei-chromadb-MiniLM-L6.py -i
```

## Example Output (Demo Mode)

```text
Connecting to ChromaDB...
✓ Loaded collection 'nuclei-import'
✓ Documents: 42

======================================================================
Query 1: High Severity Findings
======================================================================

[1] https://example.com
  Severity: high
  Template: cve-2023-xxxx

======================================================================
Query 2: Web Vulnerabilities
======================================================================

[1] https://app.example.com
  Severity: medium
  Template: http-missing-security-headers

Done. Use -i for interactive mode.
```

## Example Output (Interactive Mode)

```text
Connecting to ChromaDB...
✓ Loaded collection 'nuclei-import'
✓ Documents: 42

======================================================================
Interactive Query Mode
======================================================================
Collection: nuclei-import (42 docs)

nuclei-query [k=5]> :count
Total: 42

nuclei-query [k=5]> :severity high
https://example.com [high]
https://admin.example.com [high]

nuclei-query [k=5]> missing security headers

[1] https://app.example.com (medium) [score=0.3821]
  Template: http-missing-security-headers

nuclei-query [k=5]> :k 10
✓ Results set to 10

nuclei-query [k=10]> :q
```

## Expected Failure Output

If the collection does not exist:

```text
Connecting to ChromaDB...
Traceback (most recent call last):
...
```

If ChromaDB is unreachable (wrong host/port):

```text
Connecting to ChromaDB...
Traceback (most recent call last):
...
```

## Notes

- Metadata queries (`get`) are exact-match filters.
- Semantic queries (`query`) use vector similarity and may return conceptually related matches.
- Distances shown as `score` are returned by ChromaDB and are useful for ranking relative relevance.
