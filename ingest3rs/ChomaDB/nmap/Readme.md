# Nmap to ChromaDB Importer

This Python script imports nmap scan results from JSON files into a ChromaDB vector database collection.

## Features

- ✅ Imports nmap scan data into ChromaDB collection named "nmaptest"
- ✅ Extracts host information including IP addresses, hostnames, MAC addresses, vendors, OS detection
- ✅ Stores open ports and services information
- ✅ Creates searchable documents for each host
- ✅ Validates JSON file format
- ✅ Provides clear error messages and usage instructions

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

Or install ChromaDB directly:
```bash
pip install chromadb
```

## Usage

### Basic Usage

```bash
python nmap_to_chromadb.py <json_file_path>
```

### Examples

Import the provided sample file:
```bash
python nmap_to_chromadb.py LocalNmapTest.json
```

Import from a different location:
```bash
python nmap_to_chromadb.py /path/to/nmap_scan.json
```

### What Happens

1. The script validates that the JSON file exists and is readable
2. Parses the nmap JSON data
3. Extracts relevant information from each host:
   - IP address
   - Hostname (if available)
   - MAC address and vendor (if available)
   - Host status (up/down)
   - Open ports and services
   - Operating system detection (if available)
4. Creates a ChromaDB collection named "nmaptest" (or uses existing one)
5. Adds each host as a document with metadata

## Error Handling

The script provides helpful error messages for common issues:

### No file specified
```
❌ Error: No JSON file specified.
```
**Solution:** Provide the JSON file path as an argument

### File not found
```
❌ Error: File 'filename.json' does not exist.
```
**Solution:** Check the file path and make sure the file exists

### Invalid JSON format
```
❌ Error: Invalid JSON format in 'filename.json'
```
**Solution:** Verify the JSON file is properly formatted nmap output

## Querying the Data

After importing, the script **automatically demonstrates several query examples** that show IP addresses, ports, and services:

### Query Demonstrations Included:

1. **Search for HTTP services** - Shows all hosts running HTTP servers
2. **Search for SSH services** - Finds all SSH services  
3. **Filter by open port count** - Get hosts with metadata filters
4. **Search for specific ports** - Find services on specific ports (e.g., SMB on 445)
5. **Summary table** - Display all hosts with their IPs, ports, and services

### Example Queries You Can Run:

- ✅ downnload and execute the "cli_nmap_query_examples.py" to get a sample understanding of what type of data you can retrieve from your results.

## Data Structure

Each host is stored with:

### Document (searchable text):
- IP Address
- Hostname
- MAC Address and Vendor
- Status
- Operating System
- List of open ports with services

### Metadata (for filtering):
- `ip_address`: Host IP address
- `state`: Host state (up/down)
- `open_port_count`: Number of open ports
- `hostname`: Hostname (if available)
- `mac_address`: MAC address (if available)
- `vendor`: Network device vendor (if available)
- `os_name`: Detected OS (if available)
- `os_accuracy`: OS detection accuracy (if available)

## Example Output

```
======================================================================
Nmap to ChromaDB Importer
======================================================================
✓ Successfully loaded JSON from 'LocalNmapTest.json'
✓ Created new collection 'nmaptest'

📊 Processing 10 hosts...

✅ Successfully imported 10 hosts to ChromaDB collection 'nmaptest'

======================================================================
Import Summary
======================================================================
Collection: nmaptest
Total hosts: 10
Hosts up: 10
Total documents in collection: 10
======================================================================

💡 Example query:
   from chromadb import Client
   client = Client()
   collection = client.get_collection('nmaptest')
   results = collection.query(query_texts=['HTTP server'], n_results=5)
```

## Requirements

- Python 3.7+
- chromadb >= 0.4.0

## License

This script is provided as-is for educational and security testing purposes.

