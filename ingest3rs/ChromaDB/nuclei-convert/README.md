# Nuclei Log Converter for ChromaDB

This script converts raw **Nuclei CLI text output** into a structured JSON array that can be imported into ChromaDB.

- Script: `convert_nuclei_json-ChromaDB.py`
- Input: `.txt` log file (line-based Nuclei output)
- Output: `.json` file (normalized records)

## Purpose

`convert_nuclei_json-ChromaDB.py` is a preprocessing step in the ChromaDB pipeline:

1. Run Nuclei and collect console output.
2. Convert the output to structured JSON with this script.
3. Import the JSON into ChromaDB using `nuclei_to_chromadb-MiniLM-L6.py`.
4. Query results using `query-nuclei-chromadb-MiniLM-L6.py`.

## Requirements

- Python 3.8+
- No third-party dependencies (uses standard library only):
  - `re`
  - `json`
  - `argparse`
  - `sys`

## Architecture

The converter processes the input file line-by-line using two regex parsers:

1. **Finding parser**
   - Pattern: `[template] [protocol] [severity] target [optional metadata]`
   - Produces records with:
     - `entry_type: "finding"`
     - `template`, `protocol`, `severity`, `target`, `extra_info`

2. **Status parser**
   - Pattern: `[INF] message` or `[WRN] message`
   - Produces records with:
     - `entry_type: "log"`
     - `log_level` (`info`/`warning`), `message`

Each parsed line receives an incrementing `id`.

Unmatched or empty lines are ignored.

## Code Walkthrough

### `parse_nuclei_logs(input_path, output_path)`

Core workflow:

1. Initialize:
   - `parsed_results = []`
   - `entry_id = 1`
2. Compile regex patterns for findings and status lines.
3. Read input file line-by-line.
4. For each line:
   - Skip empty lines.
   - Try finding pattern first.
   - If no finding match, try status pattern.
   - Append structured entry and increment `entry_id`.
5. Write `parsed_results` to output JSON with indentation.
6. Print success summary.

### Error Handling

- `FileNotFoundError` → prints friendly error and exits with code `1`
- Any other exception → prints exception and exits with code `1`

### `main()`

Uses argparse with required flags:

- `-i/--input`: input text log path
- `-o/--output`: output JSON path

Then calls `parse_nuclei_logs()`.

## Usage

```bash
python convert_nuclei_json-ChromaDB.py -i nuclei_output.txt -o nuclei_results.json
```

## Input Examples

### Example raw Nuclei lines

```text
[http-missing-security-headers] [http] [info] https://example.com [x-powered-by: php]
[ssh-auth-methods] [tcp] [medium] 10.10.10.20:22 [password auth enabled]
[INF] Templates loaded: 9320
[WRN] Skipping target due to DNS resolution failure
```

## Expected JSON Output

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
    },
    {
        "id": 3,
        "entry_type": "log",
        "log_level": "info",
        "message": "Templates loaded: 9320"
    },
    {
        "id": 4,
        "entry_type": "log",
        "log_level": "warning",
        "message": "Skipping target due to DNS resolution failure"
    }
]
```

## Expected Console Output

Successful run:

```text
[+] Successfully parsed 4 entries.
[+] Output saved to: nuclei_results.json
```

Missing input file:

```text
[-] Error: The file 'nuclei_output.txt' was not found.
```

## Notes

- `extra_info` is `null` when no trailing metadata block exists.
- The script is intentionally strict about line format; non-matching lines are skipped.
- Output format is designed to be consumed by the ChromaDB import script in `ingest3rs/ChromaDB/nuclei-import/`.
