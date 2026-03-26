# Nuclei JSON → Pinecone Ingest (`MiniLM-L6`)

Script: `nuclei_to_pinecone-MiniLM-L6.py`

## Purpose

This script reads parsed Nuclei findings from a JSON file, generates vector embeddings with `all-MiniLM-L6-v2`, and upserts those vectors into a local Pinecone index.

It is intended to run after the Nuclei conversion step (for example, `ingest3rs/Pinecone/nuclei-convert/convert_nuclei_json-pinecone.py`).

---

## Requirements

- Python 3.10+
- Python packages:
  - `sentence-transformers`
  - `pinecone`
- A running local Pinecone index (for example via Docker) with:
  - `DIMENSION=384`
  - `METRIC=cosine` (recommended)

Install dependencies:

```bash
pip install sentence-transformers pinecone
```

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `PINECONE_HOST` | `http://localhost:5081` | Host URL for local Pinecone index |

---

## Architecture

The script follows a simple ingestion pipeline:

1. **Load input JSON**
   - `parse_nuclei_json(path)` loads JSON and keeps only records where `entry_type == "finding"`.

2. **Transform findings**
   - `_finding_to_text(f)` builds a semantic sentence for embedding.
   - `_finding_to_metadata(f)` maps fields into Pinecone metadata.
   - `clean_metadata(d)` removes `None` values and enforces Pinecone-safe metadata types.

3. **Embed text**
   - `embed_texts(texts, model)` runs `SentenceTransformer` (`all-MiniLM-L6-v2`) and returns 384-d vectors.

4. **Upsert into Pinecone**
   - `get_index()` creates a Pinecone client and gets the index via host.
   - `ingest(json_path)` batches vectors (`BATCH=100`) and calls `index.upsert(vectors=...)`.

---

## Code Walkthrough

### Configuration

- `PINECONE_HOST`: defaults to `http://localhost:5081`
- `EMBEDDING_MODEL`: `all-MiniLM-L6-v2`
- `EMBEDDING_DIM`: `384`

### `clean_metadata(d: dict) -> dict`

Ensures metadata complies with Pinecone constraints:

- Drops keys with `None` values
- Keeps primitive types (`str`, `int`, `float`, `bool`)
- Converts list values to `list[str]`
- Converts other objects to `str`

### `_finding_to_text(f: dict) -> str`

Builds semantic text used for embedding, combining:

- severity
- template
- target
- protocol
- extra info

### `_finding_to_metadata(f: dict) -> dict`

Creates metadata payload with fields:

- `id`
- `entry_type`
- `template`
- `severity`
- `target`
- `protocol`
- `extra_info`

Then sanitizes via `clean_metadata`.

### `parse_nuclei_json(path: str) -> list[dict]`

Loads input JSON and returns only findings (`entry_type == "finding"`).

### `ingest(json_path: str)`

Main workflow:

1. Parse findings
2. Exit if none found
3. Load embedding model
4. Connect to Pinecone
5. Build `texts`, `metas`, and IDs (`finding-<id>`)
6. Process in batches of 100:
   - embed batch texts
   - build vector dicts (`id`, `values`, `metadata`)
   - upsert
7. Print final summary

### CLI

`main()` accepts one positional argument:

```bash
python nuclei_to_pinecone-MiniLM-L6.py <json_file>
```

---

## Usage

```bash
python nuclei_to_pinecone-MiniLM-L6.py nuclei-results.json
```

Windows PowerShell with custom host:

```powershell
$env:PINECONE_HOST = "http://localhost:5090"
python nuclei_to_pinecone-MiniLM-L6.py nuclei-results.json
```

---

## Input Example

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
    "entry_type": "finding",
    "template": "ssh-auth-methods",
    "protocol": "tcp",
    "severity": "medium",
    "target": "10.10.10.20:22",
    "extra_info": "password auth enabled"
  }
]
```

---

## Expected Output

### Successful run (example)

```text
Parsed 2 findings from nuclei-results.json
Loading embedding model 'all-MiniLM-L6-v2' …
Connecting to Pinecone at http://localhost:5081 …
  upserted 2/2 findings

Done — 2 findings stored in Pinecone.
```

### No findings in file

```text
No findings found in JSON.
```

---

## Notes

- Metadata null values are removed before upsert (required by Pinecone).
- Re-running the script with the same finding IDs will overwrite existing vectors (`finding-<id>`).
- The first run may take longer due to model download and cache initialization.
