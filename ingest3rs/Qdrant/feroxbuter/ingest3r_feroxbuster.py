#!/usr/bin/env python3
"""
ingest3r_feroxbuster - Feroxbuster JSON → Qdrant ingester

Example feroxbuster JSON entry:
{
  "id": 1,
  "line_number": 2,
  "original_json": {...},
  "type": "response",
  "url": "https://23andme.com/store/car",
  "path": "/store/car",
  "status": 302,
  ...
}

CLI: ingest3r_feroxbuster.py --collection COLLECTION [--vector-size VECTOR_SIZE] json_path
"""

import argparse
import json
import os
from typing import List, Dict, Any

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 6333
DEFAULT_VECTOR_SIZE = 384


def make_dummy_vector(size: int = DEFAULT_VECTOR_SIZE) -> List[float]:
    """Dummy vector for feroxbuster entries."""
    return [0.0] * size


def load_feroxbuster_json(path: str) -> List[Dict[str, Any]]:
    """Load feroxbuster JSON file (list of entries or single entry)."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"❌ JSON file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        entries = data
    elif isinstance(data, dict):
        entries = [data]
    else:
        raise ValueError("❌ Unsupported JSON root type (expected object or array)")

    print(f"✓ Loaded {len(entries)} feroxbuster entries from '{path}'")
    return entries


def upload_feroxbuster_to_qdrant(
    json_path: str,
    collection: str,
    vector_size: int = DEFAULT_VECTOR_SIZE,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
) -> None:
    """Upload feroxbuster JSON to Qdrant."""
    # Connect to Qdrant
    client = QdrantClient(host=host, port=port)
    print(f"✓ Connected to Qdrant at {host}:{port}")

    # Load JSON
    entries = load_feroxbuster_json(json_path)
    if not entries:
        print("❌ No feroxbuster entries to upload")
        return

    # Recreate collection
    if client.collection_exists(collection):
        print(f"Collection '{collection}' exists. Recreating...")
        client.delete_collection(collection)

    client.create_collection(
        collection_name=collection,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )
    print(f"✓ Created collection '{collection}' (vector_size={vector_size})")

    # Create points
    points = []
    for idx, entry in enumerate(entries, start=1):
        point_id = entry.get("id", idx)

        # Extract key fields
        payload = {
            "id": point_id,
            "type": entry.get("type"),
            "url": entry.get("url"),
            "path": entry.get("path"),
            "original_url": entry.get("original_url"),
            "wildcard": entry.get("wildcard"),
            "status": entry.get("status"),
            "method": entry.get("method"),
            "content_length": entry.get("content_length"),
            "line_count": entry.get("line_count"),
            "word_count": entry.get("word_count"),
            "extension": entry.get("extension"),
            "truncated": entry.get("truncated"),
            "timestamp": entry.get("timestamp"),
            "line_number": entry.get("line_number"),
            
            # Preserve full original_json if present
            "original_json": entry.get("original_json"),
            
            # Preserve headers (flatten common ones)
            "headers": entry.get("headers", {}),
        }

        # Merge any additional fields
        for k, v in entry.items():
            if k not in payload:
                payload[k] = v

        point = PointStruct(
            id=point_id,
            vector=make_dummy_vector(vector_size),
            payload=payload,
        )
        points.append(point)

    if not points:
        print("❌ No valid points to upload")
        return

    # Batch upload
    batch_size = 100
    for i in range(0, len(points), batch_size):
        batch = points[i:i + batch_size]
        client.upsert(collection_name=collection, points=batch, wait=True)
        print(f"✓ Uploaded batch {i//batch_size + 1} ({len(batch)} entries)")

    print(f"✅ Uploaded {len(points)} feroxbuster entries to '{collection}'")

    # Status summary
    status_counts = {}
    for entry in entries:
        status = entry.get("status")
        if status:
            status_counts[status] = status_counts.get(status, 0) + 1
    
    print("📊 Status breakdown:")
    for status, count in sorted(status_counts.items()):
        print(f"   {status}: {count}")

    # Verification
    count = client.count(collection_name=collection)
    print(f"📈 Verified: {count.count} points in '{collection}'")


def main():
    parser = argparse.ArgumentParser(
        description="ingest3r_feroxbuster: Feroxbuster JSON → Qdrant (1 entry = 1 point)"
    )
    parser.add_argument(
        "--collection",
        required=True,
        help="Qdrant collection name",
    )
    parser.add_argument(
        "--vector-size",
        type=int,
        default=DEFAULT_VECTOR_SIZE,
        help=f"Vector dimension size (default: {DEFAULT_VECTOR_SIZE})",
    )
    parser.add_argument(
        "json_path",
        help="Path to feroxbuster JSON file",
    )

    args = parser.parse_args()

    upload_feroxbuster_to_qdrant(
        json_path=args.json_path,
        collection=args.collection,
        vector_size=args.vector_size,
    )


if __name__ == "__main__":
    main()