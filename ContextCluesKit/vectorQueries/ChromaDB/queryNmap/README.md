# Nmap ChromaDB Query Tool

`query-nmap-chromadb-MiniLM-L6.py` is a command-line query utility for exploring Nmap scan data that has already been indexed in a ChromaDB collection.

It supports:

- demo mode (7 built-in query examples)
- interactive mode (REPL-style semantic and metadata queries)

`query_nmap_to_chromadb-OpenAI-ada-002-LangChain-GPT4.py` is a LangChain-powered conversational Q&A interface for asking open-ended questions about nmap scan results stored in ChromaDB.

It supports:

- conversation history-aware retrieval (follow-up questions retain context)
- interactive chat mode with natural language questions
- security-focused analysis powered by GPT-4o

---

## Purpose

The script helps you quickly answer questions like:

- Which hosts are running HTTP/SSH/SMB?
- Which hosts expose many open ports?
- Which active hosts are currently in the dataset?
- Which systems look like database servers?

Because it uses ChromaDB semantic search, you can query in natural language (for example, `web server`) and still match related services (`http`, `nginx`, `apache`, etc.).

The LangChain GPT-4o variant extends this by enabling open-ended, conversational questions such as:

- Summarize the most critical security findings.
- Are there any hosts running outdated software?
- What operating systems were detected?
- List all web servers found in the scan.

---

## Location and File Names

This README describes:

- `query-nmap-chromadb-MiniLM-L6.py`
- `query_nmap_to_chromadb-OpenAI-ada-002-LangChain-GPT4.py`

Run commands from the same directory as the script.

---

## Requirements

- Python 3.8+
- `chromadb` Python package
- A running ChromaDB server (default host/port: `localhost:9000`)
- A populated ChromaDB collection named `nmaptest` with host documents and metadata

Install dependency:

```bash
pip install chromadb
```

### Additional Requirements for the OpenAI/LangChain Variant

- `langchain-openai`, `langchain-chroma`, `langchain-classic`, `langchain-core` Python packages
- `python-dotenv` Python package
- A valid OpenAI API key set as `OpenAI_API_KEY` in a `.env` file or environment variable
- A populated ChromaDB collection named `nmaptest_openAI` (imported using `import_nmap_to_chromadb-OpenAI-ada-002.py`)

Install dependencies:

```bash
pip install langchain-openai langchain-chroma langchain-classic langchain-core python-dotenv chromadb
```

---

## Quick Start

From the script directory:

```bash
# Demo mode
python query-nmap-chromadb-MiniLM-L6.py

# Interactive mode
python query-nmap-chromadb-MiniLM-L6.py -i
```

Optional environment variables:

```bash
set CHROMADB_HOST=localhost
set CHROMADB_PORT=9000
```

### Quick Start for the OpenAI/LangChain Variant

```bash
# Ensure your .env file contains:
# OpenAI_API_KEY=sk-...

# Launch interactive Q&A
python query_nmap_to_chromadb-OpenAI-ada-002-LangChain-GPT4.py
```

---

## Script Architecture

The script is organized into five parts:

1. **CLI entrypoint (`main`)**
   - parses `-i/--interactive`
   - initializes ChromaDB HTTP client
   - loads `nmaptest` collection
   - routes to demo or interactive mode

2. **Display helper**
   - `print_section(title)` for consistent console section formatting

3. **Demo query functions**
   - `query_http_services`
   - `query_ssh_services`
   - `query_by_port_count`
   - `query_smb_services`
   - `get_all_active_hosts`
   - `custom_query_example`
   - `simple_query_example`

4. **Interactive REPL (`interactive_mode`)**
   - semantic free-text search
   - command handlers (`:k`, `:all`, `:ports`, `:count`, `:help`, `:q`)

5. **Error handling**
   - catches connection/runtime errors
   - prints troubleshooting guidance

### OpenAI/LangChain Variant Architecture

The LangChain variant is organized into three parts:

1. **QA chain builder (`build_qa_chain`)**
   - loads environment variables via `python-dotenv`
   - initializes OpenAI embeddings (`text-embedding-ada-002`)
   - connects LangChain to the existing ChromaDB collection (`nmaptest_openAI`) via `chromadb.HttpClient`
   - configures a similarity retriever returning the top-20 most relevant host documents
   - builds a history-aware retriever that reformulates follow-up questions into standalone queries
   - builds a stuff-documents answer chain with a security analyst system prompt
   - returns the full retrieval chain and an empty chat history list

2. **Interactive chat (`interactive_chat`)**
   - REPL loop accepting natural language questions
   - invokes the retrieval chain with the current question and conversation history
   - appends each question/answer pair to chat history for multi-turn context
   - displays the answer and lists source IP addresses used as context
   - supports `clear` to reset conversation history and `exit`/`quit`/`q` to quit

3. **Main entrypoint (`main`)**
   - calls `build_qa_chain()` and launches `interactive_chat()` if successful
   - exits with an error message if the chain could not be built

---

## How the Code Works

### 1) Connection and collection load

`main()` builds a `chromadb.HttpClient` and connects to:

- host from `CHROMADB_HOST` (default `localhost`)
- port from `CHROMADB_PORT` (default `9000`)
- auth header `Authorization: Bearer my-secret-token`

It then loads `client.get_collection("nmaptest")`.

### 2) Two query strategies

- **Semantic search** (`collection.query`) for fuzzy intent-based matching
- **Metadata filtering** (`collection.get(where=...)`) for exact filters like:
  - `state == "up"`
  - `open_port_count > N`

### 3) Result rendering

Each result prints key metadata (IP, hostname, port count), then extracts service lines from the document body to keep output readable.

### 4) Interactive behavior

In interactive mode, user input is either:

- a control command (starts with `:`), or
- treated as semantic query text

The result count is adjustable live via `:k <number>`.

### How the OpenAI/LangChain Variant Works

#### 1) Connection and collection load

`build_qa_chain()` connects to ChromaDB using the same HTTP client approach:

- host: `localhost` (constant `CHROMADB_HOST`)
- port: `9000` (constant `CHROMADB_PORT`)
- auth header: `Authorization: Bearer my-secret-token`

It loads the collection `nmaptest_openAI` through LangChain's `Chroma` wrapper and verifies the document count is non-zero.

#### 2) Embedding and retrieval

- Uses OpenAI `text-embedding-ada-002` for vector embeddings (must match the model used during import)
- Retrieves the top-20 most similar documents via LangChain's similarity retriever

#### 3) History-aware question reformulation

A dedicated LangChain prompt takes the chat history and the latest user question, then reformulates it into a standalone query. This allows follow-up questions like "What about their SSH versions?" to be understood in context.

#### 4) Answer generation

- GPT-4o generates answers using a system prompt that instructs it to act as a senior network security analyst
- Only the retrieved nmap host records are used as context — the model does not fabricate data
- Answers reference specific IPs, ports, services, and OS details, and highlight security concerns with actionable recommendations

#### 5) Source attribution

After each answer, the script extracts and displays the unique IP addresses from the retrieved context documents, providing traceability back to the original scan data.

---

## Usage

```text
usage: query-nmap-chromadb-MiniLM-L6.py [-h] [-i]

ChromaDB Query Examples for Nmap Data

options:
  -h, --help         show this help message and exit
  -i, --interactive  Launch interactive query mode
```

### OpenAI/LangChain Variant Usage

```text
usage: query_nmap_to_chromadb-OpenAI-ada-002-LangChain-GPT4.py

Nmap ChromaDB LangChain Q&A

No arguments required. Launches interactive chat directly.
Data must be imported first using import_nmap_to_chromadb-OpenAI-ada-002.py
```

---

## Interactive Commands

| Command | Description |
|---|---|
| `<text>` | Semantic search across host/service documents |
| `:k <number>` | Set max results for semantic and `:ports` queries |
| `:all` | List hosts where `state = up` |
| `:ports <n>` | Hosts where `open_port_count > n` |
| `:count` | Print collection document count |
| `:help` | Show command help |
| `:quit` / `:q` | Exit interactive mode |

### OpenAI/LangChain Variant Commands

| Command | Description |
|---|---|
| `<text>` | Natural language question answered by GPT-4o using retrieved scan context |
| `clear` | Reset conversation history |
| `exit` / `quit` / `q` | Exit the session |

---

## Expected Output Examples

### Demo mode (abridged)

```text
======================================================================
ChromaDB Query Examples - Nmap Data
======================================================================

Connecting to ChromaDB and loading 'nmaptest' collection...
✓ Successfully loaded collection 'nmaptest'
✓ Total documents in collection: 42

======================================================================
Query 1: Search for HTTP Services
======================================================================

Result 1:
  IP Address: 192.168.1.10
  80/tcp open http: nginx 1.24.0
```

### Interactive mode sample

```text
nmap-query [k=5]> ssh
  Top 5 results for 'ssh':

  [1] 192.168.1.10 (fileserver.local) - 8 open ports  [score: 0.4312]
      22/tcp open ssh: OpenSSH 8.9p1

nmap-query [k=5]> :k 10
  ✓ Results per query set to 10

nmap-query [k=10]> :count
  Total documents: 42

nmap-query [k=10]> :q
Exiting interactive mode.
```

### OpenAI/LangChain Variant Output Sample

```text
✓ Connected to ChromaDB collection 'nmaptest_openAI' (42 documents)

======================================================================
🔍 Nmap Scan Q&A  (powered by LangChain + OpenAI)
======================================================================
Ask anything about your scan results. Type 'exit' to quit.

Example questions:
  • Which hosts have port 22 (SSH) open?
  • Summarize the most critical security findings.
  • What operating systems were detected?
  • Are there any hosts running outdated software?
  • List all web servers found in the scan.

You: Which hosts have SSH open?

Assistant: The following hosts have port 22 (SSH) open:
  - 192.168.1.10 (fileserver.local) — OpenSSH 8.9p1
  - 192.168.1.25 (devbox.local) — OpenSSH 9.0p1
  ...

  📎 Sources: 192.168.1.10, 192.168.1.25

You: Are any of those running outdated versions?

Assistant: Based on the scan data, 192.168.1.10 is running OpenSSH 8.9p1,
which has known vulnerabilities. I recommend upgrading to the latest
stable release...

  📎 Sources: 192.168.1.10, 192.168.1.25
```

---

## Metadata Model Assumed by the Script

Each host document is expected to include metadata like:

- `ip_address` (string)
- `hostname` (string)
- `state` (string, typically `up`/`down`)
- `open_port_count` (integer)
- `vendor` (string, optional)

The OpenAI/LangChain variant uses the same metadata model. Source attribution in answers is driven by the `ip_address` metadata field extracted from retrieved context documents.

---

## Troubleshooting

| Problem | Likely Cause | Fix |
|---|---|---|
| Connection refused | ChromaDB server not running | Start server/container on configured host/port |
| Collection not found | `nmaptest` missing | Import Nmap data into that collection |
| `ModuleNotFoundError: chromadb` | Dependency missing | `pip install chromadb` |
| No semantic matches | Empty or low-quality indexed data | Verify ingest process and use `:count` |

### Additional Troubleshooting for the OpenAI/LangChain Variant

| Problem | Likely Cause | Fix |
|---|---|---|
| `OpenAI_API_KEY not found` | Missing API key | Add `OpenAI_API_KEY=sk-...` to `.env` file or export as environment variable |
| Collection is empty | Data not imported | Run `import_nmap_to_chromadb-OpenAI-ada-002.py` first |
| `ModuleNotFoundError: langchain_openai` | LangChain dependencies missing | `pip install langchain-openai langchain-chroma langchain-classic langchain-core python-dotenv` |
| Incorrect or irrelevant answers | Embedding model mismatch | Ensure import and query both use `text-embedding-ada-002` |
| Collection name mismatch | Wrong collection | Verify the constant `COLLECTION_NAME` is set to `nmaptest_openAI` |

---

## Notes

- Default collection name is hardcoded as `nmaptest`.
- Default auth header uses a placeholder token (`my-secret-token`); update if your server enforces different auth.
- The script includes a commented local `chromadb.Client(Settings(...))` example if you want non-HTTP client usage.

### Additional Notes for the OpenAI/LangChain Variant

- Default collection name is hardcoded as `nmaptest_openAI`.
- ChromaDB connection defaults are `localhost:9000` with the same placeholder auth token (`my-secret-token`).
- The retriever returns the top-20 most similar documents (`search_kwargs={\"k\": 20}`).
- Conversation history is maintained in memory and lost when the script exits; type `clear` to reset mid-session.
- The LLM temperature is set to `0` for deterministic, factual answers.
- The system prompt restricts GPT-4o to only use retrieved context — it will not fabricate scan data.
