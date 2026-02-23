import chromadb

# Connect to the Docker ChromaDB server
client = chromadb.HttpClient(
    host="localhost",
    port=8000,
    # Include token if authentication is enabled
    headers={"Authorization": "Bearer my-secret-token"}
)

# Verify the connection
print(f"Heartbeat: {client.heartbeat()}")
print(f"Version: {client.get_version()}")
