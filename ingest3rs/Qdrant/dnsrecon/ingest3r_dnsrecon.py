#!/usr/bin/env python3
import argparse
import json
import os
import random
import sys
import time
from typing import List, Dict, Any, Optional

from qdrant_client import QdrantClient, models


def load_dnsrecon_json(path: str) -> List[Dict[str, Any]]:
    """Load ALL DNSRecon JSON content - handles ANY structure."""
    print(f"DEBUG: Loading complete DNSRecon JSON from {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    records = []
    
    # Handle ALL possible JSON structures
    if isinstance(data, list):
        records = data
    elif isinstance(data, dict):
        # Single record
        if any(key in data for key in ['host', 'name', 'address', 'ip']):
            records = [data]
        # Multiple records in dict values
        else:
            for key, value in data.items():
                if isinstance(value, (list, dict)):
                    if isinstance(value, list):
                        records.extend(value)
                    else:
                        records.append(value)
    else:
        raise ValueError("Invalid JSON format")

    print(f"DEBUG: Extracted {len(records)} total records")
    if records:
        print(f"DEBUG: First record keys: {list(records[0].keys())}")
    return records


def make_dnsrecon_vector(dim: int = 128) -> List[float]:
    """Generate dummy vector for DNSRecon records."""
    return [random.uniform(-1.0, 1.0) for _ in range(dim)]


def save_upload_report(collection_name: str, points_count: int, input_file: str, output_json: Optional[str]) -> None:
    """Save detailed upload summary."""
    report = {
        "collection_name": collection_name,
        "input_file": os.path.basename(input_file),
        "total_records_processed": points_count,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "status": "success"
    }
    if output_json:
        os.makedirs(os.path.dirname(output_json) or '.', exist_ok=True)
        with open(output_json, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"✓ Upload report saved: {output_json}")


def ensure_collection(client: QdrantClient, collection_name: str, dim: int) -> None:
    """Create or recreate Qdrant collection."""
    print(f"DEBUG: Checking collection '{collection_name}'...")
    
    if client.collection_exists(collection_name):
        print(f"DEBUG: Deleting existing '{collection_name}'...")
        client.delete_collection(collection_name)
        time.sleep(1)

    print(f"DEBUG: Creating collection with dim={dim}...")
    client.create_collection(
        collection_name=collection_name,
        vectors_config=models.VectorParams(
            size=dim,
            distance=models.Distance.COSINE,
        ),
    )
    
    time.sleep(1)
    if client.collection_exists(collection_name):
        info = client.get_collection(collection_name)
        print(f"✓ Collection '{collection_name}' created (dim={info.config.params.vectors.size})")
    else:
        raise RuntimeError(f"Failed to create collection '{collection_name}'")


def create_dnsrecon_point(record: Dict[str, Any], dim: int, index: int) -> models.PointStruct:
    """Create Qdrant PointStruct - STORES COMPLETE ORIGINAL RECORD."""
    
    # Use integer index as stable ID
    point_id = index
    
    # IDENTIFY record type for better payloads
    host = record.get("host") or record.get("name") or record.get("domain") or str(index)
    ip = record.get("address") or record.get("ip") or record.get("ptr") or None
    
    # COMPLETE record preserved + indexed fields
    payload = {
        # Original COMPLETE record - NOTHING LOST
        "complete_original_record": record,
        
        # Indexed fields for fast filtering/searching
        "host": host,
        "address": ip,
        "record_type": record.get("type") or record.get("rrtype") or "unknown",
        "ttl": record.get("ttl"),
        "source": "dnsrecon",
        "index": index,
        
        # Common DNSRecon fields (all optional)
        **{k: v for k, v in record.items() if k not in ['complete_original_record']}
    }
    
    print(f"DEBUG: Point {point_id}: host='{host}', keys={len(payload)} fields")
    
    return models.PointStruct(
        id=point_id,
        vector=make_dnsrecon_vector(dim),
        payload=payload
    )


def upload_dnsrecon_records(
    client: QdrantClient,
    collection_name: str,
    records: List[Dict[str, Any]],
    dim: int,
    output_json: Optional[str],
    input_file: str
) -> None:
    """Upload ALL DNSRecon records as Qdrant points."""
    print(f"DEBUG: Processing ALL {len(records)} records...")
    points: List[models.PointStruct] = []
    skipped = 0

    for i, record in enumerate(records):
        try:
            point = create_dnsrecon_point(record, dim, i)
            points.append(point)
        except Exception as e:
            print(f"Warning: Skipped record {i}: {e}")
            skipped += 1
            continue

    print(f"DEBUG: Created {len(points)} points, skipped {skipped}")
    
    if not points:
        raise ValueError("No valid records to upload")

    print(f"DEBUG: Uploading {len(points)} points...")
    result = client.upsert(collection_name=collection_name, points=points, wait=True)
    print(f"DEBUG: Upsert result: {result}")

    time.sleep(2)
    count = client.count(collection_name)
    print(f"✓ VERIFIED: {count.count} points uploaded to '{collection_name}'")

    save_upload_report(collection_name, len(points), input_file, output_json)

    print(f"\n🎉 SUCCESS - Sample records:")
    for p in points[:3]:
        host = p.payload.get('host', 'N/A')
        ip = p.payload.get('address', 'N/A')
        rectype = p.payload.get('record_type', 'N/A')
        print(f"  ID={p.id} | {host} | {ip} | {rectype}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Upload COMPLETE DNSRecon JSON results to Qdrant",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument("--host", default="localhost", help="Qdrant host")
    parser.add_argument("--port", type=int, default=6333, help="Qdrant port")
    parser.add_argument("--output-json", help="Save upload report")
    parser.add_argument("--vector-size", type=int, default=128, help="Vector dimension")
    parser.add_argument("input_file", help="DNSRecon JSON input file")
    parser.add_argument("collection", nargs="?", default="dnsrecon_results", help="Collection name")

    args = parser.parse_args()

    if not os.path.exists(args.input_file):
        print(f"Error: '{args.input_file}' not found", file=sys.stderr)
        sys.exit(1)

    if args.vector_size <= 0:
        print("Error: --vector-size must be positive", file=sys.stderr)
        sys.exit(1)

    try:
        print("=== DNSRecon → Qdrant (COMPLETE IMPORT) ===")
        records = load_dnsrecon_json(args.input_file)
        
        client = QdrantClient(f"http://{args.host}:{args.port}")
        print(f"✓ Connected: http://{args.host}:{args.port}")
        
        ensure_collection(client, args.collection, args.vector_size)
        upload_dnsrecon_records(client, args.collection, records, args.vector_size, 
                              args.output_json, args.input_file)

        print(f"\n✅ ALL DATA UPLOADED to '{args.collection}'!")
        print(f"   Browse: http://{args.host}:{args.port}/collections/{args.collection}")
        
    except Exception as e:
        print(f"\n✗ FAILED: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
