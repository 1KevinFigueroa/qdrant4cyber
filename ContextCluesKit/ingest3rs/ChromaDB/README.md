
<p align="center">
<img src="https://github.com/1KevinFigueroa/vector4cyber/blob/main/ContextClueskit/RTFM-Knowledge/img/appLogos/chromadb.png" align="center" width="300" height="250">
  <img src="https://github.com/1KevinFigueroa/vector4cyber/blob/main/ContextClueskit/RTFM-Knowledge/img/Vector4Cyber.png" align="center" width="400" height="250">

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

<h2 style="text-align: center;">PROJECT CONTEXT-CLUES - with ChomaDB</h2>

<h2>Setup Instructions</h2>

# ChromaDB Docker Installation

The following is instructions on how to install ChromaDB in a local docker container setup to utilize the ingest3rs

## Requirements

- ✅ 🧠
- ✅ Docker
- ✅ Python 3+
- ✅ For testing / lab
- ❌ Production 

## Installation

1. Create the following 'docker-compose.yml' file
```
services:
  chromadb:
    image: chromadb/chroma:latest
    container_name: chromadb
    ports:
      - "9000:8000"
    volumes:
      - chroma_data:/chroma/chroma
    restart: unless-stopped

volumes:
  chroma_data:
    name: chroma_data	
```
2. Execute the command "docker compose up -d"
3. Execute the command "docker ps" and you should see
* chromadb
4. browse to the <a href="https://github.com/1KevinFigueroa/vector4cyber/tree/main/ingest3rs/ChromaDB/test-connect">test-connect</a> folder
    - test-connect.py ensures your ChromaDB can be reached, Read the Readme.md to learn how to use
5. browse to the <a href="https://github.com/1KevinFigueroa/vector4cyber/tree/main/Queries/ChromaDB">queries</a>  folder
	- browse the queries folder for the tool you wish to run, Read the Readme.md to learn how to use

## Security
Remeber this is just for testing and not to be run in production, there are no security controls 

- ❌ Production 
## What to expect e.g. Nmap Queries and Nuclei Queries
<p align="center">
<img src="https://github.com/1KevinFigueroa/vector4cyber/blob/main/RTFM-Knowledge/img/ChromaNmap1.jpg" align="center" width="350" height="750">
<img src="https://github.com/1KevinFigueroa/vector4cyber/blob/main/RTFM-Knowledge/img/ChromaNmap2.jpg" align="center" width="350" height="750">
<img src="https://github.com/1KevinFigueroa/vector4cyber/blob/main/RTFM-Knowledge/img/ChromaNmap3.jpg" align="center" width="350" height="750">
<img src="https://github.com/1KevinFigueroa/vector4cyber/blob/main/RTFM-Knowledge/img/ChromaNuclei1.jpg" align="center" width="350" height="750">
<img src="https://github.com/1KevinFigueroa/vector4cyber/blob/main/RTFM-Knowledge/img/ChromaNuclei2.jpg" align="center" width="350" height="750">
<img src="https://github.com/1KevinFigueroa/vector4cyber/blob/main/RTFM-Knowledge/img/ChromaNuclei3.jpg" align="center" width="350" height="750">
</p>

