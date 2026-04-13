#!/usr/bin/env python3
import json
import os
import argparse
import random
import sys
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

# ---------------- Configuration ---------------- #

DEFAULT_VECTOR_SIZE = 384
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 6333
DEFAULT_COLLECTION_NAME = "Nmap_results"


# ---------------- Helper functions ---------------- #

def read_json_file(file_path: str) -> List[Dict[str, Any]]:
    """Read JSON file and return list of records."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if isinstance(data, dict):
        return [data]
    return data


def create_dummy_vector(size: int) -> List[float]:
    """Generate dummy vector for single-point embedding."""
    return [random.uniform(-1.0, 1.0) for _ in range(size)]


# ---------------- Qdrant upload logic ---------------- #

def upload_to_qdrant(
    points: List[PointStruct],
    host: str,
    port: int,
    collection_name: str,
    vector_size: int,
) -> None:
    """Upload points to Qdrant collection with specified vector size."""
    client = QdrantClient(host=host, port=port)
    print(f"✓ Connected to Qdrant at {host}:{port}")

    try:
        client.recreate_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
        )
        print(f"✓ Collection '{collection_name}' created with vector size {vector_size}")
    except Exception as e:
        print(f"❌ Collection creation failed: {e}")
        return

    client.upsert(collection_name=collection_name, points=points)
    print(f"✓ Uploaded {len(points)} points to '{collection_name}'")

    count = client.count(collection_name=collection_name)
    print(f"📊 Collection '{collection_name}' contains {count.count} points")


def process_json_to_single_vector(
    json_file_path: str,
    collection_name: str,
    vector_size: int,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
) -> None:
    """Process JSON file into single dummy vector and upload to Qdrant."""
    
    records = read_json_file(json_file_path)
    print(f"✓ Loaded {len(records)} records from {json_file_path}")

    # Combine all data into single text representation
    combined_text = ""
    payloads = []
    
    for i, record in enumerate(records):
        record_text = json.dumps(record, ensure_ascii=False, indent=2)
        combined_text += f"\n--- Record {i+1} ---\n{record_text}\n"
        payloads.append({
            "id": i,
            "content": record_text,
            "original_data": record
        })
    
    print(f"✓ Combined text length: {len(combined_text)} characters")

    embedding = create_dummy_vector(vector_size)
    print(f"✓ Generated dummy embedding of length {len(embedding)}")

    point = PointStruct(
        id=0,
        vector=embedding,
        payload={
            "total_records": len(records),
            "combined_content": combined_text,
            "records": payloads
        }
    )

    upload_to_qdrant([point], host, port, collection_name, vector_size)
    print(f"✅ Single-vector Qdrant collection '{collection_name}' ready!")


# ---------------- CLI entrypoint ---------------- #

def main():
    parser = argparse.ArgumentParser(
        description="Convert JSON file to single-vector Qdrant collection (dummy vectors)"
    )
    parser.add_argument("json_file", help="Path to JSON file")
    parser.add_argument(
        "collection", 
        nargs='?', 
        default=DEFAULT_COLLECTION_NAME,
        help=f"Qdrant collection name (default: {DEFAULT_COLLECTION_NAME})"
    )
    parser.add_argument(
        "--host", 
        default=DEFAULT_HOST, 
        help=f"Qdrant host (default: {DEFAULT_HOST})"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=DEFAULT_PORT, 
        help=f"Qdrant port (default: {DEFAULT_PORT})"
    )
    parser.add_argument(
        "--vector-size",
        type=int,
        default=DEFAULT_VECTOR_SIZE,
        help=f"Vector dimension size (default: {DEFAULT_VECTOR_SIZE})"
    )
    
    args = parser.parse_args()
    
    if not os.path.exists(args.json_file):
        print(f"❌ JSON file '{args.json_file}' not found.")
        sys.exit(1)
    
    try:
        process_json_to_single_vector(
            json_file_path=args.json_file,
            collection_name=args.collection,
            vector_size=args.vector_size,
            host=args.host,
            port=args.port,
        )
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
