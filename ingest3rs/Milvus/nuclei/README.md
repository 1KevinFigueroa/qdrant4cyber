# Nuclei to Milvus Importer

`nuclei_to_milvus-MiniLM-L6.py` ingests Nuclei findings into Milvus and generates embeddings during import.

## Purpose

The script converts Nuclei JSON findings into a vector-searchable Milvus dataset by:

- filtering relevant findings (`entry_type == "finding"`)
- generating MiniLM embeddings from finding content
- creating/reusing a Milvus collection
- inserting vectors plus structured fields in batches

Target collection: `nuclei_findings`.

## Requirements

- Python 3.8+
- `pymilvus`
- `sentence-transformers`
- Running Milvus server (default: `localhost:19530`)

Install dependencies:

```bash
pip install pymilvus sentence-transformers
```

## Architecture

1. **CLI layer (`main`)**
   - parses `json_file`
2. **Parsing layer (`parse_nuclei_json`)**
   - loads JSON
   - keeps only entries where `entry_type` is `finding`
3. **Embedding layer (`build_embed_text`, `embed_findings`)**
   - builds text payload from finding fields
   - generates vectors with `all-MiniLM-L6-v2`
4. **Milvus layer (`connect_milvus`, `create_collection`)**
   - connects to Milvus
   - creates `nuclei_findings` schema/index if missing
5. **Ingest layer (`ingest`)**
   - batches inserts and flushes collection

## Code Walkthrough

### `build_embed_text(entry)`

Creates an embedding input string from finding fields, for example:

```text
template:http-missing-security-headers | severity:info | target:https://example.com | protocol:http | extra_info:x-powered-by: php
```

### `embed_findings(findings)`

- loads `SentenceTransformer("all-MiniLM-L6-v2")`
- encodes all finding texts
- returns vectors as Python lists (`list[list[float]]`)

### `parse_nuclei_json(path)`

- reads JSON array
- returns only finding entries (`entry_type == "finding"`)

### `connect_milvus()`

Connects using configured constants:

- `MILVUS_HOST = "localhost"`
- `MILVUS_PORT = "19530"`

### `create_collection()`

Creates collection `nuclei_findings` if needed with fields:

- `id` (`INT64`, primary key, `auto_id=False`)
- `vector` (`FLOAT_VECTOR`, dim `384`)
- `template` (`VARCHAR`)
- `severity` (`VARCHAR`)
- `target` (`VARCHAR`)
- `protocol` (`VARCHAR`)
- `extra_info` (`VARCHAR`)

Also creates vector index:

- `index_type`: `IVF_FLAT`
- `metric_type`: `COSINE`
- `nlist`: `128`

### `ingest(json_path)`

1. parse findings
2. generate embeddings
3. connect/create Milvus collection
4. insert in batches of 100
5. `flush()` at end

### `main()`

CLI entrypoint for one required argument: input JSON file.

## Usage

Run from the same directory as `nuclei_to_milvus-MiniLM-L6.py`.

```bash
python nuclei_to_milvus-MiniLM-L6.py nuclei-results.json
```

## Input JSON Example

```json
[
  {
    "id": 1,
    "entry_type": "finding",
    "template": "http-missing-security-headers",
    "protocol": "http",
    "severity": "info",
    "target": "https://example.com",
    "extra_info": "x-powered-by: php"
  },
  {
    "id": 2,
    "entry_type": "log",
    "message": "template loaded"
  }
]
```

Only entries with `entry_type: "finding"` are ingested.

## Expected Output

### Successful run (collection created)

```text
[+] Parsed 1 findings from nuclei-results.json
[+] Loading embedding model 'all-MiniLM-L6-v2' ...
[+] Embedding 1 findings ...
[+] Connecting to Milvus at localhost:19530 ...
[+] Creating collection 'nuclei_findings' ...
[+] Creating index on vector field ...
  inserted 1/1 findings

[+] Done — 1 findings stored in Milvus.
```

### Successful run (collection already exists)

```text
[+] Parsed 1 findings from nuclei-results.json
[+] Loading embedding model 'all-MiniLM-L6-v2' ...
[+] Embedding 1 findings ...
[+] Connecting to Milvus at localhost:19530 ...
[+] Collection 'nuclei_findings' already exists.
  inserted 1/1 findings

[+] Done — 1 findings stored in Milvus.
```

### No findings case

```text
No findings found in JSON.
```

## Notes

- The script generates vectors at ingest time; input JSON does not need a `vector` field.
- `VECTOR_DIM` is fixed to `384`, matching `all-MiniLM-L6-v2`.
- IDs are taken from input `id`; duplicates may fail because `auto_id=False`.
- `clean_metadata()` exists but is currently not used in insert flow.
