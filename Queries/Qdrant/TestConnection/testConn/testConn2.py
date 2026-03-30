from qdrant_client import QdrantClient
import json

# ANSI Color Codes for Terminal Output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RESET = "\033[0m"

def print_separator(title=""):
    """Print a separator line with title"""
    width = 60
    if title:
        print(f"{BLUE}{'─' * (width // 2)} {title} {'─' * ((width - len(title) - 1) // 2)}{RESET}")
    else:
        print(f"{BLUE}{'═' * width}{RESET}\n")

# Connect to Qdrant Client
print_separator("QDRANT CONNECTION TEST")
try:
    client = QdrantClient(host="localhost", port=6333, timeout=10)
    
    # Get collections info
    info = client.get_collections()
    
    print(f"{GREEN}✅ Connection Status: SUCCESS{RESET}")
    print(f"📍 Server: {BLUE}localhost:6333{RESET}")
    print(f"🔢 Collections Found: {YELLOW}{len(info.collections)}{RESET}\n")
    
    # Print details of each collection
    if info.collections:
        for i, collection in enumerate(info.collections, 1):
            print(f"{GREEN}├─ Collection #{i}{RESET}: {collection.name}")
            print(f"   └─ Status: {collection.status.value}")
    
    print_separator("CONNECTION DETAILS")

except Exception as e:
    print(f"{RED}❌ Connection Failed{RESET}\n")
    print(f"📍 Server: {BLUE}localhost:6333{RESET}")
    print(f"⚠️  Error: {RED}{str(e)}{RESET}")

print_separator()
