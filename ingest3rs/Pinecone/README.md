
<p align="center">
<img src="https://github.com/1KevinFigueroa/vector4cyber/blob/main/RTFM-Knowledge/img/appLogos/Pinecone_Systems_Inc_Logo.jpg" align="center" width="450" height="450">
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

<h2 style="text-align: center;">PROJECT CONTEXT-CLUES - with Pinecone</h2>

Setup Instructions
Pinecone Docker Installation
The following is instructions on how to install Pinecone in a local docker container setup to utilize the ingest3rs

Requirements
- ✅ 🧠
- ✅ Docker
- ✅ Python 3+
- ✅ For testing / lab
- ❌ Production

## Installation

1. docker pull ghcr.io/pinecone-io/pinecone-index:latest
  - Downloads the latest image of Pinecone
2. docker run -d --name nmap-index -e PORT=5081 -e INDEX_TYPE=serverless -e VECTOR_TYPE=dense -e DIMENSION=384 -e METRIC=cosine -p 5081:5081 --platform linux/amd64 ghcr.io/pinecone-io/pinecone-index:latest
  - This will run the latest Pinecone docker image and start the container running on 5081 and the index will be named nmap-index
3. browse to the <a href="https://github.com/1KevinFigueroa/vector4cyber/tree/main/ingest3rs/ChomaDB/connect">nmap-import</a> folder
  - Connect.py ensures your pinecone db can be reached, Read the Readme.md to learn how to use
4. browse to the <a href="https://github.com/1KevinFigueroa/vector4cyber/tree/main/ingest3rs/ChomaDB/nmap-import">nmap-import</a>  folder
  - Imports a sample nmap json into pincone, Read the Readme.md to learn how to use
5. browse to the <a href="https://github.com/1KevinFigueroa/vector4cyber/tree/main/ingest3rs/ChomaDB/nmap-query">nmap-query</a> folder 
  - Query the pincone vector db for the nmap results, Read the Readme.md to learn how to use

## Security
Remeber this is just for testing and not to be run in production, there are no security controls 

- ❌ Production 
## What to expect e.g. Nmap Queries
<p align="center">
<img src="https://github.com/1KevinFigueroa/vector4cyber/blob/main/RTFM-Knowledge/img/pinecone-nmap1.jpg" align="center" width="350" height="750">
<img src="https://github.com/1KevinFigueroa/vector4cyber/blob/main/RTFM-Knowledge/img/pinecone-nmap2.jpg" align="center" width="350" height="750">
<img src="https://github.com/1KevinFigueroa/vector4cyber/blob/main/RTFM-Knowledge/img/pinecone-nmap3.jpg" align="center" width="350" height="750">
</p>

