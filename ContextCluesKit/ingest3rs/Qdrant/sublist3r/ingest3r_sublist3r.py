#!/usr/bin/env python3
import argparse
import json
import os
import sys
import random
from typing import List, Dict, Any
from qdrant_client import QdrantClient, models

# ---------------- Configuration ---------------- #
DEFAULT_VECTOR_SIZE = 384
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 6333
DEFAULT_COLLECTION_NAME = "subdomains"

def load_subdomains_json(path: str) -> List[Dict[str, Any]]:
    """Load subdomains JSON file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"❌ JSON file not found: {path}")
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        raise ValueError(f"❌ Error reading JSON: {e}")
    
    if isinstance(data, list):
        return data
    elif isinstance(data, dict) and "results" in data:
        return data["results"]
    else:
        raise ValueError("❌ Expected list of domains or {'results': [...]}")
    
    print(f"✓ Loaded {len(data)} domains from '{path}'")
    return data

def make_dummy_vector(dim: int = DEFAULT_VECTOR_SIZE) -> List[float]:
    """Dummy vector (replace with sentence-transformer embeddings later)."""
    return [random.uniform(-1.0, 1.0) for _ in range(dim)]

def ensure_collection(client: QdrantClient, collection_name: str, dim: int):
    """Create/recreate collection."""
    try:
        if client.collection_exists(collection_name):
            print(f"Collection '{collection_name}' exists. Recreating...")
            client.delete_collection(collection_name)
        
        print(f"✓ Creating collection '{collection_name}' (vector_size={dim})")
        client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=dim,
                distance=models.Distance.COSINE,
            ),
        )
        return True
    except Exception as e:
        print(f"❌ Collection creation failed: {e}")
        return False

def upload_subdomains(
    client: QdrantClient,
    collection_name: str,
    domains: List[Dict[str, Any]],
    dim: int,
):
    """Upload subdomains as Qdrant points."""
    points = []
    skipped = 0
    
    for domain_entry in domains:
        # Use 'id' field or generate from line_number/index
        point_id = domain_entry.get("id") or domain_entry.get("line_number")
        if not point_id:
            skipped += 1
            continue
        
        # FIXED: Clean payload - no scan_tool, original_id → id
        payload = {
            "id": point_id,  # Changed from original_id pattern
            "domain": domain_entry.get("domain"),
            "raw_line": domain_entry.get("raw_line", ""),
            "line_number": domain_entry.get("line_number"),
            **{k: v for k, v in domain_entry.items() if k not in ("id", "vector", "text")}
        }
        
        points.append(
            models.PointStruct(
                id=point_id,
                vector=make_dummy_vector(dim),
                payload=payload,
            )
        )
    
    if not points:
        print("❌ No valid domains to upload")
        return
    
    print(f"✓ Prepared {len(points)} points (skipped {skipped})")
    
    # Batch upload
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
    
    print(f"✅ Uploaded {len(points)} subdomains to '{collection_name}'")

def verify_upload(client: QdrantClient, collection_name: str):
    """Verify collection contents (FIXED scroll handling)."""
    try:
        count = client.count(collection_name=collection_name)
        print(f"📊 Verified: {count.count} points in '{collection_name}'")
        
        # FIXED: Proper scroll tuple unpacking
        sample_result = client.scroll(
            collection_name=collection_name,
            limit=3,
            with_payload=True,
            with_vectors=False,
        )
        sample_points, _ = sample_result  # Unpack tuple: (points, next_offset)
        
        print("🔍 Sample points:")
        for p in sample_points:
            domain = p.payload.get('domain', 'N/A')
            print(f"   ID {p.id}: {domain}")
            
    except Exception as e:
        print(f"ℹ️ Verification skipped: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Upload subdomains JSON to Qdrant (1 domain = 1 point)"
    )
    parser.add_argument("json_file", help="Path to subdomains JSON file")
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
    
    # Connect to Qdrant first (validate connection)
    try:
        client = QdrantClient(host=args.host, port=args.port)
        print(f"✓ Connected to Qdrant at {args.host}:{args.port}")
    except Exception as e:
        print(f"❌ Cannot connect to Qdrant: {e}")
        print("Start Qdrant: docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant")
        sys.exit(1)
    
    # Load data
    try:
        domains = load_subdomains_json(args.json_file)
    except Exception as e:
        print(e)
        sys.exit(1)
    
    # Upload
    if ensure_collection(client, args.collection, args.vector_size):
        upload_subdomains(client, args.collection, domains, args.vector_size)
        verify_upload(client, args.collection)
        print(f"\n🎉 COMPLETE: '{args.collection}' ready!")
    else:
        print("❌ Upload failed - check collection creation")

if __name__ == "__main__":
    main()