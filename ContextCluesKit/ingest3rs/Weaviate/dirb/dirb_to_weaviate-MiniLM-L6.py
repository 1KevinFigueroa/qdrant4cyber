#!/usr/bin/env python3

import argparse
import json
from urllib.parse import urlparse

import weaviate
from weaviate.classes.config import Property, DataType, Configure
from weaviate.util import generate_uuid5

# =========================================================
# ARGS
# =========================================================

parser = argparse.ArgumentParser(
    description="Ingest DIRB JSON results into Weaviate"
)

parser.add_argument(
    "input_file",
    help="Path to the DIRB results JSON file"
)

parser.add_argument(
    "--host", default="localhost",
    help="Weaviate host (default: localhost)"
)

parser.add_argument(
    "--port", type=int, default=8080,
    help="Weaviate HTTP port (default: 8080)"
)

parser.add_argument(
    "--grpc-port", type=int, default=50051,
    help="Weaviate gRPC port (default: 50051)"
)

parser.add_argument(
    "--collection", default="DirbFinding",
    help="Weaviate collection name (default: DirbFinding)"
)

args = parser.parse_args()

# =========================================================
# CONFIG
# =========================================================

WEAVIATE_HOST = args.host
WEAVIATE_PORT = args.port
WEAVIATE_GRPC_PORT = args.grpc_port

CLASS_NAME = args.collection

INPUT_FILE = args.input_file

# =========================================================
# CONNECT
# =========================================================

client = weaviate.connect_to_local(
    host=WEAVIATE_HOST,
    port=WEAVIATE_PORT,
    grpc_port=WEAVIATE_GRPC_PORT,
)

print("[+] Connected to Weaviate")

# =========================================================
# CREATE COLLECTION
# =========================================================

existing = client.collections.list_all()

if CLASS_NAME not in existing:

    client.collections.create(
        name=CLASS_NAME,

	vector_config=Configure.Vectorizer.text2vec_transformers(),

        properties=[

            Property(
                name="url",
                data_type=DataType.TEXT
            ),

            Property(
                name="path",
                data_type=DataType.TEXT
            ),

            Property(
                name="host",
                data_type=DataType.TEXT
            ),

            Property(
                name="finding_type",
                data_type=DataType.TEXT
            ),

            Property(
                name="raw_line",
                data_type=DataType.TEXT
            ),

            Property(
                name="http_code",
                data_type=DataType.INT
            ),

            Property(
                name="response_size",
                data_type=DataType.INT
            ),

            Property(
                name="scan_start_time",
                data_type=DataType.TEXT
            ),

            Property(
                name="wordlist",
                data_type=DataType.TEXT
            ),

            Property(
                name="directory_listable",
                data_type=DataType.BOOL
            ),
        ]
    )

    print(f"[+] Created collection: {CLASS_NAME}")

else:
    print(f"[+] Collection already exists: {CLASS_NAME}")

# =========================================================
# LOAD DATA
# =========================================================

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

print(f"[+] Loaded {len(data)} records")

collection = client.collections.get(CLASS_NAME)

# =========================================================
# TRACK SCAN METADATA
# =========================================================

current_start_time = ""
current_wordlist = ""

inserted = 0

# =========================================================
# IMPORT
# =========================================================

with collection.batch.dynamic() as batch:

    for item in data:

        raw_line = item.get("raw_line", "")
        item_type = item.get("type", "")

        # -----------------------------------------
        # TRACK SCAN INFO
        # -----------------------------------------

        if item.get("key") == "START_TIME":
            current_start_time = item.get("value", "")

        if item.get("key") == "WORDLIST_FILES":
            current_wordlist = item.get("value", "")

        # -----------------------------------------
        # DIRECTORIES
        # -----------------------------------------

        if item_type == "directory":

            url = raw_line.replace("==> DIRECTORY:", "").strip()

            parsed = urlparse(url)

            properties = {
                "url": url,
                "path": parsed.path,
                "host": parsed.netloc,
                "finding_type": "directory",
                "raw_line": raw_line,
                "http_code": 200,
                "response_size": 0,
                "scan_start_time": current_start_time,
                "wordlist": current_wordlist,
                "directory_listable": True
            }

            batch.add_object(
                properties=properties,
                uuid=generate_uuid5(url)
            )

            inserted += 1

        # -----------------------------------------
        # FILES
        # -----------------------------------------

        elif raw_line.startswith("+ http"):

            try:

                url_part = raw_line.split(" (CODE:")[0]
                url_part = url_part.replace("+ ", "").strip()

                code_part = raw_line.split("(CODE:")[1]

                http_code = int(
                    code_part.split("|")[0]
                )

                size = int(
                    code_part.split("SIZE:")[1]
                    .replace(")", "")
                )

                parsed = urlparse(url_part)

                properties = {
                    "url": url_part,
                    "path": parsed.path,
                    "host": parsed.netloc,
                    "finding_type": "file",
                    "raw_line": raw_line,
                    "http_code": http_code,
                    "response_size": size,
                    "scan_start_time": current_start_time,
                    "wordlist": current_wordlist,
                    "directory_listable": False
                }

                batch.add_object(
                    properties=properties,
                    uuid=generate_uuid5(url_part)
                )

                inserted += 1

            except Exception as e:

                print(f"[!] Failed parsing:")
                print(raw_line)
                print(e)

# =========================================================
# RESULTS
# =========================================================

print(f"[+] Imported {inserted} findings")

# =========================================================
# TEST QUERY
# =========================================================

response = collection.query.near_text(
    query="SQL injection directories",
    limit=5
)

print("\n[+] Semantic Search Results:\n")

for obj in response.objects:

    print(obj.properties)

client.close()

print("\n[+] Complete")
