#!/usr/bin/env python3
"""
Neo4j Usage Examples
Comprehensive examples of working with Neo4j biomedical knowledge graph
"""

import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load credentials
load_dotenv()

class Neo4jExamples:
    """Example usage patterns for Neo4j biomedical graph"""

    def __init__(self):
        self.uri = os.getenv("NEO4J_URI")
        self.username = os.getenv("NEO4J_USERNAME")
        self.password = os.getenv("NEO4J_PASSWORD")
        self.database = os.getenv("NEO4J_DATABASE")

        self.driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))

    def close(self):
        self.driver.close()

    # ========================================================================
    # EXAMPLE 1: Basic Queries
    # ========================================================================

    def get_all_drugs(self, limit=10):
        """Get all drugs in the database"""
        query = """
        MATCH (d:Drug)
        RETURN d.name as name, d.mechanism as mechanism, d.description as description
        LIMIT $limit
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(query, limit=limit)
            return [dict(record) for record in result]

    def get_drug_by_name(self, drug_name):
        """Get specific drug details"""
        query = """
        MATCH (d:Drug {name: $name})
        RETURN d
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(query, name=drug_name)
            record = result.single()
            return dict(record["d"]) if record else None

    # ========================================================================
    # EXAMPLE 2: Relationship Queries
    # ========================================================================

    def get_drug_treatments(self, disease_name):
        """Find all drugs that treat a specific disease"""
        query = """
        MATCH (d:Drug)-[r:TREATS]->(dis:Disease)
        WHERE dis.name CONTAINS $disease_name
        RETURN d.name as drug,
               d.mechanism as mechanism,
               r.efficacyRate as efficacy,
               dis.name as disease
        ORDER BY r.efficacyRate DESC
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(query, disease_name=disease_name)
            return [dict(record) for record in result]

    def get_drug_targets(self, drug_name):
        """Find protein targets for a drug"""
        query = """
        MATCH (d:Drug)-[r:TARGETS]->(p:Protein)
        WHERE d.name CONTAINS $drug_name
        RETURN d.name as drug,
               p.name as protein,
               p.proteinClass as proteinClass,
               r.bindingAffinity as affinity,
               r.mechanismType as mechanismType
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(query, drug_name=drug_name)
            return [dict(record) for record in result]

    # ========================================================================
    # EXAMPLE 3: Multi-hop Queries
    # ========================================================================

    def get_gene_disease_drug_pathway(self, gene_symbol):
        """Find complete pathway: Gene → Disease → Drug"""
        query = """
        MATCH (g:Gene)-[:ASSOCIATED_WITH]->(dis:Disease)<-[t:TREATS]-(d:Drug)
        WHERE g.symbol = $gene_symbol
        RETURN g.symbol as gene,
               dis.name as disease,
               d.name as drug,
               d.mechanism as mechanism,
               t.efficacyRate as efficacy
        ORDER BY t.efficacyRate DESC
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(query, gene_symbol=gene_symbol)
            return [dict(record) for record in result]

    def get_disease_genes(self, disease_name):
        """Find genes associated with a disease"""
        query = """
        MATCH (g:Gene)-[r:ASSOCIATED_WITH]->(d:Disease)
        WHERE d.name CONTAINS $disease_name
        RETURN g.symbol as gene,
               g.name as geneName,
               r.associationStrength as strength,
               r.evidenceLevel as evidence
        ORDER BY r.associationStrength DESC
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(query, disease_name=disease_name)
            return [dict(record) for record in result]

    # ========================================================================
    # EXAMPLE 4: Clinical Trial Queries
    # ========================================================================

    def get_clinical_trials_for_drug(self, drug_name):
        """Find clinical trials investigating a drug"""
        query = """
        MATCH (t:ClinicalTrial)-[:INVESTIGATES]->(d:Drug)
        MATCH (t)-[:STUDIES]->(dis:Disease)
        WHERE d.name CONTAINS $drug_name
        RETURN t.title as trial,
               t.phase as phase,
               t.status as status,
               t.enrollment as enrollment,
               d.name as drug,
               dis.name as disease
        ORDER BY t.startDate DESC
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(query, drug_name=drug_name)
            return [dict(record) for record in result]

    def get_adverse_events(self, drug_name):
        """Find adverse events for a drug"""
        query = """
        MATCH (d:Drug)<-[:INVESTIGATES]-(t:ClinicalTrial)-[:REPORTS]->(e:AdverseEvent)
        WHERE d.name CONTAINS $drug_name
        RETURN DISTINCT e.name as event,
               e.severity as severity,
               e.category as category,
               e.frequency as frequency
        ORDER BY e.severity DESC
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(query, drug_name=drug_name)
            return [dict(record) for record in result]

    # ========================================================================
    # EXAMPLE 5: Research Network Queries
    # ========================================================================

    def get_high_impact_researchers(self, min_h_index=70, specialization=None):
        """Find high-impact researchers"""
        if specialization:
            query = """
            MATCH (r:Researcher)-[:AFFILIATED_WITH]->(i:Institution)
            WHERE r.hIndex >= $min_h_index AND r.specialization CONTAINS $specialization
            RETURN r.name as researcher,
                   r.specialization as specialization,
                   r.hIndex as hIndex,
                   r.totalPublications as publications,
                   i.name as institution
            ORDER BY r.hIndex DESC
            """
            params = {"min_h_index": min_h_index, "specialization": specialization}
        else:
            query = """
            MATCH (r:Researcher)-[:AFFILIATED_WITH]->(i:Institution)
            WHERE r.hIndex >= $min_h_index
            RETURN r.name as researcher,
                   r.specialization as specialization,
                   r.hIndex as hIndex,
                   r.totalPublications as publications,
                   i.name as institution
            ORDER BY r.hIndex DESC
            """
            params = {"min_h_index": min_h_index}

        with self.driver.session(database=self.database) as session:
            result = session.run(query, **params)
            return [dict(record) for record in result]

    def get_research_papers_for_drug(self, drug_name):
        """Find research papers mentioning a drug"""
        query = """
        MATCH (p:ResearchPaper)-[:MENTIONS_DRUG]->(d:Drug)
        MATCH (p)-[:AUTHORED_BY]->(r:Researcher)
        WHERE d.name CONTAINS $drug_name
        RETURN p.title as paper,
               p.journal as journal,
               p.year as year,
               p.doi as doi,
               collect(r.name) as authors
        ORDER BY p.year DESC
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(query, drug_name=drug_name)
            return [dict(record) for record in result]

    # ========================================================================
    # EXAMPLE 6: Analytical Queries
    # ========================================================================

    def get_drug_statistics(self):
        """Get drug distribution statistics"""
        query = """
        MATCH (d:Drug)
        RETURN d.mechanism as mechanism,
               count(*) as drugCount,
               collect(d.name)[0..5] as sampleDrugs
        ORDER BY drugCount DESC
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(query)
            return [dict(record) for record in result]

    def get_most_researched_diseases(self, limit=10):
        """Find diseases with most clinical trials"""
        query = """
        MATCH (t:ClinicalTrial)-[:STUDIES]->(dis:Disease)
        RETURN dis.name as disease,
               count(t) as trialCount
        ORDER BY trialCount DESC
        LIMIT $limit
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(query, limit=limit)
            return [dict(record) for record in result]

    # ========================================================================
    # EXAMPLE 7: Vector Search (requires embeddings)
    # ========================================================================

    def vector_search(self, query_vector, k=10):
        """Perform vector similarity search"""
        query = """
        CALL db.index.vector.queryNodes('drug_embedding_vector', $k, $vector)
        YIELD node, score
        RETURN node.name as name,
               node.description as description,
               score
        ORDER BY score DESC
        LIMIT $k
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(query, k=k, vector=query_vector)
            return [dict(record) for record in result]

    # ========================================================================
    # EXAMPLE 8: Transaction Management
    # ========================================================================

    def create_drug(self, name, mechanism, description):
        """Create a new drug node"""
        query = """
        CREATE (d:Drug {
            name: $name,
            mechanism: $mechanism,
            description: $description,
            created_at: datetime()
        })
        RETURN d
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(query, name=name, mechanism=mechanism, description=description)
            return dict(result.single()["d"])

    def create_drug_disease_relationship(self, drug_name, disease_name, efficacy_rate):
        """Create TREATS relationship"""
        query = """
        MATCH (d:Drug {name: $drug_name})
        MATCH (dis:Disease {name: $disease_name})
        MERGE (d)-[r:TREATS]->(dis)
        SET r.efficacyRate = $efficacy_rate,
            r.created_at = datetime()
        RETURN d.name as drug, dis.name as disease, r.efficacyRate as efficacy
        """
        with self.driver.session(database=self.database) as session:
            result = session.run(
                query,
                drug_name=drug_name,
                disease_name=disease_name,
                efficacy_rate=efficacy_rate
            )
            return dict(result.single())

    # ========================================================================
    # EXAMPLE 9: Batch Operations
    # ========================================================================

    def batch_create_drugs(self, drugs):
        """Create multiple drugs in a single transaction"""
        query = """
        UNWIND $drugs as drug
        CREATE (d:Drug)
        SET d.name = drug.name,
            d.mechanism = drug.mechanism,
            d.description = drug.description,
            d.created_at = datetime()
        """
        with self.driver.session(database=self.database) as session:
            session.run(query, drugs=drugs)

    # ========================================================================
    # EXAMPLE 10: Database Statistics
    # ========================================================================

    def get_database_statistics(self):
        """Get comprehensive database statistics"""
        stats = {}

        with self.driver.session(database=self.database) as session:
            # Total nodes
            result = session.run("MATCH (n) RETURN count(n) as count")
            stats['total_nodes'] = result.single()['count']

            # Total relationships
            result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
            stats['total_relationships'] = result.single()['count']

            # Node counts by label
            result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] as label, count(*) as count
                ORDER BY count DESC
            """)
            stats['nodes_by_label'] = [dict(record) for record in result]

            # Relationship counts by type
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as type, count(*) as count
                ORDER BY count DESC
            """)
            stats['relationships_by_type'] = [dict(record) for record in result]

        return stats


# ============================================================================
# DEMO USAGE
# ============================================================================

def demo():
    """Demonstrate usage of Neo4j examples"""

    print("="*80)
    print("NEO4J USAGE EXAMPLES")
    print("="*80)

    examples = Neo4jExamples()

    try:
        # Example 1: Get database statistics
        print("\n1. Database Statistics:")
        print("-" * 40)
        stats = examples.get_database_statistics()
        print(f"Total nodes: {stats['total_nodes']:,}")
        print(f"Total relationships: {stats['total_relationships']:,}")

        # Example 2: Get all drugs
        print("\n2. All Drugs:")
        print("-" * 40)
        drugs = examples.get_all_drugs(limit=5)
        for drug in drugs:
            print(f"  • {drug['name']} ({drug['mechanism']})")

        # Example 3: Find treatments for a disease
        print("\n3. Treatments for Lung Cancer:")
        print("-" * 40)
        treatments = examples.get_drug_treatments("Lung Cancer")
        for treatment in treatments:
            print(f"  • {treatment['drug']}: {treatment['efficacy']:.2%} efficacy")

        # Example 4: Gene-Disease-Drug pathway
        print("\n4. EGFR Gene Pathway:")
        print("-" * 40)
        pathways = examples.get_gene_disease_drug_pathway("EGFR")
        for pathway in pathways:
            print(f"  • {pathway['gene']} → {pathway['disease']} → {pathway['drug']}")

        # Example 5: High-impact researchers
        print("\n5. High-Impact Researchers:")
        print("-" * 40)
        researchers = examples.get_high_impact_researchers()
        for researcher in researchers[:5]:
            print(f"  • {researcher['researcher']} (h-index: {researcher['hIndex']})")

        print("\n" + "="*80)
        print("✅ Demo complete!")
        print("="*80)

    except Exception as e:
        print(f"\n❌ Error: {e}")

    finally:
        examples.close()


if __name__ == "__main__":
    demo()
