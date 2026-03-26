import sys

try:
    from pinecone.grpc import PineconeGRPC
    from pinecone import Pinecone
except Exception as e:
    print("Pinecone import failed:", e)
    print("Fix your environment with:")
    print("  pip uninstall -y pinecone-client")
    print('  pip install "pinecone[grpc]"')
    sys.exit(1)
# Initialize a client.
# API key is required, but the value does not matter.
# Host and port of the Pinecone Local instance
# is required when starting without indexes. 

hosts = ["http://localhost:5080", "http://localhost:5081"]
last_error = None

for host in hosts:
    pc = PineconeGRPC(
        api_key="pclocal",
        host=host
    )
    try:
        indexes = pc.list_indexes()
        print(f"Pinecone is alive via {host}:", indexes)
        sys.exit(0)
    except Exception as e:
        last_error = e

# Fallback for single-index container mode (pinecone-index image).
# That mode does not support list_indexes() and will return 404 for control-plane calls.
for host in ["http://localhost:5081", "http://localhost:5080"]:
    try:
        pc = Pinecone(api_key="pclocal")
        index = pc.Index(host=host)
        stats = index.describe_index_stats()
        print(f"Pinecone index endpoint is alive via {host}:", stats)
        print("Note: list_indexes() is unavailable in pinecone-index (single-index) mode.")
        sys.exit(0)
    except Exception as e:
        last_error = e

print("Pinecone not responding:", last_error)
print("Hint: if using ghcr.io/pinecone-io/pinecone-index:latest, test the index endpoint on http://localhost:5081")

