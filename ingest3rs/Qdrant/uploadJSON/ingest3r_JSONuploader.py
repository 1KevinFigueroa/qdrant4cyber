#!/usr/bin/env python3
import argparse
import json
import os
import sys
import random
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

# ---------------- Configuration ---------------- #
DEFAULT_VECTOR_SIZE = 384
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 6333
DEFAULT_COLLECTION_NAME = "universal_json"

# ---------------- Helper functions ---------------- #

def generate_dummy_vector(size: int) -> List[float]:
    """Generate a dummy vector for each record."""
    return [random.uniform(-1.0, 1.0) for _ in range(size)]

def load_json(path: str) -> List[Dict[str, Any]]:
    """Load JSON file and ensure it is a list of dicts."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"❌ JSON file not found: {path}")
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        raise ValueError(f"❌ Error reading JSON: {e}")

    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        raise ValueError("❌ JSON root must be an array or object")

    records = [obj for obj in data if isinstance(obj, dict)]
    if not records:
        raise ValueError("❌ No valid objects found in JSON")

    print(f"✓ Loaded {len(records)} records from '{path}'")
    return records

def infer_vector_size_from_records(records: List[Dict[str, Any]]) -> int:
    """Infer vector size from JSON records or use default."""
    for r in records:
        vec = r.get("vector")
        if isinstance(vec, list) and vec and all(isinstance(x, (int, float)) for x in vec):
            return len(vec)
    return DEFAULT_VECTOR_SIZE

# ---------------- Qdrant upload logic ---------------- #

def create_collection_if_needed(client: QdrantClient, name: str, vector_size: int) -> None:
    """Create a new collection (delete if exists)."""
    try:
        if client.collection_exists(name):
            print(f"Collection '{name}' exists. Recreating...")
            client.delete_collection(name)

        print(f"✓ Created collection '{name}' with vector size {vector_size}")
        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE,
            ),
        )
    except Exception as e:
        print(f"❌ Collection creation failed: {e}")
        raise

def upload_json_to_qdrant(
    json_path: str,
    collection_name: str,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    vector_size: int = DEFAULT_VECTOR_SIZE,
) -> None:
    """Main function: read JSON, infer/create vectors, upload to Qdrant."""
    
    # Connect to Qdrant
    try:
        client = QdrantClient(host=host, port=port)
        print(f"✓ Connected to Qdrant at {host}:{port}")
    except Exception as e:
        print(f"❌ Cannot connect to Qdrant at {host}:{port}: {e}")
        print("Start Qdrant: docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant")
        return
    
    # Load data
    try:
        records = load_json(json_path)
    except Exception as e:
        print(e)
        return
    
    if not records:
        print("❌ No valid records to process!")
        return
    
    # Use provided vector_size or infer
    final_vector_size = vector_size if vector_size else infer_vector_size_from_records(records)
    print(f"✓ Using vector size: {final_vector_size}")

    # Create collection
    try:
        create_collection_if_needed(client, collection_name, final_vector_size)
    except Exception as e:
        return

    # Create points
    points = []
    for idx, record in enumerate(records, start=1):
        point_id = record.get("id", idx)

        # Use existing vector or generate dummy
        record_vector = record.get("vector")
        if isinstance(record_vector, list) and len(record_vector) == final_vector_size:
            vector = record_vector
        else:
            vector = generate_dummy_vector(final_vector_size)

        # FIXED: Clean payload structure
        payload = {
            "id": point_id,
            **{k: v for k, v in record.items() if k not in ("id", "vector", "text")}
        }

        points.append(
            PointStruct(
                id=point_id,
                vector=vector,
                payload=payload,
            )
        )

    if not points:
        print("❌ No valid points to create!")
        return

    # Batch upload
    batch_size = 100
    for i in range(0, len(points), batch_size):
        batch = points[i:i + batch_size]
        try:
            op_info = client.upsert(
                collection_name=collection_name,
                points=batch,
                wait=True,
            )
            print(f"✓ Uploaded batch {i//batch_size + 1} ({len(batch)} points)")
        except Exception as e:
            print(f"❌ Batch upload failed: {e}")
            return

    print(f"✅ Uploaded {len(points)} points to '{collection_name}'")

    # Verify with scroll (FIXED)
    try:
        count = client.count(collection_name=collection_name)
        print(f"📊 Verified: {count.count} points in collection")
        
        sample_result = client.scroll(
            collection_name=collection_name,
            limit=3,
            with_payload=True,
            with_vectors=False
        )
        sample_points, _ = sample_result  # FIXED: Unpack tuple
        
        print("🔍 Sample points:")
        for p in sample_points:
            print(f"   ID {p.id}: {p.payload}")
            
    except Exception as e:
        print(f"ℹ️ Verification skipped: {e}")

# ---------------- CLI entrypoint ---------------- #

def main():
    parser = argparse.ArgumentParser(
        description="Universal JSON → Qdrant uploader (handles any JSON structure)"
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
        help=f"Vector dimension size (default: {DEFAULT_VECTOR_SIZE}, 0=auto-infer)"
    )
    
    args = parser.parse_args()
    
    upload_json_to_qdrant(
        json_path=args.json_file,
        collection_name=args.collection,
        host=args.host,
        port=args.port,
        vector_size=args.vector_size if args.vector_size > 0 else None
    )
    
    print(f"\n🎉 COMPLETE: '{args.collection}' ready for search!")

if __name__ == "__main__":
    main()