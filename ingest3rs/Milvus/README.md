<p align="center">
<img src="https://github.com/1KevinFigueroa/vector4cyber/blob/main/RTFM-Knowledge/img/appLogos/milvus-logo.webp" align="center" width="450" height="450">
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
Milvus Docker Installation
The following is instructions on how to install Milvus in a local docker container setup to utilize the ingest3rs

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
  etcd:
    container_name: milvus-etcd
    image: quay.io/coreos/etcd:v3.5.5
    environment:
      - ETCD_AUTO_COMPACTION_MODE=revision
      - ETCD_AUTO_COMPACTION_RETENTION=1000
      - ETCD_QUOTA_BACKEND_BYTES=4294967296
    command: etcd -advertise-client-urls=http://etcd:2379 -listen-client-urls=http://0.0.0.0:2379 --data-dir /etcd
    volumes:
      - ./volumes/etcd:/etcd

  minio:
    container_name: milvus-minio
    image: minio/minio:RELEASE.2023-03-20T20-16-18Z
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    command: minio server /minio_data
    ports:
      - "9001:9000"
    volumes:
      - ./volumes/minio:/minio_data

  milvus:
    container_name: milvus-standalone
    image: milvusdb/milvus:v2.3.3
    command: ["milvus", "run", "standalone"]
    environment:
      ETCD_ENDPOINTS: etcd:2379
      MINIO_ADDRESS: minio:9000
    ports:
      - "19530:19530"
      - "9091:9091"
    depends_on:
      - etcd
      - minio
    volumes:
      - ./volumes/milvus:/var/lib/milvus

networks:
  default:
    name: milvus-network
```
2. Execute the command "docker compose up -d"
3. Execute the command "docker ps" and you should see
* milvus-standalone
* milvus-etcd
* milvus-minio
4. browse to the <a href="https://github.com/1KevinFigueroa/vector4cyber/tree/main/ingest3rs/Milvus/test-connect">test-connect</a> folder
    - Connect.py ensures your Milvus db can be reached, Read the Readme.md to learn how to use
5. browse to the <a href="https://github.com/1KevinFigueroa/vector4cyber/tree/main/Queries/ChromaDB">queries</a>  folder
	- browse the queries folder for the tool you wish to run, Read the Readme.md to learn how to use

## Security
Remeber this is just for testing and not to be run in production, there are no security controls 

- ❌ Production 
## What to expect e.g. Nmap Queries
<p align="center">
<img src="https://github.com/1KevinFigueroa/vector4cyber/blob/main/RTFM-Knowledge/img/milvus-nmap1.jpg" align="center" width="350" height="750">
<img src="https://github.com/1KevinFigueroa/vector4cyber/blob/main/RTFM-Knowledge/img/milvus-nmap2.jpg" align="center" width="350" height="750">
<img src="https://github.com/1KevinFigueroa/vector4cyber/blob/main/RTFM-Knowledge/img/milvus-nmap3.jpg" align="center" width="350" height="750">
</p>

