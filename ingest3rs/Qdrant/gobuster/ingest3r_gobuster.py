#!/usr/bin/env python3
"""
ingest3r_gobuster - Gobuster JSON → Qdrant ingester

Reads gobuster JSON (from gobuster_to_json.py):
{
  "vector_size": 384,
  "total_entries": 25,
  "entries": [...]
}

CLI: ingest3r_gobuster.py --collection COLLECTION [--vector-size VECTOR_SIZE] json_path
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
    """Dummy vector matching recorded vector_size."""
    return [0.0] * size


def load_gobuster_json(path: str) -> tuple[List[Dict[str, Any]], int]:
    """Load gobuster JSON and extract entries + vector_size."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"❌ JSON file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Extract entries and vector_size
    entries = data.get("entries", [])
    vector_size = data.get("vector_size", DEFAULT_VECTOR_SIZE)
    
    print(f"✓ Loaded {len(entries)} gobuster entries from '{path}'")
    print(f"✓ Vector size: {vector_size}")
    return entries, vector_size


def upload_gobuster_json_to_qdrant(
    json_path: str,
    collection: str,
    vector_size: int = DEFAULT_VECTOR_SIZE,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
) -> None:
    """Upload gobuster JSON to Qdrant."""
    # Connect to Qdrant
    client = QdrantClient(host=host, port=port)
    print(f"✓ Connected to Qdrant at {host}:{port}")

    # Load gobuster JSON
    entries, file_vector_size = load_gobuster_json(json_path)
    if not entries:
        print("❌ No gobuster entries to upload")
        return

    # Use CLI vector_size or file vector_size
    final_vector_size = vector_size or file_vector_size
    print(f"✓ Using vector size: {final_vector_size}")

    # Recreate collection
    if client.collection_exists(collection):
        print(f"Collection '{collection}' exists. Recreating...")
        client.delete_collection(collection)

    client.create_collection(
        collection_name=collection,
        vectors_config=VectorParams(size=final_vector_size, distance=Distance.COSINE),
    )
    print(f"✓ Created collection '{collection}' (vector_size={final_vector_size})")

    # Create Qdrant points
    points = []
    for idx, entry in enumerate(entries, start=1):
        # Use existing ID or assign sequential
        point_id = entry.get("id") or idx
        
        payload = {
            "id": point_id,
            "path": entry.get("path"),
            "status": entry.get("status"),
            "size": entry.get("size"),
            "redirect_url": entry.get("redirect_url"),
            "line_number": entry.get("line_number"),
            "raw_line": entry.get("raw_line"),
            # Preserve all original fields
            **{k: v for k, v in entry.items() if k not in ("id", "vector")}
        }

        point = PointStruct(
            id=point_id,
            vector=make_dummy_vector(final_vector_size),
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

    print(f"✅ Uploaded {len(points)} gobuster entries to '{collection}'")

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
        description="ingest3r_gobuster: Gobuster JSON → Qdrant (1 entry = 1 point)"
    )
    parser.add_argument(
        "--collection",
        required=True,
        help="Qdrant collection name",
    )
    parser.add_argument(
        "--vector-size",
        type=int,
        default=0,  # 0 = use file's vector_size
        help=f"Vector dimension size (0=use file default: {DEFAULT_VECTOR_SIZE})",
    )
    parser.add_argument(
        "json_path",
        help="Path to gobuster JSON file (from gobuster_to_json.py)",
    )

    args = parser.parse_args()

    upload_gobuster_json_to_qdrant(
        json_path=args.json_path,
        collection=args.collection,
        vector_size=args.vector_size,
    )


if __name__ == "__main__":
    main()