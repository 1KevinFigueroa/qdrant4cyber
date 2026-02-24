"""
Nmap to ChromaDB Importer
--------------------------
This script imports nmap scan results from a JSON file into a ChromaDB collection.

Usage:
    python nmap_to_chromadb-MiniLM-L6.py <json_file_path>

Example:
    python nmap_to_chromadb-MiniLM-L6.py LocalNmapTest.json
"""

import sys
import json
import argparse
from pathlib import Path
import chromadb
from chromadb.config import Settings


def print_usage():
    """Print usage information."""
    print("\n" + "="*70)
    print("Nmap to ChromaDB Importer")
    print("="*70)
    print("\nUsage:")
    print("    python nmap_to_chromadb-MiniLM-L6.py <json_file_path>")
    print("\nExample:")
    print("    python nmap_to_chromadb-MiniLM-L6.py LocalNmapTest.json")
    print("    python nmap_to_chromadb-MiniLM-L6.py /path/to/nmap_scan.json")
    print("\nDescription:")
    print("    This script imports nmap scan results from a JSON file")
    print("    into a ChromaDB collection named 'nmaptest'.")
    print("="*70 + "\n")


def validate_json_file(file_path):
    """Validate that the file exists and is a JSON file."""
    path = Path(file_path)
    
    if not path.exists():
        print(f"❌ Error: File '{file_path}' does not exist.")
        return False
    
    if not path.is_file():
        print(f"❌ Error: '{file_path}' is not a file.")
        return False
    
    if path.suffix.lower() != '.json':
        print(f"⚠️  Warning: File '{file_path}' does not have a .json extension.")
        print("   Attempting to parse anyway...")
    
    return True


def load_json_data(file_path):
    """Load and parse JSON data from file."""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        print(f"✓ Successfully loaded JSON from '{file_path}'")
        return data
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON format in '{file_path}'")
        print(f"   {str(e)}")
        return None
    except Exception as e:
        print(f"❌ Error reading file: {str(e)}")
        return None


def extract_host_info(host):
    """Extract relevant information from a host entry."""
    info = {}
    
    # Extract IP address
    if isinstance(host.get('address'), dict):
        info['ip_address'] = host['address'].get('@addr', 'unknown')
    elif isinstance(host.get('address'), list):
        for addr in host['address']:
            if addr.get('@addrtype') == 'ipv4':
                info['ip_address'] = addr.get('@addr', 'unknown')
                break
            elif addr.get('@addrtype') == 'mac':
                info['mac_address'] = addr.get('@addr', 'unknown')
                info['vendor'] = addr.get('@vendor', 'unknown')
    
    # Extract hostname
    hostnames = host.get('hostnames')
    if hostnames and isinstance(hostnames, dict):
        hostname_entry = hostnames.get('hostname')
        if hostname_entry:
            info['hostname'] = hostname_entry.get('@name', 'unknown')
    
    # Extract status
    status = host.get('status', {})
    info['state'] = status.get('@state', 'unknown')
    
    # Extract ports
    ports_info = []
    ports = host.get('ports', {})
    port_list = ports.get('port', [])
    
    if isinstance(port_list, dict):
        port_list = [port_list]
    
    for port in port_list:
        port_info = {
            'port': port.get('@portid', 'unknown'),
            'protocol': port.get('@protocol', 'unknown'),
            'state': port.get('state', {}).get('@state', 'unknown'),
            'service': port.get('service', {}).get('@name', 'unknown'),
            'product': port.get('service', {}).get('@product', ''),
            'version': port.get('service', {}).get('@version', '')
        }
        ports_info.append(port_info)
    
    info['ports'] = ports_info
    info['open_port_count'] = len([p for p in ports_info if p['state'] == 'open'])
    
    # Extract OS info if available
    os_matches = host.get('os', {}).get('osmatch', [])
    if os_matches:
        if isinstance(os_matches, dict):
            os_matches = [os_matches]
        if os_matches:
            info['os_name'] = os_matches[0].get('@name', 'unknown')
            info['os_accuracy'] = os_matches[0].get('@accuracy', '0')
    
    return info


def create_document_text(host_info):
    """Create searchable text document from host info."""
    parts = []
    
    parts.append(f"IP Address: {host_info.get('ip_address', 'unknown')}")
    
    if 'hostname' in host_info:
        parts.append(f"Hostname: {host_info['hostname']}")
    
    if 'mac_address' in host_info:
        parts.append(f"MAC Address: {host_info['mac_address']}")
        if 'vendor' in host_info and host_info['vendor'] != 'unknown':
            parts.append(f"Vendor: {host_info['vendor']}")
    
    parts.append(f"Status: {host_info.get('state', 'unknown')}")
    
    if 'os_name' in host_info:
        parts.append(f"Operating System: {host_info['os_name']} (Accuracy: {host_info['os_accuracy']}%)")
    
    # Add port information
    if host_info.get('ports'):
        parts.append(f"\nOpen Ports: {host_info.get('open_port_count', 0)}")
        for port in host_info['ports']:
            if port['state'] == 'open':
                service_info = f"{port['port']}/{port['protocol']}: {port['service']}"
                if port.get('product'):
                    service_info += f" ({port['product']}"
                    if port.get('version'):
                        service_info += f" {port['version']}"
                    service_info += ")"
                parts.append(service_info)
    
    return "\n".join(parts)


def import_to_chromadb(data):
    """Import nmap data into ChromaDB collection."""
    try:
        # Connect to the Docker ChromaDB server
        client = chromadb.HttpClient(
            host="localhost",
            port=8000,
            # Include token if authentication is enabled
            headers={"Authorization": "Bearer my-secret-token"}
        )
                
        # Create or get collection
        collection_name = "nmaptest"
        try:
            collection = client.get_collection(name=collection_name)
            print(f"✓ Using existing collection '{collection_name}'")
        except:
            collection = client.create_collection(name=collection_name)
            print(f"✓ Created new collection '{collection_name}'")
        
        # Extract hosts from JSON
        nmaprun = data.get('nmaprun', {})
        hosts = nmaprun.get('host', [])
        
        if isinstance(hosts, dict):
            hosts = [hosts]
        
        if not hosts:
            print("⚠️  Warning: No hosts found in the JSON data.")
            return
        
        print(f"\n📊 Processing {len(hosts)} hosts...")
        
        # Prepare data for ChromaDB
        documents = []
        metadatas = []
        ids = []
        
        for idx, host in enumerate(hosts):
            host_info = extract_host_info(host)
            
            # Create document text
            doc_text = create_document_text(host_info)
            documents.append(doc_text)
            
            # Create metadata (ChromaDB metadata must be flat dict with simple types)
            metadata = {
                'ip_address': host_info.get('ip_address', 'unknown'),
                'state': host_info.get('state', 'unknown'),
                'open_port_count': host_info.get('open_port_count', 0)
            }
            
            if 'hostname' in host_info:
                metadata['hostname'] = host_info['hostname']
            
            if 'mac_address' in host_info:
                metadata['mac_address'] = host_info['mac_address']
            
            if 'vendor' in host_info and host_info['vendor'] != 'unknown':
                metadata['vendor'] = host_info['vendor']
            
            if 'os_name' in host_info:
                metadata['os_name'] = host_info['os_name']
                metadata['os_accuracy'] = host_info['os_accuracy']
            
            metadatas.append(metadata)
            
            # Create unique ID
            ids.append(f"host_{idx}_{host_info.get('ip_address', 'unknown').replace('.', '_')}")
        
        # Add to collection
        collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        
        print(f"\n✅ Successfully imported {len(hosts)} hosts to ChromaDB collection '{collection_name}'")
        
        # Print summary
        print("\n" + "="*70)
        print("Import Summary")
        print("="*70)
        print(f"Collection: {collection_name}")
        print(f"Total hosts: {len(hosts)}")
        print(f"Hosts up: {len([h for h in hosts if extract_host_info(h).get('state') == 'up'])}")
        print(f"Total documents in collection: {collection.count()}")
        print("="*70)
        
        # Show example query
        print("\n💡 Example query:")
        print("   from chromadb import Client")
        print(f"   client = Client()")
        print(f"   collection = client.get_collection('{collection_name}')")
        print("   results = collection.query(query_texts=['HTTP server'], n_results=5)")
        print()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error importing to ChromaDB: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Import nmap JSON scan results into ChromaDB',
        usage='python nmap_to_chromadb-MiniLM-L6.py <json_file_path>'
    )
    parser.add_argument('json_file', nargs='?', help='Path to the nmap JSON file')
    
    args = parser.parse_args()
    
    # Check if file argument was provided
    if not args.json_file:
        print("\n❌ Error: No JSON file specified.")
        print_usage()
        sys.exit(1)
    
    # Validate file
    if not validate_json_file(args.json_file):
        print_usage()
        sys.exit(1)
    
    # Load JSON data
    data = load_json_data(args.json_file)
    if data is None:
        sys.exit(1)
    
    # Import to ChromaDB
    success = import_to_chromadb(data)
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
