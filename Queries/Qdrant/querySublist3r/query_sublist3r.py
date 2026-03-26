#!/usr/bin/env python3
import argparse
from qdrant_client import QdrantClient
from qdrant_client.http import models


def connect_qdrant(url: str) -> QdrantClient:
    """Connect to local Qdrant HTTP API."""
    return QdrantClient(url=url)


def show_collection_info(client: QdrantClient, collection: str):
    """Print basic info about the collection."""
    info = client.get_collection(collection)
    print(f"Collection: {collection}")
    print(f"  Vector size: {info.config.params.vectors.size}")
    print(f"  Distance:    {info.config.params.vectors.distance}")
    print(f"  Status:      {info.status}")


def sample_relations(client: QdrantClient, collection: str, limit: int = 10):
    """Scroll a few points and print DNS relation info."""
    points, _ = client.scroll(
        collection_name=collection,
        limit=limit,
        with_payload=True,
        with_vectors=False,
    )

    print(f"\nSample {len(points)} DNS relation records:")
    for p in points:
        payload = p.payload or {}
        source = payload.get("source", "unknown")
        relation = payload.get("relation", "unknown")
        target = payload.get("target", "unknown")
        print(f"- ID: {p.id} | {source} --[{relation}]--> {target}")


def query_by_source_target(
    client: QdrantClient,
    collection: str,
    source: str | None,
    relation: str | None,
    target: str | None,
    limit: int = 50,
):
    """
    Query collection by payload fields:
      source, relation, target

    Any of source / relation / target can be omitted; only provided ones are filtered on.
    """
    must_conditions: list[models.FieldCondition] = []

    if source:
        must_conditions.append(
            models.FieldCondition(
                key="source",
                match=models.MatchValue(value=source),
            )
        )

    if relation:
        must_conditions.append(
            models.FieldCondition(
                key="relation",
                match=models.MatchValue(value=relation),
            )
        )

    if target:
        must_conditions.append(
            models.FieldCondition(
                key="target",
                match=models.MatchValue(value=target),
            )
        )

    if not must_conditions:
        print("\nNo filters provided (source / relation / target); nothing to query.")
        return

    flt = models.Filter(must=must_conditions)

    points, _ = client.scroll(
        collection_name=collection,
        limit=limit,
        with_payload=True,
        with_vectors=False,
        scroll_filter=flt,
    )

    print(f"\nQuery results (limit {limit}):")
    if not points:
        print("  No matches found.")
        return

    for p in points:
        payload = p.payload or {}
        src = payload.get("source", "unknown")
        rel = payload.get("relation", "unknown")
        dst = payload.get("target", "unknown")
        print(f"- ID: {p.id} | {src} --[{rel}]--> {dst}")


def main():
    parser = argparse.ArgumentParser(
        description="Query a Qdrant collection of DNS relations (source, relation, target)"
    )
    parser.add_argument(
        "collection",
        help="Qdrant collection name that stores DNS relation data",
    )
    parser.add_argument(
        "--url",
        default="http://localhost:6333",
        help="Qdrant URL (default: http://localhost:6333)",
    )
    parser.add_argument(
        "--source",
        help='Filter by "source" FQDN (e.g., yandex.ru)',
    )
    parser.add_argument(
        "--relation",
        default="ns_record",
        help='Filter by "relation" (default: ns_record)',
    )
    parser.add_argument(
        "--target",
        help='Filter by "target" FQDN (e.g., ns1.yandex.ru)',
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Max number of results to return (default: 50)",
    )
    args = parser.parse_args()

    client = connect_qdrant(args.url)

    # Basic info and sample
    show_collection_info(client, args.collection)
    sample_relations(client, args.collection)

    # Query if any filter provided
    if args.source or args.relation or args.target:
        query_by_source_target(
            client,
            args.collection,
            source=args.source,
            relation=args.relation,
            target=args.target,
            limit=args.limit,
        )


if __name__ == "__main__":
    main()
