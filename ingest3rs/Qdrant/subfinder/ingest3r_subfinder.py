#!/usr/bin/env python3
import argparse
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
import numpy as np
from qdrant_client import QdrantClient, models

# ---------------- Configuration ---------------- #
DEFAULT_VECTOR_SIZE = 384
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 6333
DEFAULT_COLLECTION_NAME = "Subfinder_json"

def embed_text(text: str, vector_size: int = DEFAULT_VECTOR_SIZE) -> List[float]:
    """Dummy embedding function - replace with real embedding model."""
    rng = np.random.default_rng(abs(hash(text)) % (2**32))
    vec = rng.random(vector_size)
    return vec.astype(float).tolist()

def load_json(path: str) -> List[Dict[str, Any]]:
    """Load JSON file with error handling."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"❌ JSON file not found: {p}")
    
    try:
        with p.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        raise ValueError(f"❌ Error reading JSON: {e}")
    
    # Flexible data extraction (handles lists, objects, nested structures)
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        # Try common patterns
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
        raise ValueError(f"❌ Unsupported JSON root type: {type(data)}")
    
    print(f"✓ Loaded {len(items)} items from '{path}'")
    return items

def ensure_collection(client: QdrantClient, collection_name: str, vector_size: int):
    """Create/recreate collection."""
    try:
        if client.collection_exists(collection_name):
            print(f"Collection '{collection_name}' exists. Recreating...")
            client.delete_collection(collection_name)
        
        print(f"✓ Creating collection '{collection_name}' (vector_size={vector_size})")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=vector_size,
                distance=models.Distance.COSINE,
            ),
        )
    except Exception as e:
        print(f"❌ Collection creation failed: {e}")
        raise

def upload_json_to_qdrant(
    json_path: str, 
    collection_name: str,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    vector_size: int = DEFAULT_VECTOR_SIZE
):
    """Main function: read JSON and upload to Qdrant."""
    
    # Connect to Qdrant
    try:
        client = QdrantClient(host=host, port=port)
        print(f"✓ Connected to Qdrant at {host}:{port}")
    except Exception as e:
        print(f"❌ Cannot connect to Qdrant at {host}:{port}: {e}")
        print("Start Qdrant: docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant")
        return
    
    # Load data
    try:
        items = load_json(json_path)
    except Exception as e:
        print(e)
        return
    
    if not items:
        print("❌ No valid items to process!")
        return
    
    # Ensure collection exists
    try:
        ensure_collection(client, collection_name, vector_size)
    except Exception as e:
        return
    
    # Create points
    points = []
    skipped = 0
    
    for idx, item in enumerate(items, 1):
        # Flexible text extraction
        text = (
            item.get("text") or
            item.get("content") or
            item.get("#text") or
            f"{item.get('Hostname', '')} {item.get('ip', '')}".strip() or
            f"{item.get('hostname', '')} {item.get('IP', item.get('#text', ''))}".strip() or
            str(item)
        )
        
        if not text.strip():
            print(f"⚠️ Skipping item {idx}: no text content")
            skipped += 1
            continue
        
        vector = embed_text(text, vector_size)
        point_id = item.get("id", idx)
        
        # FIXED: Clean payload - no scan_tool, original_id → id
        payload = {
            "id": item.get("id", idx),  # Changed from original_id
            **{k: v for k, v in item.items() if k not in ("id", "vector", "text")}
        }
        
        points.append(
            models.PointStruct(
                id=point_id,
                vector=vector,
                payload=payload,
            )
        )
    
    if not points:
        print("❌ No valid points to upload!")
        return
    
    print(f"✓ Prepared {len(points)} points (skipped {skipped})")
    
    # Upload with batching
    batch_size = 100
    for i in range(0, len(points), batch_size):
        batch = points[i:i + batch_size]
        try:
            client.upsert(
                collection_name=collection_name,
                points=batch,
                wait=True,
            )
            print(f"✓ Uploaded batch {i//batch_size + 1} ({len(batch)} points)")
        except Exception as e:
            print(f"❌ Batch upload failed: {e}")
            return
    
    # Verify upload
    try:
        count = client.count(collection_name=collection_name)
        print(f"\n🎉 SUCCESS!")
        print(f"   Total points: {len(points)}")
        print(f"   Collection: '{collection_name}'")
        print(f"   Vector size: {vector_size}")
        print(f"   Qdrant verified: {count.count}")
        
        # Verify with scroll (FIXED tuple handling)
        sample_result = client.scroll(collection_name=collection_name, limit=2, with_payload=True)
        sample_points, _ = sample_result  # Unpack tuple: (points, next_offset)
        sample_ids = [p.id for p in sample_points]
        print(f"✅ Sample IDs: {sample_ids}")
        
    except Exception as e:
        print(f"ℹ️ Verification skipped: {e}")

# ---------------- CLI entrypoint ---------------- #
def main():
    parser = argparse.ArgumentParser(
        description="Upload ANY JSON to Qdrant (flexible data extraction)"
    )
    parser.add_argument("json_file", help="Path to JSON file")
    parser.add_argument(
        "collection", 
        nargs='?', 
        default=DEFAULT_COLLECTION_NAME,
        help=f"Qdrant collection name (default: {DEFAULT_COLLECTION_NAME})"
    )
    parser.add_argument(
        "--host", 
        default=DEFAULT_HOST, 
        help=f"Qdrant host (default: {DEFAULT_HOST})"
    )
    parser.add_argument(
        "--port", 
        type=int, 
        default=DEFAULT_PORT, 
        help=f"Qdrant port (default: {DEFAULT_PORT})"
    )
    parser.add_argument(
        "--vector-size",
        type=int,
        default=DEFAULT_VECTOR_SIZE,
        help=f"Vector dimension size (default: {DEFAULT_VECTOR_SIZE})"
    )
    
    args = parser.parse_args()
    
    upload_json_to_qdrant(
        json_path=args.json_file,
        collection_name=args.collection,
        host=args.host,
        port=args.port,
        vector_size=args.vector_size
    )

if __name__ == "__main__":
    main()