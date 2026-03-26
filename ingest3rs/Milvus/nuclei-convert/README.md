# Nuclei Log Converter for Milvus (MiniLM-L6 Embeddings)

This script converts raw **Nuclei CLI text output** into structured JSON records and adds a semantic embedding vector to each record for Milvus ingestion.

- Script: `convert_nuclei_json-milvus-MiniLM-L6.py`
- Input: line-based `.txt` Nuclei output
- Output: `.json` array with normalized fields + embedding vectors

## Purpose

Use this script as a preprocessing step before importing Nuclei data into Milvus:

1. Run Nuclei and save output to a text file.
2. Convert the text output into structured JSON.
3. Generate embeddings for each parsed line using SentenceTransformers.
4. Pass the JSON into your Milvus import pipeline.

## Requirements

- Python `3.8+`
- Python packages:
  - `sentence-transformers`
- Standard library modules used:
  - `re`
  - `json`
  - `argparse`
  - `sys`

Install dependency:

```bash
pip install sentence-transformers
```

## Architecture

The parser processes the input file line-by-line and applies two regex parsers:

1. **Finding parser**
   - Format: `[template] [protocol] [severity] target [optional metadata]`
   - Output fields:
     - `entry_type: "finding"`
     - `template`, `protocol`, `severity`, `target`, `extra_info`

2. **Log parser**
   - Format: `[INF] message` or `[WRN] message`
   - Output fields:
     - `entry_type: "log"`
     - `log_level` (`info` or `warning`), `message`

For each parsed record:

- `build_text(entry)` creates a text representation.
- `SentenceTransformer.encode()` generates a dense vector.
- The script writes:
  - `id`
  - parsed fields
  - `text`
  - `vector`

## Code Walkthrough

### `build_text(entry)`

Builds the string that is sent to the embedding model.

- For findings: combines template, severity, target, and metadata.
- For logs: combines log level and message.

### `parse_nuclei_logs(input_path, output_path, model_name)`

Main workflow:

1. Loads the embedding model (`SentenceTransformer(model_name)`).
2. Compiles regex patterns for findings and logs.
3. Reads input lines.
4. Parses each line into a normalized entry.
5. Builds embedding text and encodes vector.
6. Appends entry to results with incrementing `id`.
7. Saves full result list to output JSON (`indent=4`).

### `main()`

CLI interface:

- `-i` / `--input` (required)
- `-o` / `--output` (required)
- `-m` / `--model` (optional, default: `all-MiniLM-L6-v2`)

## Usage

```bash
python convert_nuclei_json-milvus-MiniLM-L6.py -i nuclei_output.txt -o nuclei_milvus.json
```

Using a custom model:

```bash
python convert_nuclei_json-milvus-MiniLM-L6.py -i nuclei_output.txt -o nuclei_milvus.json -m all-MiniLM-L6-v2
```

## Example Input

```text
[http-missing-security-headers] [http] [info] https://example.com [x-powered-by: php]
[ssh-auth-methods] [tcp] [medium] 10.10.10.20:22 [password auth enabled]
[INF] Templates loaded: 9320
[WRN] Skipping target due to DNS resolution failure
```

## Expected JSON Output (shape)

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
        "vector": [0.0123, -0.0441, 0.0987, "..."]
    },
    {
        "id": 3,
        "entry_type": "log",
        "log_level": "info",
        "message": "Templates loaded: 9320",
        "text": "info Templates loaded: 9320",
        "vector": [0.0211, 0.0034, -0.0770, "..."]
    }
]
```

> `vector` is a full numeric embedding array. Its length depends on the model (for `all-MiniLM-L6-v2`, typically 384 dimensions).

## Expected Console Output

Successful run:

```text
[+] Loading embedding model: all-MiniLM-L6-v2
[+] Successfully parsed 4 entries.
[+] Output saved to: nuclei_milvus.json
```

Missing input file:

```text
[-] Error: File 'nuclei_output.txt' not found.
```

Unexpected error:

```text
[-] Unexpected error: <error details>
```

## Notes

- Empty and non-matching lines are skipped.
- `extra_info` is `null` when no metadata block exists.
- Output format is Milvus-ingestion friendly because each record includes text + vector.
