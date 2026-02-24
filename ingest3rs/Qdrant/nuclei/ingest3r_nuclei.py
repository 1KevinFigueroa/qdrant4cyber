#!/usr/bin/env python3
import json
import os
import argparse
import random
import sys
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct

# ---------------- Configuration ---------------- #
DEFAULT_VECTOR_SIZE = 384
DEFAULT_HOST = "localhost"
DEFAULT_PORT = 6333
DEFAULT_COLLECTION_NAME = "nuclei_entries"

# ---------------- Helper functions ---------------- #

def read_nuclei_json(file_path: str) -> List[Dict[str, Any]]:
    """Read Nuclei JSON file and return list of entries."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, dict):
            return [data]
        return data
    except Exception as e:
        print(f"❌ Error reading JSON: {e}")
        sys.exit(1)

def create_dummy_vector(size: int) -> List[float]:
    """Generate unique dummy vector for each entry."""
    random.seed()  # Ensure unique randomness per call
    return [random.uniform(-1.0, 1.0) for _ in range(size)]

# ---------------- Qdrant upload logic ---------------- #

def upload_nuclei_json_to_qdrant(
    entries: List[Dict[str, Any]],
    collection_name: str,
    vector_size: int,
    host: str,
    port: int
) -> None:
    """Upload each JSON entry as individual Qdrant point."""
    client = QdrantClient(host=host, port=port)
    print(f"✓ Connected to Qdrant at {host}:{port}")

    # Create/recreate collection
    try:
        client.recreate_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
        )
        print(f"✓ Collection '{collection_name}' created (vector_size={vector_size})")
    except Exception as e:
        print(f"❌ Collection creation failed: {e}")
        return

    # Convert each entry to Qdrant PointStruct
    points = []
    for entry in entries:
        entry_id = entry["id"]
        
        # Create unique vector for this entry
        vector = create_dummy_vector(vector_size)
        
        # Build complete payload from entry
        payload = {
            "entry_id": entry["id"],
            "entry_type": entry["entry_type"],
            "scan_tool": "nuclei"
        }
        
        # Add finding-specific fields
        if entry["entry_type"] == "finding":
            payload.update({
                "template": entry.get("template"),
                "protocol": entry.get("protocol"),
                "severity": entry.get("severity"),
                "target": entry.get("target"),
                "extra_info": entry.get("extra_info")
            })
        
        # Add log-specific fields
        elif entry["entry_type"] == "log":
            payload.update({
                "log_level": entry.get("log_level"),
                "message": entry.get("message")
            })
        
        # Create PointStruct
        point = PointStruct(
            id=entry_id,  # Use original entry ID
            vector=vector,
            payload=payload
        )
        points.append(point)

    # Batch upload all points
    client.upsert(collection_name=collection_name, points=points, wait=True)
    
    # Verify upload
    count = client.count(collection_name=collection_name)
    findings_count = len([e for e in entries if e["entry_type"] == "finding"])
    
    print(f"🎉 SUCCESS!")
    print(f"   Total points: {len(points)}")
    print(f"   Findings: {findings_count}")
    print(f"   Logs: {len(entries) - findings_count}")
    print(f"   Qdrant verified: {count.count}")
    
    # Show sample points
    sample = client.scroll(collection_name=collection_name, limit=3, with_payload=True)
    print(f"✅ Sample point IDs: {[p.id for p in sample.points]}")

# ---------------- CLI entrypoint ---------------- #

def main():
    parser = argparse.ArgumentParser(
        description="Upload Nuclei JSON to Qdrant (1 entry = 1 point)"
    )
    parser.add_argument("json_file", help="Path to Nuclei JSON file")
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
    
    if not os.path.exists(args.json_file):
        print(f"❌ JSON file '{args.json_file}' not found.")
        sys.exit(1)
    
    try:
        # Read JSON
        entries = read_nuclei_json(args.json_file)
        print(f"✓ Loaded {len(entries)} entries from '{args.json_file}'")
        
        # Count findings vs logs
        findings = len([e for e in entries if e["entry_type"] == "finding"])
        print(f"✓ Findings: {findings}, Logs: {len(entries) - findings}")
        
        # Upload to Qdrant
        upload_nuclei_json_to_qdrant(
            entries=entries,
            collection_name=args.collection,
            vector_size=args.vector_size,
            host=args.host,
            port=args.port
        )
        
        print(f"\n✅ COMPLETE: '{args.collection}' ready for search!")
        
    except KeyboardInterrupt:
        print("\n❌ Interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()