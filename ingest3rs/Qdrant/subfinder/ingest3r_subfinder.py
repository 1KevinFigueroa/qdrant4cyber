import json
import sys
from pathlib import Path
from typing import List

import numpy as np
from qdrant_client import QdrantClient, models


VECTOR_SIZE = 384


def embed_text(text: str) -> List[float]:
    """Dummy embedding function - replace with real embedding model."""
    rng = np.random.default_rng(abs(hash(text)) % (2**32))
    vec = rng.random(VECTOR_SIZE)
    return vec.astype(float).tolist()


def load_json(path: str):
    """Load JSON file with error handling."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"JSON file not found: {p}")
    with p.open("r", encoding="utf-8") as f:
        return json.load(f)


def ensure_collection(client: QdrantClient, collection_name: str):
    """Create collection if it doesn't exist."""
    if not client.collection_exists(collection_name):
        print(f"Creating collection '{collection_name}'")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=VECTOR_SIZE,
                distance=models.Distance.COSINE,
            ),
        )
    else:
        print(f"Using existing collection '{collection_name}'")


def upload_json_to_qdrant(json_path: str, collection_name: str):
    """Main function: read JSON and upload to Qdrant."""
    data = load_json(json_path)
    
    # Flexible data extraction (handles lists, objects, nested structures)
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        # Try common patterns from conversation history
        if "magictree" in data and "testdata" in data["magictree"]:
            items = data["magictree"]["testdata"].get("host", [])
        elif any(key in data for key in ["items", "data", "records"]):
            for key in ["items", "data", "records"]:
                if key in data and isinstance(data[key], list):
                    items = data[key]
                    break
            else:
                items = [data]
        else:
            items = [data]
    else:
        raise ValueError(f"Unsupported JSON root type: {type(data)}")
    
    print(f"Found {len(items)} items to process")
    
    client = QdrantClient("localhost", port=6333)
    ensure_collection(client, collection_name)
    
    points = []
    for idx, item in enumerate(items, 1):
        # Flexible text extraction based on conversation context
        text = (
            item.get("text") or
            item.get("content") or
            item.get("#text") or
            f"{item.get('Hostname', '')} {item.get('ip', '')}".strip() or
            f"{item.get('hostname', '')} {item.get('IP', item.get('#text', ''))}".strip() or
            str(item)
        )
        
        if not text.strip():
            print(f"Skipping item {idx}: no text content")
            continue
        
        vector = embed_text(text)
        point_id = item.get("id", idx)
        
        # Create payload from all fields except id/vector
        payload = {
            k: v for k, v in item.items() 
            if k not in ("id", "vector", "text")
        }
        
        points.append(
            models.PointStruct(
                id=point_id,
                vector=vector,
                payload=payload,
            )
        )
    
    if not points:
        print("No valid items to upload!")
        return
    
    print(f"Uploading {len(points)} points...")
    result = client.upsert(
        collection_name=collection_name,
        points=points,
        wait=True,
    )
    print(f"Upload complete! Result: {result}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        script = Path(sys.argv[0]).name
        print(f"Usage: python {script} input.json collection_name")
        print("Example: python script.py yandex.json yandex_hosts")
        sys.exit(1)
    
    json_file = sys.argv[1]
    collection = sys.argv[2]
    upload_json_to_qdrant(json_file, collection)