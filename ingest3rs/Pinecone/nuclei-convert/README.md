# Nuclei Log Converter for Pinecone

This script converts raw **Nuclei CLI text output** into a structured JSON array that can be used by the Pinecone ingestion pipeline.

- Script: `convert_nuclei_json-pinecone.py`
- Input: `.txt` log file (line-based Nuclei output)
- Output: `.json` file (normalized records)

## Purpose

`convert_nuclei_json-pinecone.py` acts as a preprocessing step:

1. Run Nuclei and capture CLI output.
2. Convert the output to structured JSON with this script.
3. Feed the JSON into downstream Pinecone import/indexing scripts.

## Requirements

- Python 3.8+
- Standard library modules only:
  - `re`
  - `json`
  - `argparse`
  - `sys`

No external dependencies are required.

## Architecture

The parser reads the input file line-by-line and applies two regex patterns:

1. **Finding parser**
   - Expected format: `[template] [protocol] [severity] target [optional metadata]`
   - Produces:
     - `entry_type: "finding"`
     - `template`, `protocol`, `severity`, `target`, `extra_info`

2. **Status parser**
   - Expected format: `[INF] message` or `[WRN] message`
   - Produces:
     - `entry_type: "log"`
     - `log_level` (`info` or `warning`), `message`

Each parsed line gets a sequential `id`.

Empty lines and non-matching lines are ignored.

## Code Walkthrough

### `parse_nuclei_logs(input_path, output_path)`

Core flow:

1. Initialize storage (`parsed_results`) and counter (`entry_id`).
2. Compile regex patterns for findings and status messages.
3. Open input file and iterate over lines.
4. For each line:
   - Trim whitespace and skip empties.
   - Attempt finding match first.
   - If not matched, attempt status match.
   - Build a structured entry, append to results, increment `entry_id`.
5. Write results to output JSON (`indent=4`).
6. Print success summary.

### Error Handling

- `FileNotFoundError`: prints a clear error and exits with code `1`.
- Any other exception: prints the exception and exits with code `1`.

### `main()`

Defines required CLI flags:

- `-i` / `--input`: path to raw Nuclei text output
- `-o` / `--output`: path to generated JSON

Then calls `parse_nuclei_logs(args.input, args.output)`.

## Usage

```bash
python convert_nuclei_json-pinecone.py -i nuclei_output.txt -o nuclei_results.json
```

## Example Input

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

- `extra_info` is `null` if no metadata block is present.
- The parser is format-driven; lines that do not match expected patterns are skipped.
- Output is designed for downstream Pinecone ingestion workflows.
