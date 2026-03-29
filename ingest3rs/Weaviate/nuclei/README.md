# Nuclei to Weaviate Importer

`nuclei_to_weaviate-MiniLM-L6.py` imports Nuclei findings from JSON into Weaviate and generates embeddings with MiniLM during ingestion.

## Purpose

The script turns flat Nuclei finding records into a vector-searchable Weaviate dataset by:

- reading finding entries from JSON
- generating semantic text per finding
- encoding that text with `all-MiniLM-L6-v2`
- storing both properties and vectors in `NucleiFinding`

## Requirements

- Python 3.8+
- `weaviate-client`
- `sentence-transformers`
- Local Weaviate instance reachable on port `8082`

Install dependencies:

```bash
pip install weaviate-client sentence-transformers
```

Example Docker run (host 8082 mapped to container 8080):

```bash
docker run -d --name weaviate \
  -p 8082:8080 -p 50051:50051 \
  semitechnologies/weaviate:latest
```

## Architecture

1. **CLI layer (`main`)**
   - parses one required argument: `json_file`
2. **Parsing layer (`parse_nuclei_json`)**
   - loads JSON list of findings
3. **Transformation layer**
   - `_finding_to_text`: semantic text used for embeddings
   - `_finding_to_metadata`: compact metadata payload
   - `clean_metadata`: removes nulls and normalizes types
4. **Embedding layer (`embed_texts`)**
   - generates vectors with `all-MiniLM-L6-v2`
5. **Weaviate layer**
   - `get_client`: connect via `weaviate.connect_to_local(port=8082)`
   - `ensure_collection`: create `NucleiFinding` schema if missing
6. **Ingest layer (`ingest`)**
   - batch insert objects + vectors into Weaviate

## Code Walkthrough

### `embed_texts(texts, model)`

Encodes a list of strings and returns vectors as `list[list[float]]`.

### `clean_metadata(d)`

Makes metadata safe and consistent:

- drops `None` values
- keeps primitives (`str`, `int`, `float`, `bool`)
- converts lists to `list[str]`
- stringifies other objects

### `_finding_to_text(f)`

Builds embedding text from fields:

- severity
- template
- target
- protocol
- extra_info

### `_finding_to_metadata(f)`

Builds metadata from finding fields and sanitizes with `clean_metadata`.

### `parse_nuclei_json(path)`

Loads and returns JSON data from file.

### `get_client()`

Creates a local Weaviate client using port `8082`.

### `ensure_collection(client)`

Creates collection `NucleiFinding` if it does not exist, with properties:

- `finding_id` (INT)
- `entry_type` (TEXT)
- `template` (TEXT)
- `protocol` (TEXT)
- `severity` (TEXT)
- `target` (TEXT)
- `extra_info` (TEXT)
- `description` (TEXT)
- `metadata` (TEXT, JSON string)

### `ingest(json_path)`

Main flow:

1. load findings
2. fail if empty
3. load embedding model
4. connect to Weaviate
5. ensure collection exists
6. batch process (`BATCH = 100`):
   - embed texts
   - add objects with vectors via dynamic batch
7. close client and print summary

## Usage

Run from the same directory as `nuclei_to_weaviate-MiniLM-L6.py`.

```bash
python nuclei_to_weaviate-MiniLM-L6.py nuclei-results.json
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
  }
]
```

## Expected Output

### First run (collection created)

```text
Parsed 1 findings from nuclei-results.json
Loading embedding model 'all-MiniLM-L6-v2' …
Connecting to Weaviate at http://localhost:8082 …
[+] Creating collection 'NucleiFinding'...
  upserted 1/1 findings

Done — 1 findings stored in Weaviate.
```

### Later run (collection exists)

```text
Parsed 1 findings from nuclei-results.json
Loading embedding model 'all-MiniLM-L6-v2' …
Connecting to Weaviate at http://localhost:8082 …
[+] Collection 'NucleiFinding' already exists
  upserted 1/1 findings

Done — 1 findings stored in Weaviate.
```

### Empty input case

```text
No findings found in JSON.
```

## Notes

- Embedding dimension is `384`, matching `all-MiniLM-L6-v2`.
- `metadata` is stored as JSON text (`json.dumps(meta)`), not as nested object.
- Input is expected to be a flat findings array; script does not filter by `entry_type` before ingest.
