# Nmap → Weaviate Ingest (`nmap_to_weaviate-MiniLM-L6.py`)

This script ingests Nmap scan results (JSON format) into a Weaviate collection using local sentence embeddings from `all-MiniLM-L6-v2`.

It converts each live host into:

- searchable text (`text`)
- structured metadata (`ip`, `hostname`, `os`, `tags`)
- a 384-dim embedding vector for semantic search

The resulting dataset is ready for hybrid search (keyword + vector).

---

## Purpose

Nmap output is rich but hard to query semantically at scale. This importer creates a retrieval-friendly index in Weaviate so you can ask questions like:

- “show Linux hosts exposing search services”
- “find likely Kubernetes control-plane nodes”
- “hosts running web servers and monitoring tools”

---

## Requirements

### Python

- Python 3.10+
- Packages:

```bash
pip install weaviate-client sentence-transformers tqdm
```

### Weaviate

A reachable Weaviate instance (default: `http://localhost:8080`) with gRPC exposed.

> The script derives gRPC port automatically:
>
> - if HTTP is `8080` → gRPC `50051`
> - otherwise gRPC uses the same numeric port as HTTP

---

## Architecture

```text
Nmap JSON
   │
   ▼
parse_nmap_json()
   │  (live hosts, IPv4, open ports/services, OS)
   ▼
host_to_text() + generate_tags()
   │
   ▼
SentenceTransformer(all-MiniLM-L6-v2)
   │  (384-dim vectors)
   ▼
Weaviate collection: NmapHost
   ├─ properties: text, ip, hostname, os, tags
   └─ vector: self-provided embedding
```

---

## Collection Schema

Class/collection name: `NmapHost`

| Property | Type | Notes |
|---|---|---|
| `text` | `TEXT` | Full host description used for semantic context |
| `ip` | `TEXT` | IPv4 address |
| `hostname` | `TEXT` | Hostname (currently empty in parser) |
| `os` | `TEXT` | OS match name from Nmap |
| `tags` | `TEXT_ARRAY` | Derived labels (e.g., `linux`, `database`, `k8s_api`) |

Vector config: `self_provided` (script supplies vectors explicitly).

---

## How the Code Works

### 1. `connect()`

- Parses `WEAVIATE_URL`
- Configures HTTP + gRPC endpoints
- Connects with timeout settings
- Exits with a clear message if gRPC is unavailable

### 2. `create_schema(client, reset=False)`

- Creates `NmapHost` if missing
- If `--reset` is passed, drops and recreates schema

### 3. `parse_nmap_json(path)`

- Loads JSON
- Reads `nmaprun.host`
- Keeps only hosts with status `up`
- Extracts:
  - IPv4
  - OS name
  - open ports + service product

### 4. `generate_tags(ports, os_name)`

Builds tags from service names and common port indicators, for example:

- `kubernetes`, `orchestration`, `k8s_api`
- `database`, `cache`, `streaming`
- `web_server`, `reverse_proxy`
- `linux`, `windows`

### 5. `host_to_text(host)`

Creates normalized descriptive text such as:

```text
Host 10.0.0.15 running Linux 5.x
Open services:
22 OpenSSH
6443 Kubernetes
```

### 6. `ingest(json_path, reset=False)`

- Parses hosts
- Builds text + tags
- Encodes text into vectors using MiniLM
- Inserts objects in dynamic batch mode
- Closes client cleanly

### 7. `main()` CLI

- positional arg: `json_file`
- option: `--reset`

---

## Usage

Run commands from the same directory as `nmap_to_weaviate-MiniLM-L6.py`.

### Basic import

```bash
python nmap_to_weaviate-MiniLM-L6.py scan.json
```

### Recreate schema then import

```bash
python nmap_to_weaviate-MiniLM-L6.py scan.json --reset
```

---

## Example Input Shape

The parser expects Nmap-style JSON keys like:

- `nmaprun.host`
- `host.status.@state`
- `host.address[].@addrtype`
- `host.ports.port[]`

Minimal host example:

```json
{
  "status": { "@state": "up" },
  "address": [{ "@addrtype": "ipv4", "@addr": "10.0.0.15" }],
  "os": { "osmatch": { "@name": "Linux 5.x" } },
  "ports": {
    "port": [
      {
        "@portid": "22",
        "state": { "@state": "open" },
        "service": { "@product": "OpenSSH" }
      }
    ]
  }
}
```

---

## Expected Console Output

Typical successful run:

```text
[INFO] Creating schema: NmapHost
[INFO] Parsed 42 hosts
[INFO] Generating embeddings...
[INFO] Inserting into Weaviate...
100%|████████████████████████████████████████| 42/42 [00:00<00:00, 120.10it/s]

✅ Done: 42 hosts ingested into 'NmapHost'
```

If no valid live IPv4 hosts are found:

```text
No valid hosts found
```

If Weaviate gRPC is unreachable:

```text
Could not connect to Weaviate gRPC at localhost:50051. Ensure Weaviate is running and the gRPC port is exposed.
```

---

## Notes

- Embedding model: `sentence-transformers/all-MiniLM-L6-v2` (first run downloads model files).
- `BATCH_SIZE` constant exists but current ingestion uses Weaviate dynamic batching.
- `hostname` is currently set to empty string by parser logic.
