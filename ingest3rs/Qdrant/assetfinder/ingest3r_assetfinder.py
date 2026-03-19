#!/usr/bin/env python3
"""
Assetfinder JSON → Qdrant ingester

Example JSON item:
{
    "id": 1,
    "line_number": 1,
    "domain": "yandex.ru",
    "raw_line": "yandex.ru"
}
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
    """Simple deterministic dummy vector for each assetfinder entry."""
    # You can later replace this with a real embedding (e.g., based on domain)
    return [0.0] * size


def load_assetfinder_json(path: str) -> List[Dict[str, Any]]:
    """
    Load Assetfinder JSON file and normalize to a list of entries.

    Supports:
    - A list of objects
    - A single object
    """
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

    print(f"✓ Loaded {len(entries)} assetfinder entry(ies) from '{path}'")
    return entries


def upload_assetfinder_to_qdrant(
    json_path: str,
    collection: str,
    vector_size: int = DEFAULT_VECTOR_SIZE,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
) -> None:
    """Read Assetfinder JSON and upload to Qdrant."""
    # Connect to Qdrant
    client = QdrantClient(host=host, port=port)
    print(f"✓ Connected to Qdrant at {host}:{port}")

    entries = load_assetfinder_json(json_path)
    if not entries:
        print("❌ No assetfinder entries to upload")
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

    points: List[PointStruct] = []
    for idx, item in enumerate(entries, start=1):
        point_id = item.get("id", idx)

        payload = {
            "id": point_id,
            "domain": item.get("domain"),
            "raw_line": item.get("raw_line"),
            "line_number": item.get("line_number"),
            # Preserve any extra keys if present
            **{k: v for k, v in item.items() if k not in ("id", "vector")}
        }

        points.append(
            PointStruct(
                id=point_id,
                vector=make_dummy_vector(vector_size),
                payload=payload,
            )
        )

    if not points:
        print("❌ No valid points to upload")
        return

    client.upsert(collection_name=collection, points=points, wait=True)
    print(f"✅ Uploaded {len(points)} assetfinder entries to '{collection}'")

    # Quick verification
    count = client.count(collection_name=collection)
    print(f"📊 Verified: {count.count} points in collection '{collection}'")


def main():
    parser = argparse.ArgumentParser(
        description="Ingest assetfinder JSON results into Qdrant"
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
        help="Path to assetfinder JSON output file",
    )

    args = parser.parse_args()

    upload_assetfinder_to_qdrant(
        json_path=args.json_path,
        collection=args.collection,
        vector_size=args.vector_size,
    )


if __name__ == "__main__":
    main()