#!/usr/bin/env python3
import argparse
from qdrant_client import QdrantClient
from qdrant_client.http import models


def connect_qdrant(url: str) -> QdrantClient:
    """Connect to local Qdrant HTTP API."""
    return QdrantClient(url=url)  # e.g., http://localhost:6333[web:236]


def show_collection_info(client: QdrantClient, collection: str):
    """Print basic info about the Nmap collection."""
    info = client.get_collection(collection)
    print(f"Collection: {collection}")
    print(f"  Vectors size: {info.config.params.vectors.size}")
    print(f"  Distance: {info.config.params.vectors.distance}")
    print(f"  Status: {info.status}")


def sample_points(client: QdrantClient, collection: str, limit: int = 5):
    """Scroll a few Nmap points and print basic fields."""
    points, _ = client.scroll(
        collection_name=collection,
        limit=limit,
        with_payload=True,
        with_vectors=False,
    )
    print(f"\nSample {len(points)} Nmap records:")
    for p in points:
        payload = p.payload or {}
        host = payload.get("host") or payload.get("ip") or "unknown"
        ports = payload.get("ports") or payload.get("port") or []
        print(f"- ID: {p.id} | Host: {host} | Ports: {ports}")


def search_by_host(client: QdrantClient, collection: str, host: str, limit: int = 10):
    """
    Example: filter by host/IP in payload.
    Adjust 'host' / 'ip' key to match your stored Nmap schema.
    """
    flt = models.Filter(
        must=[
            models.FieldCondition(
                key="host",  # or "ip" depending on your payload
                match=models.MatchValue(value=host),
            )
        ]
    )

    results = client.scroll(
        collection_name=collection,
        limit=limit,
        with_payload=True,
        with_vectors=False,
        scroll_filter=flt,
    )[0]

    print(f"\nResults for host = {host}:")
    if not results:
        print("  No matches found.")
        return

    for p in results:
        payload = p.payload or {}
        ports = payload.get("ports") or payload.get("port") or []
        print(f"- ID: {p.id} | Host: {host} | Ports: {ports}")


def main():
    parser = argparse.ArgumentParser(
        description="Connect to local Qdrant and inspect an Nmap collection"
    )
    parser.add_argument(
        "collection",
        help="Qdrant collection name that stores Nmap data (e.g., nmap_yandex)",
    )
    parser.add_argument(
        "--url",
        default="http://localhost:6333",
        help="Qdrant URL (default: http://localhost:6333)",
    )
    parser.add_argument(
        "--host",
        help="Optional host/IP to filter by in payload (key 'host' or 'ip')",
    )
    args = parser.parse_args()

    client = connect_qdrant(args.url)
    show_collection_info(client, args.collection)
    sample_points(client, args.collection)

    if args.host:
        search_by_host(client, args.collection, args.host)


if __name__ == "__main__":
    main()
