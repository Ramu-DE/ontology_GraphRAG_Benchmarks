#!/usr/bin/env python3
"""
Real GraphRAG Performance Benchmark
Connects to actual databases and measures real performance

Requirements:
- Neo4j Aura (we have credentials)
- AWS Neptune Database + OpenSearch (need setup)
- AWS Neptune Analytics (need setup)

This measures ACTUAL performance, not simulations.
"""

import time
import json
import statistics
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

# Database clients
try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("⚠️  neo4j package not installed. Install: pip install neo4j")

try:
    from gremlin_python.driver import client as gremlin_client
    from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
    from gremlin_python.process.anonymous_traversal import traversal
    NEPTUNE_AVAILABLE = True
except ImportError:
    NEPTUNE_AVAILABLE = False
    print("⚠️  gremlinpython package not installed. Install: pip install gremlinpython")

try:
    from opensearchpy import OpenSearch
    OPENSEARCH_AVAILABLE = True
except ImportError:
    OPENSEARCH_AVAILABLE = False
    print("⚠️  opensearch-py package not installed. Install: pip install opensearch-py")


# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class BenchmarkConfig:
    """Real benchmark configuration"""
    scales: List[int]
    iterations: int = 10
    k: int = 10  # Top-k results
    vector_dim: int = 384

    # Database credentials
    neo4j_uri: str = ""
    neo4j_user: str = ""
    neo4j_password: str = ""

    neptune_endpoint: str = ""
    neptune_port: int = 8182

    opensearch_host: str = ""
    opensearch_port: int = 9200

    neptune_analytics_endpoint: str = ""


@dataclass
class RealBenchmarkResult:
    """Results from actual database measurements"""
    architecture: str
    scale: int
    operation: str
    latency_ms: float
    iterations: int
    timestamp: str
    query: str
    metadata: Dict[str, Any]


# ============================================================================
# NEO4J REAL BENCHMARK
# ============================================================================

class Neo4jRealBenchmark:
    """
    Benchmark Neo4j Aura with real queries
    We have credentials, so this can run NOW
    """

    def __init__(self, uri: str, user: str, password: str):
        if not NEO4J_AVAILABLE:
            raise RuntimeError("neo4j package not installed")

        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.uri = uri

    def close(self):
        """Close database connection"""
        self.driver.close()

    def verify_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1 as n")
                return result.single()["n"] == 1
        except Exception as e:
            print(f"❌ Neo4j connection failed: {e}")
            return False

    def get_node_count(self) -> int:
        """Get current node count"""
        with self.driver.session() as session:
            result = session.run("MATCH (n) RETURN count(n) as count")
            return result.single()["count"]

    def check_vector_index(self, index_name: str = "drug_embedding_vector") -> bool:
        """Check if vector index exists"""
        with self.driver.session() as session:
            result = session.run("SHOW INDEXES")
            indices = [record["name"] for record in result]
            return index_name in indices

    def benchmark_vector_search(self, query_vector: List[float], k: int = 10,
                               iterations: int = 10) -> RealBenchmarkResult:
        """
        Benchmark real vector search on Neo4j
        """
        query = """
        CALL db.index.vector.queryNodes('drug_embedding_vector', $k, $vector)
        YIELD node, score
        RETURN node.name as name, score
        LIMIT $k
        """

        latencies = []

        with self.driver.session() as session:
            # Warm-up query
            session.run(query, k=k, vector=query_vector).consume()

            # Actual measurements
            for _ in range(iterations):
                start = time.time()
                result = session.run(query, k=k, vector=query_vector)
                result.consume()  # Ensure query completes
                end = time.time()

                latencies.append((end - start) * 1000)

        return RealBenchmarkResult(
            architecture="Neo4j Aura",
            scale=self.get_node_count(),
            operation="vector_search",
            latency_ms=statistics.mean(latencies),
            iterations=iterations,
            timestamp=datetime.now().isoformat(),
            query=query,
            metadata={
                "min_ms": min(latencies),
                "max_ms": max(latencies),
                "median_ms": statistics.median(latencies),
                "stdev_ms": statistics.stdev(latencies) if len(latencies) > 1 else 0,
                "k": k,
                "vector_dim": len(query_vector)
            }
        )

    def benchmark_graph_traversal(self, start_node_id: str, iterations: int = 10) -> RealBenchmarkResult:
        """
        Benchmark real graph traversal on Neo4j
        """
        query = """
        MATCH (drug:Drug {id: $node_id})
        MATCH (drug)-[:TREATS]->(disease:Disease)
        OPTIONAL MATCH (disease)<-[:ASSOCIATED_WITH]-(gene:Gene)
        RETURN drug.name, collect(DISTINCT disease.name) as diseases,
               collect(DISTINCT gene.symbol) as genes
        """

        latencies = []

        with self.driver.session() as session:
            # Warm-up
            session.run(query, node_id=start_node_id).consume()

            # Measurements
            for _ in range(iterations):
                start = time.time()
                result = session.run(query, node_id=start_node_id)
                result.consume()
                end = time.time()

                latencies.append((end - start) * 1000)

        return RealBenchmarkResult(
            architecture="Neo4j Aura",
            scale=self.get_node_count(),
            operation="graph_traversal",
            latency_ms=statistics.mean(latencies),
            iterations=iterations,
            timestamp=datetime.now().isoformat(),
            query=query,
            metadata={
                "min_ms": min(latencies),
                "max_ms": max(latencies),
                "median_ms": statistics.median(latencies),
                "stdev_ms": statistics.stdev(latencies) if len(latencies) > 1 else 0
            }
        )

    def benchmark_unified_query(self, query_vector: List[float], k: int = 10,
                               iterations: int = 10) -> RealBenchmarkResult:
        """
        Benchmark unified vector + graph query (THE HOLY GRAIL)
        This is the key metric - vector search AND graph traversal in ONE query
        """
        query = """
        // Vector search + Graph traversal in ONE query
        CALL db.index.vector.queryNodes('drug_embedding_vector', $k, $vector)
        YIELD node AS drug, score

        // Graph traversal (same query!)
        MATCH (drug)-[:TREATS]->(disease:Disease)
        OPTIONAL MATCH (disease)<-[:ASSOCIATED_WITH]-(gene:Gene)

        RETURN drug.name, score,
               collect(DISTINCT disease.name) as diseases,
               collect(DISTINCT gene.symbol) as genes
        ORDER BY score DESC
        LIMIT $k
        """

        latencies = []

        with self.driver.session() as session:
            # Warm-up
            session.run(query, k=k, vector=query_vector).consume()

            # Measurements
            for _ in range(iterations):
                start = time.time()
                result = session.run(query, k=k, vector=query_vector)
                result.consume()
                end = time.time()

                latencies.append((end - start) * 1000)

        return RealBenchmarkResult(
            architecture="Neo4j Aura",
            scale=self.get_node_count(),
            operation="unified_vector_graph",
            latency_ms=statistics.mean(latencies),
            iterations=iterations,
            timestamp=datetime.now().isoformat(),
            query=query,
            metadata={
                "min_ms": min(latencies),
                "max_ms": max(latencies),
                "median_ms": statistics.median(latencies),
                "stdev_ms": statistics.stdev(latencies) if len(latencies) > 1 else 0,
                "k": k,
                "vector_dim": len(query_vector),
                "friction": "NONE - unified query"
            }
        )


# ============================================================================
# NEPTUNE + OPENSEARCH REAL BENCHMARK
# ============================================================================

class NeptuneOpenSearchRealBenchmark:
    """
    Benchmark Neptune Database + OpenSearch (two-layer architecture)
    Measures REAL two-layer friction
    """

    def __init__(self, neptune_endpoint: str, opensearch_host: str,
                 neptune_port: int = 8182, opensearch_port: int = 9200):
        if not NEPTUNE_AVAILABLE:
            raise RuntimeError("gremlinpython not installed")
        if not OPENSEARCH_AVAILABLE:
            raise RuntimeError("opensearch-py not installed")

        # Neptune connection
        self.neptune_endpoint = f"wss://{neptune_endpoint}:{neptune_port}/gremlin"
        self.neptune_client = gremlin_client.Client(
            self.neptune_endpoint, 'g'
        )

        # OpenSearch connection
        self.opensearch = OpenSearch(
            hosts=[{'host': opensearch_host, 'port': opensearch_port}],
            http_compress=True,
            use_ssl=True,
            verify_certs=True
        )

    def verify_connection(self) -> bool:
        """Test both connections"""
        try:
            # Test Neptune
            result = self.neptune_client.submit("g.V().limit(1).count()").all().result()

            # Test OpenSearch
            self.opensearch.info()

            return True
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False

    def benchmark_two_layer(self, query_vector: List[float], k: int = 10,
                           iterations: int = 10) -> Dict[str, RealBenchmarkResult]:
        """
        Benchmark the TWO-LAYER approach:
        1. OpenSearch vector search
        2. Serialize results
        3. Network transfer
        4. Neptune graph traversal

        This measures REAL friction
        """
        results = {}

        # Phase 1: OpenSearch vector search
        opensearch_latencies = []
        candidate_ids = []

        for _ in range(iterations):
            start = time.time()

            search_body = {
                "size": k,
                "query": {
                    "knn": {
                        "embedding": {
                            "vector": query_vector,
                            "k": k
                        }
                    }
                }
            }

            response = self.opensearch.search(
                index="drugs",
                body=search_body
            )

            end = time.time()
            opensearch_latencies.append((end - start) * 1000)

            # Extract IDs for Neptune query
            candidate_ids = [hit["_id"] for hit in response["hits"]["hits"]]

        results["phase1_opensearch"] = RealBenchmarkResult(
            architecture="Neptune + OpenSearch (Two-Layer)",
            scale=0,  # Will update
            operation="vector_search_opensearch",
            latency_ms=statistics.mean(opensearch_latencies),
            iterations=iterations,
            timestamp=datetime.now().isoformat(),
            query="OpenSearch KNN query",
            metadata={
                "min_ms": min(opensearch_latencies),
                "max_ms": max(opensearch_latencies),
                "friction_point": "PHASE 1: Vector search"
            }
        )

        # Phase 2: Neptune graph traversal (with handover overhead)
        neptune_latencies = []
        serialization_time = []
        network_time = []

        for _ in range(iterations):
            # Measure serialization
            ser_start = time.time()
            ids_string = ",".join([f"'{id}'" for id in candidate_ids])
            ser_end = time.time()
            serialization_time.append((ser_end - ser_start) * 1000)

            # Network + Neptune query
            net_start = time.time()

            gremlin_query = f"""
            g.V().hasId({ids_string})
                 .out('TREATS')
                 .dedup()
                 .valueMap()
            """

            result = self.neptune_client.submit(gremlin_query).all().result()

            net_end = time.time()
            neptune_latencies.append((net_end - net_start) * 1000)
            network_time.append((net_end - net_start) * 1000)

        results["phase2_neptune"] = RealBenchmarkResult(
            architecture="Neptune + OpenSearch (Two-Layer)",
            scale=0,
            operation="graph_traversal_neptune",
            latency_ms=statistics.mean(neptune_latencies),
            iterations=iterations,
            timestamp=datetime.now().isoformat(),
            query=gremlin_query,
            metadata={
                "min_ms": min(neptune_latencies),
                "max_ms": max(neptune_latencies),
                "friction_point": "PHASE 2: Graph traversal + network"
            }
        )

        results["overhead_serialization"] = RealBenchmarkResult(
            architecture="Neptune + OpenSearch (Two-Layer)",
            scale=0,
            operation="serialization_overhead",
            latency_ms=statistics.mean(serialization_time),
            iterations=iterations,
            timestamp=datetime.now().isoformat(),
            query="ID list serialization",
            metadata={
                "friction_point": "OVERHEAD: Serialization"
            }
        )

        # Calculate total two-layer latency
        total_latencies = [
            opensearch_latencies[i] + serialization_time[i] + neptune_latencies[i]
            for i in range(iterations)
        ]

        results["total_two_layer"] = RealBenchmarkResult(
            architecture="Neptune + OpenSearch (Two-Layer)",
            scale=0,
            operation="total_with_friction",
            latency_ms=statistics.mean(total_latencies),
            iterations=iterations,
            timestamp=datetime.now().isoformat(),
            query="OpenSearch + Neptune (two operations)",
            metadata={
                "opensearch_ms": statistics.mean(opensearch_latencies),
                "serialization_ms": statistics.mean(serialization_time),
                "neptune_ms": statistics.mean(neptune_latencies),
                "total_friction_ms": statistics.mean(serialization_time),
                "friction_percentage": (statistics.mean(serialization_time) /
                                       statistics.mean(total_latencies)) * 100
            }
        )

        return results


# ============================================================================
# DATA GENERATION FOR REAL BENCHMARKS
# ============================================================================

class DataGenerator:
    """Generate realistic data for benchmarks"""

    @staticmethod
    def generate_drug_embedding(drug_name: str, dim: int = 384) -> List[float]:
        """
        Generate embedding for a drug
        In production, use SentenceTransformers or OpenAI embeddings
        """
        import hashlib
        import random

        # Use drug name as seed for reproducibility
        seed = int(hashlib.md5(drug_name.encode()).hexdigest(), 16) % (2**32)
        random.seed(seed)

        # Generate normalized vector
        vector = [random.gauss(0, 1) for _ in range(dim)]

        # Normalize
        magnitude = sum(x**2 for x in vector) ** 0.5
        return [x / magnitude for x in vector]

    @staticmethod
    def generate_query_vector(dim: int = 384) -> List[float]:
        """Generate a random query vector"""
        import random
        vector = [random.gauss(0, 1) for _ in range(dim)]
        magnitude = sum(x**2 for x in vector) ** 0.5
        return [x / magnitude for x in vector]


# ============================================================================
# BENCHMARK ORCHESTRATOR
# ============================================================================

class RealBenchmarkRunner:
    """
    Orchestrates real benchmarks across multiple databases
    """

    def __init__(self, config: BenchmarkConfig):
        self.config = config
        self.results = []

    def run_neo4j_benchmarks(self) -> List[RealBenchmarkResult]:
        """Run benchmarks on Neo4j Aura"""
        print("\n" + "="*80)
        print("🚀 Running REAL Neo4j Aura Benchmarks")
        print("="*80)

        if not self.config.neo4j_uri:
            print("❌ Neo4j credentials not configured")
            return []

        benchmark = Neo4jRealBenchmark(
            self.config.neo4j_uri,
            self.config.neo4j_user,
            self.config.neo4j_password
        )

        # Verify connection
        if not benchmark.verify_connection():
            print("❌ Cannot connect to Neo4j")
            return []

        print(f"✅ Connected to Neo4j: {self.config.neo4j_uri}")

        # Check current state
        node_count = benchmark.get_node_count()
        print(f"📊 Current node count: {node_count:,}")

        has_vector_index = benchmark.check_vector_index()
        print(f"🔍 Vector index exists: {has_vector_index}")

        if not has_vector_index:
            print("⚠️  No vector index found. You need to:")
            print("   1. Load data with embeddings")
            print("   2. Create vector index")
            print("   See setup guide below.")
            return []

        results = []

        # Generate test query
        query_vector = DataGenerator.generate_query_vector(self.config.vector_dim)

        # Benchmark 1: Vector search only
        print("\n🔍 Benchmarking vector search...")
        result = benchmark.benchmark_vector_search(
            query_vector,
            k=self.config.k,
            iterations=self.config.iterations
        )
        results.append(result)
        print(f"   Average latency: {result.latency_ms:.2f}ms")

        # Benchmark 2: Unified vector + graph
        print("\n⚡ Benchmarking unified query (vector + graph)...")
        result = benchmark.benchmark_unified_query(
            query_vector,
            k=self.config.k,
            iterations=self.config.iterations
        )
        results.append(result)
        print(f"   Average latency: {result.latency_ms:.2f}ms")
        print(f"   ✅ NO FRICTION - unified query!")

        benchmark.close()
        return results

    def run_neptune_opensearch_benchmarks(self) -> List[RealBenchmarkResult]:
        """Run benchmarks on Neptune + OpenSearch"""
        print("\n" + "="*80)
        print("🚀 Running REAL Neptune + OpenSearch Benchmarks")
        print("="*80)

        if not self.config.neptune_endpoint or not self.config.opensearch_host:
            print("❌ Neptune/OpenSearch credentials not configured")
            return []

        # Implementation would go here
        print("⚠️  Neptune + OpenSearch setup required")
        return []

    def save_results(self, filename: str = "real_benchmark_results.json"):
        """Save results to JSON"""
        output = {
            "timestamp": datetime.now().isoformat(),
            "config": {
                "scales": self.config.scales,
                "iterations": self.config.iterations,
                "k": self.config.k,
                "vector_dim": self.config.vector_dim
            },
            "results": [asdict(r) for r in self.results]
        }

        with open(filename, 'w') as f:
            json.dump(output, f, indent=2)

        print(f"\n✅ Results saved to {filename}")


# ============================================================================
# SETUP GUIDE
# ============================================================================

def print_setup_guide():
    """Print setup instructions for real benchmarks"""
    print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                    REAL BENCHMARK SETUP GUIDE                              ║
╚════════════════════════════════════════════════════════════════════════════╝

📋 Prerequisites:
    1. Neo4j Aura account (we have credentials!)
    2. AWS Neptune Database + OpenSearch
    3. AWS Neptune Analytics (optional)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1️⃣  NEO4J AURA SETUP (READY TO USE)

    We have credentials:
    • URI: neo4j+s://cad612f1.databases.neo4j.io
    • User: neo4j
    • Password: (in .env file)

    Install client:
    $ pip install neo4j

    Load data script will be provided in next file.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

2️⃣  NEPTUNE DATABASE + OPENSEARCH SETUP

    A. Create Neptune cluster:
    $ aws neptune create-db-cluster \\
        --db-cluster-identifier graphrag-benchmark \\
        --engine neptune \\
        --master-username admin \\
        --master-user-password YourPassword

    B. Create OpenSearch domain:
    $ aws opensearch create-domain \\
        --domain-name graphrag-vectors \\
        --engine-version OpenSearch_2.11

    C. Install clients:
    $ pip install gremlinpython opensearch-py

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

3️⃣  NEPTUNE ANALYTICS SETUP

    $ aws neptune-graph create-graph \\
        --graph-name graphrag-benchmark \\
        --provisioned-memory 128

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💰 COST ESTIMATES:

    Neo4j Aura:
    • Free tier: 200K nodes, 400K relationships
    • Professional: $65+/month

    Neptune Database:
    • db.r6g.large: $0.348/hour (~$250/month)
    • Storage: $0.10/GB-month

    OpenSearch:
    • m6g.large: $0.139/hour (~$100/month)
    • Storage: $0.10/GB-month

    Neptune Analytics:
    • $1.00 per GB-hour (expensive for large graphs)

    Total for small-scale test: ~$400-500/month

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚡ QUICK START (Neo4j Aura - We have access!):

    1. Run data loader:
       $ python3 neo4j_data_loader.py

    2. Run benchmark:
       $ python3 real_benchmark_implementation.py

    3. View results:
       $ cat real_benchmark_results.json

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run real benchmarks"""

    print_setup_guide()

    # Load credentials from .env
    from dotenv import load_dotenv
    load_dotenv()

    config = BenchmarkConfig(
        scales=[1000, 10000, 100000],  # Start small, scale up
        iterations=10,
        k=10,
        vector_dim=384,
        neo4j_uri=os.getenv("NEO4J_URI", ""),
        neo4j_user=os.getenv("NEO4J_USER", "neo4j"),
        neo4j_password=os.getenv("NEO4J_PASSWORD", ""),
        neptune_endpoint=os.getenv("NEPTUNE_ENDPOINT", ""),
        opensearch_host=os.getenv("OPENSEARCH_HOST", "")
    )

    runner = RealBenchmarkRunner(config)

    # Run Neo4j benchmarks (we have credentials!)
    results = runner.run_neo4j_benchmarks()
    runner.results.extend(results)

    # Run Neptune benchmarks (if configured)
    # results = runner.run_neptune_opensearch_benchmarks()
    # runner.results.extend(results)

    # Save results
    if runner.results:
        runner.save_results()

    print("\n" + "="*80)
    print("✅ Real benchmark complete!")
    print("="*80)


if __name__ == "__main__":
    main()
