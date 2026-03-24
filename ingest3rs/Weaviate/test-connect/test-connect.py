import weaviate
import uuid
import weaviate.classes as wvc
from weaviate.classes.config import Configure, DataType, Property
from weaviate.exceptions import WeaviateGRPCUnavailableError

# Connect to local Weaviate
try:
    client = weaviate.connect_to_local(
        additional_config=wvc.init.AdditionalConfig(
            timeout=wvc.init.Timeout(init=30)
        )
    )
except WeaviateGRPCUnavailableError as exc:
    raise SystemExit(
        "Could not connect to Weaviate gRPC at localhost:50051. "
        "Ensure Weaviate is running and port 50051 is exposed (e.g. Docker ports 8080 and 50051)."
    ) from exc

# Define a class (collection)
class_name = "TestDocument"

# Clean up if exists
if client.collections.exists(class_name):
    client.collections.delete(class_name)

# Create schema
client.collections.create(
    class_name,
    vector_config=Configure.Vectors.text2vec_transformers(),
    properties=[
        Property(name="content", data_type=DataType.TEXT)
    ],
)

print("[+] Schema created")

collection = client.collections.get(class_name)

# Insert sample data
data = [
    {"content": "Weaviate is a vector database"},
    {"content": "MiniLM is a lightweight embedding model"},
    {"content": "Docker makes deployment easy"},
]

for item in data:
    collection.data.insert(properties=item, uuid=str(uuid.uuid4()))

print("[+] Data inserted")

# Query using semantic search
query = "What is a vector database?"

result = collection.query.near_text(
    query=query,
    limit=2,
    return_properties=["content"],
)

print("\n[+] Query Results:")
for obj in result.objects:
    print("-", obj.properties["content"])

client.close()
