# Nuclei TXT → Weaviate JSON Converter (`MiniLM-L6` Pipeline)

Script: `nuclei_to_weaviate-MiniLm-L6.py`

## Purpose

This script converts raw Nuclei CLI text output into **Weaviate-ready JSON objects**.

It parses each finding line, extracts structured fields, builds a searchable `description`, and outputs objects shaped like:

- `class: "NucleiFinding"`
- `properties: { ... }`

This is the conversion step before importing findings into Weaviate.

---

## Requirements

- Python `3.8+`
- Standard library only:
  - `re`
  - `json`
  - `argparse`
  - `datetime`

No external Python packages are required.

---

## Architecture

```text
Nuclei TXT lines
      │
      ▼
parse_nuclei_txt()
(regex finding parser)
      │
      ▼
parse_metadata()
(extract key/value + arrays)
      │
      ▼
build_description()
(concatenate searchable text)
      │
      ▼
Weaviate object builder
(class + properties + timestamp)
      │
      ▼
JSON file output
```

---

## Code Walkthrough

### `parse_metadata(meta_str)`

Parses optional trailing metadata text.

- Extracts key/value pairs in the form `key="value"`
- Extracts bracket values like `["7.0.30"]`
- Stores extracted array values under `metadata["values"]`

If no metadata exists, returns `{}`.

### `build_description(template, protocol, severity, target, metadata)`

Builds a compact text string combining main fields and metadata.

This `description` field is useful for Weaviate text search / vectorization pipelines.

### `parse_nuclei_txt(input_file)`

Main parser logic:

1. Compiles regex for finding lines:
   - `[template] [protocol] [severity] target [optional meta]`
2. Reads input file line-by-line.
3. Skips empty and non-matching lines.
4. Extracts fields and parsed metadata.
5. Builds `description`.
6. Appends Weaviate-formatted object:
   - `class: "NucleiFinding"`
   - `properties`: `template`, `protocol`, `severity`, `target`, `metadata`, `description`, `raw`, `timestamp`

Returns a list of parsed objects.

### `main()`

CLI wrapper:

- `-i` / `--input`: input Nuclei text file
- `-o` / `--output`: output JSON file

Writes parsed results as pretty JSON (`indent=4`) and prints summary.

---

## Usage

```bash
python nuclei_to_weaviate-MiniLm-L6.py -i nuclei_output.txt -o weaviate_nuclei.json
```

---

## Example Input

```text
[phpinfo-exposure] [http] [medium] https://example.com ["7.0.30"] [paths="/phpinfo.php"]
[ssh-auth-methods] [tcp] [low] 10.10.10.20:22 [methods="password,publickey"]
```

---

## Expected JSON Output (example)

```json
[
    {
        "class": "NucleiFinding",
        "properties": {
            "template": "phpinfo-exposure",
            "protocol": "http",
            "severity": "medium",
            "target": "https://example.com",
            "metadata": {
                "paths": "/phpinfo.php",
                "values": [
                    "7.0.30",
                    "paths=\"/phpinfo.php\""
                ]
            },
            "description": "phpinfo-exposure http medium https://example.com paths:/phpinfo.php values:7.0.30,paths=\"/phpinfo.php\"",
            "raw": "[phpinfo-exposure] [http] [medium] https://example.com [\"7.0.30\"] [paths=\"/phpinfo.php\"]",
            "timestamp": "2026-01-01T12:00:00.000000"
        }
    }
]
```

> `timestamp` is generated at runtime with `datetime.utcnow().isoformat()`, so values will differ.

---

## Expected Console Output

Successful run:

```text
[+] Parsed 2 findings
[+] Output written to weaviate_nuclei.json
```

---

## Notes

- Only lines matching the expected Nuclei finding format are converted.
- Log/status lines are ignored.
- Metadata parsing is pattern-based; uncommon metadata formats may not be fully normalized.
