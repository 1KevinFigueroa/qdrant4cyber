# ChromaDB Docker Connection Script

This script establishes a connection to a ChromaDB server running in a Docker container and verifies the connection status.

## Overview

`connect.py` is a simple Python script that connects to a ChromaDB instance via HTTP and performs basic health checks to ensure the database is accessible and responding correctly.

## Requirements

### Software Dependencies

- **Python**: 3.7 or higher
- **ChromaDB Python Client**: Install via pip

```bash
pip install chromadb
```

### Infrastructure Requirements

- **Docker**: Must be installed and running
- **ChromaDB Docker Container**: Must be running and accessible on the specified host and port

## ChromaDB Docker Setup

Before running this script, you need to have ChromaDB running in a Docker container. Here's how to set it up:

### Basic Docker Run Command

```bash
docker run -p 8000:8000 chromadb/chroma
```

## Code Explanation

### Import Statement

```python
import chromadb
```

Imports the ChromaDB client library, which provides the interface to interact with ChromaDB servers.

### Client Initialization

```python
client = chromadb.HttpClient(
    host="localhost",
    port=8000,
    headers={"Authorization": "Bearer my-secret-token"}
)
```

Creates an HTTP client instance with the following parameters:

- **host**: The hostname where ChromaDB is running (default: "localhost")
- **port**: The port number ChromaDB is listening on (default: 8000)
- **headers**: HTTP headers for authentication
  - The `Authorization` header uses Bearer token authentication
  - Token value: `my-secret-token` (should match your Docker configuration)

### Connection Verification

```python
print(f"Heartbeat: {client.heartbeat()}")
print(f"Version: {client.get_version()}")
```

Performs two health checks:

1. **Heartbeat**: Returns a timestamp indicating the server is alive and responding
2. **Version**: Returns the ChromaDB server version number

## Usage

### Running the Script

```bash
python connect.py
```

### Expected Output

If the connection is successful, you should see output similar to:

```
Heartbeat: 1234567890
Version: 0.4.x
```

### Troubleshooting Connection Issues

If you encounter errors, check the following:

1. **Docker Container Running**: Verify ChromaDB is running
   ```bash
   docker ps | grep chroma
   ```

2. **Port Availability**: Ensure port 8000 is not blocked
   ```bash
   netstat -an | grep 8000
   ```

3. **Authentication Token**: Verify the token matches between script and Docker configuration

4. **Network Connectivity**: If running Docker on a different machine, update the `host` parameter

## Configuration

### Connecting to Remote ChromaDB

To connect to a ChromaDB instance on a different machine:

```python
client = chromadb.HttpClient(
    host="192.168.1.100",  # Replace with actual IP
    port=8000,
    headers={"Authorization": "Bearer my-secret-token"}
)
```

### Running Without Authentication

If your ChromaDB instance doesn't require authentication:

```python
client = chromadb.HttpClient(
    host="localhost",
    port=8000
)
```

### Using Different Port

If ChromaDB is running on a different port:

```python
client = chromadb.HttpClient(
    host="localhost",
    port=9000,  # Your custom port
    headers={"Authorization": "Bearer my-secret-token"}
)
```
## Next Steps

After successfully connecting to ChromaDB, you can:

- Create collections to store embeddings
- Add documents with embeddings
- Query for similar documents
- Update and delete documents
- Manage metadata

## Additional Resources

- [ChromaDB Official Documentation](https://docs.trychroma.com/)
- [ChromaDB GitHub Repository](https://github.com/chroma-core/chroma)
- [ChromaDB Docker Hub](https://hub.docker.com/r/chromadb/chroma)

## License

This script is provided as-is for educational and development purposes.
