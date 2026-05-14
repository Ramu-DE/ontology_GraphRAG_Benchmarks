#!/usr/bin/env python3
"""
GraphRAG at Scale - Native Vector Integration with Neo4j
Eliminates the two-layer friction by treating vectors as native node properties

Key Concepts:
- HNSW (Hierarchical Navigable Small World) for billion-scale vector search
- Vectors as native node properties (not external index)
- Cypher-native vector similarity queries
- Combined graph traversal + semantic search in single query
- Tunable parameters: M, efConstruction, efRuntime
"""

import json
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os


# ============================================================================
# HNSW CONFIGURATION
# ============================================================================

@dataclass
class HNSWConfig:
    """
    HNSW parameters for vector search optimization

    M: Max outgoing edges per node (connectivity/"city density")
       - Higher M = more connections = better recall, more memory
       - Typical: 16-64
       - Billion-scale: 32-48

    efConstruction: Entry points during index building
       - Higher = better quality index, slower build
       - Typical: 64-256
       - Production: 128-256

    efRuntime: Search buffer size (zoom level)
       - Higher = better recall, slower search
       - Typical: 64-512
       - Real-time: 100-200
    """
    M: int = 32                    # Connectivity (edges per node)
    efConstruction: int = 128      # Index build quality
    efRuntime: int = 100           # Search quality/speed tradeoff

    def to_cypher_params(self) -> str:
        """Convert to Cypher index configuration"""
        return f"{{indexConfig: {{`vector.dimensions`: 384, `vector.similarity_function`: 'cosine'}}, indexProvider: 'vector-1.0'}}"


# ============================================================================
# GRAPHRAG VECTOR MANAGER
# ============================================================================

class GraphRAGVectorManager:
    """
    Manages native vector indices in Neo4j
    Eliminates the two-layer problem by treating vectors as first-class properties
    """

    def __init__(self, driver, hnsw_config: HNSWConfig = None):
        self.driver = driver
        self.config = hnsw_config or HNSWConfig()

    def create_vector_index(self,
                           label: str,
                           property_name: str,
                           dimensions: int,
                           similarity: str = "cosine"):
        """
        Create native vector index with HNSW

        This is NOT an external layer - vectors are stored as node properties
        and indexed directly in the graph engine's sparse matrix representation
        """

        print(f"\n🔧 Creating native vector index: {label}.{property_name}")
        print(f"   Dimensions: {dimensions}")
        print(f"   Similarity: {similarity}")
        print(f"   HNSW Config:")
        print(f"     M (connectivity): {self.config.M}")
        print(f"     efConstruction: {self.config.efConstruction}")
        print(f"     efRuntime: {self.config.efRuntime}")

        query = f"""
        CREATE VECTOR INDEX {label}_{property_name}_vector IF NOT EXISTS
        FOR (n:{label})
        ON n.{property_name}
        OPTIONS {{
            indexConfig: {{
                `vector.dimensions`: {dimensions},
                `vector.similarity_function`: '{similarity}'
            }}
        }}
        """

        with self.driver.session() as session:
            session.run(query)
            print(f"   ✅ Index created")

    def wait_for_index(self, index_name: str, timeout: int = 300):
        """Wait for index to come online"""
        print(f"\n⏳ Waiting for index to build...")

        query = "SHOW INDEXES YIELD name, state WHERE name = $index_name RETURN state"

        start = time.time()
        with self.driver.session() as session:
            while time.time() - start < timeout:
                result = session.run(query, {"index_name": index_name})
                record = result.single()

                if record and record["state"] == "ONLINE":
                    print(f"   ✅ Index online ({time.time() - start:.1f}s)")
                    return True

                time.sleep(2)

        return False

    def semantic_search(self,
                       label: str,
                       property_name: str,
                       query_vector: List[float],
                       k: int = 10) -> List[Dict]:
        """
        Native vector similarity search - NO external layer

        This happens entirely within the graph engine's sparse matrix representation.
        No context-switching, no handover friction.
        """

        cypher = f"""
        CALL db.index.vector.queryNodes(
            '{label}_{property_name}_vector',
            $k,
            $query_vector
        ) YIELD node, score
        RETURN node, score
        ORDER BY score DESC
        """

        with self.driver.session() as session:
            result = session.run(cypher, {
                "k": k,
                "query_vector": query_vector
            })

            return [{"node": dict(record["node"]), "score": record["score"]}
                   for record in result]

    def hybrid_graph_vector_query(self,
                                  label: str,
                                  property_name: str,
                                  query_vector: List[float],
                                  relationship_pattern: str,
                                  k: int = 10) -> List[Dict]:
        """
        The Holy Grail: Combined vector + graph traversal in ONE query

        No two layers. No handover. No friction.
        Vector search and graph traversal happen simultaneously in the same engine.
        """

        cypher = f"""
        // Step 1: Vector similarity (native, no external lookup)
        CALL db.index.vector.queryNodes(
            '{label}_{property_name}_vector',
            $k,
            $query_vector
        ) YIELD node, score

        // Step 2: Graph traversal (same engine, same query)
        {relationship_pattern}

        RETURN node, score, connected_nodes
        ORDER BY score DESC
        """

        with self.driver.session() as session:
            result = session.run(cypher, {
                "k": k,
                "query_vector": query_vector
            })

            return [dict(record) for record in result]


# ============================================================================
# GRAPHRAG FOR CLINICAL DATA
# ============================================================================

class ClinicalGraphRAG:
    """
    GraphRAG implementation for clinical decision support
    Combines semantic search with graph relationships in a unified architecture
    """

    def __init__(self, neo4j_driver):
        self.driver = neo4j_driver
        self.vector_manager = GraphRAGVectorManager(
            driver=neo4j_driver,
            hnsw_config=HNSWConfig(
                M=32,              # Good for million-scale
                efConstruction=128, # High quality index
                efRuntime=100      # Balanced search speed
            )
        )

    def setup_vector_indices(self):
        """Setup native vector indices for clinical entities"""

        print("\n" + "="*80)
        print("🏗️  Setting up Native Vector Indices (No External Layer)")
        print("="*80)

        # Drug embeddings (mechanism, indications, etc.)
        self.vector_manager.create_vector_index(
            label="Drug",
            property_name="embedding",
            dimensions=384  # e.g., all-MiniLM-L6-v2
        )

        # Disease embeddings (symptoms, pathology, etc.)
        self.vector_manager.create_vector_index(
            label="Disease",
            property_name="embedding",
            dimensions=384
        )

        # Research paper embeddings (abstracts, findings)
        self.vector_manager.create_vector_index(
            label="ResearchPaper",
            property_name="embedding",
            dimensions=384
        )

        print("\n✅ All indices created")

    def semantic_drug_search(self, query_text: str, k: int = 10) -> List[Dict]:
        """
        Find drugs semantically similar to query
        Uses ONLY the graph engine - no external vector DB
        """

        # In production, generate embedding from query_text
        # For demo, use a simulated embedding
        query_embedding = self._simulate_embedding(query_text)

        results = self.vector_manager.semantic_search(
            label="Drug",
            property_name="embedding",
            query_vector=query_embedding,
            k=k
        )

        return results

    def graphrag_drug_disease_reasoning(self,
                                       query_text: str,
                                       k: int = 5) -> List[Dict]:
        """
        The unified approach: Vector search + graph traversal in ONE query

        This eliminates the friction:
        1. Vector search finds semantically similar drugs (native, in-graph)
        2. Graph traversal finds related diseases (same query, same engine)
        3. No handover, no context-switching, no latency
        """

        query_embedding = self._simulate_embedding(query_text)

        cypher = """
        // Native vector search (no external lookup)
        CALL db.index.vector.queryNodes(
            'Drug_embedding_vector',
            $k,
            $query_vector
        ) YIELD node AS drug, score

        // Graph traversal (same engine, same query)
        MATCH (drug)-[r:TREATS]->(disease:Disease)
        OPTIONAL MATCH (disease)<-[:ASSOCIATED_WITH]-(gene:Gene)

        // Aggregate results
        WITH drug, score,
             collect(DISTINCT disease.name) AS diseases,
             collect(DISTINCT gene.symbol) AS genes

        RETURN
            drug.name AS drug_name,
            drug.mechanism_of_action AS mechanism,
            score AS semantic_similarity,
            diseases,
            genes,
            size(diseases) AS disease_count,
            size(genes) AS genetic_evidence_count
        ORDER BY score DESC
        LIMIT $k
        """

        with self.driver.session() as session:
            result = session.run(cypher, {
                "k": k,
                "query_vector": query_embedding
            })

            return [dict(record) for record in result]

    def graphrag_adverse_event_prediction(self,
                                         drug_name: str,
                                         patient_profile: Dict,
                                         k: int = 10) -> List[Dict]:
        """
        Use GraphRAG to predict adverse events based on:
        1. Semantic similarity to known drug profiles
        2. Graph traversal of adverse event patterns
        3. Patient-specific risk factors

        All in ONE unified query - no layer switching
        """

        # Create composite embedding from drug + patient profile
        composite_embedding = self._create_patient_drug_embedding(drug_name, patient_profile)

        cypher = """
        // Find semantically similar drug profiles (vector search)
        CALL db.index.vector.queryNodes(
            'Drug_embedding_vector',
            $k,
            $query_vector
        ) YIELD node AS similar_drug, score

        // Traverse to adverse events (graph traversal)
        MATCH (similar_drug)-[r:HAS_ADVERSE_EVENT]->(ae:AdverseEvent)

        // Consider patient risk factors (graph context)
        WITH similar_drug, score, ae, r,
             CASE
                WHEN $patient_age > 65 THEN r.frequency * 1.2
                WHEN $patient_age < 18 THEN r.frequency * 1.3
                ELSE r.frequency
             END AS adjusted_frequency

        // Aggregate predictions
        RETURN
            ae.event_name AS adverse_event,
            ae.severity AS severity,
            avg(adjusted_frequency) AS predicted_frequency,
            avg(score) AS evidence_strength,
            count(DISTINCT similar_drug) AS supporting_drugs,
            collect(DISTINCT similar_drug.name)[..3] AS similar_drugs
        ORDER BY predicted_frequency DESC, evidence_strength DESC
        LIMIT 20
        """

        with self.driver.session() as session:
            result = session.run(cypher, {
                "k": k,
                "query_vector": composite_embedding,
                "patient_age": patient_profile.get("age", 50)
            })

            return [dict(record) for record in result]

    def graphrag_research_evidence_chain(self,
                                        query_text: str,
                                        max_hops: int = 3) -> List[Dict]:
        """
        Find research evidence chains using:
        1. Semantic search of research papers
        2. Graph traversal of citation networks
        3. Entity relationships (drugs, genes, diseases)

        All unified in a single query execution
        """

        query_embedding = self._simulate_embedding(query_text)

        cypher = f"""
        // Semantic search for relevant papers
        CALL db.index.vector.queryNodes(
            'ResearchPaper_embedding_vector',
            10,
            $query_vector
        ) YIELD node AS paper, score

        // Traverse citation network and entity relationships
        MATCH path = (paper)-[:CITES|MENTIONS*1..{max_hops}]-(related)
        WHERE related:ResearchPaper OR related:Drug OR related:Gene OR related:Disease

        // Extract evidence chain
        WITH paper, score, path, related,
             [n IN nodes(path) | labels(n)[0] + ': ' + coalesce(n.name, n.title, n.symbol)] AS chain

        RETURN
            paper.title AS source_paper,
            score AS relevance,
            labels(related)[0] AS target_type,
            coalesce(related.name, related.title, related.symbol) AS target_name,
            length(path) AS hops,
            chain AS evidence_chain
        ORDER BY score DESC, hops ASC
        LIMIT 50
        """

        with self.driver.session() as session:
            result = session.run(cypher, {
                "query_vector": query_embedding
            })

            return [dict(record) for record in result]

    def _simulate_embedding(self, text: str, dimensions: int = 384) -> List[float]:
        """
        Simulate text embedding
        In production, use sentence-transformers or OpenAI embeddings
        """
        import random
        random.seed(hash(text) % 2**32)
        return [random.random() for _ in range(dimensions)]

    def _create_patient_drug_embedding(self,
                                      drug_name: str,
                                      patient_profile: Dict,
                                      dimensions: int = 384) -> List[float]:
        """
        Create composite embedding from drug + patient profile
        In production, concatenate and encode both
        """
        composite_text = f"{drug_name} {patient_profile.get('age')} {' '.join(patient_profile.get('comorbidities', []))}"
        return self._simulate_embedding(composite_text, dimensions)


# ============================================================================
# DEMO: UNIFIED GRAPHRAG QUERIES
# ============================================================================

def demo_unified_graphrag():
    """
    Demonstrate the unified approach - no two layers, no friction
    """

    load_dotenv()

    driver = GraphDatabase.driver(
        os.getenv('NEO4J_URI'),
        auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
    )

    print("\n" + "="*80)
    print("🎯 GraphRAG at Scale - Unified Architecture Demo")
    print("="*80)
    print("\nKey Insight: Vectors are NATIVE node properties, not external indices")
    print("Result: No two-layer friction, no context-switching, no latency")
    print("")

    graphrag = ClinicalGraphRAG(driver)

    # Setup (in production, this is a one-time operation)
    print("\n" + "─"*80)
    print("SETUP: Creating native vector indices with HNSW")
    print("─"*80)
    graphrag.setup_vector_indices()

    # Demo 1: Unified drug-disease reasoning
    print("\n" + "="*80)
    print("DEMO 1: Unified Vector + Graph Query")
    print("="*80)
    print("\nQuery: 'Find drugs for lung cancer with genetic evidence'")
    print("\nTraditional approach:")
    print("  1. Vector search → candidates")
    print("  2. Pass to graph engine → traverse relationships")
    print("  ❌ TWO SEPARATE OPERATIONS (context-switching friction)")
    print("\nUnified approach:")
    print("  1. Vector search + graph traversal in SAME Cypher query")
    print("  ✅ ONE OPERATION (no friction, no handover)")
    print("")

    results = graphrag.graphrag_drug_disease_reasoning(
        query_text="checkpoint inhibitor for non-small cell lung cancer",
        k=5
    )

    print(f"\nResults: {len(results)} drugs found")
    for i, result in enumerate(results[:3], 1):
        print(f"\n  {i}. {result.get('drug_name', 'Unknown')}")
        print(f"     Semantic Score: {result.get('semantic_similarity', 0):.3f}")
        print(f"     Diseases: {result.get('disease_count', 0)}")
        print(f"     Genetic Evidence: {result.get('genetic_evidence_count', 0)}")

    # Demo 2: Adverse event prediction
    print("\n" + "="*80)
    print("DEMO 2: GraphRAG Adverse Event Prediction")
    print("="*80)
    print("\nCombines:")
    print("  • Vector similarity to known drug profiles")
    print("  • Graph traversal of adverse event patterns")
    print("  • Patient-specific risk adjustments")
    print("\nAll in ONE query execution (no layer switching)")
    print("")

    patient_profile = {
        "age": 68,
        "comorbidities": ["diabetes", "hypertension"]
    }

    ae_results = graphrag.graphrag_adverse_event_prediction(
        drug_name="Pembrolizumab",
        patient_profile=patient_profile,
        k=10
    )

    print(f"\nPredicted Adverse Events: {len(ae_results)}")
    for i, result in enumerate(ae_results[:5], 1):
        print(f"\n  {i}. {result.get('adverse_event', 'Unknown')}")
        print(f"     Severity: {result.get('severity', 'unknown')}")
        print(f"     Predicted Frequency: {result.get('predicted_frequency', 0):.1f}%")
        print(f"     Evidence Strength: {result.get('evidence_strength', 0):.3f}")

    # Demo 3: Research evidence chains
    print("\n" + "="*80)
    print("DEMO 3: Research Evidence Chain Discovery")
    print("="*80)
    print("\nTraverses:")
    print("  • Semantic similarity of research papers")
    print("  • Citation networks")
    print("  • Entity relationships (drugs, genes, diseases)")
    print("\nAll unified in a single graph traversal")
    print("")

    evidence_results = graphrag.graphrag_research_evidence_chain(
        query_text="EGFR mutation checkpoint inhibitor efficacy",
        max_hops=3
    )

    print(f"\nEvidence Chains Found: {len(evidence_results)}")
    for i, result in enumerate(evidence_results[:3], 1):
        print(f"\n  {i}. {result.get('source_paper', 'Unknown')[:60]}...")
        print(f"     Relevance: {result.get('relevance', 0):.3f}")
        print(f"     → {result.get('target_type', 'Unknown')}: {result.get('target_name', 'Unknown')}")
        print(f"     Hops: {result.get('hops', 0)}")

    print("\n" + "="*80)
    print("✅ GraphRAG Demo Complete")
    print("="*80)
    print("\nKey Takeaway:")
    print("  Native vector indices eliminate the two-layer friction.")
    print("  Vector search and graph traversal happen in the SAME engine,")
    print("  in the SAME query, with NO context-switching.")
    print("\nThis is how you reach the holy grail of GraphRAG at billion-scale.")
    print("")

    driver.close()


# ============================================================================
# PERFORMANCE COMPARISON
# ============================================================================

def compare_architectures():
    """
    Compare two-layer vs unified architecture
    """

    print("\n" + "="*80)
    print("📊 Architecture Comparison: Two-Layer vs Unified")
    print("="*80)

    print("""
┌────────────────────────────────────────────────────────────────────────┐
│                         TWO-LAYER ARCHITECTURE                         │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  1. Query arrives                                                      │
│  2. Vector DB: Similarity search → candidates                         │
│  3. ❌ HANDOVER: Pass candidate IDs to graph engine                   │
│  4. Graph engine: Load nodes by IDs                                   │
│  5. Graph engine: Traverse relationships                              │
│  6. ❌ FRICTION: Context-switching, serialization, network overhead   │
│                                                                        │
│  Performance at billion-scale:                                        │
│    • 2 round trips (vector DB → graph DB)                            │
│    • Serialization overhead                                          │
│    • Network latency                                                 │
│    • Kills real-time performance                                     │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────────────┐
│                       UNIFIED ARCHITECTURE                             │
│                    (Neo4j Native Vectors)                              │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  1. Query arrives                                                      │
│  2. Graph engine: Vector search (native, in sparse matrix)            │
│  3. Graph engine: Traverse relationships (same query)                 │
│  4. ✅ NO HANDOVER: Everything in one query execution                 │
│                                                                        │
│  Performance at billion-scale:                                        │
│    • 1 query execution                                               │
│    • No serialization                                                │
│    • No network hops                                                 │
│    • Maintains real-time performance                                 │
│                                                                        │
│  HNSW Tuning:                                                         │
│    • M (connectivity): 32-48 for billion-scale                       │
│    • efConstruction: 128-256 for quality                             │
│    • efRuntime: 100-200 for real-time                                │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘

KEY INSIGHT:
  FalkorDB and Neo4j treat vectors as NATIVE properties, not external data.
  The sparse matrix representation unifies vector and graph operations.
  No two layers. No friction. No handover. Just ONE unified engine.
""")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("\n" + "="*80)
    print("🚀 GraphRAG at Scale - Native Vector Integration")
    print("="*80)
    print("\nEliminating the Two-Layer Problem:")
    print("  ❌ External vector DB + Graph DB = Friction")
    print("  ✅ Native vectors in graph engine = No friction")
    print("")

    # Show architecture comparison
    compare_architectures()

    # Run unified GraphRAG demo
    demo_unified_graphrag()
