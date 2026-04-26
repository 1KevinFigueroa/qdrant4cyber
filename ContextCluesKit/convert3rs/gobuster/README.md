<table align="center">
  <tr>
    <td align="center" width="50%">
      <a href="https://github.com/Oj/gobuster">
        <img src="https://img.shields.io/badge/Open%20Source-10000000?style=flat&logo=github&logoColor=black" alt="Gobuster open-source tool" width="100">
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
        <img src="https://github.com/1KevinFigueroa/vector4cyber/blob/main/ContextCluesKit/RTFM-Knowledge/img/appLogos/gobuster2.png" width="300" alt="Gobuster Logo">
      </a>
    </td>
    <td align="center" width="50%">
      <img src="https://github.com/1KevinFigueroa/vector4cyber/blob/main/ContextCluesKit/RTFM-Knowledge/img/Vector4Cyber_extraSmalllogo.png" width="300" alt="Program Logo">
    </td>
  </tr>
</table>


# Converter Gobuster results  → JSON Converter vectorized

Converting Gobuster results from a plain text file to a structured JSON format makes a significant difference when the data is being vectorized. Properly structured JSON with unique IDs is extremely useful for aggregating and correlating complex data in a vectorized workflow. High-quality, fast, and accurate data is critical for red team pipelines, security dashboards, and vector databases.

The problem with gobuster's output to a text file will be structured subdomains in a list. When the output in a JSON file.

### Usage:
convert3r_gobusterEmbed.py [-h] [--embed] [-o OUTPUT_FILE] input_file

### Gobuster file structure output example ❌
```
/_archive              (Status: 302)   [Size: 43]  [--> hxxps://wwww.example.com]  
/_images               (Status: 302)   [Size: 41]  [--> //example.com/blog]  
/~logs                 (Status: 302)   [Size: 39]  [--> //example.com/blogs2]  
/1000                  (Status: 302)   [Size: 0]  [--> hxxps://example.com]  
/20                    (Status: 302)   [Size: 0]  [--> hxxps://example.com]  
/42                    (Status: 302)   [Size: 0]  [--> hxxps://example.com]  
/a                     (Status: 302)   [Size: 0]  [--> hxxps://example.com/]  
/about                 (Status: 302)   [Size: 47]  [--> hxxps://example.com/company]  
/About                 (Status: 302)   [Size: 47]  [--> hxxps://example.com/company]  
/activate              (Status: 302)   [Size: 75]  [--> hxxps://passport.example.com/auth/device?origin=smarttv]  
/ad                    (Status: 302)   [Size: 44]  [--> hxxps://example.com/adv/]  
/add                   (Status: 302)   [Size: 44]  [--> hxxps://example.com/adv/]  
/address               (Status: 302)   [Size: 57]  [--> hxxps://example.com/company/contacts/]  
/ADM                   (Status: 302)   [Size: 44]  [--> hxxps://example.com/adv/]  
/adm                   (Status: 302)   [Size: 44]  [--> hxxps://example.com/adv/]  
/adv                  (Status: 200)   [Size: 613789]
```

### A JSON structure option to vectorized ✅
JSON file structure example:
{
      "path": "/_archive",
      "status": 302,
      "size": "43",
      "redirect_url": "https://wwww.example.com",
      "line_number": 1,
      "raw_line": "/_archive              (Status: 302)   [Size: 43]  [--> https://www.example.com",
      "id": 1
    }

With a plain text file, two important pieces of information are missing: the original input and the source from which the data was obtained. From a cybersecurity perspective, these small but crucial data points are essential for traceability, context, and confident decision-making during analysis.

## Overview
From a high-level architecture perspective, the shift from flat-file ingestion to structured JSON isn't just a formatting preference; it’s the difference between a "data swamp" and a high-fidelity Cyber Threat Intelligence (CTI) pipeline.

In the world of vector databases—specifically Qdrant, Milvus, and Weaviate, context is the currency of accuracy. Here is the breakdown of why parsers is the "missing link" for these systems.

- Reads a text file containing subdomains
- Cleans and normalizes each line
- Assigns a unique, stable ID to every entry
- Serializes the result as JSON for downstream automation

Typical use cases:

- Ingesting into a **vector database** and allow a user to select vector sizing (Qdrant, Milvus, Weaviate, more coming soon etc.) for semantic search and correlation made easier
- Powering recon dashboards or graphs (e.g., host → vuln → service relationships)
- Joining subdomains with WHOIS, DNS, HTTP fingerprinting, or vulnerability scan data