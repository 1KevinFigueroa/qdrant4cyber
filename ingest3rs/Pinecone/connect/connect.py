from pinecone.grpc import PineconeGRPC, GRPCClientConfig
from pinecone import ServerlessSpec
import requests


# Initialize a client.
# API key is required, but the value does not matter.
# Host and port of the Pinecone Local instance
# is required when starting without indexes. 
pc = PineconeGRPC(
    api_key="pclocal", 
    host="http://localhost:5080" 
)
