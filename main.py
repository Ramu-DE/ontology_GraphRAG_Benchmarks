#!/usr/bin/env python3
"""
Biomedical Knowledge Graph - Main Application
Demonstrates the full W3C Semantic Stack:
- RDF (Resource Description Framework)
- RDFS (RDF Schema)
- OWL (Web Ontology Language)
- SPARQL (Query Language)
- SHACL (Shapes Constraint Language)
"""

import os
import sys
from rdflib import Graph, Namespace
from rdflib.plugins.sparql import prepareQuery
from pyshacl import validate
import json


class BiomedicalKnowledgeGraph:
    """Main class for biomedical knowledge graph operations"""

    def __init__(self):
        self.graph = Graph()
        self.BIO = Namespace("http://example.com/biomedical#")
        self.DATA = Namespace("http://example.com/data/")

        # Bind namespaces
        self.graph.bind("bio", self.BIO)
        self.graph.bind("data", self.DATA)

        print("=" * 80)
        print("BIOMEDICAL KNOWLEDGE GRAPH - W3C SEMANTIC STACK DEMONSTRATION")
        print("=" * 80)

    def load_ontology(self, ontology_file):
        """Load the OWL ontology (RDFS + OWL)"""
        print("\n[STEP 1] Loading Ontology (RDFS + OWL)...")
        print("-" * 80)

        if not os.path.exists(ontology_file):
            print(f"Error: Ontology file not found: {ontology_file}")
            return False

        self.graph.parse(ontology_file, format="turtle")
        print(f"✓ Loaded ontology: {ontology_file}")
        print(f"  Classes, properties, and reasoning rules defined")
        return True

    def load_data(self, data_file):
        """Load RDF data triples"""
        print("\n[STEP 2] Loading RDF Data...")
        print("-" * 80)

        if not os.path.exists(data_file):
            print(f"Error: Data file not found: {data_file}")
            return False

        before_count = len(self.graph)
        self.graph.parse(data_file, format="turtle")
        after_count = len(self.graph)
        data_triples = after_count - before_count

        print(f"✓ Loaded RDF data: {data_file}")
        print(f"  Total triples in graph: {after_count:,}")
        print(f"  Data triples: {data_triples:,}")
        return True

    def validate_with_shacl(self, shapes_file):
        """Validate RDF data using SHACL shapes"""
        print("\n[STEP 3] Validating with SHACL...")
        print("-" * 80)

        if not os.path.exists(shapes_file):
            print(f"Error: SHACL shapes file not found: {shapes_file}")
            return False

        shapes_graph = Graph()
        shapes_graph.parse(shapes_file, format="turtle")

        conforms, results_graph, results_text = validate(
            self.graph,
            shacl_graph=shapes_graph,
            ont_graph=None,
            inference='rdfs',
            abort_on_first=False,
            allow_warnings=True,
            meta_shacl=False
        )

        print(f"✓ SHACL validation completed")
        print(f"  Conforms: {conforms}")

        if not conforms:
            print("\n  Validation Issues Found:")
            print(results_text)
        else:
            print("  All data conforms to SHACL shapes!")

        return conforms

    def execute_sparql_query(self, query_string, query_name="Query"):
        """Execute a SPARQL query and return results"""
        print(f"\n[SPARQL] {query_name}")
        print("-" * 80)

        try:
            results = self.graph.query(query_string)
            return list(results)
        except Exception as e:
            print(f"Error executing query: {e}")
            return []

    def display_results(self, results, limit=10):
        """Display query results in a formatted table"""
        if not results:
            print("No results found.")
            return

        if len(results) == 0:
            print("Query returned 0 results.")
            return

        # Get column headers from first result
        if hasattr(results[0], 'labels'):
            headers = results[0].labels
        else:
            headers = list(results[0].asdict().keys())

        # Print header
        print("\nResults:")
        header_line = " | ".join(f"{h:30}" for h in headers)
        print(header_line)
        print("-" * len(header_line))

        # Print rows (up to limit)
        count = 0
        for row in results:
            if count >= limit:
                print(f"\n... and {len(results) - limit} more results")
                break

            values = []
            for var in headers:
                val = row.get(var, "")
                if val:
                    # Clean up URIs to show only the local part
                    val_str = str(val)
                    if "#" in val_str:
                        val_str = val_str.split("#")[-1]
                    elif "/" in val_str:
                        val_str = val_str.split("/")[-1]
                    values.append(val_str[:30])
                else:
                    values.append("")

            print(" | ".join(f"{v:30}" for v in values))
            count += 1

        print(f"\nTotal results: {len(results)}")

    def run_demonstration_queries(self):
        """Run demonstration SPARQL queries"""
        print("\n" + "=" * 80)
        print("DEMONSTRATION: SPARQL QUERIES")
        print("=" * 80)

        # Query 1: List all drugs
        query1 = """
        PREFIX bio: <http://example.com/biomedical#>

        SELECT ?drugName ?drugType ?approvalStatus ?approvalYear
        WHERE {
            ?drug a bio:Drug ;
                  bio:drugName ?drugName ;
                  bio:drugType ?drugType ;
                  bio:approvalStatus ?approvalStatus ;
                  bio:approvalYear ?approvalYear .
        }
        ORDER BY DESC(?approvalYear)
        """
        results1 = self.execute_sparql_query(query1, "Query 1: All Drugs")
        self.display_results(results1, limit=5)

        # Query 2: Drugs treating specific diseases
        query2 = """
        PREFIX bio: <http://example.com/biomedical#>

        SELECT ?drugName ?diseaseName ?efficacy
        WHERE {
            ?drug a bio:Drug ;
                  bio:drugName ?drugName ;
                  bio:treats ?disease .

            ?disease bio:diseaseName ?diseaseName .

            ?treatment a <http://www.w3.org/1999/02/22-rdf-syntax-ns#Statement> ;
                      <http://www.w3.org/1999/02/22-rdf-syntax-ns#subject> ?drug ;
                      <http://www.w3.org/1999/02/22-rdf-syntax-ns#predicate> bio:treats ;
                      <http://www.w3.org/1999/02/22-rdf-syntax-ns#object> ?disease ;
                      bio:efficacyRate ?efficacy .

            FILTER(?efficacy > 0.40)
        }
        ORDER BY DESC(?efficacy)
        """
        results2 = self.execute_sparql_query(query2, "Query 2: High-Efficacy Treatments")
        self.display_results(results2, limit=5)

        # Query 3: Immunotherapy drugs (using OWL reasoning)
        query3 = """
        PREFIX bio: <http://example.com/biomedical#>

        SELECT ?drugName ?proteinName ?proteinClass
        WHERE {
            ?drug a bio:Drug ;
                  bio:drugName ?drugName ;
                  bio:targets ?protein .

            ?protein a bio:ImmuneCheckpointProtein ;
                    bio:proteinName ?proteinName ;
                    bio:proteinClass ?proteinClass .
        }
        """
        results3 = self.execute_sparql_query(query3, "Query 3: Immunotherapy Drugs")
        self.display_results(results3)

        # Query 4: Gene-Disease-Drug pathways
        query4 = """
        PREFIX bio: <http://example.com/biomedical#>

        SELECT ?geneSymbol ?diseaseName ?drugName
        WHERE {
            ?gene bio:geneSymbol ?geneSymbol .

            ?disease bio:associatedWithGene ?gene ;
                    bio:diseaseName ?diseaseName .

            ?drug bio:treats ?disease ;
                  bio:drugName ?drugName .
        }
        ORDER BY ?geneSymbol
        """
        results4 = self.execute_sparql_query(query4, "Query 4: Gene → Disease → Drug Pathways")
        self.display_results(results4, limit=10)

        # Query 5: Clinical trial statistics
        query5 = """
        PREFIX bio: <http://example.com/biomedical#>

        SELECT ?phase (COUNT(?trial) as ?count) (AVG(?enrollment) as ?avgEnrollment)
        WHERE {
            ?trial a bio:ClinicalTrial ;
                  bio:phase ?phase ;
                  bio:enrollment ?enrollment .
        }
        GROUP BY ?phase
        ORDER BY ?phase
        """
        results5 = self.execute_sparql_query(query5, "Query 5: Clinical Trial Statistics")
        self.display_results(results5)

        # Query 6: High-impact researchers
        query6 = """
        PREFIX bio: <http://example.com/biomedical#>

        SELECT ?name ?specialization ?hIndex ?publications
        WHERE {
            ?researcher a bio:Researcher ;
                       bio:researcherName ?name ;
                       bio:specialization ?specialization ;
                       bio:hIndex ?hIndex ;
                       bio:totalPublications ?publications .

            FILTER(?hIndex >= 70)
        }
        ORDER BY DESC(?hIndex)
        """
        results6 = self.execute_sparql_query(query6, "Query 6: High-Impact Researchers")
        self.display_results(results6)

    def demonstrate_ai_integration(self):
        """Demonstrate how AI can use this knowledge graph"""
        print("\n" + "=" * 80)
        print("DEMONSTRATION: AI INTEGRATION USE CASES")
        print("=" * 80)

        print("""
The knowledge graph provides structured, semantically-rich context for AI systems:

1. QUESTION ANSWERING
   User: "What drugs treat lung cancer?"
   → AI queries graph with SPARQL
   → Returns: Pembrolizumab, Nivolumab, Atezolizumab
   → AI can explain: mechanism, efficacy, clinical trials, adverse events

2. DRUG DISCOVERY
   User: "Find drugs that target PD-1"
   → AI traverses: Drug → targets → Protein(PD-1)
   → Discovers: immunotherapy class pattern
   → AI can suggest: similar mechanisms for new targets

3. CLINICAL DECISION SUPPORT
   User: "Patient has BRCA1 mutation and breast cancer"
   → AI reasons: Gene(BRCA1) → Disease(Breast Cancer) → Drug(Trastuzumab)
   → AI retrieves: efficacy rates, trial data, biomarkers
   → Provides evidence-based recommendation

4. SAFETY MONITORING
   User: "What are risks of immunotherapy?"
   → AI queries: Immunotherapy → ClinicalTrial → AdverseEvent
   → Returns: immune-related pneumonitis, colitis, etc.
   → AI explains severity, frequency, monitoring requirements

5. RESEARCH EXPLORATION
   User: "Who's working on Alzheimer's treatments?"
   → AI traverses: Disease → studiedIn → ClinicalTrial → Institution → Researcher
   → Finds research networks, collaborations, publications
   → AI summarizes current state of research

KEY ADVANTAGE: AI doesn't hallucinate relationships
- Every connection is a verified triple in the graph
- Provenance is traceable
- Reasoning is explainable
        """)

    def generate_statistics(self):
        """Generate statistics about the knowledge graph"""
        print("\n" + "=" * 80)
        print("KNOWLEDGE GRAPH STATISTICS")
        print("=" * 80)

        stats = {}

        # Count entities by type
        entity_types = [
            ("Drug", self.BIO.Drug),
            ("Disease", self.BIO.Disease),
            ("ClinicalTrial", self.BIO.ClinicalTrial),
            ("Gene", self.BIO.Gene),
            ("Protein", self.BIO.Protein),
            ("Biomarker", self.BIO.Biomarker),
            ("Researcher", self.BIO.Researcher),
            ("Institution", self.BIO.Institution),
            ("ResearchPaper", self.BIO.ResearchPaper),
            ("AdverseEvent", self.BIO.AdverseEvent)
        ]

        print("\nEntity Counts:")
        print("-" * 40)
        for name, entity_type in entity_types:
            query = f"""
            PREFIX bio: <http://example.com/biomedical#>
            SELECT (COUNT(?entity) as ?count)
            WHERE {{
                ?entity a bio:{name} .
            }}
            """
            results = list(self.graph.query(query))
            count = int(results[0][0]) if results and results[0][0] else 0
            stats[name] = count
            print(f"  {name:20} : {count:5}")

        # Count relationships
        print("\nRelationship Counts:")
        print("-" * 40)

        relationships = [
            ("treats", self.BIO.treats),
            ("targets", self.BIO.targets),
            ("associatedWithGene", self.BIO.associatedWithGene),
            ("investigatesDrug", self.BIO.investigatesDrug),
            ("studiesDisease", self.BIO.studiesDisease)
        ]

        for name, rel in relationships:
            query = f"""
            PREFIX bio: <http://example.com/biomedical#>
            SELECT (COUNT(*) as ?count)
            WHERE {{
                ?s bio:{name} ?o .
            }}
            """
            results = list(self.graph.query(query))
            count = int(results[0][0]) if results and results[0][0] else 0
            print(f"  {name:20} : {count:5}")

        print(f"\n  Total Triples       : {len(self.graph):5,}")

        return stats

    def export_summary(self, output_file="output/kg_summary.json"):
        """Export knowledge graph summary"""
        stats = self.generate_statistics()

        summary = {
            "knowledge_graph": "Biomedical Knowledge Graph",
            "standards_used": [
                "RDF (Resource Description Framework)",
                "RDFS (RDF Schema)",
                "OWL (Web Ontology Language)",
                "SPARQL (Query Language)",
                "SHACL (Shapes Constraint Language)"
            ],
            "statistics": stats,
            "total_triples": len(self.graph),
            "capabilities": [
                "Semantic data representation",
                "Ontology-based reasoning",
                "Graph traversal queries",
                "Data validation",
                "AI integration"
            ]
        }

        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2)

        print(f"\n✓ Summary exported to: {output_file}")


def main():
    """Main execution function"""

    # Initialize knowledge graph
    kg = BiomedicalKnowledgeGraph()

    # Step 1: Load ontology (RDFS + OWL)
    ontology_file = "ontology/biomedical_ontology.ttl"
    if not kg.load_ontology(ontology_file):
        print("\nError: Could not load ontology. Please run csv_to_rdf.py first.")
        return

    # Step 2: Load RDF data
    data_file = "output/biomedical_data.ttl"
    if not kg.load_data(data_file):
        print("\nError: Could not load data. Please run csv_to_rdf.py first.")
        print("\nTo generate the data file, run:")
        print("  python scripts/csv_to_rdf.py")
        return

    # Step 3: Validate with SHACL
    shapes_file = "validation/shacl_shapes.ttl"
    kg.validate_with_shacl(shapes_file)

    # Step 4: Run demonstration queries
    kg.run_demonstration_queries()

    # Step 5: Generate statistics
    kg.generate_statistics()

    # Step 6: Demonstrate AI integration
    kg.demonstrate_ai_integration()

    # Step 7: Export summary
    kg.export_summary()

    print("\n" + "=" * 80)
    print("DEMONSTRATION COMPLETE!")
    print("=" * 80)
    print("""
This demonstration showed the full W3C semantic stack in action:

✓ RDF      : Data represented as subject-predicate-object triples
✓ RDFS     : Schema defining classes and properties
✓ OWL      : Ontology with logical reasoning rules
✓ SPARQL   : Powerful graph query language
✓ SHACL    : Data validation and quality constraints

The knowledge graph is now ready for AI integration!
    """)


if __name__ == "__main__":
    main()
