#!/usr/bin/env python3
"""
ChromaDB Query Examples for Nmap Data
--------------------------------------
This script demonstrates how to query the 'nmaptest' collection
and retrieve IP addresses, ports, and services.

Prerequisites:
- Run nmap_to_chromadb.py first to import your nmap data
- ChromaDB must be installed: pip install chromadb
"""

import chromadb
from chromadb.config import Settings


def print_section(title):
    """Print a formatted section header."""
    print("\n" + "="*70)
    print(title)
    print("="*70)


def query_http_services(collection):
    """Query for HTTP services and display IP, port, service."""
    print_section("Query 1: Search for HTTP Services")
    
    results = collection.query(
        query_texts=["HTTP web server"],
        n_results=5
    )
    
    if results['documents'] and results['documents'][0]:
        for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0]), 1):
            print(f"\nResult {i}:")
            print(f"  IP Address: {metadata.get('ip_address', 'N/A')}")
            
            # Extract port and service information from document
            lines = doc.split('\n')
            for line in lines:
                if '/' in line and 'http' in line.lower():
                    print(f"  {line.strip()}")
    else:
        print("No HTTP services found")


def query_ssh_services(collection):
    """Query for SSH services."""
    print_section("Query 2: Search for SSH Services")
    
    results = collection.query(
        query_texts=["SSH secure shell"],
        n_results=5
    )
    
    if results['documents'] and results['documents'][0]:
        for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0]), 1):
            print(f"\nResult {i}:")
            print(f"  IP Address: {metadata.get('ip_address', 'N/A')}")
            
            lines = doc.split('\n')
            for line in lines:
                if 'ssh' in line.lower() or '22/tcp' in line:
                    print(f"  {line.strip()}")
    else:
        print("No SSH services found")


def query_by_port_count(collection):
    """Query hosts with multiple open ports."""
    print_section("Query 3: Hosts with More Than 3 Open Ports")
    
    results = collection.get(
        where={"open_port_count": {"$gt": 3}},
        limit=5
    )
    
    if results['documents']:
        for i, (doc, metadata) in enumerate(zip(results['documents'], results['metadatas']), 1):
            print(f"\nHost {i}:")
            print(f"  IP Address: {metadata.get('ip_address', 'N/A')}")
            print(f"  Hostname: {metadata.get('hostname', 'N/A')}")
            print(f"  Open Ports: {metadata.get('open_port_count', 0)}")
            print("  Services:")
            
            # Extract service lines
            lines = doc.split('\n')
            port_count = 0
            for line in lines:
                if '/' in line and 'tcp' in line.lower() and ':' in line:
                    print(f"    {line.strip()}")
                    port_count += 1
                    if port_count >= 3:  # Show first 3 services
                        remaining = metadata.get('open_port_count', 0) - 3
                        if remaining > 0:
                            print(f"    ... and {remaining} more services")
                        break
    else:
        print("No hosts found with more than 3 open ports")


def query_smb_services(collection):
    """Query for SMB/CIFS services (port 445)."""
    print_section("Query 4: Search for SMB Services (Port 445)")
    
    results = collection.query(
        query_texts=["445 SMB netbios microsoft-ds CIFS"],
        n_results=5
    )
    
    if results['documents'] and results['documents'][0]:
        for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0]), 1):
            print(f"\nResult {i}:")
            print(f"  IP Address: {metadata.get('ip_address', 'N/A')}")
            print(f"  Vendor: {metadata.get('vendor', 'N/A')}")
            
            lines = doc.split('\n')
            for line in lines:
                if '445' in line or 'smb' in line.lower() or 'microsoft-ds' in line.lower():
                    print(f"  {line.strip()}")
    else:
        print("No SMB services found")


def get_all_active_hosts(collection):
    """Get all hosts that are up."""
    print_section("Query 5: All Active Hosts Summary")
    
    results = collection.get(
        where={"state": "up"},
        limit=20
    )
    
    if results['documents']:
        print(f"\nFound {len(results['documents'])} active hosts")
        print("\n" + "-"*70)
        print(f"{'IP Address':<18} {'Hostname':<25} {'Ports':<8} {'Sample Service'}")
        print("-"*70)
        
        for metadata, doc in zip(results['metadatas'], results['documents']):
            ip = metadata.get('ip_address', 'N/A')
            hostname = metadata.get('hostname', 'N/A')[:24]
            ports = metadata.get('open_port_count', 0)
            
            # Extract first service
            lines = doc.split('\n')
            first_service = ""
            for line in lines:
                if '/' in line and ':' in line and 'tcp' in line.lower():
                    parts = line.strip().split(':')
                    if len(parts) >= 2:
                        first_service = parts[0].strip()[-8:] + ":" + parts[1].strip()[:15]
                    break
            
            print(f"{ip:<18} {hostname:<25} {ports:<8} {first_service}")
    else:
        print("No active hosts found")


def custom_query_example(collection):
    """Demonstrate a custom query."""
    print_section("Query 6: Custom Query - Search for Database Services")
    
    results = collection.query(
        query_texts=["database mysql postgresql mongodb redis sql"],
        n_results=5
    )
    
    if results['documents'] and results['documents'][0]:
        for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0]), 1):
            print(f"\nResult {i}:")
            print(f"  IP Address: {metadata.get('ip_address', 'N/A')}")
            
            lines = doc.split('\n')
            for line in lines:
                # Look for common database ports
                if any(port in line for port in ['3306', '5432', '27017', '6379', '1433', 'mysql', 'postgres', 'mongo', 'redis']):
                    print(f"  {line.strip()}")
    else:
        print("No database services found")

def simple_query_example(collection):
    """Demonstrate a simple query."""
    print_section("Query 7: Simple Query - Search for what you enter --> SMTP")

    results = collection.query(
        query_texts=["smtp"],
        n_results=5
    )

    if results['documents'] and results['documents'][0]:
        for i, (doc, metadata) in enumerate(zip(results['documents'][0], results['metadatas'][0]), 1):
            print(f"  IP Address: {metadata.get('ip_address', 'N/A')}")
            print(f"  Hostname: {metadata.get('hostname', 'N/A')}")
    else:
        print("No Results")


def main():
    """Main function to demonstrate all queries."""
    print("\n" + "="*70)
    print("ChromaDB Query Examples - Nmap Data")
    print("="*70)
    print("\nConnecting to ChromaDB and loading 'nmaptest' collection...")
    
    try:
        # Initialize ChromaDB client
        #client = chromadb.Client(Settings(
        #    anonymized_telemetry=False,
        #    allow_reset=True
        #))
        
        # Connect to the Docker ChromaDB server
        client = chromadb.HttpClient(
            host="localhost",
            port=8000,
            # Include token if authentication is enabled
            headers={"Authorization": "Bearer my-secret-token"}
        )


        # Get the collection
        collection = client.get_collection("nmaptest")
        
        print(f"✓ Successfully loaded collection 'nmaptest'")
        print(f"✓ Total documents in collection: {collection.count()}")
        
        # Run all query demonstrations
        query_http_services(collection)
        query_ssh_services(collection)
        query_by_port_count(collection)
        query_smb_services(collection)
        get_all_active_hosts(collection)
        custom_query_example(collection)
        simple_query_example(collection)
        
        print("\n" + "="*70)
        print("Query demonstrations complete!")
        print("="*70)
        print("\nTip: Modify these functions to create your own custom queries")
        print("     based on your specific needs.\n")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nMake sure you have:")
        print("  1. Installed ChromaDB: pip install chromadb")
        print("  2. Run nmap_to_chromadb.py first to import your data")
        print()


if __name__ == "__main__":
    main()
