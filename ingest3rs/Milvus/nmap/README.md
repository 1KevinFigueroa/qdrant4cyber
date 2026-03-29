# Nmap to Milvus Importer

`import_nmap_to_milvus-MiniLM-L6.py` ingests Nmap JSON scan data into Milvus using MiniLM embeddings.

## Purpose

The script converts scan results into:

- semantic vectors for similarity search
- structured fields for host context (`ip`, `hostname`, `os`)
- a reusable Milvus collection (`nmap_test`)

This enables downstream natural-language and hybrid search workflows over Nmap data.

## Requirements

- Python 3.8+
- `pymilvus`
- `sentence-transformers`
- Running Milvus instance on `localhost:19530`

Install dependencies:

```bash
pip install pymilvus sentence-transformers
```

## Architecture

1. **CLI layer (`main`)**
   - parses `json_file` and optional `--reset`
2. **Connection layer (`connect`)**
   - opens Milvus connection
3. **Collection layer (`create_collection`)**
   - creates schema/index or reuses existing collection
4. **Parsing layer (`parse_nmap_json`)**
   - extracts up hosts, IPv4, and open ports from Nmap JSON
5. **Text transformation (`host_to_text`)**
   - builds semantic text per host
6. **Embedding + ingest layer (`ingest`)**
   - encodes text with `all-MiniLM-L6-v2`
   - batch inserts vectors and metadata
7. **Finalize**
   - flushes and loads collection

## Code Walkthrough

### `connect()`

Connects to Milvus using configured host/port constants.

### `create_collection(reset=False)`

- If collection exists:
  - drops it when `reset=True`
  - otherwise returns existing collection
- If absent, creates schema with fields:
  - `id` (auto primary key)
  - `embedding` (`FLOAT_VECTOR`, dim `384`)
  - `text`
  - `ip`
  - `hostname`
  - `os`
- Creates IVF_FLAT index on `embedding` with COSINE metric

### `parse_nmap_json(path)`

Reads Nmap JSON and keeps only valid, up hosts with IPv4 addresses. Extracts open ports/services and returns normalized host objects.

### `host_to_text(h)`

Builds semantic text such as:

```text
Host 192.168.1.10
Open ports:
22 - ssh
80 - http
```

### `ingest(json_path, reset=False)`

Core pipeline:

1. connect to Milvus
2. create/reuse collection
3. parse hosts
4. generate text list
5. encode embeddings with `SentenceTransformer`
6. insert in batches (`BATCH_SIZE = 64`)
7. `flush()` and `load()` collection

### `main()`

Parses CLI args and calls `ingest(...)`.

## Usage

Run commands from the same directory as `import_nmap_to_milvus-MiniLM-L6.py`.

### Standard import

```bash
python import_nmap_to_milvus-MiniLM-L6.py scan.json
```

### Reset and re-create collection before import

```bash
python import_nmap_to_milvus-MiniLM-L6.py scan.json --reset
```

## Expected Output

### Successful run (example)

```text
[INFO] Creating collection: nmap_test
[INFO] Parsed 5 hosts
[INFO] Generating embeddings...
[INFO] Inserting into Milvus...
  inserted 5/5

✅ Done: 5 records inserted into 'nmap_test'
```

### When no valid hosts are found

```text
No valid hosts found.
```

## Example Input Shape

```json
{
  "nmaprun": {
    "host": {
      "status": {"@state": "up"},
      "address": {"@addr": "192.168.1.10", "@addrtype": "ipv4"},
      "ports": {
        "port": {
          "@portid": "22",
          "state": {"@state": "open"},
          "service": {"@name": "ssh"}
        }
      }
    }
  }
}
```

## Notes

- Collection name is fixed to `nmap_test` in this script.
- Embedding dimension is fixed to `384`; schema and model must stay aligned.
- Use `--reset` when schema/index settings change.

