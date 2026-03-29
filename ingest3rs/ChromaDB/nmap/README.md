# Nmap to ChromaDB Importer

`nmap_to_chromadb-MiniLM-L6.py` imports Nmap JSON scan results into a ChromaDB collection for semantic and metadata-based querying.

## Purpose

The script transforms raw Nmap host records into:

- searchable text documents (host + service context)
- structured metadata fields (for exact filtering)

This makes it easier to run downstream search/query workflows against a normalized `nmaptest` collection.

## Requirements

- Python 3.8+
- `chromadb`
- A running ChromaDB server (default: `localhost:9000`)
- Nmap JSON input file (expected under `nmaprun.host` structure)

Install dependency:

```bash
pip install chromadb
```

Optional environment variables:

- `CHROMADB_HOST` (default: `localhost`)
- `CHROMADB_PORT` (default: `9000`)

## Architecture

`nmap_to_chromadb-MiniLM-L6.py` is organized in these layers:

1. **CLI and validation**
   - Parses input file argument
   - Verifies file existence/type
2. **JSON load/parsing**
   - Loads Nmap JSON safely with error handling
3. **Host normalization**
   - Extracts host info (IP, state, ports, OS, vendor, hostname)
4. **Document/metadata generation**
   - Builds text document per host
   - Builds flat metadata dict compatible with ChromaDB
5. **Persistence**
   - Connects to ChromaDB HTTP server
   - Gets/creates `nmaptest`
   - Adds documents, metadata, and deterministic IDs
6. **Summary output**
   - Prints import stats and an example query snippet

## Code Walkthrough

### `print_usage()`

Prints command usage and examples when no file is provided or validation fails.

### `validate_json_file(file_path)`

Checks:

- file exists
- path is a file
- warns if extension is not `.json`

### `load_json_data(file_path)`

Loads JSON and handles:

- invalid JSON
- read/runtime exceptions

### `extract_host_info(host)`

Extracts and normalizes host-level data:

- `ip_address`, optional `mac_address`, `vendor`
- `hostname`
- host `state`
- port list with service/product/version
- `open_port_count`
- optional OS detection (`os_name`, `os_accuracy`)

### `create_document_text(host_info)`

Builds a multiline, human-readable document including:

- host identity/details
- status/OS
- open services formatted like `port/protocol: service (product version)`

This text is what gets semantically searched later.

### `import_to_chromadb(data)`

Core import flow:

1. Connects with `chromadb.HttpClient(...)`
2. Gets or creates collection `nmaptest`
3. Iterates over hosts from `data['nmaprun']['host']`
4. Builds:
   - `documents` list
   - `metadatas` list
   - `ids` list (`host_<index>_<ip>`)
5. Calls `collection.add(...)`
6. Prints summary and collection count

### `main()`

Coordinates the full process:

- parse args
- validate input
- load JSON
- import to ChromaDB
- return appropriate exit code

## Usage

Run commands from the same directory as `nmap_to_chromadb-MiniLM-L6.py`.

### Basic import

```bash
python nmap_to_chromadb-MiniLM-L6.py LocalNmapTest.json
```

### Import using another file

```bash
python nmap_to_chromadb-MiniLM-L6.py nmap_scan.json
```

### Use custom ChromaDB host/port

```bash
set CHROMADB_HOST=localhost
set CHROMADB_PORT=9000
python nmap_to_chromadb-MiniLM-L6.py LocalNmapTest.json
```

## Expected Output

### Successful import (example)

```text
✓ Successfully loaded JSON from 'LocalNmapTest.json'
✓ Created new collection 'nmaptest'

📊 Processing 10 hosts...

✅ Successfully imported 10 hosts to ChromaDB collection 'nmaptest'

======================================================================
Import Summary
======================================================================
Collection: nmaptest
Total hosts: 10
Hosts up: 8
Total documents in collection: 10
======================================================================
```

### Common error output (examples)

No input file:

```text
❌ Error: No JSON file specified.
```

Missing file:

```text
❌ Error: File 'missing.json' does not exist.
```

Invalid JSON:

```text
❌ Error: Invalid JSON format in 'bad.json'
```

## Stored Data Model

Each host is stored as:

- **Document text**: host context + open-service lines
- **Metadata**:
  - `ip_address`
  - `state`
  - `open_port_count`
  - optional `hostname`, `mac_address`, `vendor`, `os_name`, `os_accuracy`

## Notes

- Collection name is hardcoded as `nmaptest`.
- Script uses HTTP ChromaDB client and a placeholder auth header token.
- Re-importing the same data without unique ID strategy changes can cause duplicate-ID conflicts if IDs collide.
