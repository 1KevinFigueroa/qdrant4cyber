#!/usr/bin/env python3
import argparse
import json
import os
import sys
from pathlib import Path
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
import numpy as np
import random
from typing import List, Dict, Any

# ---------------- Configuration ---------------- #
DEFAULT_VECTOR_SIZE = 384
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 6333
DEFAULT_COLLECTION_NAME = "sslscan_results"

def create_simple_embedding(text: str, dim: int = 128) -> List[float]:
    """Simple hash-based embedding for demo purposes."""
    vec = np.zeros(dim)
    for i, char in enumerate(text.lower()):
        if i >= dim:
            break
        vec[i] = (ord(char) % 256) / 255.0
    
    # Add slight random noise for unique vectors
    vec += np.random.normal(0, 0.01, dim)
    vec = np.clip(vec, -1.0, 1.0)
    
    return vec.tolist()

def upload_sslscan_to_qdrant(
    json_file: str, 
    collection_name: str = DEFAULT_COLLECTION_NAME,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    vector_size: int = DEFAULT_VECTOR_SIZE
):
    """Parse sslscan JSON and upload to Qdrant with full CLI options."""
    
    # Verify file exists
    if not os.path.exists(json_file):
        print(f"❌ SSLscan JSON file '{json_file}' not found.")
        return
    
    # Connect to Qdrant
    try:
        client = QdrantClient(host=host, port=port)
        print(f"✓ Connected to Qdrant at {host}:{port}")
    except Exception as e:
        print(f"❌ Cannot connect to Qdrant at {host}:{port}: {e}")
        print("Start Qdrant: docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant")
        return
    
    # Read JSON results
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            sslscan_data = json.load(f)
        if isinstance(sslscan_data, dict):
            sslscan_data = [sslscan_data]
    except Exception as e:
        print(f"❌ Error reading JSON: {e}")
        return
    
    print(f"✓ Loaded {len(sslscan_data)} sslscan entries")
    
    # Create/recreate collection
    try:
        if client.collection_exists(collection_name):
            print(f"Collection '{collection_name}' exists. Recreating...")
            client.delete_collection(collection_name)
        
        client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
        )
        print(f"✓ Collection '{collection_name}' created (vector_size={vector_size})")
        
    except Exception as e:
        print(f"❌ Collection creation failed: {e}")
        return
    
    # Prepare points for upload
    points = []
    
    for entry in sslscan_data:
        entry_id = entry.get("id", len(points) + 1)
        
        # Create comprehensive text summary for embedding
        protocols = list(entry.get('protocols', {}).keys()) if entry.get('protocols') else []
        ciphers_count = len(entry.get('ciphers', []))
        cert = entry.get('certificate', {})
        subject = cert.get('subject', 'N/A')
        
        summary = (
            f"{entry.get('target', 'N/A')} "
            f"{entry.get('ip', 'N/A')} "
            f"TLS protocols: {', '.join(protocols)} "
            f"Ciphers: {ciphers_count} "
            f"Subject: {subject}"
        )
        
        # Generate embedding with correct dimension
        vector = create_simple_embedding(summary, vector_size)
        
        # Build complete payload
        payload = {
            "entry_id": entry_id,
            "scan_tool": "sslscan",
            "ip": entry.get("ip"),
            "target": entry.get("target"),
            "port": entry.get("port", 443),
            "sni": entry.get("sni"),
            "protocols": entry.get("protocols", {}),
            "ciphers_count": ciphers_count,
            "weak_protocols_count": sum(1 for k, v in entry.get("protocols", {}).items() 
                                      if v == "enabled" and any(weak in k for weak in ["TLSv1.0", "TLSv1.1"])),
            "certificate_subject": subject,
            "certificate_issuer": cert.get("issuer"),
            "certificate_altnames_count": len(cert.get("altnames", [])),
            "summary": summary,
            **cert  # Include full certificate data
        }
        
        point = PointStruct(
            id=entry_id,
            vector=vector,
            payload=payload
        )
        points.append(point)
    
    # Upload in batches
    batch_size = 50
    for i in range(0, len(points), batch_size):
        batch = points[i:i + batch_size]
        client.upsert(collection_name=collection_name, points=batch, wait=True)
        print(f"✓ Uploaded batch {i//batch_size + 1} ({len(batch)} points)")
    
    # Verify upload
    count = client.count(collection_name=collection_name)
    print(f"\n🎉 SUCCESS!")
    print(f"   Total points: {len(points)}")
    print(f"   Collection: '{collection_name}'")
    print(f"   Vector size: {vector_size}")
    print(f"   Qdrant verified: {count.count}")
    
    # FIXED: Correct scroll() handling - returns (points_list, next_offset)
    try:
        sample_result = client.scroll(collection_name=collection_name, limit=2, with_payload=True)
        sample_points, _ = sample_result  # Unpack tuple: (points, next_offset)
        sample_ids = [p.id for p in sample_points]
        print(f"✅ Sample IDs: {sample_ids}")
    except Exception as e:
        print(f"ℹ️ Sample retrieval skipped: {e}")

def main():
    parser = argparse.ArgumentParser(
        description="Upload sslscan JSON to Qdrant (1 entry = 1 point)"
    )
    parser.add_argument("json_file", help="Path to sslscan JSON file")
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
    
    upload_sslscan_to_qdrant(
        json_file=args.json_file,
        collection_name=args.collection,
        host=args.host,
        port=args.port,
        vector_size=args.vector_size
    )

if __name__ == "__main__":
    main()