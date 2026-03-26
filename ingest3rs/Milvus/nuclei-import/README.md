# Nuclei JSON → Milvus Importer (MiniLM-L6)

This script imports preprocessed Nuclei findings into Milvus.

- Script: `nuclei_to_milvus-MiniLM-L6.py`
- Input: Nuclei JSON file (must already contain `vector` embeddings)
- Output: Inserted records in Milvus collection `nuclei_findings`

## Purpose

`nuclei_to_milvus-MiniLM-L6.py` is the ingestion step after conversion/embedding.

It:
1. Reads Nuclei JSON results.
2. Keeps only entries where `entry_type == "finding"`.
3. Connects to Milvus.
4. Creates collection + vector index if missing.
5. Inserts findings in batches with metadata fields.

Use this when embeddings are already generated (for example by your converter script using `all-MiniLM-L6-v2`).

## Requirements

### Python
- Python `3.10+` (script uses `list[dict]` typing and `from __future__ import annotations`)

### Packages
```bash
pip install pymilvus
```

### Milvus
A running Milvus instance reachable at:
- Host: `localhost`
- Port: `19530`

Example (Docker):
```bash
docker run -d --name milvus \
  -p 19530:19530 -p 9091:9091 \
  milvusdb/milvus:v2.4.0
```

## Architecture

```text
Nuclei JSON (with vectors)
          │
          ▼
 parse_nuclei_json()
 (filter finding entries)
          │
          ▼
 connect_milvus()
          │
          ▼
 create_collection()
 (schema + IVF_FLAT index)
          │
          ▼
 ingest()
 (batch insert + flush)
          │
          ▼
 Milvus collection: nuclei_findings
```

## Collection Schema

The script creates `nuclei_findings` with these fields:

| Field | Type | Notes |
|---|---|---|
| `id` | `INT64` | Primary key (`auto_id=False`) |
| `vector` | `FLOAT_VECTOR(384)` | Must match embedding size |
| `template` | `VARCHAR(256)` | Nuclei template name |
| `severity` | `VARCHAR(32)` | Severity label |
| `target` | `VARCHAR(512)` | URL/IP target |
| `protocol` | `VARCHAR(32)` | Protocol (http/tcp/etc.) |
| `extra_info` | `VARCHAR(1024)` | Optional metadata |

Index settings:
- `index_type`: `IVF_FLAT`
- `metric_type`: `COSINE`
- `params`: `{ "nlist": 128 }`

## Code Walkthrough

### `parse_nuclei_json(path)`
- Loads JSON file.
- Filters only entries with `entry_type == "finding"`.
- Returns list of findings.

### `connect_milvus()`
- Connects using `pymilvus.connections.connect()`.
- Uses constants:
  - `MILVUS_HOST = "localhost"`
  - `MILVUS_PORT = "19530"`

### `create_collection()`
- If collection already exists, reuses it.
- Otherwise:
  - Creates schema.
  - Creates vector index on `vector`.

### `ingest(json_path)`
- Parses findings.
- Exits if none found.
- Inserts data in batches (`BATCH = 100`).
- Calls `collection.flush()` after all inserts.

### `main()`
- CLI entrypoint.
- Accepts one positional argument: `json_file`.

## Usage

```bash
python nuclei_to_milvus-MiniLM-L6.py nuclei_milvus.json
```

## Example Input (minimal)

```json
[
  {
    "id": 1,
    "entry_type": "finding",
    "template": "http-missing-security-headers",
    "protocol": "http",
    "severity": "info",
    "target": "https://example.com",
    "extra_info": "x-powered-by: php",
    "text": "http-missing-security-headers info https://example.com x-powered-by: php",
    "vector": [0.0123, -0.0441, 0.0987]
  },
  {
    "id": 2,
    "entry_type": "log",
    "log_level": "info",
    "message": "Templates loaded: 9320"
  }
]
```

> The importer inserts only the first object above because only `entry_type: "finding"` is ingested.

## Expected Console Output

### First run (collection created)
```text
[+] Parsed 1 findings from nuclei_milvus.json
[+] Connecting to Milvus at localhost:19530 ...
[+] Creating collection 'nuclei_findings' ...
[+] Creating index on vector field ...
  inserted 1/1 findings

[+] Done — 1 findings stored in Milvus.
```

### Subsequent run (collection exists)
```text
[+] Parsed 1 findings from nuclei_milvus.json
[+] Connecting to Milvus at localhost:19530 ...
[+] Collection 'nuclei_findings' already exists.
  inserted 1/1 findings

[+] Done — 1 findings stored in Milvus.
```

### No findings in file
```text
No findings found in JSON.
```

## Notes

- `VECTOR_DIM` is hardcoded to `384`; your vectors must match this dimension.
- IDs are inserted from JSON (`auto_id=False`), so duplicate IDs will fail in Milvus.
- `clean_metadata()` exists in the script but is not currently used by ingestion logic.
