#!/usr/bin/env python3
"""
Neo4j Large-Scale Data Generator
Generates synthetic biomedical data at scale for real benchmarks

Usage:
    python3 neo4j_data_generator.py --scale 10000    # 10K nodes
    python3 neo4j_data_generator.py --scale 1000000  # 1M nodes
"""

import os
import argparse
import hashlib
import random
from typing import List
from datetime import datetime

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False
    print("❌ neo4j package not installed: pip install neo4j")
    exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass


# ============================================================================
# CONFIGURATION
# ============================================================================

# Drug name patterns
DRUG_PREFIXES = ["Pem", "Niv", "Osim", "Erl", "Gef", "Bev", "Ima", "Tras", "Rit", "Ate"]
DRUG_SUFFIXES = ["mab", "tinib", "lizumab", "itinib", "tuzumab", "imumab"]

# Disease patterns
DISEASE_TYPES = ["Cancer", "Carcinoma", "Lymphoma", "Leukemia", "Melanoma", "Sarcoma"]
DISEASE_LOCATIONS = ["Lung", "Breast", "Colon", "Liver", "Brain", "Kidney", "Pancreas"]

# Gene patterns
GENE_PREFIXES = ["EGFR", "KRAS", "TP53", "BRAF", "PIK3", "ALK", "ROS", "MET", "RET", "NTRK"]
GENE_SUFFIXES = ["", "1", "2", "A", "B", "L1"]


# ============================================================================
# EMBEDDING GENERATION
# ============================================================================

def generate_embedding(text: str, dim: int = 384) -> List[float]:
    """Generate deterministic embedding"""
    seed = int(hashlib.md5(text.encode()).hexdigest(), 16) % (2**32)
    random.seed(seed)
    vector = [random.gauss(0, 1) for _ in range(dim)]
    magnitude = sum(x**2 for x in vector) ** 0.5
    return [x / magnitude for x in vector]


# ============================================================================
# DATA GENERATION
# ============================================================================

class DataGenerator:
    """Generate synthetic biomedical data"""

    @staticmethod
    def generate_drug_name(index: int) -> str:
        """Generate synthetic drug name"""
        random.seed(index)
        prefix = random.choice(DRUG_PREFIXES)
        suffix = random.choice(DRUG_SUFFIXES)
        return f"{prefix}{suffix}-{index}"

    @staticmethod
    def generate_disease_name(index: int) -> str:
        """Generate synthetic disease name"""
        random.seed(index)
        location = random.choice(DISEASE_LOCATIONS)
        dtype = random.choice(DISEASE_TYPES)
        return f"{location} {dtype} Type-{index}"

    @staticmethod
    def generate_gene_symbol(index: int) -> str:
        """Generate synthetic gene symbol"""
        random.seed(index)
        prefix = random.choice(GENE_PREFIXES)
        suffix = random.choice(GENE_SUFFIXES)
        return f"{prefix}{suffix}{index}"


# ============================================================================
# BATCH LOADER
# ============================================================================

class BatchLoader:
    """Load data in batches for performance"""

    def __init__(self, driver, batch_size: int = 1000):
        self.driver = driver
        self.batch_size = batch_size

    def load_drugs_batch(self, start_idx: int, count: int):
        """Load drug nodes in batches"""
        print(f"  Loading drugs {start_idx:,} to {start_idx + count:,}...")

        drugs = []
        for i in range(start_idx, start_idx + count):
            name = DataGenerator.generate_drug_name(i)
            description = f"Synthetic drug {i} for benchmark testing"
            embedding = generate_embedding(name + " " + description)

            drugs.append({
                'name': name,
                'description': description,
                'mechanism': 'synthetic',
                'embedding': embedding,
                'index': i
            })

        # Batch insert
        with self.driver.session() as session:
            session.run("""
                UNWIND $drugs as drug
                CREATE (d:Drug)
                SET d.name = drug.name,
                    d.description = drug.description,
                    d.mechanism = drug.mechanism,
                    d.embedding = drug.embedding,
                    d.index = drug.index,
                    d.created_at = datetime()
            """, drugs=drugs)

    def load_diseases_batch(self, start_idx: int, count: int):
        """Load disease nodes in batches"""
        print(f"  Loading diseases {start_idx:,} to {start_idx + count:,}...")

        diseases = []
        for i in range(start_idx, start_idx + count):
            name = DataGenerator.generate_disease_name(i)
            diseases.append({
                'name': name,
                'code': f"SYND-{i}",
                'category': 'synthetic',
                'index': i
            })

        with self.driver.session() as session:
            session.run("""
                UNWIND $diseases as disease
                CREATE (d:Disease)
                SET d.name = disease.name,
                    d.code = disease.code,
                    d.category = disease.category,
                    d.index = disease.index,
                    d.created_at = datetime()
            """, diseases=diseases)

    def load_genes_batch(self, start_idx: int, count: int):
        """Load gene nodes in batches"""
        print(f"  Loading genes {start_idx:,} to {start_idx + count:,}...")

        genes = []
        for i in range(start_idx, start_idx + count):
            symbol = DataGenerator.generate_gene_symbol(i)
            genes.append({
                'symbol': symbol,
                'name': f"Gene {symbol}",
                'chromosome': str((i % 23) + 1),
                'index': i
            })

        with self.driver.session() as session:
            session.run("""
                UNWIND $genes as gene
                CREATE (g:Gene)
                SET g.symbol = gene.symbol,
                    g.name = gene.name,
                    g.chromosome = gene.chromosome,
                    g.index = gene.index,
                    g.created_at = datetime()
            """, genes=genes)

    def create_relationships_batch(self, drug_count: int, disease_count: int,
                                   gene_count: int):
        """Create relationships between nodes"""
        print("  Creating relationships...")

        with self.driver.session() as session:
            # Drug-Disease relationships (each drug treats 1-3 diseases)
            session.run("""
                MATCH (drug:Drug)
                WHERE drug.index IS NOT NULL
                WITH drug, (drug.index % $disease_count) as disease_idx
                MATCH (disease:Disease)
                WHERE disease.index = disease_idx
                MERGE (drug)-[r:TREATS]->(disease)
                SET r.created_at = datetime()
            """, disease_count=disease_count)

            # Disease-Gene relationships (each disease associated with 1-2 genes)
            session.run("""
                MATCH (disease:Disease)
                WHERE disease.index IS NOT NULL
                WITH disease, (disease.index % $gene_count) as gene_idx
                MATCH (gene:Gene)
                WHERE gene.index = gene_idx
                MERGE (disease)-[r:ASSOCIATED_WITH]->(gene)
                SET r.created_at = datetime()
            """, gene_count=gene_count)


# ============================================================================
# MAIN GENERATOR
# ============================================================================

def generate_data(uri: str, user: str, password: str, target_scale: int):
    """Generate data at specified scale"""

    print("="*80)
    print("NEO4J LARGE-SCALE DATA GENERATOR")
    print("="*80)
    print(f"\nTarget scale: {target_scale:,} nodes")
    print(f"Connecting to: {uri}")

    driver = GraphDatabase.driver(uri, auth=(user, password))

    # Verify connection
    with driver.session() as session:
        result = session.run("RETURN 1 as n")
        if result.single()["n"] != 1:
            print("❌ Connection failed")
            return

    print("✅ Connected")

    # Calculate distribution (70% drugs, 20% diseases, 10% genes)
    drug_count = int(target_scale * 0.7)
    disease_count = int(target_scale * 0.2)
    gene_count = int(target_scale * 0.1)

    print(f"\nDistribution:")
    print(f"  Drugs:    {drug_count:,}")
    print(f"  Diseases: {disease_count:,}")
    print(f"  Genes:    {gene_count:,}")

    # Ask for confirmation
    response = input("\n⚠️  This will create new nodes. Continue? (yes/no): ")
    if response.lower() != 'yes':
        print("Cancelled")
        return

    loader = BatchLoader(driver, batch_size=1000)
    start_time = datetime.now()

    # Load drugs in batches
    print(f"\n💊 Loading {drug_count:,} drugs...")
    for i in range(0, drug_count, 1000):
        batch_size = min(1000, drug_count - i)
        loader.load_drugs_batch(i, batch_size)

    # Load diseases in batches
    print(f"\n🏥 Loading {disease_count:,} diseases...")
    for i in range(0, disease_count, 1000):
        batch_size = min(1000, disease_count - i)
        loader.load_diseases_batch(i, batch_size)

    # Load genes in batches
    print(f"\n🧬 Loading {gene_count:,} genes...")
    for i in range(0, gene_count, 1000):
        batch_size = min(1000, gene_count - i)
        loader.load_genes_batch(i, batch_size)

    # Create relationships
    print(f"\n🔗 Creating relationships...")
    loader.create_relationships_batch(drug_count, disease_count, gene_count)

    # Create vector index
    print(f"\n🔍 Creating vector index...")
    with driver.session() as session:
        try:
            session.run("DROP INDEX drug_embedding_vector IF EXISTS")
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
            print("✅ Vector index created")
        except Exception as e:
            print(f"⚠️  Vector index: {e}")

    # Get final stats
    with driver.session() as session:
        result = session.run("MATCH (n) RETURN count(n) as total")
        total_nodes = result.single()['total']

        result = session.run("MATCH ()-[r]->() RETURN count(r) as total")
        total_rels = result.single()['total']

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print("\n" + "="*80)
    print("✅ DATA GENERATION COMPLETE")
    print("="*80)
    print(f"\nStatistics:")
    print(f"  Total nodes:         {total_nodes:,}")
    print(f"  Total relationships: {total_rels:,}")
    print(f"  Time taken:          {duration:.1f} seconds")
    print(f"  Rate:                {int(total_nodes / duration):,} nodes/sec")

    print("\n🚀 Ready for benchmarking!")
    print("   Run: python3 real_benchmark_implementation.py")

    driver.close()


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Generate large-scale data for Neo4j benchmarks"
    )
    parser.add_argument(
        '--scale',
        type=int,
        default=10000,
        help='Target number of total nodes (default: 10000)'
    )

    args = parser.parse_args()

    # Load credentials
    uri = os.getenv("NEO4J_URI", "")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "")

    if not uri or not password:
        print("❌ Neo4j credentials not found in .env")
        print("Set: NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD")
        return

    generate_data(uri, user, password, args.scale)


if __name__ == "__main__":
    main()
