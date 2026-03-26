# Nuclei JSON to ChromaDB Importer

Script: `nuclei_to_chromadb-MiniLM-L6.py`

## Purpose

This script imports parsed Nuclei findings from a JSON file into a ChromaDB collection (`nuclei-import`).

It is designed to be used after converting raw Nuclei CLI output into structured JSON (for example, with the converter in `ingest3rs/ChromaDB/nuclei-convert/`).

## Requirements

- Python 3.8+
- `chromadb` Python package
  - Install: `pip install chromadb`
- Running ChromaDB server (Docker or remote)
- Input JSON must be an array of finding objects

### Environment Variables

The script reads connection settings from environment variables:

- `CHROMADB_HOST` (default: `localhost`)
- `CHROMADB_PORT` (default: `9000`)

Authentication header used by script:

- `Authorization: Bearer my-secret-token`

## Architecture

The script has four layers:

1. **Input validation layer**
   - `validate_json_file()` checks existence and file type.
2. **Data loading layer**
   - `load_json_data()` parses JSON into Python objects.
3. **Transformation layer**
   - `extract_finding_info()` normalizes fields.
   - `create_document_text()` builds semantic text for embedding/search.
4. **Persistence layer**
   - `import_to_chromadb()` connects to ChromaDB, creates/loads collection, and inserts documents + metadata + IDs.

## Code Walkthrough

### `print_usage()`
Prints manual usage instructions when no input file argument is provided.

### `validate_json_file(file_path)`
Verifies:
- path exists
- path is a file

Returns `True` or `False`.

### `load_json_data(file_path)`
Loads JSON and prints success/failure.

Returns parsed data or `None` on error.

### `extract_finding_info(entry)`
Maps expected fields from each input item:

- `id`
- `template`
- `severity`
- `protocol`
- `target`
- `extra_info`
- `entry_type`

### `create_document_text(finding)`
Builds a multi-line text document used by ChromaDB semantic search, for example:

- `Target: ...`
- `Template: ...`
- `Severity: ...`
- `Protocol: ...`
- optional `Type: ...`
- optional `Extra Info: ...`

### `import_to_chromadb(data)`
Main import workflow:

1. Build HTTP client using env vars.
2. Get or create collection `nuclei-import`.
3. Validate that JSON root is a list.
4. For each finding:
   - build document text
   - create flat metadata
   - generate unique ID (`finding_<idx>_<safe_target>`)
5. Call `collection.add(...)` to store all records.
6. Print import summary and severity counts.

Returns `True` on success, `False` on failure.

### `main()`
- Parses positional argument `json_file`
- Validates input
- Loads data
- Calls import function
- Exits with process code:
  - `0` success
  - `1` failure

## Usage

```bash
python nuclei_to_chromadb-MiniLM-L6.py nuclei-results.json
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
    "entry_type": "finding",
    "template": "ssh-auth-methods",
    "protocol": "tcp",
    "severity": "medium",
    "target": "10.10.10.20:22",
    "extra_info": "password auth enabled"
  }
]
```

## Expected Console Output (Success)

```text
✓ Loaded JSON file: nuclei-results.json
✓ Created collection 'nuclei-import'

📊 Processing 2 findings...

✅ Imported 2 findings into 'nuclei-import'

======================================================================
Import Summary
======================================================================
Collection: nuclei-import
Total findings: 2

Severity Breakdown:
  info: 1
  medium: 1

Total documents in DB: 2
======================================================================

💡 Example query:
results = collection.query(query_texts=['missing security headers'], n_results=5)
```

## Expected Console Output (Failure Cases)

### Missing file

```text
❌ File does not exist: nuclei-results.json
```

### Invalid JSON

```text
❌ Failed to load JSON: Expecting value: line 1 column 1 (char 0)
```

### Wrong JSON structure

```text
❌ Expected JSON array of findings
```

## Notes

- ChromaDB metadata is intentionally flat (`severity`, `template`, `protocol`, `target`, `entry_type`).
- Script does not deduplicate findings before insert.
- If you rerun import with same generated IDs, ChromaDB may reject duplicate IDs depending on backend behavior.
