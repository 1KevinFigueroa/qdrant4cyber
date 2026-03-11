from pinecone.grpc import PineconeGRPC
import requests
# Initialize a client.
# API key is required, but the value does not matter.
# Host and port of the Pinecone Local instance
# is required when starting without indexes. 

pc = PineconeGRPC(
    api_key="pclocal",
    host="http://localhost:5081"
)

try:
    indexes = pc.list_indexes()
    print("Pinecone is alive:", indexes)
except Exception as e:
    print("Pinecone not responding:", e)

