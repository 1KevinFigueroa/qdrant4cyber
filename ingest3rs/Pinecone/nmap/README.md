# Nmap to Pinecone Importer

`nmap_to_pinecone-MiniLM-L6.py` ingests Nmap JSON scan results into a local Pinecone index and generates embeddings with MiniLM.

## Purpose

The script converts Nmap host/service data into:

- semantic vectors for natural-language search
- structured host metadata for context
- consistent host IDs for repeatable upserts

This enables querying scan data by intent (for example: `hosts running Redis`) instead of only exact keyword matching.

## Requirements

- Python 3.8+
- `pinecone[grpc]`
- `sentence-transformers`
- Local Pinecone index container running (default endpoint: `http://localhost:5081`)

Install dependencies:

```bash
pip install pinecone[grpc] sentence-transformers
```

## Docker Setup (Local Pinecone)

Run local Pinecone index container with embedding-compatible settings:

```bash
docker run -d --name nmap-index \
  -e PORT=5081 \
  -e INDEX_TYPE=serverless \
  -e VECTOR_TYPE=dense \
  -e DIMENSION=384 \
  -e METRIC=cosine \
  -p 5081:5081 \
  --platform linux/amd64 \
  ghcr.io/pinecone-io/pinecone-index:latest
```

Important:

- `DIMENSION` must be `384` (matches `all-MiniLM-L6-v2`)
- `METRIC` should be `cosine`

## Architecture

1. **CLI layer (`main`)**
   - accepts `json_file`
2. **Parse layer (`parse_nmap_json`)**
   - reads Nmap JSON and extracts live hosts
3. **Normalization layer (`_normalize_host`)**
   - standardizes host fields (IP, hostname, OS, ports, uptime)
4. **Text/metadata layer (`_host_to_text`, `_host_to_metadata`)**
   - builds semantic text and metadata payloads
5. **Embedding layer (`embed_texts`)**
   - encodes host text with `all-MiniLM-L6-v2`
6. **Storage layer (`get_index`, `ingest`)**
   - upserts vectors + metadata to Pinecone in batches

## Code Walkthrough

### `_normalize_host(host)`

Normalizes a raw Nmap host entry and keeps only hosts where status is `up`.

Extracts:

- `ip`, `mac`, `hostname`
- OS + OS accuracy
- uptime / last boot
- port records (service/product/version/extra)

### `_host_to_text(h)`

Builds a multiline host summary used as embedding input.

### `_host_to_metadata(h)`

Builds metadata stored with each vector, including:

- `ip`, `hostname`, `mac`, `os`
- `open_port_numbers`, `services`, `products`
- `port_count`
- full `text` summary

### `parse_nmap_json(path)`

Loads JSON and collects valid normalized hosts from `nmaprun.host`.

### `embed_texts(texts, model)`

Encodes host text to dense vectors.

### `get_index()`

Connects to local Pinecone index using:

- local key: `pclocal`
- host: `PINECONE_HOST` env var (default `http://localhost:5081`)

### `ingest(json_path)`

Core ingest flow:

1. parse hosts
2. load embedding model
3. connect to Pinecone
4. build text/metadata/IDs
5. embed and upsert in batches (`BATCH = 100`)

Vector ID format:

- `host-<ip_with_underscores>`
- Example: `host-192_168_1_10`

## Usage

Run commands from the same directory as `nmap_to_pinecone-MiniLM-L6.py`.

### Basic import

```bash
python nmap_to_pinecone-MiniLM-L6.py nmap_results.json
```

### Use custom Pinecone host

```powershell
$env:PINECONE_HOST = "http://localhost:5090"
python nmap_to_pinecone-MiniLM-L6.py nmap_results.json
```

## Expected Output

### Successful run (example)

```text
Parsed 50 live hosts from nmap_results.json
Loading embedding model 'all-MiniLM-L6-v2' …
Connecting to local Pinecone index at http://localhost:5081 …
  upserted 50/50 vectors

Done — 50 host records stored in Pinecone index at http://localhost:5081.
```

### No hosts found case

```text
No hosts found in the scan file.
```

## Environment Variable

- `PINECONE_HOST` (default: `http://localhost:5081`)

## Notes

- Use the same embedding model for ingest and query (`all-MiniLM-L6-v2`).
- Local Pinecone index container is in-memory; data persistence depends on container lifecycle.
- Re-running ingest updates existing host vectors when IDs match.

