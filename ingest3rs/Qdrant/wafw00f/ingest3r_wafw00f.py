import argparse
import json
import os
import random
import sys
from typing import List, Dict, Any, Optional

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

# ---------------- Helper functions ---------------- #

def generate_dummy_vector(size: int) -> List[float]:
    """
    Generate a dummy vector for each record.
    Replace this with a real embedding model in production.
    """
    return [random.uniform(-1.0, 1.0) for _ in range(size)]


def load_json(path: str) -> List[Dict[str, Any]]:
    """
    Load JSON file and ensure it is a list of dicts.
    """
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
    """
    Infer vector size from JSON records.
    - If a record has a 'vector' field that is a list of numbers, use its length.
    - Otherwise return None (will use CLI arg or default).
    """
    for r in records:
        vec = r.get("vector")
        if isinstance(vec, list) and vec and all(isinstance(x, (int, float)) for x in vec):
            return len(vec)
    return None


def save_upload_report(collection_name: str, points_count: int, output_json: Optional[str]) -> None:
    """Save upload summary to JSON file."""
    report = {
        "collection_name": collection_name,
        "points_uploaded": points_count,
        "timestamp": os.path.basename(output_json) if output_json else "no_output",
        "status": "success"
    }
    if output_json:
        os.makedirs(os.path.dirname(output_json) or '.', exist_ok=True)
        with open(output_json, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"✓ Upload report saved to: {output_json}")


# ---------------- Qdrant upload logic ---------------- #

def create_collection_if_needed(client: QdrantClient, name: str, vector_size: int) -> None:
    """Create a new collection with given name and vector size. Delete existing first."""
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
    input_file: str,
    collection_name: str,
    host: str,
    port: int,
    vector_size_override: Optional[int],
    output_json: Optional[str],
) -> None:
    """
    Main upload function with full CLI parameter support.
    """
    records = load_json(input_file)
    print(f"✓ Loaded {len(records)} records from {input_file}")

    # Determine vector size: CLI override > inferred > error
    inferred_size = infer_vector_size_from_records(records)
    if vector_size_override is not None:
        vector_size = vector_size_override
        print(f"✓ Using vector size from CLI: {vector_size}")
    elif inferred_size is not None:
        vector_size = inferred_size
        print(f"✓ Using inferred vector size: {vector_size}")
    else:
        raise ValueError("No vector size provided and none could be inferred from JSON data")

    qdrant_url = f"http://{host}:{port}"
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

        points.append(PointStruct(id=point_id, vector=vector, payload=record))

    op_info = client.upsert(collection_name=collection_name, points=points, wait=True)
    print(f"✓ Upsert completed: {op_info.status}")
    print(f"✓ Uploaded {len(points)} points to '{collection_name}'")

    if output_json:
        save_upload_report(collection_name, len(points), output_json)

    print("\nSample payloads:")
    for p in points[:3]:
        print(f"  ID={p.id}")


# ---------------- CLI entrypoint ---------------- #

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Upload JSON records to Qdrant vector database",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--output-json",
        help="Save upload report to JSON file"
    )
    parser.add_argument(
        "--host", 
        default="localhost",
        help="Qdrant host (default: localhost)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=6333,
        help="Qdrant port (default: 6333)"
    )
    parser.add_argument(
        "--vector-size",
        type=int,
        help="Vector dimension size (overrides inference)"
    )
    parser.add_argument(
        "input_file",
        help="Input JSON file path"
    )
    parser.add_argument(
        "collection",
        nargs="?",
        default="default_collection",
        help="Qdrant collection name (default: default_collection)"
    )

    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print(f"Error: Input file '{args.input_file}' not found", file=sys.stderr)
        sys.exit(1)

    if args.vector_size and args.vector_size <= 0:
        print("Error: --vector-size must be positive integer", file=sys.stderr)
        sys.exit(1)

    try:
        upload_json_to_qdrant(
            args.input_file,
            args.collection,
            args.host,
            args.port,
            args.vector_size,
            args.output_json,
        )
        print(f"\n✓ Done! Collection '{args.collection}' ready for queries.")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
