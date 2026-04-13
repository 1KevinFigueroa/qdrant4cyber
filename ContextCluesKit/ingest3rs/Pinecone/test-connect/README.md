# Pinecone Local Connectivity Test

## Overview

This Python script is a simple **health-check utility** for a local Pinecone instance.
It attempts to connect to a **Pinecone Local server** using the Pinecone gRPC client and verifies whether the service is reachable by requesting a list of indexes.

If the server responds successfully, the script prints the available indexes.
If the server is not reachable or an error occurs, it prints an error message indicating that Pinecone is not responding.

The script is primarily useful for:

* Verifying that **Pinecone Local is running**
* Testing **network connectivity to the Pinecone service**
* Debugging **local development environments**
* Confirming that the Pinecone API client is correctly configured

The script first tries the Pinecone Local control endpoint:

```
http://localhost:5080
```

and falls back to:

```
http://localhost:5081
```

before performing a basic API call to list indexes.

---

# Requirements

## Python Version

* Python **3.8+** recommended

## Dependencies

Install required dependencies using pip:

```bash
pip install "pinecone[grpc]"
```

### Libraries Used

| Library       | Purpose                           |
| ------------- | --------------------------------- |
| pinecone.grpc | Provides the Pinecone gRPC client |

---

# Project Structure

```
project/
│
├── test-connect.py        # Script that checks Pinecone connectivity
└── README.md         # Documentation
```

---

# How the Script Works

The script performs three main steps:

1. **Initialize a Pinecone client**
2. **Attempt to retrieve indexes**
3. **Handle errors if the server is unavailable**

---

# Architecture

The script follows a simple flow:

```
Start
  │
  ▼
Create Pinecone Client
  │
  ▼
Call list_indexes()
  │
  ├── Success → Print indexes
  │
  └── Failure → Print error message
```

Because the script only performs a **single API call**, it functions primarily as a **service health check**.

---

# Code Explanation

## 1. Import Dependencies

```python
from pinecone.grpc import PineconeGRPC
```

* `PineconeGRPC` provides the gRPC client for interacting with Pinecone.

---

## 2. Initialize the Pinecone Client

```python
pc = PineconeGRPC(
    api_key="pclocal",
    host="http://localhost:5080"
)
```

### Parameters

| Parameter | Description                                            |
| --------- | ------------------------------------------------------ |
| api_key   | Required by the client but not validated in local mode |
| host      | Address of the Pinecone control endpoint (`list_indexes`) |

The API key value `"pclocal"` is a placeholder used for local environments.

---

## 3. Query Pinecone for Indexes

```python
indexes = pc.list_indexes()
```

This sends a request to the Pinecone server to retrieve the list of existing indexes.

If the server is reachable, it returns a list of indexes.

---

## 4. Handle Errors

```python
try:
    indexes = pc.list_indexes()
    print("Pinecone is alive:", indexes)
except Exception as e:
    print("Pinecone not responding:", e)
```

The `try/except` block ensures the script:

* Does **not crash**
* Returns a helpful error message if Pinecone is not running.

---

# Running the Script

Execute the script with:

```bash
python test-connect.py
```

---

# Example Outputs

## Case 1 — Pinecone Running

```
Pinecone is alive: ['example-index', 'test-index']
```

This indicates:

* The Pinecone service is reachable
* The API client is working correctly
* Index metadata was returned successfully

---

## Case 2 — Pinecone Not Running

```
Pinecone not responding: Connection refused
```

This usually means:

* Pinecone Local is not started
* The port is incorrect
* The server is unreachable

---

# Starting Pinecone Local (Example)

If you are running Pinecone locally, ensure it is started before running the script.

Example:

```bash
docker run -p 5080-5090:5080-5090 ghcr.io/pinecone-io/pinecone-local:latest
```

Then run:

```bash
python test-connect.py
```

---

# Possible Improvements

Future enhancements could include:

* Adding **command-line arguments** for host and port
* Implementing **logging instead of print statements**
* Removing unused imports (`requests`)
* Adding a **timeout and retry mechanism**
* Adding support for **creating or deleting indexes**

---

# Example Enhanced Version

Example improvement:

```python
import argparse
from pinecone.grpc import PineconeGRPC

parser = argparse.ArgumentParser()
parser.add_argument("--host", default="http://localhost:5081")

args = parser.parse_args()

pc = PineconeGRPC(api_key="pclocal", host=args.host)

try:
    indexes = pc.list_indexes()
    print("Pinecone is alive:", indexes)
except Exception as e:
    print("Pinecone not responding:", e)
```

---

# License

MIT License

---

# Summary

This script is a **lightweight connectivity test** for Pinecone Local. It helps developers quickly verify that their Pinecone environment is running and responding to API requests.

