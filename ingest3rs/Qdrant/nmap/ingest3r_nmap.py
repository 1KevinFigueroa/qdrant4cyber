import json
import qdrant_client
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any

def read_json_file(file_path: str) -> List[Dict[str, Any]]:
    """Read JSON file and return list of records."""
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # Handle both single object and array
    if isinstance(data, dict):
        return [data]
    return data

def create_single_vector_embedding(text: str, model_name: str = "all-MiniLM-L6-v2") -> List[float]:
    """Create embedding for entire concatenated content."""
    model = SentenceTransformer(model_name)
    embedding = model.encode(text)
    return embedding.tolist()

def upload_to_qdrant(points: List[PointStruct], host: str = "localhost", port: int = 6333, 
                    collection_name: str = "yandex_nikto_results", vector_size: int = 384):
    """Upload points to new Qdrant collection."""
    client = qdrant_client.QdrantClient(host=host, port=port)
    
    # Create collection if not exists
    client.recreate_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
    )
    
    # Upsert all points
    client.upsert(
        collection_name=collection_name,
        points=points
    )
    print(f"Uploaded {len(points)} points to Qdrant collection '{collection_name}'")

def main(json_file_path: str, host: str = "localhost", port: int = 6333):
    # Step 1: Read JSON file
    records = read_json_file(json_file_path)
    print(f"Loaded {len(records)} records from {json_file_path}")
    
    # Step 2: Combine all data into single text representation
    combined_text = ""
    payloads = []
    
    for i, record in enumerate(records):
        # Convert record to string representation
        record_text = json.dumps(record, ensure_ascii=False, indent=2)
        combined_text += f"\n--- Record {i+1} ---\n{record_text}\n"
        
        # Store original record as payload
        payloads.append({
            "id": i,
            "content": record_text,
            "original_data": record
        })
    
    print(f"Combined text length: {len(combined_text)} characters")
    
    # Step 3: Create single embedding for entire content
    embedding = create_single_vector_embedding(combined_text)
    
    # Step 4: Create point with single vector + all payloads
    point = PointStruct(
        id=0,  # Single point ID
        vector=embedding,
        payload={
            "total_records": len(records),
            "combined_content": combined_text,
            "records": payloads
        }
    )
    
    # Step 5: Upload to Qdrant
    upload_to_qdrant([point], host, port)
    
    print("✅ Successfully created single-vector Qdrant collection with all JSON data!")

if __name__ == "__main__":
    # Usage example
    json_file_path = "yandex_nikto.json"  # Replace with your JSON file path
    main(json_file_path)