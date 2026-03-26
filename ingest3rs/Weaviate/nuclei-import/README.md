# Nuclei JSON → Weaviate Importer (`MiniLM-L6`)

Script: `nuclei_to_weaviate-MiniLM-L6.py`

## Purpose

This script ingests Nuclei findings (JSON format) into Weaviate for semantic search.

It:
- loads Nuclei finding objects,
- builds semantic text per finding,
- generates embeddings with `all-MiniLM-L6-v2`,
- stores both properties and vectors in a Weaviate collection.

Target collection/class: `NucleiFinding`.

---

## Requirements

### Python
- Python `3.10+`

### Packages
```bash
pip install weaviate-client sentence-transformers
```

### Weaviate
- Local Weaviate instance running (default expected by the script).
- Script connects via `weaviate.connect_to_local()`.

Example Docker run:
```bash
docker run -d --name weaviate \
  -p 8080:8080 -p 50051:50051 \
  semitechnologies/weaviate:latest
```

---

## Architecture

```text
Nuclei JSON file
      │
      ▼
parse_nuclei_json()
      │
      ▼
_finding_to_text() + _finding_to_metadata()
      │
      ▼
SentenceTransformer(all-MiniLM-L6-v2)
      │ (384-d embeddings)
      ▼
ensure_collection()
(create NucleiFinding schema if missing)
      │
      ▼
batch add_object(properties + vector)
      │
      ▼
Weaviate collection: NucleiFinding
```

---

## Code Walkthrough

### Configuration constants
- `WEAVIATE_URL = "http://localhost:8080"` (status text only)
- `EMBEDDING_MODEL = "all-MiniLM-L6-v2"`
- `EMBEDDING_DIM = 384`
- `CLASS_NAME = "NucleiFinding"`

### `embed_texts(texts, model)`
Encodes a list of strings into vectors using SentenceTransformers.

### `clean_metadata(d)`
Normalizes metadata values:
- removes `None`,
- keeps primitives,
- converts list items to strings,
- stringifies unsupported types.

### `_finding_to_text(f)`
Builds semantic text from `properties` fields (severity/template/target/protocol + metadata summary).
This text is what gets embedded.

### `_finding_to_metadata(f)`
Extracts core metadata fields (`template`, `severity`, `target`, `protocol`) and cleans them.

### `parse_nuclei_json(path)`
Loads the input JSON list from disk.

### `get_client()`
Creates a local Weaviate client via `weaviate.connect_to_local()`.

### `ensure_collection(client)`
Checks whether `NucleiFinding` exists. If not, creates it with properties:
- `template`
- `protocol`
- `severity`
- `target`
- `description`
- `raw`
- `timestamp`
- `metadata` (stored as JSON string)

### `ingest(json_path)`
Main workflow:
1. Load findings.
2. Exit if empty.
3. Load embedding model.
4. Connect to Weaviate.
5. Ensure collection exists.
6. Build semantic texts + metadata.
7. Process batches (`BATCH=100`):
   - generate embeddings,
   - insert objects with vectors.
8. Close client and print summary.

### `main()`
CLI entrypoint with one positional argument: `json_file`.

---

## Input Format Example

The script expects objects like:

```json
[
  {
    "class": "NucleiFinding",
    "properties": {
      "template": "phpinfo-files",
      "protocol": "http",
      "severity": "low",
      "target": "http://dvwa/phpinfo.php",
      "metadata": {"paths": "/phpinfo.php"},
      "raw": "[phpinfo-files] [http] [low] http://dvwa/phpinfo.php",
      "timestamp": "2026-03-26T05:16:43.045942"
    }
  }
]
```

---

## Usage

```bash
python nuclei_to_weaviate-MiniLM-L6.py fake-nuclei-results-weaviate.json
```

---

## Expected Console Output

### First run (collection created)
```text
Parsed 24 findings from fake-nuclei-results-weaviate.json
Loading embedding model 'all-MiniLM-L6-v2' …
Connecting to Weaviate at http://localhost:8080 …
[+] Creating collection 'NucleiFinding'...
  upserted 24/24 findings

Done — 24 findings stored in Weaviate.
```

### Later runs (collection already exists)
```text
Parsed 24 findings from fake-nuclei-results-weaviate.json
Loading embedding model 'all-MiniLM-L6-v2' …
Connecting to Weaviate at http://localhost:8080 …
[+] Collection 'NucleiFinding' already exists
  upserted 24/24 findings

Done — 24 findings stored in Weaviate.
```

### Empty file case
```text
No findings found in JSON.
```

---

## Notes

- Keep ingestion and query model consistent (`all-MiniLM-L6-v2`).
- First model load may download files and take longer.
- `metadata` is stored as a JSON string in Weaviate (`json.dumps(meta)`).
- `WEAVIATE_URL` is printed for user clarity, but connection is currently done through local client settings (`connect_to_local`).
