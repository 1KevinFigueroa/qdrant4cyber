from collections import Counter
import json
from typing import List, Dict, Any


class AmassQueryAnalyzer:
    """Analyzes Qdrant query results for three types of information"""
    
    def __init__(self, points: List[Dict[str, Any]]):
        self.points = points
    
    def analyze_relation_statistics(self) -> Dict[str, int]:
        """Type 1: Query statistics by relation type"""
        relations = [p['payload']['relation'] for p in self.points]
        return dict(Counter(relations))
    
    def extract_network_assets(self) -> Dict[str, List[Dict[str, str]]]:
        """Type 2: Extract and categorize network assets (IPs vs Domains)"""
        ip_addresses = []
        domains = []
        
        for point in self.points:
            source = point['payload']['source']
            target = point['payload']['target']
            
            if 'IPAddress' in source:
                ip_addresses.append({'id': point['id'], 'value': source, 'relation': point['payload']['relation']})
            elif 'FQDN' in source or '.ru' in source or '.com' in source:
                domains.append({'id': point['id'], 'value': source, 'relation': point['payload']['relation']})
            
            if 'IPAddress' in target:
                ip_addresses.append({'id': point['id'], 'value': target, 'relation': point['payload']['relation']})
            elif 'FQDN' in target or '.ru' in target or '.com' in target:
                domains.append({'id': point['id'], 'value': target, 'relation': point['payload']['relation']})
        
        return {'ip_addresses': ip_addresses, 'domains': domains}
    
    def query_high_confidence_relations(self, min_score: float = 0.85) -> List[Dict[str, Any]]:
        """Type 3: Query relations with high confidence scores"""
        high_confidence_points = [
            point for point in self.points 
            if point['score'] >= min_score
        ]
        return sorted(high_confidence_points, key=lambda x: x['score'], reverse=True)

def main():
    analyzer = AmassQueryAnalyzer(points)
    
    print("=" * 80)
    print("AMASS QUERY RESULTS ANALYZER")
    print("=" * 80)
    
    # Query Type 1: Relation Statistics
    print("\n[TYPE 1] RELATION TYPE STATISTICS:")
    print("-" * 40)
    relation_stats = analyzer.analyze_relation_statistics()
    for rel, count in relation_stats.items():
        percentage = (count / len(points)) * 100
        print(f"  {rel}: {count} points ({percentage:.1f}%)")
    
    # Query Type 2: Network Assets Extraction
    print("\n[TYPE 2] NETWORK ASSETS EXTRACTION:")
    print("-" * 40)
    assets = analyzer.extract_network_assets()
    print(f"\n  IP Addresses Found: {len(assets['ip_addresses'])}")
    for ip in assets['ip_addresses']:
        print(f"    - [{ip['relation']}] {ip['value']}")
    
    print(f"\n  Domains Found: {len(assets['domains'])}")
    for domain in assets['domains']:
        print(f"    - [{domain['relation']}] {domain['value']}")
    
    # Query Type 3: High Confidence Relations
    print("\n[TYPE 3] HIGH CONFIDENCE RELATIONS (score >= 0.85):")
    print("-" * 40)
    high_conf = analyzer.query_high_confidence_relations(min_score=0.85)
    for point in high_conf:
        print(f"\n  ID: {point['id']} | Score: {point['score']:.4f}")
        print(f"    Source -> Target")
        print(f"      {point['payload']['source']}")
        print(f"      ↓ ({point['payload']['relation']})")
        print(f"      {point['payload']['target']}")
    
    # Summary Statistics
    print("\n" + "=" * 80)
    print("SUMMARY:")
    print("=" * 80)
    print(f"Total Points Analyzed: {len(points)}")
    print(f"Unique Relations: {len(relation_stats)}")
    print(f"High Confidence Relations: {len(high_conf)}")
    print(f"IP Addresses Found: {len(assets['ip_addresses'])}")
    print(f"Domains Found: {len(assets['domains'])}")

if __name__ == "__main__":
    main()
