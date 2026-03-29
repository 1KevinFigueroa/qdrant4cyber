from pymilvus import (
    connections,
    FieldSchema, CollectionSchema, DataType,
    Collection
)
import random

# Connect to Milvus
connections.connect("default", host="localhost", port="19530")

# Define schema
fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=4)
]

schema = CollectionSchema(fields, description="test collection")

collection_name = "demo_collection"

# Create collection
collection = Collection(name=collection_name, schema=schema)

# Insert sample data
data = [[
    [random.random() for _ in range(4)]
    for _ in range(10)
]]

collection.insert(data)

# Create index
collection.create_index(
    field_name="embedding",
    index_params={
        "index_type": "IVF_FLAT",
        "metric_type": "L2",
        "params": {"nlist": 128}
    }
)

# Load collection into memory
collection.load()

# Search
query_vectors = [[random.random() for _ in range(4)]]

results = collection.search(
    data=query_vectors,
    anns_field="embedding",
    param={"metric_type": "L2", "params": {"nprobe": 10}},
    limit=3
)

# Print results
for hits in results:
    for hit in hits:
        print(f"ID: {hit.id}, Distance: {hit.distance}")