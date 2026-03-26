import chromadb
import os

chromadb_host = os.getenv("CHROMADB_HOST", "localhost")
chromadb_port = int(os.getenv("CHROMADB_PORT", "9000"))

# Connect to the Docker ChromaDB server
client = chromadb.HttpClient(
    host=chromadb_host,
    port=chromadb_port,
    # Include token if authentication is enabled
    headers={"Authorization": "Bearer my-secret-token"}
)

# Verify the connection
print(f"Heartbeat: {client.heartbeat()}")
print(f"Version: {client.get_version()}")
