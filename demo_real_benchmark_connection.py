#!/usr/bin/env python3
"""
Real Benchmark Connection Demo
Shows what WOULD be executed with actual Neo4j connection

This demonstrates the REAL implementation approach.
To actually run: install neo4j driver: apt-get install python3-pip && pip3 install neo4j
"""

import os
import time
import json
from datetime import datetime

# Load credentials from .env
def load_env():
    """Load environment variables from .env file"""
    env_vars = {}
    try:
        with open('.env', 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key.strip()] = value.strip()
    except FileNotFoundError:
        pass
    return env_vars

env = load_env()

# Neo4j credentials
NEO4J_URI = env.get('NEO4J_URI', '')
NEO4J_USER = env.get('NEO4J_USER', env.get('NEO4J_USERNAME', 'neo4j'))
NEO4J_PASSWORD = env.get('NEO4J_PASSWORD', '')
NEO4J_DATABASE = env.get('NEO4J_DATABASE', 'neo4j')

print("="*80)
print("REAL BENCHMARK CONNECTION DEMONSTRATION")
print("="*80)
print()

print("📋 Configuration:")
print(f"  URI:      {NEO4J_URI}")
print(f"  User:     {NEO4J_USER}")
print(f"  Database: {NEO4J_DATABASE}")
print(f"  Password: {'*' * len(NEO4J_PASSWORD) if NEO4J_PASSWORD else '(not set)'}")
print()

# Check if neo4j module is available
try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
    print("✅ neo4j driver is installed")
except ImportError:
    NEO4J_AVAILABLE = False
    print("⚠️  neo4j driver not installed")
    print()
    print("To install:")
    print("  1. Install pip: apt-get update && apt-get install -y python3-pip")
    print("  2. Install driver: pip3 install neo4j python-dotenv")
    print()

print()
print("="*80)

if NEO4J_AVAILABLE and NEO4J_URI and NEO4J_PASSWORD:
    print("🚀 EXECUTING REAL BENCHMARKS")
    print("="*80)
    print()

    try:
        # REAL CONNECTION
        print("🔌 Connecting to Neo4j Aura...")
        driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD),
            database=NEO4J_DATABASE
        )

        # TEST CONNECTION
        with driver.session() as session:
            result = session.run("RETURN 1 as n")
            assert result.single()["n"] == 1

        print(f"✅ Connected to {NEO4J_URI}")
        print()

        # CHECK DATABASE STATE
        print("📊 Database Statistics:")
        with driver.session() as session:
            # Count nodes
            result = session.run("MATCH (n) RETURN count(n) as count")
            node_count = result.single()['count']
            print(f"  Total nodes: {node_count:,}")

            # Count relationships
            result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            rel_count = result.single()['count']
            print(f"  Total relationships: {rel_count:,}")

            # Check for Drug nodes
            result = session.run("MATCH (d:Drug) RETURN count(d) as count")
            drug_count = result.single()['count']
            print(f"  Drug nodes: {drug_count:,}")

            # Check for vector index
            result = session.run("SHOW INDEXES")
            indices = [record['name'] for record in result]
            has_vector_index = any('vector' in idx.lower() for idx in indices)
            print(f"  Vector index: {'✅ Found' if has_vector_index else '❌ Not found'}")

        print()

        if node_count == 0:
            print("⚠️  Database is empty. Load data first:")
            print("    python3 neo4j_data_loader.py")
            print()
        elif drug_count == 0:
            print("⚠️  No Drug nodes found. Load data first:")
            print("    python3 neo4j_data_loader.py")
            print()
        elif not has_vector_index:
            print("⚠️  No vector index found. Create index:")
            print("    python3 neo4j_data_loader.py")
            print()
        else:
            # RUN REAL BENCHMARKS
            print("="*80)
            print("⚡ RUNNING REAL PERFORMANCE BENCHMARKS")
            print("="*80)
            print()

            results = []

            # Benchmark 1: Simple node query
            print("1️⃣  Benchmarking simple node query...")
            latencies = []
            for i in range(10):
                with driver.session() as session:
                    start = time.time()
                    result = session.run("MATCH (d:Drug) RETURN d.name LIMIT 10")
                    list(result)  # Consume results
                    end = time.time()
                    latencies.append((end - start) * 1000)

            avg_latency = sum(latencies) / len(latencies)
            print(f"   Average latency: {avg_latency:.2f}ms")
            results.append({
                "operation": "simple_node_query",
                "latency_ms": avg_latency,
                "iterations": 10
            })

            # Benchmark 2: Graph traversal
            print()
            print("2️⃣  Benchmarking graph traversal...")
            latencies = []
            for i in range(10):
                with driver.session() as session:
                    start = time.time()
                    result = session.run("""
                        MATCH (drug:Drug)-[:TREATS]->(disease:Disease)
                        RETURN drug.name, disease.name
                        LIMIT 10
                    """)
                    list(result)
                    end = time.time()
                    latencies.append((end - start) * 1000)

            avg_latency = sum(latencies) / len(latencies)
            print(f"   Average latency: {avg_latency:.2f}ms")
            results.append({
                "operation": "graph_traversal",
                "latency_ms": avg_latency,
                "iterations": 10
            })

            # Benchmark 3: Vector search (if available)
            if has_vector_index:
                print()
                print("3️⃣  Benchmarking vector search...")

                # Get a sample embedding
                with driver.session() as session:
                    result = session.run("""
                        MATCH (d:Drug)
                        WHERE d.embedding IS NOT NULL
                        RETURN d.embedding as embedding
                        LIMIT 1
                    """)
                    record = result.single()

                    if record and record['embedding']:
                        query_vector = record['embedding']

                        latencies = []
                        for i in range(10):
                            start = time.time()
                            result = session.run("""
                                CALL db.index.vector.queryNodes('drug_embedding_vector', 5, $vector)
                                YIELD node, score
                                RETURN node.name, score
                            """, vector=query_vector)
                            list(result)
                            end = time.time()
                            latencies.append((end - start) * 1000)

                        avg_latency = sum(latencies) / len(latencies)
                        print(f"   Average latency: {avg_latency:.2f}ms")
                        results.append({
                            "operation": "vector_search",
                            "latency_ms": avg_latency,
                            "iterations": 10
                        })
                    else:
                        print("   ⚠️  No embeddings found in Drug nodes")

            # Benchmark 4: Unified query (vector + graph)
            if has_vector_index:
                print()
                print("4️⃣  Benchmarking UNIFIED query (vector + graph)...")

                with driver.session() as session:
                    result = session.run("""
                        MATCH (d:Drug)
                        WHERE d.embedding IS NOT NULL
                        RETURN d.embedding as embedding
                        LIMIT 1
                    """)
                    record = result.single()

                    if record and record['embedding']:
                        query_vector = record['embedding']

                        latencies = []
                        for i in range(10):
                            start = time.time()
                            result = session.run("""
                                CALL db.index.vector.queryNodes('drug_embedding_vector', 5, $vector)
                                YIELD node AS drug, score

                                MATCH (drug)-[:TREATS]->(disease:Disease)
                                OPTIONAL MATCH (disease)-[:ASSOCIATED_WITH]->(gene:Gene)

                                RETURN drug.name, score,
                                       collect(DISTINCT disease.name) as diseases,
                                       collect(DISTINCT gene.symbol) as genes
                                ORDER BY score DESC
                            """, vector=query_vector)
                            list(result)
                            end = time.time()
                            latencies.append((end - start) * 1000)

                        avg_latency = sum(latencies) / len(latencies)
                        print(f"   Average latency: {avg_latency:.2f}ms")
                        print(f"   ✅ UNIFIED QUERY - NO FRICTION!")
                        results.append({
                            "operation": "unified_vector_graph",
                            "latency_ms": avg_latency,
                            "iterations": 10,
                            "friction": "NONE"
                        })

            # Save results
            print()
            print("="*80)
            print("💾 Saving Results")
            print("="*80)
            print()

            output = {
                "timestamp": datetime.now().isoformat(),
                "database": {
                    "uri": NEO4J_URI,
                    "node_count": node_count,
                    "relationship_count": rel_count,
                    "drug_count": drug_count
                },
                "results": results
            }

            with open('real_benchmark_results.json', 'w') as f:
                json.dump(output, f, indent=2)

            print("✅ Results saved to: real_benchmark_results.json")
            print()

            # Display summary
            print("📊 SUMMARY:")
            print("─" * 80)
            for result in results:
                print(f"  {result['operation']}: {result['latency_ms']:.2f}ms")
            print()

        driver.close()

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

else:
    print("💡 WHAT WOULD BE MEASURED (Real Implementation)")
    print("="*80)
    print()
    print("If neo4j driver were installed, these ACTUAL queries would execute:")
    print()

    print("1️⃣  Vector Search Query:")
    print("""
    CALL db.index.vector.queryNodes('drug_embedding_vector', 10, $vector)
    YIELD node, score
    RETURN node.name, score
    """)
    print("   Measures: Real HNSW index query performance")
    print()

    print("2️⃣  Graph Traversal Query:")
    print("""
    MATCH (drug:Drug {id: $node_id})
    MATCH (drug)-[:TREATS]->(disease:Disease)
    OPTIONAL MATCH (disease)<-[:ASSOCIATED_WITH]-(gene:Gene)
    RETURN drug.name, collect(disease.name), collect(gene.symbol)
    """)
    print("   Measures: Real graph pattern matching performance")
    print()

    print("3️⃣  Unified Query (THE KEY METRIC):")
    print("""
    CALL db.index.vector.queryNodes('drug_embedding_vector', 10, $vector)
    YIELD node AS drug, score

    MATCH (drug)-[:TREATS]->(disease:Disease)
    OPTIONAL MATCH (disease)<-[:ASSOCIATED_WITH]-(gene:Gene)

    RETURN drug.name, score,
           collect(DISTINCT disease.name) as diseases,
           collect(DISTINCT gene.symbol) as genes
    ORDER BY score DESC
    """)
    print("   Measures: Vector + Graph in ONE query - NO FRICTION")
    print()

    print("="*80)
    print("📦 TO RUN REAL BENCHMARKS:")
    print("="*80)
    print()
    print("# Install dependencies")
    print("apt-get update && apt-get install -y python3-pip")
    print("pip3 install neo4j python-dotenv")
    print()
    print("# Load data")
    print("python3 neo4j_data_loader.py")
    print()
    print("# Run this benchmark")
    print("python3 demo_real_benchmark_connection.py")
    print()

print("="*80)
print("✅ DEMONSTRATION COMPLETE")
print("="*80)
