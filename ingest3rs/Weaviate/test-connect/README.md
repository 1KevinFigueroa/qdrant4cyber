# Weaviate `test-connect.py`

This folder contains a minimal end-to-end connectivity and semantic search test for a local Weaviate instance.

## Purpose

The script `test-connect.py` is a smoke test that verifies:

1. Python can connect to local Weaviate over gRPC.
2. A collection can be created and configured for vectorization.
3. Documents can be inserted.
4. A semantic `near_text` query returns relevant results.

It is useful for quickly validating that your local Weaviate setup, vectorizer module, and Python client are all working together.

## Requirements

### Software

- Python `3.9+`
- Local Weaviate instance running
- gRPC exposed on port `50051`
- HTTP API exposed on port `8080`

### Python dependencies

Install the client:

`pip install weaviate-client`

### Weaviate module expectation

The script creates a collection using `text2vec-transformers`:

- `Configure.Vectors.text2vec_transformers()`

Make sure your Weaviate instance is started with this vectorizer available.

## Architecture

The script follows this flow:

1. **Connect** to local Weaviate with an init timeout.
2. **Reset collection state** by deleting `TestDocument` if it already exists.
3. **Create collection schema** with one text property: `content`.
4. **Insert sample documents** with generated UUIDs.
5. **Run semantic query** using `near_text`.
6. **Print results** and close the client.

## Code walkthrough

### 1) Connection and error handling

- Uses `weaviate.connect_to_local(...)`.
- Sets init timeout with `wvc.init.Timeout(init=30)`.
- Catches `WeaviateGRPCUnavailableError` and exits with a clear message when gRPC is unavailable.

### 2) Collection lifecycle

- Collection name: `TestDocument`
- If collection exists, it is deleted to ensure deterministic test behavior.
- Re-created with:
  - vector config: `text2vec-transformers`
  - property: `content` as `TEXT`

### 3) Data ingestion

Inserts three sample text records:

- `Weaviate is a vector database`
- `MiniLM is a lightweight embedding model`
- `Docker makes deployment easy`

Each record is inserted with a random UUID.

### 4) Semantic query

Runs:

- Query text: `What is a vector database?`
- `limit=2`
- Returns only `content`

Then prints the top 2 semantically similar objects.

## Usage

From this directory:

`python test-connect.py`

## Example output

Expected console output will look similar to:

`[+] Schema created`
`[+] Data inserted`

`[+] Query Results:`
`- Weaviate is a vector database`
`- MiniLM is a lightweight embedding model`

Notes:

- Result ordering can vary slightly depending on model behavior and environment.
- If Weaviate gRPC is unreachable, the script exits with:
  - `Could not connect to Weaviate gRPC at localhost:50051...`

## Troubleshooting

- Verify Weaviate is running.
- Verify ports `8080` and `50051` are exposed.
- Verify the `text2vec-transformers` module is enabled in your Weaviate setup.
