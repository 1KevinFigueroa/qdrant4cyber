<table align="center">
  <tr>
    <td align="center" width="50%">
      <a href="https://github.com/nmap/nmap">
        <img src="https://img.shields.io/badge/Open%20Source-ff0000?style=flat&logo=github&logoColor=black" alt="Nmap open-source tool" width="100">
      </a>
    </td>
    <td align="center" width="50%">
      <a href="https://github.com/1KevinFigueroa/vector4cyber/blob/main/LICENSE">
        <img src="https://img.shields.io/badge/License-Apache%202.0-brightgreen?labelColor=gray&logo=github" alt="Apache 2.0">
    </a>
      </a>
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <a href="">
        <img src="https://github.com/1KevinFigueroa/vector4cyber/blob/main/RTFM-Knowledge/img/appLogos/nmap.png" width="150" alt="Amass Logo">
      </a>
    </td>
    <td align="center" width="50%">
      <img src="https://github.com/1KevinFigueroa/vector4cyber/blob/main/RTFM-Knowledge/img/Vector4Cyber_extraSmalllogo.png" width="300" alt="Program Logo">
    </td>
  </tr>
</table>

# Converter Nmap TXT file  → JSON file vectorized

Converting Subfinder results from a plain text file to a structured JSON format makes a significant difference when the data is being vectorized. Properly structured JSON with unique IDs is extremely useful for aggregating and correlating complex data in a vectorized workflow. High-quality, fast, and accurate data is critical for red team pipelines, security dashboards, and vector databases.

The problem with subfinder's output to a text file will be structured subdomains in a list. When the output in a JSON file 

### Usage:
convert_NmapTXT.py [-h] [--pretty] input_file [output_file]

### Nmap TEXT file structure output example ❌
ORT    STATE SERVICE   VERSION
80/tcp  open  http      Netlify
| fingerprint-strings:
|   DNSVersionBindReqTCP, GenericLines, Help, Kerberos, RPCCheck, RTSPRequest, SSLSessionReq, TLSSessionReq, TerminalServerCookie:
|     HTTP/1.1 400 Bad Request
|     Content-Type: text/plain; charset=utf-8
|     Connection: close
|     Request
|   FourOhFourRequest:
|     HTTP/1.0 400 Bad Request
|     Date: Fri, 16 Jan 2026 03:52:10 GMT
|     Server: Netlify
|     X-Nf-Request-Id: 01KF2EX6YJ13HBH5H645EQC8SP
|     Content-Length: 0
|   GetRequest:
|     HTTP/1.0 400 Bad Request
|     Date: Fri, 16 Jan 2026 03:52:05 GMT
|     Server: Netlify
|     X-Nf-Request-Id: 01KF2EX1RBFJ5DZN54NZR658CW
|     Content-Length: 0
|   HTTPOptions:
|     HTTP/1.0 400 Bad Request
|     Date: Fri, 16 Jan 2026 03:52:05 GMT
|     Server: Netlify
|     X-Nf-Request-Id: 01KF2EX1XTTWM1WZ7BS3A1A02X
|_Content-Length: 0
|_http-server-header: Netlify
443/tcp open  ssl/https Netlify

### A JSON structure option to vectorized ✅
JSON file structure example:
{"id": 1, "host": "example.com", "input": "example.com", "source": "subfinder"}

With a plain text file, two important pieces of information are missing: the original input and the source from which the data was obtained. From a cybersecurity perspective, these small but crucial data points are essential for traceability, context, and confident decision-making during analysis.

## Overview
From a high-level architecture perspective, the shift from flat-file ingestion to structured JSON isn't just a formatting preference; it’s the difference between a "data swamp" and a high-fidelity Cyber Threat Intelligence (CTI) pipeline.

In the world of vector databases—specifically Qdrant, Milvus, and Weaviate, context is the currency of accuracy. Here is the breakdown of why parsers is the "missing link" for these systems.

- Reads a text file containing subdomains
- Cleans and normalizes each line
- Assigns a unique, stable ID to every entry
- Serializes the result as JSON for downstream automation

Typical use cases:

- Ingesting subdomains into a **vector database** and user can select vector sizing (Qdrant, Milvus, Weaviate, more coming soon etc.) for semantic search and correlation made easier
- Powering recon dashboards or graphs (e.g., host → vuln → service relationships)
- Joining subdomains with WHOIS, DNS, HTTP fingerprinting, or vulnerability scan data