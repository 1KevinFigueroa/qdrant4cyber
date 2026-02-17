import json
import random
import argparse
from typing import List

from qdrant_client import QdrantClient, models


QDRANT_URL = "http://localhost:6333"
VECTOR_SIZE = 4  # adjust if you later use real embeddings


def load_json(path: str) -> List[dict]:
    """Load list of records from JSON file."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)  # expects a JSON array
    if not isinstance(data, list):
        raise ValueError("Top-level JSON must be a list of objects")
    return data


def make_dummy_vector(dim: int) -> List[float]:
    """Create a random vector as placeholder."""
    return [random.random() for _ in range(dim)]


def ensure_collection(client: QdrantClient, collection_name: str):
    """Create collection if it does not exist."""
    collections = client.get_collections().collections
    existing = {c.name for c in collections}
    if collection_name in existing:
        return

    client.recreate_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(
            size=VECTOR_SIZE,
            distance=models.Distance.COSINE,
        ),
    )


def upload_records(client: QdrantClient, records: List[dict], collection_name: str):
    points = []
    for rec in records:
        # required fields
        rec_id = rec["id"]
        source = rec.get("source")
        relation = rec.get("relation")
        target = rec.get("target")

        payload = {
            "source": source,
            "relation": relation,
            "target": target,
        }

        point = models.PointStruct(
            id=rec_id,
            vector=make_dummy_vector(VECTOR_SIZE),
            payload=payload,
        )
        points.append(point)

    if not points:
        return

    client.upsert(
        collection_name=collection_name,
        points=points,
        wait=True,
    )


def main():
    parser = argparse.ArgumentParser(
        description="Load DNS relation JSON into local Qdrant"
    )
    parser.add_argument(
        "json_path",
        help="Path to JSON file containing a list of records",
    )
    parser.add_argument(
        "--collection",
        required=True,
        help="Name of the Qdrant collection to use/store data in",
    )
    args = parser.parse_args()

    records = load_json(args.json_path)
    client = QdrantClient(url=QDRANT_URL)

    ensure_collection(client, args.collection)
    upload_records(client, records, args.collection)
    print(f"Uploaded {len(records)} records into collection '{args.collection}'")


if __name__ == "__main__":
    main()