#!/usr/bin/env python3
"""
Neo4j Aura Data Loader for Real Benchmarks
Loads biomedical knowledge graph with embeddings

This prepares Neo4j for real performance benchmarking.
"""

import os
import json
import hashlib
import random
from typing import List, Dict, Any
from datetime import datetime

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("❌ neo4j package not installed")
    print("Install: pip install neo4j")
    exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass


# ============================================================================
# EMBEDDING GENERATION
# ============================================================================

def generate_embedding(text: str, dim: int = 384) -> List[float]:
    """
    Generate deterministic embedding from text
    For production: use sentence-transformers or OpenAI API
    """
    # Use text as seed for reproducibility
    seed = int(hashlib.md5(text.encode()).hexdigest(), 16) % (2**32)
    random.seed(seed)

    # Generate vector
    vector = [random.gauss(0, 1) for _ in range(dim)]

    # Normalize to unit vector
    magnitude = sum(x**2 for x in vector) ** 0.5
    return [x / magnitude for x in vector]


# ============================================================================
# SAMPLE BIOMEDICAL DATA
# ============================================================================

SAMPLE_DRUGS = [
    {"name": "Pembrolizumab", "description": "PD-1 inhibitor for cancer immunotherapy", "mechanism": "checkpoint_inhibitor"},
    {"name": "Nivolumab", "description": "PD-1 antibody for melanoma and lung cancer", "mechanism": "checkpoint_inhibitor"},
    {"name": "Osimertinib", "description": "EGFR inhibitor for non-small cell lung cancer", "mechanism": "tyrosine_kinase_inhibitor"},
    {"name": "Erlotinib", "description": "EGFR inhibitor for NSCLC and pancreatic cancer", "mechanism": "tyrosine_kinase_inhibitor"},
    {"name": "Gefitinib", "description": "EGFR inhibitor for NSCLC", "mechanism": "tyrosine_kinase_inhibitor"},
    {"name": "Bevacizumab", "description": "VEGF inhibitor for colorectal and lung cancer", "mechanism": "angiogenesis_inhibitor"},
    {"name": "Imatinib", "description": "BCR-ABL inhibitor for chronic myeloid leukemia", "mechanism": "tyrosine_kinase_inhibitor"},
    {"name": "Trastuzumab", "description": "HER2 antibody for breast cancer", "mechanism": "monoclonal_antibody"},
    {"name": "Rituximab", "description": "CD20 antibody for lymphoma", "mechanism": "monoclonal_antibody"},
    {"name": "Atezolizumab", "description": "PD-L1 inhibitor for various cancers", "mechanism": "checkpoint_inhibitor"},
]

SAMPLE_DISEASES = [
    {"name": "Non-Small Cell Lung Cancer", "code": "NSCLC", "category": "cancer"},
    {"name": "Melanoma", "code": "MEL", "category": "cancer"},
    {"name": "Breast Cancer", "code": "BRCA", "category": "cancer"},
    {"name": "Colorectal Cancer", "code": "CRC", "category": "cancer"},
    {"name": "Chronic Myeloid Leukemia", "code": "CML", "category": "cancer"},
    {"name": "Pancreatic Cancer", "code": "PANC", "category": "cancer"},
    {"name": "Non-Hodgkin Lymphoma", "code": "NHL", "category": "cancer"},
]

SAMPLE_GENES = [
    {"symbol": "EGFR", "name": "Epidermal Growth Factor Receptor", "chromosome": "7"},
    {"symbol": "PD-1", "name": "Programmed Cell Death Protein 1", "chromosome": "2"},
    {"symbol": "PD-L1", "name": "Programmed Death-Ligand 1", "chromosome": "9"},
    {"symbol": "VEGF", "name": "Vascular Endothelial Growth Factor", "chromosome": "6"},
    {"symbol": "HER2", "name": "Human Epidermal Growth Factor Receptor 2", "chromosome": "17"},
    {"symbol": "BCR-ABL", "name": "BCR-ABL Fusion Gene", "chromosome": "9/22"},
    {"symbol": "CD20", "name": "B-lymphocyte antigen CD20", "chromosome": "11"},
    {"symbol": "KRAS", "name": "Kirsten Rat Sarcoma Viral Oncogene", "chromosome": "12"},
]

# Define relationships
DRUG_DISEASE_RELATIONSHIPS = [
    ("Pembrolizumab", "Non-Small Cell Lung Cancer"),
    ("Pembrolizumab", "Melanoma"),
    ("Nivolumab", "Non-Small Cell Lung Cancer"),
    ("Nivolumab", "Melanoma"),
    ("Osimertinib", "Non-Small Cell Lung Cancer"),
    ("Erlotinib", "Non-Small Cell Lung Cancer"),
    ("Erlotinib", "Pancreatic Cancer"),
    ("Gefitinib", "Non-Small Cell Lung Cancer"),
    ("Bevacizumab", "Colorectal Cancer"),
    ("Bevacizumab", "Non-Small Cell Lung Cancer"),
    ("Imatinib", "Chronic Myeloid Leukemia"),
    ("Trastuzumab", "Breast Cancer"),
    ("Rituximab", "Non-Hodgkin Lymphoma"),
    ("Atezolizumab", "Non-Small Cell Lung Cancer"),
]

DISEASE_GENE_RELATIONSHIPS = [
    ("Non-Small Cell Lung Cancer", "EGFR"),
    ("Non-Small Cell Lung Cancer", "KRAS"),
    ("Melanoma", "PD-1"),
    ("Melanoma", "PD-L1"),
    ("Breast Cancer", "HER2"),
    ("Colorectal Cancer", "VEGF"),
    ("Colorectal Cancer", "KRAS"),
    ("Chronic Myeloid Leukemia", "BCR-ABL"),
    ("Non-Hodgkin Lymphoma", "CD20"),
]


# ============================================================================
# NEO4J LOADER
# ============================================================================

class Neo4jDataLoader:
    """Load biomedical data into Neo4j with embeddings"""

    def __init__(self, uri: str, user: str, password: str):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.uri = uri

    def close(self):
        self.driver.close()

    def verify_connection(self) -> bool:
        """Test connection"""
        try:
            with self.driver.session() as session:
                result = session.run("RETURN 1 as n")
                return result.single()["n"] == 1
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False

    def clear_database(self):
        """Clear all data (use carefully!)"""
        print("⚠️  Clearing database...")
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        print("✅ Database cleared")

    def create_constraints(self):
        """Create uniqueness constraints"""
        print("📋 Creating constraints...")

        with self.driver.session() as session:
            # Drug constraints
            try:
                session.run("CREATE CONSTRAINT drug_name IF NOT EXISTS FOR (d:Drug) REQUIRE d.name IS UNIQUE")
            except:
                pass

            # Disease constraints
            try:
                session.run("CREATE CONSTRAINT disease_name IF NOT EXISTS FOR (d:Disease) REQUIRE d.name IS UNIQUE")
            except:
                pass

            # Gene constraints
            try:
                session.run("CREATE CONSTRAINT gene_symbol IF NOT EXISTS FOR (g:Gene) REQUIRE g.symbol IS UNIQUE")
            except:
                pass

        print("✅ Constraints created")

    def load_drugs(self, drugs: List[Dict[str, Any]]):
        """Load drugs with embeddings"""
        print(f"\n💊 Loading {len(drugs)} drugs...")

        with self.driver.session() as session:
            for drug in drugs:
                # Generate embedding
                text = f"{drug['name']} {drug['description']}"
                embedding = generate_embedding(text)

                # Create drug node
                session.run("""
                    MERGE (d:Drug {name: $name})
                    SET d.description = $description,
                        d.mechanism = $mechanism,
                        d.embedding = $embedding,
                        d.loaded_at = datetime()
                """, name=drug['name'],
                    description=drug['description'],
                    mechanism=drug['mechanism'],
                    embedding=embedding)

                print(f"  ✓ {drug['name']}")

        print(f"✅ Loaded {len(drugs)} drugs with embeddings")

    def load_diseases(self, diseases: List[Dict[str, Any]]):
        """Load diseases"""
        print(f"\n🏥 Loading {len(diseases)} diseases...")

        with self.driver.session() as session:
            for disease in diseases:
                session.run("""
                    MERGE (d:Disease {name: $name})
                    SET d.code = $code,
                        d.category = $category,
                        d.loaded_at = datetime()
                """, name=disease['name'],
                    code=disease['code'],
                    category=disease['category'])

                print(f"  ✓ {disease['name']}")

        print(f"✅ Loaded {len(diseases)} diseases")

    def load_genes(self, genes: List[Dict[str, Any]]):
        """Load genes"""
        print(f"\n🧬 Loading {len(genes)} genes...")

        with self.driver.session() as session:
            for gene in genes:
                session.run("""
                    MERGE (g:Gene {symbol: $symbol})
                    SET g.name = $name,
                        g.chromosome = $chromosome,
                        g.loaded_at = datetime()
                """, symbol=gene['symbol'],
                    name=gene['name'],
                    chromosome=gene['chromosome'])

                print(f"  ✓ {gene['symbol']}")

        print(f"✅ Loaded {len(genes)} genes")

    def create_drug_disease_relationships(self, relationships: List[tuple]):
        """Create TREATS relationships"""
        print(f"\n🔗 Creating {len(relationships)} drug-disease relationships...")

        with self.driver.session() as session:
            for drug_name, disease_name in relationships:
                session.run("""
                    MATCH (drug:Drug {name: $drug_name})
                    MATCH (disease:Disease {name: $disease_name})
                    MERGE (drug)-[r:TREATS]->(disease)
                    SET r.created_at = datetime()
                """, drug_name=drug_name, disease_name=disease_name)

                print(f"  ✓ {drug_name} → {disease_name}")

        print(f"✅ Created {len(relationships)} TREATS relationships")

    def create_disease_gene_relationships(self, relationships: List[tuple]):
        """Create ASSOCIATED_WITH relationships"""
        print(f"\n🔗 Creating {len(relationships)} disease-gene relationships...")

        with self.driver.session() as session:
            for disease_name, gene_symbol in relationships:
                session.run("""
                    MATCH (disease:Disease {name: $disease_name})
                    MATCH (gene:Gene {symbol: $gene_symbol})
                    MERGE (disease)-[r:ASSOCIATED_WITH]->(gene)
                    SET r.created_at = datetime()
                """, disease_name=disease_name, gene_symbol=gene_symbol)

                print(f"  ✓ {disease_name} → {gene_symbol}")

        print(f"✅ Created {len(relationships)} ASSOCIATED_WITH relationships")

    def create_vector_index(self):
        """Create vector index for similarity search"""
        print("\n🔍 Creating vector index...")

        with self.driver.session() as session:
            try:
                # Check if index exists
                result = session.run("SHOW INDEXES")
                indices = [record["name"] for record in result]

                if "drug_embedding_vector" in indices:
                    print("⚠️  Vector index already exists, dropping...")
                    session.run("DROP INDEX drug_embedding_vector IF EXISTS")

                # Create vector index
                session.run("""
                    CREATE VECTOR INDEX drug_embedding_vector IF NOT EXISTS
                    FOR (d:Drug)
                    ON d.embedding
                    OPTIONS {
                        indexConfig: {
                            `vector.dimensions`: 384,
                            `vector.similarity_function`: 'cosine'
                        }
                    }
                """)

                print("✅ Vector index created: drug_embedding_vector")
                print("   Dimensions: 384")
                print("   Similarity: cosine")

            except Exception as e:
                print(f"❌ Vector index creation failed: {e}")
                print("⚠️  Note: Vector indices require Neo4j 5.11+")

    def get_statistics(self) -> Dict[str, int]:
        """Get database statistics"""
        with self.driver.session() as session:
            stats = {}

            # Node counts
            result = session.run("MATCH (d:Drug) RETURN count(d) as count")
            stats['drugs'] = result.single()['count']

            result = session.run("MATCH (d:Disease) RETURN count(d) as count")
            stats['diseases'] = result.single()['count']

            result = session.run("MATCH (g:Gene) RETURN count(g) as count")
            stats['genes'] = result.single()['count']

            # Relationship counts
            result = session.run("MATCH ()-[r:TREATS]->() RETURN count(r) as count")
            stats['treats'] = result.single()['count']

            result = session.run("MATCH ()-[r:ASSOCIATED_WITH]->() RETURN count(r) as count")
            stats['associated_with'] = result.single()['count']

            return stats

    def test_vector_search(self):
        """Test vector search functionality"""
        print("\n🧪 Testing vector search...")

        with self.driver.session() as session:
            # Generate test query vector
            test_query = generate_embedding("lung cancer treatment")

            try:
                result = session.run("""
                    CALL db.index.vector.queryNodes('drug_embedding_vector', 5, $vector)
                    YIELD node, score
                    RETURN node.name as drug, score
                    LIMIT 5
                """, vector=test_query)

                print("✅ Vector search working! Top 5 results:")
                for record in result:
                    print(f"   {record['drug']}: {record['score']:.4f}")

            except Exception as e:
                print(f"❌ Vector search failed: {e}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Load data into Neo4j Aura"""

    print("="*80)
    print("NEO4J AURA DATA LOADER")
    print("="*80)

    # Load credentials
    uri = os.getenv("NEO4J_URI", "")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "")

    if not uri or not password:
        print("❌ Neo4j credentials not found in .env")
        print("Set: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD")
        return

    print(f"\n📡 Connecting to: {uri}")

    loader = Neo4jDataLoader(uri, user, password)

    # Verify connection
    if not loader.verify_connection():
        return

    print("✅ Connected to Neo4j Aura")

    # Ask before clearing
    response = input("\n⚠️  Clear existing data? (yes/no): ")
    if response.lower() == 'yes':
        loader.clear_database()

    # Load data
    loader.create_constraints()
    loader.load_drugs(SAMPLE_DRUGS)
    loader.load_diseases(SAMPLE_DISEASES)
    loader.load_genes(SAMPLE_GENES)
    loader.create_drug_disease_relationships(DRUG_DISEASE_RELATIONSHIPS)
    loader.create_disease_gene_relationships(DISEASE_GENE_RELATIONSHIPS)

    # Create vector index
    loader.create_vector_index()

    # Get statistics
    print("\n" + "="*80)
    print("DATABASE STATISTICS")
    print("="*80)

    stats = loader.get_statistics()
    print(f"Drugs:              {stats['drugs']:,}")
    print(f"Diseases:           {stats['diseases']:,}")
    print(f"Genes:              {stats['genes']:,}")
    print(f"TREATS:             {stats['treats']:,}")
    print(f"ASSOCIATED_WITH:    {stats['associated_with']:,}")

    # Test vector search
    loader.test_vector_search()

    loader.close()

    print("\n" + "="*80)
    print("✅ DATA LOADING COMPLETE")
    print("="*80)
    print("\nNext steps:")
    print("  1. Run real benchmarks:")
    print("     $ python3 real_benchmark_implementation.py")
    print()
    print("  2. Scale up data for billion-scale tests:")
    print("     $ python3 neo4j_data_generator.py --scale 1000000")
    print()


if __name__ == "__main__":
    main()
