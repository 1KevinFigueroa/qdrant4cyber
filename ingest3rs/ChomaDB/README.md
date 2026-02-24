
<p align="center">
<img src="https://github.com/1KevinFigueroa/vector4cyber/blob/main/ingest3rs/ChomaDB/chromadb.png" align="center" width="300" height="250">
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

1. docker run -p 8000:8000 chromadb/chroma
	- This will download the latest Chromadb docker image and start the container running on 8000
2. pip install chromadb
	- Highly suggested to be installed in a virtual python environment 🔍 https://docs.python.org/3/library/venv.html
3. Browse to http://localhost:8000/api/v2/heartbeat
	- This will return the heartbeat 
	- Sample expected result:
		{"nanosecond heartbeat":1771827785706459389}
3. python connect.py
	- This is a test script that if your setup is correct will return a heartbeat and the version of ChromaDB 
	- Sample exepcted results: 
		Heartbeat: 1771827370416586781
		Version: 1.0.0

## Security
Remeber this is just for testing and not to be run in production, there are no security controls 

- ❌ Production 
## What to expect e.g. Nmap Queries
<p align="center">
<img src="https://github.com/1KevinFigueroa/vector4cyber/tree/main/RTFM-Knowledge/img/ChromaNmap1.jpg" align="center" width="350" height="750">
<img src="https://github.com/1KevinFigueroa/vector4cyber/tree/main/RTFM-Knowledge/img/ChromaNmap2.jpg" align="center" width="350" height="750">
<img src="https://github.com/1KevinFigueroa/vector4cyber/tree/main/RTFM-Knowledge/img/ChromaNmap3.jpg" align="center" width="350" height="750">
</p>

