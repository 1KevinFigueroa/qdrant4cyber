from qdrant_client import QdrantClient

client = QdrantClient(host="localhost", port=6333, timeout=10)

try:
    info = client.get_collections()
    print(f"✅ Connected! Collections found: {info.collections}")
except Exception as e:
    print(f"❌ Connection failed: {e}")
