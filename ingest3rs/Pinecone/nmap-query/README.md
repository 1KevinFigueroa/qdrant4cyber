# nmap → Pinecone Ingest

Parses nmap scan results (JSON format) and loads them into a **local Pinecone vector database** running in Docker. Each discovered host becomes a semantically searchable vector, enabling natural-language queries over your network scan data.

Embeddings are generated locally using the **all-MiniLM-L6-v2** model from [sentence-transformers](https://www.sbert.net/) — no external API keys are required.

---

## Requirements

| Requirement | Version |
|---|---|
| Python | 3.10+ |
| Docker | Any recent version |
| pip packages | `pinecone[grpc]`, `sentence-transformers` |

### Install Python dependencies

```bash
pip install pinecone[grpc] sentence-transformers
```

> **Note:** The first run will download the `all-MiniLM-L6-v2` model (~80 MB). Subsequent runs use the cached version.

---

## Docker Setup

The script targets the [`pinecone-index`](https://github.com/pinecone-io/pinecone-local) Docker image, which runs a single Pinecone index as a lightweight, in-memory container. There is no cloud account or API key needed.

### Start the container

**Linux / macOS:**

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

**Windows (PowerShell):**

```powershell
docker run -d --name nmap-index `
    -e PORT=5081 `
    -e INDEX_TYPE=serverless `
    -e VECTOR_TYPE=dense `
    -e DIMENSION=384 `
    -e METRIC=cosine `
    -p 5081:5081 `
    --platform linux/amd64 `
    ghcr.io/pinecone-io/pinecone-index:latest
```

### Key parameters

| Variable | Value | Why |
|---|---|---|
| `DIMENSION` | `384` | Must match the embedding model output. `all-MiniLM-L6-v2` produces 384-dimensional vectors. |
| `METRIC` | `cosine` | Cosine similarity is the standard metric for sentence embeddings. |
| `PORT` | `5081` | The port the index listens on. Map this to the same host port. |

### Verify the container is running

```bash
docker ps --filter name=nmap-index
```

### Stop / reset

```bash
docker stop nmap-index && docker rm nmap-index
```

> **Important:** Pinecone Local is an in-memory emulator. All data is lost when the container stops.

---

## How It Works

The script processes nmap JSON scan results through a four-stage pipeline:

### 1. Parse

Reads the nmap JSON file and extracts every host that was reported as `"up"`. For each host it pulls out:

- IP address and MAC address
- Hostname (from PTR records)
- Operating system name and detection accuracy
- Uptime and last boot time
- Every open port with its service name, product, version, and extra info

### 2. Build text descriptions

Each host is converted into a rich natural-language description that captures all of the extracted data. For example:

```
Host 192.168.47.6 (srv-web-01.internal)
MAC address: F7:F3:F6:B5:E2:2A
Operating system: Ubuntu 22.04 LTS (accuracy 98%)
Last boot: Mon Feb 3 02:30:58 2026 (uptime 709148s)
Open ports (14):
  22/tcp — ssh (OpenSSH 9.1p1)
  80/tcp — http (Apache httpd 2.4.57, CentOS Stream)
  443/tcp — ssl/http (nginx 1.24.0)
  6379/tcp — redis (Redis 7.0.10)
  ...
```

This textual representation is what the embedding model encodes, making semantic queries like *"hosts running Redis"* or *"databases on the network"* possible.

### 3. Embed

The text descriptions are passed through the `all-MiniLM-L6-v2` sentence-transformer model, producing a 384-dimensional vector for each host. This runs entirely on your local CPU (or GPU if available) with no external API calls.

### 4. Upsert

Each vector is upserted into Pinecone along with structured metadata fields:

| Metadata field | Type | Description |
|---|---|---|
| `ip` | string | IPv4 address |
| `hostname` | string | PTR hostname |
| `mac` | string | MAC address |
| `os` | string | Detected operating system |
| `os_accuracy` | string | OS detection confidence (%) |
| `last_boot` | string | Last boot timestamp |
| `uptime_seconds` | string | Uptime in seconds |
| `open_port_numbers` | list[string] | List of open port numbers |
| `services` | list[string] | List of service names (ssh, http, etc.) |
| `products` | list[string] | List of product names (OpenSSH, nginx, etc.) |
| `port_count` | int | Number of open ports |
| `text` | string | Full natural-language description |

The vector ID for each host follows the pattern `host-<ip_with_underscores>` (e.g., `host-192_168_47_6`), so re-running the script on updated scan data will overwrite existing records for the same IPs.

Vectors are upserted in batches of 100 for efficiency.

---

## Usage

### Basic usage

```bash
python query-nmap-pinecone-MiniLM-L6.py nmap_results.json
```

### Expected output

```
Parsed 50 live hosts from nmap_results.json
Loading embedding model 'all-MiniLM-L6-v2' …
Connecting to local Pinecone index at http://localhost:5081 …
  upserted 50/50 vectors

Done — 50 host records stored in Pinecone index at http://localhost:5081.
```

### Custom Pinecone host

If your Docker container is on a different port:

**Linux / macOS:**

```bash
export PINECONE_HOST="http://localhost:5090"
python query-nmap-pinecone-MiniLM-L6.py nmap_results.json
```

**Windows (PowerShell):**

```powershell
$env:PINECONE_HOST = "http://localhost:5090"
python query-nmap-pinecone-MiniLM-L6.py nmap_results.json
```

---

## Input Format

The script expects nmap JSON output with the standard `nmaprun.host[]` structure. This is typically produced by converting nmap XML output (`-oX`) to JSON using tools like `xml2json` or `xmltodict`.

Example nmap command that produces compatible XML:

```bash
nmap -sV -sC -O -p- -oX scan_results.xml 192.168.1.0/24
```

Then convert to JSON:

```python
import xmltodict, json

with open("scan_results.xml") as f:
    data = xmltodict.parse(f.read())

with open("scan_results.json", "w") as f:
    json.dump(data, f, indent=2)
```

---

## Querying the Data

Once data is ingested, use `nmap_query.py` to search it with natural language. The script embeds your question with the same `all-MiniLM-L6-v2` model and finds the most similar hosts via cosine similarity.

### One-shot query

```bash
python nmap_query.py "hosts running Redis"
```

Example output:

```
================================================================================
  Query: hosts running Redis
  Results: 5
================================================================================

  [1]  192.168.47.6 (srv-web-01.internal)   —   score: 0.7832
  ------------------------------------------------------------
  OS          : Ubuntu 22.04 LTS
  Open ports  : 14
  Services    : ssh, http, ssl/http, redis, ...
  Products    : OpenSSH, Apache httpd, nginx, Redis, ...

    Host 192.168.47.6 (srv-web-01.internal)
    MAC address: F7:F3:F6:B5:E2:2A
    Operating system: Ubuntu 22.04 LTS (accuracy 98%)
    Open ports (14):
      22/tcp — ssh (OpenSSH 9.1p1)
      6379/tcp — redis (Redis 7.0.10)
      ...
```

### Return more results

```bash
python nmap_query.py "Windows servers with SQL Server" --top-k 10
```

### Interactive mode

Start a session where you can ask multiple questions without reloading the model each time:

```bash
python nmap_query.py --interactive
```

Inside the session:

```
nmap-query> databases exposed on the network
nmap-query> web servers on port 443
nmap-query> :k 10
  top-k set to 10
nmap-query> hosts with Kubernetes or Docker
nmap-query> :quit
```

### Example queries

| Query | What it finds |
|---|---|
| `"hosts running Redis"` | Hosts with Redis in their service/product list |
| `"databases exposed on the network"` | Hosts running MySQL, MariaDB, PostgreSQL, MSSQL, etc. |
| `"Windows servers"` | Hosts with a Windows OS detection |
| `"web servers on port 443"` | Hosts serving HTTPS traffic |
| `"hosts with Kubernetes or Docker"` | Hosts running container orchestration services |
| `"SSH servers with old versions"` | Hosts where SSH service details mention older versions |
| `"mail servers"` | Hosts running IMAP, POP3, SMTP, or Dovecot |
| `"monitoring and observability"` | Hosts running Grafana, Prometheus, Nagios, etc. |

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `PINECONE_HOST` | `http://localhost:5081` | URL of the local Pinecone index container |

---

## Troubleshooting

### `NotFoundException (404)` on `list_indexes()`

You are using the `pinecone-index` Docker image, which exposes a single index with no control-plane API. The script is already designed for this — make sure you are running the latest version of `query-nmap-pinecone-MiniLM-L6.py`.

### `UnauthorizedException (401)`

This usually means the Pinecone client is connecting to the cloud API instead of your local instance. Verify that `PINECONE_HOST` points to your Docker container (e.g., `http://localhost:5081`).

### Dimension mismatch errors

The Docker container must be started with `DIMENSION=384` to match the `all-MiniLM-L6-v2` embedding model. If you started it with a different dimension, stop and recreate the container.

### Connection refused

Verify the container is running (`docker ps`) and that the port mapping matches what the script expects.

---

## Project Structure

```
.
├── query-nmap-pinecone-MiniLM-L6.py            # Ingest nmap JSON into Pinecone
├── nmap_query.py             # Query the ingested data
├── nmap_results.json    # Example nmap scan data (JSON)
└── README.md                 # This file
```

---

## License

This project is provided as-is for educational and internal use.

