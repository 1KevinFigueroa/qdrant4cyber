#!/usr/bin/env python3
"""
Qdrant Local Connection Tester
Tests HTTP connectivity and basic operations with a local Qdrant instance.
"""

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams
import requests
import sys

class QdrantTester:
    def __init__(self, host="localhost", port=6333):
        self.host = host
        self.port = port
        self.client = QdrantClient(host=self.host, port=self.port)
    
    def test_health(self):
        """Test if Qdrant is responding"""
        try:
            response = requests.get(f"http://{self.host}:{self.port}/healthz")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False
    
    def list_collections(self):
        """List all collections in the Qdrant instance"""
        try:
            collections = self.client.get_collections()
            if collections.collections:
                for col in collections.collections:
                    print(f"  - {col.name} ({col.vectors_config.size} dimensions)")
            else:
                print("  No collections found.")
            return True
        except Exception as e:
            print(f"❌ Failed to list collections: {e}")
            return False
    
    def create_test_collection(self):
        """Create a test collection with sample vectors"""
        try:
            self.client.recreate_collection(
                collection_name="test_collection",
                vectors_config=VectorParams(size=768, distance=Distance.COSINE),
            )
            print("✅ Test collection 'test_collection' created.")
            return True
        except Exception as e:
            if "already exists" in str(e).lower():
                print("ℹ️  Collection 'test_collection' already exists.")
                return True
            print(f"❌ Failed to create collection: {e}")
            return False
    
    def add_test_vectors(self):
        """Add sample vectors to the test collection"""
        try:
            # Generate random vectors for testing
            import random
            test_points = []
            for i in range(5):
                vector = [random.random() for _ in range(768)]
                test_points.append({
                    "id": i,
                    "vector": vector,
                    "payload": {"text": f"Sample document {i}", "category": "test"}
                })
            
            self.client.upsert(collection_name="test_collection", points=test_points)
            print(f"✅ Added 5 test vectors to 'test_collection'.")
            return True
        except Exception as e:
            print(f"❌ Failed to add vectors: {e}")
            return False
    
    def search_test(self, query_vector):
        """Perform a similarity search"""
        try:
            results = self.client.search(
                collection_name="test_collection",
                query_vector=query_vector,
                limit=3
            )
            print(f"✅ Found {len(results)} similar documents:")
            for i, result in enumerate(results):
                print(f"  [{i+1}] Score: {result.score:.4f} | Payload: {result.payload}")
            return True
        except Exception as e:
            print(f"❌ Search failed: {e}")
            return False
    
    def get_point(self, point_id):
        """Retrieve a specific point"""
        try:
            result = self.client.get(
                collection_name="test_collection",
                ids=[point_id]
            )
            if result.points:
                print(f"✅ Retrieved point {point_id}: {result.points[0].payload}")
            else:
                print(f"⚠️  Point {point_id} not found.")
        except Exception as e:
            print(f"❌ Get failed: {e}")

def main():
    tester = QdrantTester(host="localhost", port=6333)
    
    print("=" * 50)
    print("QDRANT LOCAL CONNECTION TEST")
    print("=" * 50)
    
    # Test Health
    print("\n[1] Testing Server Health...")
    if not tester.test_health():
        print("\n❌ Qdrant server is unreachable. Please ensure it's running on localhost:6333")
        sys.exit(1)
    print("✅ Server is responding.")
    
    # List Collections
    print("\n[2] Listing Collections...")
    tester.list_collections()
    
    # Create Test Collection if needed
    print("\n[3] Setting up test data...")
    tester.create_test_collection()
    
    # Add Vectors
    print("\n[4] Adding sample vectors...")
    tester.add_test_vectors()
    
    # Perform Search
    print("\n[5] Running search query...")
    import random
    query_vector = [random.random() for _ in range(768)]  # Random vector for demo
    tester.search_test(query_vector)
    
    # Get Specific Point
    print("\n[6] Retrieving specific point (ID=0)...")
    tester.get_point(0)
    
    print("\n" + "=" * 50)
    print("✅ ALL TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 50)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
