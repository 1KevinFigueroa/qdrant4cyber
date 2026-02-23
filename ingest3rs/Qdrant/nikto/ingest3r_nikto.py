#!/usr/bin/env python3
import json
import os
import argparse
import random
from typing import List, Dict, Any

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

# ---------------- Configuration ---------------- #

QDRANT_URL = "http://localhost:6333"
DEFAULT_VECTOR_SIZE = 384


# ---------------- Helper functions ---------------- #

def generate_dummy_vector(size: int) -> List[float]:
    """Generate a dummy vector for each record."""
    return [random.uniform(-1.0, 1.0) for _ in range(size)]


def load_json(path: str) -> List[Dict[str, Any]]:
    """Load JSON file and ensure it is a list of dicts."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        raise ValueError("JSON root must be an array or object")

    records = [obj for obj in data if isinstance(obj, dict)]
    if not records:
        raise ValueError("No valid objects found in JSON")

    return records


def infer_vector_size_from_records(records: List[Dict[str, Any]]) -> int:
    """Infer vector size from JSON records."""
    for r in records:
        vec = r.get("vector")
        if isinstance(vec, list) and vec and all(isinstance(x, (int, float)) for x in vec):
            return len(vec)
    return DEFAULT_VECTOR_SIZE


# ---------------- Qdrant upload logic ---------------- #

def create_collection_if_needed(client: QdrantClient, name: str, vector_size: int) -> None:
    """Create a new collection with given name and vector size (deletes existing)."""
    if client.collection_exists(name):
        client.delete_collection(name)

    client.create_collection(
        collection_name=name,
        vectors_config=VectorParams(
            size=vector_size,
            distance=Distance.COSINE,
        ),
    )
    print(f"✓ Created collection '{name}' with vector size {vector_size}")


def upload_json_to_qdrant(
    json_path: str,
    collection_name: str,
    vector_size: int = None,
    qdrant_url: str = QDRANT_URL,
) -> None:
    """Load JSON, determine vector size, create collection, and upload points."""
    
    records = load_json(json_path)
    print(f"✓ Loaded {len(records)} records from {json_path}")

    if vector_size is None:
        vector_size = infer_vector_size_from_records(records)
        print(f"✓ Inferred vector size: {vector_size}")
    else:
        print(f"✓ Using specified vector size: {vector_size}")

    client = QdrantClient(url=qdrant_url)
    print(f"✓ Connected to Qdrant at {qdrant_url}")

    create_collection_if_needed(client, collection_name, vector_size)

    points: List[PointStruct] = []
    for idx, record in enumerate(records, start=1):
        point_id = record.get("id", idx)
        record_vector = record.get("vector")

        if isinstance(record_vector, list) and len(record_vector) == vector_size:
            vector = record_vector
        else:
            vector = generate_dummy_vector(vector_size)

        points.append(
            PointStruct(
                id=point_id,
                vector=vector,
                payload=record,
            )
        )

    op_info = client.upsert(collection_name=collection_name, points=points, wait=True)
    print(f"✓ Upsert completed: {op_info.status}")
    print(f"✓ Uploaded {len(points)} points to '{collection_name}'")

    print("\nSample payloads:")
    for p in points[:3]:
        print(f"  ID={p.id}  payload={p.payload}")


# ---------------- CLI entrypoint ---------------- #

def main():
    parser = argparse.ArgumentParser(description="Upload JSON data to Qdrant collection")
    parser.add_argument("collection_name", help="Name of the Qdrant collection")
    parser.add_argument("json_file", help="Path to JSON file")
    parser.add_argument(
        "--vector-size",
        type=int,
        default=DEFAULT_VECTOR_SIZE,
        help=f"Vector size (default: {DEFAULT_VECTOR_SIZE}, overrides inference)",
    )
    args = parser.parse_args()

    if not os.path.exists(args.json_file):
        print(f"❌ JSON file '{args.json_file}' not found.")
        sys.exit(1)

    try:
        upload_json_to_qdrant(
            json_path=args.json_file,
            collection_name=args.collection_name,
            vector_size=args.vector_size,
        )
        print(f"\n✅ Done! Query Qdrant collection: {args.collection_name}")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import sys
    main()