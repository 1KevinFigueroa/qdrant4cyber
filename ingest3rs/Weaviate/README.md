<p align="center">
<img src="https://github.com/1KevinFigueroa/vector4cyber/blob/main/RTFM-Knowledge/img/appLogos/weaviate-logo.jpg" align="center" width="450" height="450">
  <img src="https://github.com/1KevinFigueroa/vector4cyber/blob/main/RTFM-Knowledge/img/Vector4Cyber.png" align="center" width="400" height="250">

<p align="center">
  <a href="https://github.com/1KevinFigueroa/vector4cyber/tree/main/CyberToolConverterKit">
    <img src="https://img.shields.io/badge/Build-repo%20workflow-ff0000" alt="Build Status">
  </a>
  <a href="https://github.com/1KevinFigueroa/vector4cyber/tree/main/RTFM-Knowledge">
    <img src="https://img.shields.io/badge/docs-latest-blue.svg" alt="Documentation">
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/github/license/1KevinFigueroa/vector4cyber" alt="License">
  </a>
  <a href="https://github.com/1KevinFigueroa/vector4cyber/blob/main/RTFM-Knowledge/Roadmap/README.md">
    <img src="https://img.shields.io/badge/Roadmap-Live%20Board-00b8d4" alt="Roadmap">
  </a>
</p>
</p>

<h2 style="text-align: center;">PROJECT CONTEXT-CLUES - with Milvus</h2>

Setup Instructions
Weaviate Docker Installation
The following is instructions on how to install Weaviate in a local docker container setup to utilize the ingest3rs

Requirements
- ✅ 🧠
- ✅ Docker
- ✅ Python 3+
- ✅ For testing / lab
- ❌ Production

## Installation
1. Create the following 'docker-compose.yml' file
```docker-compose.yml
services:
  weaviate:
    image: semitechnologies/weaviate:latest
    container_name: weaviate
    restart: unless-stopped

    ports:
      - "8080:8080"      # REST / GraphQL API
      - "50051:50051"    # gRPC API (NEW + recommended)

    environment:
      # General
      QUERY_DEFAULTS_LIMIT: 20
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: "true"
      PERSISTENCE_DATA_PATH: "/var/lib/weaviate"
      CLUSTER_HOSTNAME: "node1"

      # Modules
      DEFAULT_VECTORIZER_MODULE: text2vec-transformers
      ENABLE_MODULES: text2vec-transformers
      TRANSFORMERS_INFERENCE_API: http://t2v-transformers:8080

    volumes:
      - weaviate_data:/var/lib/weaviate

    depends_on:
      - t2v-transformers

  t2v-transformers:
    image: semitechnologies/transformers-inference:sentence-transformers-all-MiniLM-L6-v2
    container_name: t2v-transformers
    restart: unless-stopped

    environment:
      ENABLE_CUDA: "0"   # Set to "1" if using NVIDIA GPU

    ports:
      - "8081:8080"      # Optional: expose MiniLM service externally

volumes:
  weaviate_data:
```
2. Execute the command "docker compose up -d"
3. browse to the <a href="https://github.com/1KevinFigueroa/vector4cyber/tree/main/ingest3rs/Weaviate/test-connect">connect</a> folder
    - test-connect.py ensures your Weaviate db can be reached, Read the Readme.md to learn how to use
4. browse to the <a href="https://github.com/1KevinFigueroa/vector4cyber/tree/main/ingest3rs/Weaviate/nmap-import">nmap-import</a>  folder
    - Imports a sample nmap json into Weaviate, Read the Readme.md to learn how to use
5. browse to the <a href="https://github.com/1KevinFigueroa/vector4cyber/tree/main/ingest3rs/Weaviate/nmap-query">nmap-query</a> folder 
    - Query the Weaviate vector db for the nmap results, Read the Readme.md to learn how to use