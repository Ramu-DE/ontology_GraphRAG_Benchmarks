#!/usr/bin/env python3
"""
Simple Neo4j Connection Test
Tests connection and shows current database state
"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_connection():
    """Test Neo4j connection and show database info"""

    uri = os.getenv("NEO4J_URI")
    username = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE")

    print("="*80)
    print("NEO4J CONNECTION TEST")
    print("="*80)
    print(f"\nURI:      {uri}")
    print(f"Username: {username}")
    print(f"Database: {database}")
    print()

    try:
        # Connect to Neo4j
        driver = GraphDatabase.driver(uri, auth=(username, password))

        # Verify connectivity
        driver.verify_connectivity()
        print("✅ Connection successful!")

        with driver.session(database=database) as session:
            # Get database info
            print("\n" + "="*80)
            print("DATABASE STATISTICS")
            print("="*80)

            # Total nodes
            result = session.run("MATCH (n) RETURN count(n) as count")
            total_nodes = result.single()["count"]
            print(f"\nTotal nodes: {total_nodes:,}")

            # Total relationships
            result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            total_rels = result.single()["count"]
            print(f"Total relationships: {total_rels:,}")

            # Node labels
            result = session.run("CALL db.labels()")
            labels = [record["label"] for record in result]
            print(f"\nNode labels ({len(labels)}):")
            for label in labels:
                result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
                count = result.single()["count"]
                print(f"  - {label}: {count:,}")

            # Relationship types
            result = session.run("CALL db.relationshipTypes()")
            rel_types = [record["relationshipType"] for record in result]
            print(f"\nRelationship types ({len(rel_types)}):")
            for rel_type in rel_types:
                result = session.run(f"MATCH ()-[r:{rel_type}]->() RETURN count(r) as count")
                count = result.single()["count"]
                print(f"  - {rel_type}: {count:,}")

            # Check for vector indices
            print("\n" + "="*80)
            print("INDICES")
            print("="*80)
            result = session.run("SHOW INDEXES")
            indices = list(result)
            if indices:
                print(f"\nFound {len(indices)} indices:")
                for idx in indices:
                    print(f"  - {idx['name']}: {idx['type']} on {idx.get('labelsOrTypes', 'N/A')}")
            else:
                print("\nNo indices found")

            # Sample data
            print("\n" + "="*80)
            print("SAMPLE DATA (first 5 nodes)")
            print("="*80)
            result = session.run("MATCH (n) RETURN labels(n) as labels, properties(n) as props LIMIT 5")
            for i, record in enumerate(result, 1):
                print(f"\n{i}. {record['labels']}")
                for key, value in record['props'].items():
                    if key != 'embedding':  # Skip embedding vectors
                        print(f"   {key}: {value}")

        driver.close()

        print("\n" + "="*80)
        print("✅ TEST COMPLETE")
        print("="*80)

    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        print("\nTroubleshooting:")
        print("  1. Check credentials in .env file")
        print("  2. Verify Neo4j Aura instance is running")
        print("  3. Check network connectivity")
        return False

    return True

if __name__ == "__main__":
    test_connection()
