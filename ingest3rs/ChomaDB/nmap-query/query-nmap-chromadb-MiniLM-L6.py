#!/usr/bin/env python3
"""
ChromaDB Query Examples for Nmap Data
--------------------------------------
This script demonstrates how to query the 'nmaptest' collection
and retrieve IP addresses, ports, and services.

Prerequisites:
- Run query-nmap-chromadb-MiniLM-L6.py first to import your nmap data
- ChromaDB must be installed: pip install chromadb
"""

import argparse
import sys
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


def interactive_mode(collection):
    """Run an interactive query session against the collection."""
    print_section("Interactive Query Mode")
    print(f"Collection: 'nmaptest' ({collection.count()} documents)")
    print("\nCommands:")
    print("  <query>          Search for services/hosts (e.g. 'http', 'ssh', 'mysql')")
    print("  :k <number>      Set number of results to return (default: 5)")
    print("  :all              List all active hosts")
    print("  :ports <n>        Show hosts with more than <n> open ports")
    print("  :count            Show total document count")
    print("  :help             Show this help message")
    print("  :quit / :q        Exit interactive mode")
    print()

    n_results = 5

    while True:
        try:
            user_input = input(f"nmap-query [k={n_results}]> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting interactive mode.")
            break

        if not user_input:
            continue

        # Handle commands
        if user_input.lower() in (":quit", ":q", ":exit"):
            print("Exiting interactive mode.")
            break

        if user_input.lower() == ":help":
            print("\nCommands:")
            print("  <query>          Search for services/hosts")
            print("  :k <number>      Set number of results (current: {})".format(n_results))
            print("  :all             List all active hosts")
            print("  :ports <n>       Show hosts with more than <n> open ports")
            print("  :count           Show total document count")
            print("  :help            Show this help message")
            print("  :quit / :q       Exit interactive mode")
            continue

        if user_input.lower().startswith(":k "):
            try:
                new_k = int(user_input.split()[1])
                if new_k < 1:
                    print("  ⚠ Number of results must be at least 1")
                    continue
                n_results = new_k
                print(f"  ✓ Results per query set to {n_results}")
            except (ValueError, IndexError):
                print("  ⚠ Usage: :k <number>  (e.g. :k 10)")
            continue

        if user_input.lower() == ":count":
            print(f"  Total documents: {collection.count()}")
            continue

        if user_input.lower() == ":all":
            results = collection.get(
                where={"state": "up"},
                limit=100
            )
            if results['documents']:
                print(f"\n  Found {len(results['documents'])} active hosts\n")
                print(f"  {'IP Address':<18} {'Hostname':<25} {'Ports'}")
                print(f"  {'-'*55}")
                for metadata in results['metadatas']:
                    ip = metadata.get('ip_address', 'N/A')
                    hostname = metadata.get('hostname', 'N/A')[:24]
                    ports = metadata.get('open_port_count', 0)
                    print(f"  {ip:<18} {hostname:<25} {ports}")
            else:
                print("  No active hosts found")
            continue

        if user_input.lower().startswith(":ports"):
            try:
                threshold = int(user_input.split()[1]) if len(user_input.split()) > 1 else 3
            except ValueError:
                threshold = 3
            results = collection.get(
                where={"open_port_count": {"$gt": threshold}},
                limit=n_results
            )
            if results['documents']:
                print(f"\n  Hosts with more than {threshold} open ports:")
                for i, (doc, metadata) in enumerate(zip(results['documents'], results['metadatas']), 1):
                    print(f"\n  [{i}] {metadata.get('ip_address', 'N/A')} "
                          f"({metadata.get('hostname', 'N/A')}) - "
                          f"{metadata.get('open_port_count', 0)} open ports")
                    lines = doc.split('\n')
                    shown = 0
                    for line in lines:
                        if '/' in line and 'tcp' in line.lower() and ':' in line:
                            print(f"      {line.strip()}")
                            shown += 1
                            if shown >= 5:
                                remaining = metadata.get('open_port_count', 0) - shown
                                if remaining > 0:
                                    print(f"      ... and {remaining} more")
                                break
            else:
                print(f"  No hosts found with more than {threshold} open ports")
            continue

        # Default: treat input as a semantic search query
        results = collection.query(
            query_texts=[user_input],
            n_results=n_results
        )

        if results['documents'] and results['documents'][0]:
            print(f"\n  Top {len(results['documents'][0])} results for '{user_input}':\n")
            for i, (doc, metadata, distance) in enumerate(
                zip(results['documents'][0], results['metadatas'][0], results['distances'][0]), 1
            ):
                ip = metadata.get('ip_address', 'N/A')
                hostname = metadata.get('hostname', 'N/A')
                ports = metadata.get('open_port_count', 0)
                print(f"  [{i}] {ip} ({hostname}) - {ports} open ports  [score: {distance:.4f}]")

                # Show matching lines from the document
                lines = doc.split('\n')
                query_terms = user_input.lower().split()
                shown = 0
                for line in lines:
                    if any(term in line.lower() for term in query_terms):
                        print(f"      {line.strip()}")
                        shown += 1
                        if shown >= 3:
                            break
                # If no specific matches found, show first service line
                if shown == 0:
                    for line in lines:
                        if '/' in line and ':' in line:
                            print(f"      {line.strip()}")
                            break
            print()
        else:
            print(f"  No results found for '{user_input}'")


def main():
    """Main function to demonstrate all queries."""
    parser = argparse.ArgumentParser(
        description="ChromaDB Query Examples for Nmap Data"
    )
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Launch interactive query mode"
    )
    args = parser.parse_args()

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
        
        if args.interactive:
            interactive_mode(collection)
        else:
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
            print("\nTip: Run with -i or --interactive for interactive query mode")
            print("     Modify these functions to create your own custom queries")
            print("     based on your specific needs.\n")
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        print("\nMake sure you have:")
        print("  1. Installed ChromaDB: pip install chromadb")
        print("  2. Run query-nmap-chromadb-MiniLM-L6.py first to import your data")
        print()


if __name__ == "__main__":
    main()
