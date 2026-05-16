"""
Advanced Multi-Hop Reasoning Queries for Neo4j
Demonstrates complex graph traversals and analytical queries
"""

from neo4j import GraphDatabase
import os
from typing import List, Dict, Any
import json


class AdvancedNeo4jQueries:
    """Advanced query patterns for knowledge graph reasoning"""

    def __init__(self, uri: str, user: str, password: str, database: str = "neo4j"):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.database = database

    def close(self):
        self.driver.close()

    def _execute_query(self, query: str, parameters: dict = None) -> List[Dict[str, Any]]:
        """Execute query and return results"""
        with self.driver.session(database=self.database) as session:
            result = session.run(query, parameters or {})
            return [dict(record) for record in result]

    # ========================================================================
    # QUERY 1: Gene-Protein-Drug-Disease Multi-Hop Traversal
    # ========================================================================

    def query_1_full_pathway(self):
        """
        Find complete pathways: Gene -> Protein -> Drug -> Disease
        Shows: Which genes, when targeted, lead to disease treatments
        """
        query = """
        // Multi-hop: Gene encodes Protein, Drug targets Protein, Drug treats Disease
        MATCH (g:Gene)-[:ASSOCIATED_WITH]->(d:Disease)
        MATCH (drug:Drug)-[:TREATS]->(d)
        RETURN
            g.symbol AS gene_symbol,
            g.name AS gene_name,
            d.name AS disease_name,
            collect(DISTINCT drug.name) AS treating_drugs,
            count(DISTINCT drug) AS drug_count
        ORDER BY drug_count DESC
        LIMIT 10
        """

        print("\n" + "="*80)
        print("QUERY 1: Complete Gene → Disease → Drug Pathway")
        print("="*80)
        print("Finding: Which genes are associated with diseases and what drugs treat them\n")

        results = self._execute_query(query)

        for i, record in enumerate(results, 1):
            print(f"{i}. Gene: {record['gene_symbol']} ({record['gene_name']})")
            print(f"   Disease: {record['disease_name']}")
            print(f"   Treating Drugs ({record['drug_count']}): {', '.join(record['treating_drugs'])}")
            print()

        return results

    # ========================================================================
    # QUERY 2: Find Alternative Treatment Pathways
    # ========================================================================

    def query_2_alternative_pathways(self, disease_name: str = "Non-Small Cell Lung Cancer"):
        """
        Find all possible treatment pathways for a disease
        Shows: Multiple therapeutic approaches for the same disease
        """
        query = """
        // Find all drugs treating the disease
        MATCH (disease:Disease {name: $disease_name})
        MATCH (drug:Drug)-[:TREATS]->(disease)

        // Find genes associated with the disease
        OPTIONAL MATCH (gene:Gene)-[:ASSOCIATED_WITH]->(disease)

        RETURN
            disease.name AS disease,
            drug.name AS drug,
            drug.description AS mechanism,
            drug.mechanism AS drug_class,
            collect(DISTINCT gene.symbol) AS associated_genes
        ORDER BY drug.name
        """

        print("\n" + "="*80)
        print(f"QUERY 2: Alternative Treatment Pathways for {disease_name}")
        print("="*80)
        print("Finding: All therapeutic approaches targeting this disease\n")

        results = self._execute_query(query, {"disease_name": disease_name})

        for i, record in enumerate(results, 1):
            print(f"{i}. Drug: {record['drug']}")
            print(f"   Mechanism: {record['mechanism']}")
            print(f"   Class: {record['drug_class']}")
            if record['associated_genes']:
                print(f"   Target Genes: {', '.join(record['associated_genes'])}")
            print()

        return results

    # ========================================================================
    # QUERY 3: Drug Combination Discovery
    # ========================================================================

    def query_3_drug_combinations(self):
        """
        Find drugs that could work together (treat same disease via different mechanisms)
        Shows: Potential combination therapy opportunities
        """
        query = """
        // Find pairs of drugs treating the same disease with different mechanisms
        MATCH (d1:Drug)-[:TREATS]->(disease:Disease)<-[:TREATS]-(d2:Drug)
        WHERE d1.name < d2.name  // Avoid duplicates
          AND d1.mechanism <> d2.mechanism  // Different mechanisms

        RETURN
            disease.name AS disease,
            d1.name AS drug_1,
            d1.mechanism AS mechanism_1,
            d2.name AS drug_2,
            d2.mechanism AS mechanism_2,
            'Synergistic potential: different mechanisms' AS rationale
        ORDER BY disease.name, d1.name
        LIMIT 15
        """

        print("\n" + "="*80)
        print("QUERY 3: Drug Combination Discovery")
        print("="*80)
        print("Finding: Drugs treating same disease via different mechanisms (combination therapy)\n")

        results = self._execute_query(query)

        for i, record in enumerate(results, 1):
            print(f"{i}. Disease: {record['disease']}")
            print(f"   Combination:")
            print(f"     • {record['drug_1']} ({record['mechanism_1']})")
            print(f"     • {record['drug_2']} ({record['mechanism_2']})")
            print(f"   {record['rationale']}")
            print()

        return results

    # ========================================================================
    # QUERY 4: Cross-Disease Gene Analysis
    # ========================================================================

    def query_4_cross_disease_genes(self):
        """
        Find genes associated with multiple diseases
        Shows: Potential drug repurposing opportunities
        """
        query = """
        // Find genes associated with multiple diseases
        MATCH (g:Gene)-[:ASSOCIATED_WITH]->(d:Disease)
        WITH g, collect(DISTINCT d.name) AS diseases, count(DISTINCT d) AS disease_count
        WHERE disease_count > 1

        // Find drugs that could target these genes
        MATCH (drug:Drug)-[:TREATS]->(disease:Disease)
        WHERE disease.name IN diseases

        RETURN
            g.symbol AS gene,
            g.name AS gene_name,
            diseases AS associated_diseases,
            disease_count,
            collect(DISTINCT drug.name) AS potential_drugs
        ORDER BY disease_count DESC
        """

        print("\n" + "="*80)
        print("QUERY 4: Cross-Disease Gene Analysis")
        print("="*80)
        print("Finding: Genes associated with multiple diseases (drug repurposing targets)\n")

        results = self._execute_query(query)

        for i, record in enumerate(results, 1):
            print(f"{i}. Gene: {record['gene']} ({record['gene_name']})")
            print(f"   Associated with {record['disease_count']} diseases:")
            for disease in record['associated_diseases']:
                print(f"     • {disease}")
            print(f"   Potential drugs: {', '.join(record['potential_drugs'])}")
            print()

        return results

    # ========================================================================
    # QUERY 5: Disease Similarity via Shared Genes
    # ========================================================================

    def query_5_disease_similarity(self):
        """
        Find diseases that share genetic associations
        Shows: Disease relationships and potential treatment crossover
        """
        query = """
        // Find pairs of diseases sharing genes
        MATCH (d1:Disease)<-[:ASSOCIATED_WITH]-(g:Gene)-[:ASSOCIATED_WITH]->(d2:Disease)
        WHERE id(d1) < id(d2)  // Avoid duplicates

        WITH d1, d2, collect(DISTINCT g.symbol) AS shared_genes, count(DISTINCT g) AS gene_count
        WHERE gene_count > 0

        // Find drugs treating either disease
        OPTIONAL MATCH (drug:Drug)-[:TREATS]->(d1)
        OPTIONAL MATCH (drug2:Drug)-[:TREATS]->(d2)

        RETURN
            d1.name AS disease_1,
            d2.name AS disease_2,
            shared_genes,
            gene_count AS shared_gene_count,
            collect(DISTINCT drug.name) AS drugs_for_disease_1,
            collect(DISTINCT drug2.name) AS drugs_for_disease_2
        ORDER BY gene_count DESC
        LIMIT 10
        """

        print("\n" + "="*80)
        print("QUERY 5: Disease Similarity via Shared Genes")
        print("="*80)
        print("Finding: Diseases with common genetic associations (treatment crossover potential)\n")

        results = self._execute_query(query)

        for i, record in enumerate(results, 1):
            print(f"{i}. Disease Pair:")
            print(f"   • {record['disease_1']}")
            print(f"   • {record['disease_2']}")
            print(f"   Shared Genes ({record['shared_gene_count']}): {', '.join(record['shared_genes'])}")
            if record['drugs_for_disease_1']:
                print(f"   Drugs for {record['disease_1']}: {', '.join(record['drugs_for_disease_1'])}")
            if record['drugs_for_disease_2']:
                print(f"   Drugs for {record['disease_2']}: {', '.join(record['drugs_for_disease_2'])}")
            print()

        return results

    # ========================================================================
    # QUERY 6: Mechanism-Based Drug Clustering
    # ========================================================================

    def query_6_mechanism_clusters(self):
        """
        Group drugs by mechanism and show disease coverage
        Shows: Therapeutic mechanism landscape
        """
        query = """
        // Group drugs by mechanism
        MATCH (drug:Drug)-[:TREATS]->(disease:Disease)

        RETURN
            drug.mechanism AS mechanism,
            count(DISTINCT drug) AS drug_count,
            collect(DISTINCT drug.name) AS drugs,
            collect(DISTINCT disease.name) AS diseases_treated,
            count(DISTINCT disease) AS disease_count
        ORDER BY drug_count DESC, disease_count DESC
        """

        print("\n" + "="*80)
        print("QUERY 6: Mechanism-Based Drug Clustering")
        print("="*80)
        print("Finding: Drug mechanisms and their disease coverage\n")

        results = self._execute_query(query)

        for i, record in enumerate(results, 1):
            print(f"{i}. Mechanism: {record['mechanism']}")
            print(f"   Drugs ({record['drug_count']}): {', '.join(record['drugs'])}")
            print(f"   Treats {record['disease_count']} diseases: {', '.join(record['diseases_treated'])}")
            print()

        return results

    # ========================================================================
    # QUERY 7: Patient Treatment Recommendation Simulation
    # ========================================================================

    def query_7_treatment_recommendation(self, gene_mutation: str = "EGFR"):
        """
        Simulate treatment recommendation based on gene mutation
        Shows: Precision medicine pathway
        """
        query = """
        // Given a gene mutation, find:
        // 1. Diseases associated with this gene
        // 2. Drugs treating those diseases
        // 3. Prioritize by number of connections

        MATCH (g:Gene {symbol: $gene_symbol})-[:ASSOCIATED_WITH]->(disease:Disease)
        MATCH (drug:Drug)-[:TREATS]->(disease)

        RETURN
            g.symbol AS mutated_gene,
            g.name AS gene_name,
            disease.name AS associated_disease,
            drug.name AS recommended_drug,
            drug.description AS drug_description,
            drug.mechanism AS mechanism
        ORDER BY disease.name, drug.name
        """

        print("\n" + "="*80)
        print(f"QUERY 7: Treatment Recommendation for {gene_mutation} Mutation")
        print("="*80)
        print(f"Precision Medicine: Finding treatments for patients with {gene_mutation} mutations\n")

        results = self._execute_query(query, {"gene_symbol": gene_mutation})

        if not results:
            print(f"No treatment recommendations found for {gene_mutation} mutation.")
            return []

        current_disease = None
        for record in results:
            if record['associated_disease'] != current_disease:
                current_disease = record['associated_disease']
                print(f"Disease: {record['associated_disease']}")
                print(f"  (Associated with {record['mutated_gene']} gene: {record['gene_name']})\n")

            print(f"  ✓ Recommended: {record['recommended_drug']}")
            print(f"    Mechanism: {record['mechanism']}")
            print(f"    Description: {record['drug_description']}")
            print()

        return results

    # ========================================================================
    # QUERY 8: Shortest Path Between Any Two Entities
    # ========================================================================

    def query_8_shortest_path(self, start_name: str = "EGFR", end_name: str = "Melanoma"):
        """
        Find shortest path between any two entities
        Shows: Connection discovery and reasoning chains
        """
        query = """
        // Find nodes by name (could be Gene, Drug, or Disease)
        MATCH (start) WHERE start.name CONTAINS $start_name OR start.symbol CONTAINS $start_name
        MATCH (end) WHERE end.name CONTAINS $end_name OR end.symbol CONTAINS $end_name

        // Find shortest path
        MATCH path = shortestPath((start)-[*..5]-(end))

        RETURN
            [node in nodes(path) | {
                type: labels(node)[0],
                name: coalesce(node.name, node.symbol),
                description: node.description
            }] AS path_nodes,
            [rel in relationships(path) | type(rel)] AS relationships,
            length(path) AS path_length
        ORDER BY path_length ASC
        LIMIT 5
        """

        print("\n" + "="*80)
        print(f"QUERY 8: Shortest Path from '{start_name}' to '{end_name}'")
        print("="*80)
        print("Finding: Connection chains and reasoning pathways\n")

        results = self._execute_query(query, {
            "start_name": start_name,
            "end_name": end_name
        })

        if not results:
            print(f"No path found between '{start_name}' and '{end_name}'")
            return []

        for i, record in enumerate(results, 1):
            print(f"Path {i} (Length: {record['path_length']} hops):")

            nodes = record['path_nodes']
            rels = record['relationships']

            for j, node in enumerate(nodes):
                indent = "  " * j
                print(f"{indent}• [{node['type']}] {node['name']}")
                if node.get('description'):
                    print(f"{indent}  ({node['description']})")

                if j < len(rels):
                    print(f"{indent}  ↓ {rels[j]}")

            print()

        return results

    # ========================================================================
    # QUERY 9: Drug Repurposing Opportunities
    # ========================================================================

    def query_9_drug_repurposing(self):
        """
        Find drugs that could be repurposed for other diseases
        Based on shared genetic associations
        """
        query = """
        // Find: Drug treats Disease1, Disease1 and Disease2 share genes,
        // suggest Drug for Disease2 (repurposing)

        MATCH (drug:Drug)-[:TREATS]->(d1:Disease)
        MATCH (d1)<-[:ASSOCIATED_WITH]-(g:Gene)-[:ASSOCIATED_WITH]->(d2:Disease)
        WHERE d1 <> d2
          AND NOT (drug)-[:TREATS]->(d2)  // Drug doesn't already treat d2

        WITH drug, d1, d2, collect(DISTINCT g.symbol) AS shared_genes, count(DISTINCT g) AS gene_count
        WHERE gene_count >= 1

        RETURN
            drug.name AS drug,
            drug.mechanism AS mechanism,
            d1.name AS currently_treats,
            d2.name AS repurposing_target,
            shared_genes AS shared_genetic_basis,
            gene_count AS evidence_strength
        ORDER BY gene_count DESC, drug.name
        LIMIT 15
        """

        print("\n" + "="*80)
        print("QUERY 9: Drug Repurposing Opportunities")
        print("="*80)
        print("Finding: Drugs that could be repurposed for other diseases via shared genetics\n")

        results = self._execute_query(query)

        for i, record in enumerate(results, 1):
            print(f"{i}. Repurposing Opportunity:")
            print(f"   Drug: {record['drug']} ({record['mechanism']})")
            print(f"   Currently treats: {record['currently_treats']}")
            print(f"   Could treat: {record['repurposing_target']}")
            print(f"   Shared genetic basis ({record['evidence_strength']} genes): {', '.join(record['shared_genetic_basis'])}")
            print(f"   Evidence strength: {'●' * record['evidence_strength']}")
            print()

        return results

    # ========================================================================
    # QUERY 10: Graph Statistics and Insights
    # ========================================================================

    def query_10_graph_statistics(self):
        """
        Comprehensive graph statistics
        Shows: Overall knowledge graph structure
        """
        queries = {
            "node_counts": """
                MATCH (n)
                RETURN labels(n)[0] AS node_type, count(n) AS count
                ORDER BY count DESC
            """,

            "relationship_counts": """
                MATCH ()-[r]->()
                RETURN type(r) AS relationship_type, count(r) AS count
                ORDER BY count DESC
            """,

            "most_connected_genes": """
                MATCH (g:Gene)-[r]-()
                RETURN g.symbol AS gene, g.name AS gene_name, count(r) AS connections
                ORDER BY connections DESC
                LIMIT 5
            """,

            "most_versatile_drugs": """
                MATCH (d:Drug)-[:TREATS]->(disease:Disease)
                RETURN d.name AS drug, d.mechanism AS mechanism,
                       count(disease) AS diseases_treated
                ORDER BY diseases_treated DESC
                LIMIT 5
            """,

            "diseases_by_treatment_options": """
                MATCH (disease:Disease)<-[:TREATS]-(drug:Drug)
                RETURN disease.name AS disease, count(drug) AS treatment_options
                ORDER BY treatment_options DESC
            """
        }

        print("\n" + "="*80)
        print("QUERY 10: Graph Statistics and Insights")
        print("="*80)

        all_results = {}

        # Node counts
        print("\nNode Counts:")
        print("-" * 40)
        results = self._execute_query(queries["node_counts"])
        for record in results:
            print(f"  {record['node_type']}: {record['count']}")
        all_results['node_counts'] = results

        # Relationship counts
        print("\nRelationship Counts:")
        print("-" * 40)
        results = self._execute_query(queries["relationship_counts"])
        for record in results:
            print(f"  {record['relationship_type']}: {record['count']}")
        all_results['relationship_counts'] = results

        # Most connected genes
        print("\nMost Connected Genes:")
        print("-" * 40)
        results = self._execute_query(queries["most_connected_genes"])
        for i, record in enumerate(results, 1):
            print(f"  {i}. {record['gene']} ({record['gene_name']}): {record['connections']} connections")
        all_results['most_connected_genes'] = results

        # Most versatile drugs
        print("\nMost Versatile Drugs (treats multiple diseases):")
        print("-" * 40)
        results = self._execute_query(queries["most_versatile_drugs"])
        for i, record in enumerate(results, 1):
            print(f"  {i}. {record['drug']} ({record['mechanism']}): treats {record['diseases_treated']} diseases")
        all_results['most_versatile_drugs'] = results

        # Diseases by treatment options
        print("\nDiseases by Treatment Options:")
        print("-" * 40)
        results = self._execute_query(queries["diseases_by_treatment_options"])
        for record in results:
            print(f"  {record['disease']}: {record['treatment_options']} treatment options")
        all_results['diseases_by_treatment_options'] = results

        return all_results


def main():
    """Run all advanced queries"""

    # Load credentials
    uri = os.getenv("NEO4J_URI", "")
    username = os.getenv("NEO4J_USERNAME", "")
    password = os.getenv("NEO4J_PASSWORD", "")
    database = os.getenv("NEO4J_DATABASE", "")

    print("="*80)
    print("ADVANCED NEO4J MULTI-HOP REASONING QUERIES")
    print("="*80)
    print(f"Connecting to: {uri}")
    print(f"Database: {database}")
    print("="*80)

    queries = AdvancedNeo4jQueries(uri, username, password, database)

    try:
        # Run all queries
        queries.query_1_full_pathway()
        queries.query_2_alternative_pathways()
        queries.query_3_drug_combinations()
        queries.query_4_cross_disease_genes()
        queries.query_5_disease_similarity()
        queries.query_6_mechanism_clusters()
        queries.query_7_treatment_recommendation()
        queries.query_8_shortest_path()
        queries.query_9_drug_repurposing()
        queries.query_10_graph_statistics()

        print("\n" + "="*80)
        print("ALL QUERIES COMPLETED SUCCESSFULLY")
        print("="*80)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        queries.close()


if __name__ == "__main__":
    main()
