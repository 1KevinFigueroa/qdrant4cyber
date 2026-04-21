#!/usr/bin/env python3
import argparse
import json
import os
import sys
from typing import List, Dict, Any

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

DEFAULT_HOST = "localhost"
DEFAULT_PORT = 6333
DEFAULT_VECTOR_SIZE = 128


def make_dummy_vector(size: int = DEFAULT_VECTOR_SIZE) -> List[float]:
    """Simple dummy vector for each DNSMap entry (replace with real embeddings later)."""
    return [0.0] * size


def load_dnsmap_json(path: str) -> List[Dict[str, Any]]:
    """Load DNSMap JSON file and return a list of result entries."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"❌ JSON file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        if "results" in data and isinstance(data["results"], list):
            items = data["results"]
        elif "records" in data and isinstance(data["records"], list):
            items = data["records"]
        elif "data" in data and isinstance(data["data"], list):
            items = data["data"]
        elif "items" in data and isinstance(data["items"], list):
            items = data["items"]
        else:
            items = [data]
    else:
        raise ValueError("❌ Unsupported JSON root type (expected list or object)")

    print(f"✓ Loaded {len(items)} DNSMap entries from '{path}'")
    return items


def upload_dnsmap_to_qdrant(
    json_path: str,
    collection: str,
    vector_size: int = DEFAULT_VECTOR_SIZE,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
) -> None:
    """Read DNSMap JSON and upload to local Qdrant."""
    client = QdrantClient(host=host, port=port)
    print(f"✓ Connected to Qdrant at {host}:{port}")

    records = load_dnsmap_json(json_path)
    if not records:
        print("❌ No entries to upload")
        return

    if client.collection_exists(collection):
        print(f"Collection '{collection}' exists. Recreating...")
        client.delete_collection(collection)

    client.create_collection(
        collection_name=collection,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )
    print(f"✓ Created collection '{collection}' (vector_size={vector_size})")

    points: List[PointStruct] = []
    for idx, item in enumerate(records, start=1):
        if not isinstance(item, dict):
            item = {"value": item}

        point_id = item.get("id", idx)

        payload = {
            "id": point_id,
            "domain": item.get("domain"),
            "ip": item.get("ip"),
            "source": "dnsmap",
            **{k: v for k, v in item.items() if k != "id"},
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

    client.upsert(
        collection_name=collection,
        points=points,
        wait=True,
    )
    print(f"✅ Uploaded {len(points)} DNSMap entries to '{collection}'")

    count = client.count(collection_name=collection)
    print(f"📊 Verified: {count.count} points in collection '{collection}'")


def main():
    parser = argparse.ArgumentParser(
        description="Ingest DNSMap JSON results into Qdrant"
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
        "--host",
        default=DEFAULT_HOST,
        help=f"Qdrant host (default: {DEFAULT_HOST})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Qdrant port (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "json_path",
        help="Path to DNSMap JSON output file",
    )

    args = parser.parse_args()

    upload_dnsmap_to_qdrant(
        json_path=args.json_path,
        collection=args.collection,
        vector_size=args.vector_size,
        host=args.host,
        port=args.port,
    )


if __name__ == "__main__":
    main()