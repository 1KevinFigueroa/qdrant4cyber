#!/usr/bin/env python3
import json
import argparse
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
import numpy as np

DEFAULT_VECTOR_SIZE = 384
DEFAULT_QDRANT_URL = "http://localhost:6333"

def load_dirb_json(json_file: str) -> List[Dict[str, Any]]:
    """Load parsed dirb JSON file."""
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if isinstance(data, dict):
        return data.get('results', [])
    if isinstance(data, list):
        return data
    return []

def create_dummy_vector(dim: int) -> List[float]:
    """Generate a dummy vector for dirb entries (replace with real embeddings later)."""
    return list(np.random.rand(dim).astype(np.float32))

def import_to_qdrant(
    json_file: str,
    collection_name: str,
    vector_size: int,
    qdrant_url: str = DEFAULT_QDRANT_URL,
) -> None:
    """Import dirb results into a Qdrant collection with chosen vector size."""
    client = QdrantClient(url=qdrant_url)
    print(f"✓ Connected to Qdrant at {qdrant_url}")

    try:
        client.recreate_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
        )
        print(f"✓ Collection '{collection_name}' created with vector size {vector_size}")
    except Exception as e:
        print(f"❌ Failed to create/recreate collection: {e}")
        return

    entries = load_dirb_json(json_file)
    if not entries:
        print("❌ No entries found in JSON file.")
        return
    print(f"✓ Loaded {len(entries)} dirb results from '{json_file}'")

    points: List[PointStruct] = []
    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            entry = {"value": entry}

        point_id = entry.get('id') or entry.get('line_number') or i + 1
        payload = {k: v for k, v in entry.items() if k not in ['id', 'line_number']}
        payload['raw_line'] = entry.get('raw_line', '')

        point = PointStruct(
            id=point_id,
            vector=create_dummy_vector(vector_size),
            payload=payload,
        )
        points.append(point)

    client.upsert(collection_name=collection_name, points=points, wait=True)
    print(f"✓ Successfully imported {len(points)} points into '{collection_name}'")

    count = client.count(collection_name=collection_name)
    print(f"📊 Collection '{collection_name}' now contains {count.count} points.")

def main():
    parser = argparse.ArgumentParser(
        description="Import dirb JSON results into a Qdrant collection."
    )
    parser.add_argument("json_file", help="Path to dirb JSON file (exported from parser)")
    parser.add_argument("collection", help="Name of the Qdrant collection")
    parser.add_argument(
        "--url",
        default=DEFAULT_QDRANT_URL,
        help="Qdrant service URL (default: http://localhost:6333)",
    )
    parser.add_argument(
        "--vector-size",
        type=int,
        default=DEFAULT_VECTOR_SIZE,
        help=f"Vector dimension size (default: {DEFAULT_VECTOR_SIZE})",
    )

    args = parser.parse_args()
    import_to_qdrant(args.json_file, args.collection, args.vector_size, args.url)

if __name__ == "__main__":
    main()