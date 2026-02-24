<table align="center">
  <tr>
    <td align="center" width="50%">
      <a href="https://github.com/rbsec/sslscan">
        <img src="https://img.shields.io/badge/sslscan-active-orange?style=flat&logo=simple-icons&logoColor=white" alt="sslscan" width="100">
      </a>
    </td>
    <td align="center" width="50%">
      <a href="https://github.com/1KevinFigueroa/vector4cyber/blob/main/LICENSE">
        <img src="https://img.shields.io/badge/License-Apache%202.0-brightgreen?labelColor=gray&logo=github" alt="Apache 2.0 License">
      </a>
    </td>
  </tr>
  <tr>
    <td align="center" width="50%">
      <a href="">
        <img src="https://github.com/1KevinFigueroa/vector4cyber/blob/main/RTFM-Knowledge/img/appLogos/sslscan.png" width="300" alt="Amass Logo">
      </a>
    </td>
    <td align="center" width="50%">
      <img src="https://github.com/1KevinFigueroa/vector4cyber/blob/main/RTFM-Knowledge/img/Vector4Cyber_extraSmalllogo.png" width="300" alt="Program Logo">
    </td>
  </tr>
</table>

# Convert SSLScan results → JSON file vectoized

Converting SSLScan results from a plain text file to a structured JSON format makes a significant difference when the data is being vectorized. Properly structured JSON with unique IDs is extremely useful for aggregating and correlating complex data in a vectorized workflow. High-quality, fast, and accurate data is critical for red team pipelines, security dashboards, and vector databases.

The problem with subfinder's output to a text file will be structured subdomains in a list. When the output in a JSON file

### Usage

convertSSLScanTXT2JSON.py [-h] input_file output_file


### SSLscan JSON file output structure example ❌

{"host":"aleksandr-kulishov.yandex.ru","input":"yandex.ru","source":"reconeer"}

### A JSON structure option to vectorized ✅

JSON file structure example:
 {
    "id": 1,
    "ip": " ",
    "target": " ",
    "port": 443,
    "sni": " ",
    "protocols": {
      "SSLv2": "disabled",
      "SSLv3": "disabled",
      "TLSv1.0": "disabled",
      "TLSv1.1": "disabled",
      "TLSv1.2": "enabled",
      "TLSv1.3": "enabled"
    },
    "heartbleed": {
      "TLSv1.3": "not vulnerable to heartbleed",
      "TLSv1.2": "not vulnerable to heartbleed"
    },

With a plain text file, two important pieces of information are missing: the original input and the source from which the data was obtained. From a cybersecurity perspective, these small but crucial data points are essential for traceability, context, and confident decision-making during analysis.

## Overview

From a high-level architecture perspective, the shift from flat-file ingestion to structured JSON isn't just a formatting preference; it’s the difference between a "data swamp" and a high-fidelity Cyber Threat Intelligence (CTI) pipeline.

In the world of vector databases—specifically Qdrant, Milvus, and Weaviate, context is the currency of accuracy. Here is the breakdown of why parsers is the "missing link" for these systems.

- Reads a text file containing subdomains
- Cleans and normalizes each line
- Assigns a unique, stable ID to every entry
- Serializes the result as JSON for downstream automation

Typical use cases:

- Ingesting SSLScan information into a **vector database** and the ability to select a vector size for (Qdrant, Milvus, Weaviate, more coming soon etc.) for semantic search and correlation made easier
- Powering recon dashboards or graphs (e.g., host → vuln → service relationships)
- Joining subdomains with WHOIS, DNS, HTTP fingerprinting, or vulnerability scan data
