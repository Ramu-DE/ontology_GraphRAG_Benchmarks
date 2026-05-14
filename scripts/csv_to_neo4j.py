#!/usr/bin/env python3
"""
CSV to Neo4j Converter for Biomedical Knowledge Graph
Loads data from CSV files into Neo4j Aura instance
"""

import os
import csv
from neo4j import GraphDatabase
from dotenv import load_dotenv
from datetime import datetime


class BiomedicalNeo4jLoader:
    """Loads biomedical data into Neo4j graph database"""

    def __init__(self):
        # Load environment variables
        load_dotenv()

        self.uri = os.getenv('NEO4J_URI')
        self.username = os.getenv('NEO4J_USERNAME')
        self.password = os.getenv('NEO4J_PASSWORD')
        self.database = os.getenv('NEO4J_DATABASE', 'neo4j')

        print("=" * 80)
        print("BIOMEDICAL KNOWLEDGE GRAPH - Neo4j Loader")
        print("=" * 80)
        print(f"\nConnecting to Neo4j Aura...")
        print(f"  URI: {self.uri}")
        print(f"  Database: {self.database}")

        self.driver = GraphDatabase.driver(
            self.uri,
            auth=(self.username, self.password)
        )

        # Test connection
        self.driver.verify_connectivity()
        print("✓ Connected successfully!")

    def close(self):
        """Close Neo4j connection"""
        self.driver.close()

    def clear_database(self):
        """Clear all nodes and relationships (use with caution!)"""
        print("\nClearing existing data...")
        with self.driver.session(database=self.database) as session:
            session.run("MATCH (n) DETACH DELETE n")
        print("✓ Database cleared")

    def create_constraints(self):
        """Create uniqueness constraints for better performance"""
        print("\nCreating constraints and indexes...")

        constraints = [
            "CREATE CONSTRAINT drug_id IF NOT EXISTS FOR (d:Drug) REQUIRE d.drugId IS UNIQUE",
            "CREATE CONSTRAINT disease_id IF NOT EXISTS FOR (d:Disease) REQUIRE d.diseaseId IS UNIQUE",
            "CREATE CONSTRAINT trial_id IF NOT EXISTS FOR (t:ClinicalTrial) REQUIRE t.trialId IS UNIQUE",
            "CREATE CONSTRAINT gene_id IF NOT EXISTS FOR (g:Gene) REQUIRE g.geneId IS UNIQUE",
            "CREATE CONSTRAINT protein_id IF NOT EXISTS FOR (p:Protein) REQUIRE p.proteinId IS UNIQUE",
            "CREATE CONSTRAINT biomarker_id IF NOT EXISTS FOR (b:Biomarker) REQUIRE b.biomarkerId IS UNIQUE",
            "CREATE CONSTRAINT researcher_id IF NOT EXISTS FOR (r:Researcher) REQUIRE r.researcherId IS UNIQUE",
            "CREATE CONSTRAINT institution_id IF NOT EXISTS FOR (i:Institution) REQUIRE i.institutionId IS UNIQUE",
            "CREATE CONSTRAINT paper_id IF NOT EXISTS FOR (p:ResearchPaper) REQUIRE p.paperId IS UNIQUE",
            "CREATE CONSTRAINT event_id IF NOT EXISTS FOR (e:AdverseEvent) REQUIRE e.eventId IS UNIQUE"
        ]

        with self.driver.session(database=self.database) as session:
            for constraint in constraints:
                try:
                    session.run(constraint)
                except Exception as e:
                    # Constraint might already exist
                    pass

        print("✓ Constraints created")

    def load_drugs(self, filepath):
        """Load drugs from CSV"""
        if not os.path.exists(filepath):
            return

        print(f"\nLoading drugs...")

        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            drugs = list(reader)

        query = """
        UNWIND $drugs AS drug
        CREATE (d:Drug {
            drugId: drug.drug_id,
            name: drug.name,
            genericName: drug.generic_name,
            drugType: drug.drug_type,
            approvalStatus: drug.approval_status,
            approvalYear: toInteger(drug.approval_year),
            mechanism: drug.mechanism
        })
        """

        with self.driver.session(database=self.database) as session:
            result = session.run(query, drugs=drugs)
            print(f"  ✓ Created {len(drugs)} drug nodes")

    def load_diseases(self, filepath):
        """Load diseases from CSV"""
        if not os.path.exists(filepath):
            return

        print(f"\nLoading diseases...")

        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            diseases = list(reader)

        query = """
        UNWIND $diseases AS disease
        CREATE (d:Disease {
            diseaseId: disease.disease_id,
            name: disease.name,
            category: disease.category,
            icd10Code: disease.icd10_code,
            prevalence: disease.prevalence
        })
        """

        with self.driver.session(database=self.database) as session:
            result = session.run(query, diseases=diseases)
            print(f"  ✓ Created {len(diseases)} disease nodes")

    def load_clinical_trials(self, filepath):
        """Load clinical trials from CSV"""
        if not os.path.exists(filepath):
            return

        print(f"\nLoading clinical trials...")

        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            trials = list(reader)

        query = """
        UNWIND $trials AS trial
        CREATE (t:ClinicalTrial {
            trialId: trial.trial_id,
            nctId: trial.nct_id,
            title: trial.title,
            phase: trial.phase,
            status: trial.status,
            startDate: date(trial.start_date),
            enrollment: toInteger(trial.enrollment),
            sponsor: trial.sponsor
        })
        """

        with self.driver.session(database=self.database) as session:
            result = session.run(query, trials=trials)
            print(f"  ✓ Created {len(trials)} clinical trial nodes")

    def load_genes(self, filepath):
        """Load genes from CSV"""
        if not os.path.exists(filepath):
            return

        print(f"\nLoading genes...")

        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            genes = list(reader)

        query = """
        UNWIND $genes AS gene
        CREATE (g:Gene {
            geneId: gene.gene_id,
            symbol: gene.symbol,
            name: gene.name,
            chromosome: gene.chromosome,
            function: gene.function
        })
        """

        with self.driver.session(database=self.database) as session:
            result = session.run(query, genes=genes)
            print(f"  ✓ Created {len(genes)} gene nodes")

    def load_proteins(self, filepath):
        """Load proteins from CSV"""
        if not os.path.exists(filepath):
            return

        print(f"\nLoading proteins...")

        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            proteins = list(reader)

        query = """
        UNWIND $proteins AS protein
        CREATE (p:Protein {
            proteinId: protein.protein_id,
            name: protein.name,
            uniprotId: protein.uniprot_id,
            proteinClass: protein.protein_class,
            cellularLocation: protein.cellular_location
        })
        """

        with self.driver.session(database=self.database) as session:
            result = session.run(query, proteins=proteins)
            print(f"  ✓ Created {len(proteins)} protein nodes")

    def load_biomarkers(self, filepath):
        """Load biomarkers from CSV"""
        if not os.path.exists(filepath):
            return

        print(f"\nLoading biomarkers...")

        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            biomarkers = list(reader)

        query = """
        UNWIND $biomarkers AS biomarker
        CREATE (b:Biomarker {
            biomarkerId: biomarker.biomarker_id,
            name: biomarker.name,
            type: biomarker.type,
            measurementUnit: biomarker.measurement_unit,
            clinicalSignificance: biomarker.clinical_significance
        })
        """

        with self.driver.session(database=self.database) as session:
            result = session.run(query, biomarkers=biomarkers)
            print(f"  ✓ Created {len(biomarkers)} biomarker nodes")

    def load_researchers(self, filepath):
        """Load researchers from CSV"""
        if not os.path.exists(filepath):
            return

        print(f"\nLoading researchers...")

        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            researchers = list(reader)

        query = """
        UNWIND $researchers AS researcher
        CREATE (r:Researcher {
            researcherId: researcher.researcher_id,
            name: researcher.name,
            title: researcher.title,
            specialization: researcher.specialization,
            hIndex: toInteger(researcher.h_index),
            totalPublications: toInteger(researcher.total_publications)
        })
        """

        with self.driver.session(database=self.database) as session:
            result = session.run(query, researchers=researchers)
            print(f"  ✓ Created {len(researchers)} researcher nodes")

    def load_institutions(self, filepath):
        """Load institutions from CSV"""
        if not os.path.exists(filepath):
            return

        print(f"\nLoading institutions...")

        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            institutions = list(reader)

        query = """
        UNWIND $institutions AS institution
        CREATE (i:Institution {
            institutionId: institution.institution_id,
            name: institution.name
        })
        """

        with self.driver.session(database=self.database) as session:
            result = session.run(query, institutions=institutions)
            print(f"  ✓ Created {len(institutions)} institution nodes")

    def load_research_papers(self, filepath):
        """Load research papers from CSV"""
        if not os.path.exists(filepath):
            return

        print(f"\nLoading research papers...")

        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            papers = list(reader)

        query = """
        UNWIND $papers AS paper
        CREATE (p:ResearchPaper {
            paperId: paper.paper_id,
            title: paper.title,
            journal: paper.journal,
            year: toInteger(paper.year),
            doi: paper.doi
        })
        """

        with self.driver.session(database=self.database) as session:
            result = session.run(query, papers=papers)
            print(f"  ✓ Created {len(papers)} research paper nodes")

    def load_adverse_events(self, filepath):
        """Load adverse events from CSV"""
        if not os.path.exists(filepath):
            return

        print(f"\nLoading adverse events...")

        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            events = list(reader)

        query = """
        UNWIND $events AS event
        CREATE (e:AdverseEvent {
            eventId: event.event_id,
            name: event.name,
            severity: event.severity,
            category: event.category,
            frequency: event.frequency
        })
        """

        with self.driver.session(database=self.database) as session:
            result = session.run(query, events=events)
            print(f"  ✓ Created {len(events)} adverse event nodes")

    def load_relationships(self, data_dir):
        """Load all relationships"""
        print("\n" + "=" * 80)
        print("Loading relationships...")
        print("=" * 80)

        rel_dir = f"{data_dir}/relationships"

        # Drug treats disease
        self.load_drug_treats_disease(f"{rel_dir}/drug_treats_disease.csv")

        # Drug targets protein
        self.load_drug_targets_protein(f"{rel_dir}/drug_targets_protein.csv")

        # Gene associated with disease
        self.load_gene_disease(f"{rel_dir}/gene_associated_with_disease.csv")

        # Trial relationships
        self.load_trial_drug(f"{rel_dir}/trial_investigates_drug.csv")
        self.load_trial_disease(f"{rel_dir}/trial_studies_disease.csv")
        self.load_trial_adverse_event(f"{rel_dir}/trial_reports_adverse_event.csv")

        # Biomarker relationships
        self.load_biomarker_drug(f"{rel_dir}/biomarker_predicts_response.csv")

        # Research relationships
        self.load_paper_author(f"{rel_dir}/paper_authored_by.csv")
        self.load_researcher_institution(f"{rel_dir}/researcher_affiliated_with.csv")
        self.load_institution_trial(f"{rel_dir}/institution_sponsors_trial.csv")
        self.load_paper_drug(f"{rel_dir}/paper_mentions_drug.csv")
        self.load_paper_disease(f"{rel_dir}/paper_mentions_disease.csv")

    def load_drug_treats_disease(self, filepath):
        """Create TREATS relationships"""
        if not os.path.exists(filepath):
            return

        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            rels = list(reader)

        query = """
        UNWIND $rels AS rel
        MATCH (d:Drug {drugId: rel.drug_id})
        MATCH (dis:Disease {diseaseId: rel.disease_id})
        CREATE (d)-[r:TREATS {
            efficacyRate: toFloat(rel.efficacy_rate),
            approvalYear: toInteger(rel.approval_year)
        }]->(dis)
        """

        with self.driver.session(database=self.database) as session:
            session.run(query, rels=rels)
            print(f"  ✓ Created {len(rels)} TREATS relationships")

    def load_drug_targets_protein(self, filepath):
        """Create TARGETS relationships"""
        if not os.path.exists(filepath):
            return

        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            rels = list(reader)

        query = """
        UNWIND $rels AS rel
        MATCH (d:Drug {drugId: rel.drug_id})
        MATCH (p:Protein {proteinId: rel.protein_id})
        CREATE (d)-[r:TARGETS {
            bindingAffinity: rel.binding_affinity,
            mechanismType: rel.mechanism_type
        }]->(p)
        """

        with self.driver.session(database=self.database) as session:
            session.run(query, rels=rels)
            print(f"  ✓ Created {len(rels)} TARGETS relationships")

    def load_gene_disease(self, filepath):
        """Create ASSOCIATED_WITH relationships"""
        if not os.path.exists(filepath):
            return

        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            rels = list(reader)

        query = """
        UNWIND $rels AS rel
        MATCH (g:Gene {geneId: rel.gene_id})
        MATCH (d:Disease {diseaseId: rel.disease_id})
        CREATE (g)-[r:ASSOCIATED_WITH {
            associationStrength: rel.association_strength,
            evidenceLevel: rel.evidence_level
        }]->(d)
        """

        with self.driver.session(database=self.database) as session:
            session.run(query, rels=rels)
            print(f"  ✓ Created {len(rels)} ASSOCIATED_WITH relationships")

    def load_trial_drug(self, filepath):
        """Create INVESTIGATES relationships"""
        if not os.path.exists(filepath):
            return

        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            rels = list(reader)

        query = """
        UNWIND $rels AS rel
        MATCH (t:ClinicalTrial {trialId: rel.trial_id})
        MATCH (d:Drug {drugId: rel.drug_id})
        CREATE (t)-[r:INVESTIGATES]->(d)
        """

        with self.driver.session(database=self.database) as session:
            session.run(query, rels=rels)
            print(f"  ✓ Created {len(rels)} INVESTIGATES relationships")

    def load_trial_disease(self, filepath):
        """Create STUDIES relationships"""
        if not os.path.exists(filepath):
            return

        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            rels = list(reader)

        query = """
        UNWIND $rels AS rel
        MATCH (t:ClinicalTrial {trialId: rel.trial_id})
        MATCH (d:Disease {diseaseId: rel.disease_id})
        CREATE (t)-[r:STUDIES]->(d)
        """

        with self.driver.session(database=self.database) as session:
            session.run(query, rels=rels)
            print(f"  ✓ Created {len(rels)} STUDIES relationships")

    def load_trial_adverse_event(self, filepath):
        """Create REPORTS relationships"""
        if not os.path.exists(filepath):
            return

        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            rels = list(reader)

        query = """
        UNWIND $rels AS rel
        MATCH (t:ClinicalTrial {trialId: rel.trial_id})
        MATCH (e:AdverseEvent {eventId: rel.event_id})
        CREATE (t)-[r:REPORTS]->(e)
        """

        with self.driver.session(database=self.database) as session:
            session.run(query, rels=rels)
            print(f"  ✓ Created {len(rels)} REPORTS relationships")

    def load_biomarker_drug(self, filepath):
        """Create PREDICTS_RESPONSE relationships"""
        if not os.path.exists(filepath):
            return

        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            rels = list(reader)

        query = """
        UNWIND $rels AS rel
        MATCH (b:Biomarker {biomarkerId: rel.biomarker_id})
        MATCH (d:Drug {drugId: rel.drug_id})
        CREATE (b)-[r:PREDICTS_RESPONSE]->(d)
        """

        with self.driver.session(database=self.database) as session:
            session.run(query, rels=rels)
            print(f"  ✓ Created {len(rels)} PREDICTS_RESPONSE relationships")

    def load_paper_author(self, filepath):
        """Create AUTHORED_BY relationships"""
        if not os.path.exists(filepath):
            return

        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            rels = list(reader)

        query = """
        UNWIND $rels AS rel
        MATCH (p:ResearchPaper {paperId: rel.paper_id})
        MATCH (r:Researcher {researcherId: rel.researcher_id})
        CREATE (p)-[rel:AUTHORED_BY]->(r)
        """

        with self.driver.session(database=self.database) as session:
            session.run(query, rels=rels)
            print(f"  ✓ Created {len(rels)} AUTHORED_BY relationships")

    def load_researcher_institution(self, filepath):
        """Create AFFILIATED_WITH relationships"""
        if not os.path.exists(filepath):
            return

        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            rels = list(reader)

        query = """
        UNWIND $rels AS rel
        MATCH (r:Researcher {researcherId: rel.researcher_id})
        MATCH (i:Institution {institutionId: rel.institution_id})
        CREATE (r)-[rel:AFFILIATED_WITH]->(i)
        """

        with self.driver.session(database=self.database) as session:
            session.run(query, rels=rels)
            print(f"  ✓ Created {len(rels)} AFFILIATED_WITH relationships")

    def load_institution_trial(self, filepath):
        """Create SPONSORS relationships"""
        if not os.path.exists(filepath):
            return

        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            rels = list(reader)

        query = """
        UNWIND $rels AS rel
        MATCH (i:Institution {institutionId: rel.institution_id})
        MATCH (t:ClinicalTrial {trialId: rel.trial_id})
        CREATE (i)-[r:SPONSORS]->(t)
        """

        with self.driver.session(database=self.database) as session:
            session.run(query, rels=rels)
            print(f"  ✓ Created {len(rels)} SPONSORS relationships")

    def load_paper_drug(self, filepath):
        """Create MENTIONS_DRUG relationships"""
        if not os.path.exists(filepath):
            return

        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            rels = list(reader)

        query = """
        UNWIND $rels AS rel
        MATCH (p:ResearchPaper {paperId: rel.paper_id})
        MATCH (d:Drug {drugId: rel.drug_id})
        CREATE (p)-[r:MENTIONS_DRUG]->(d)
        """

        with self.driver.session(database=self.database) as session:
            session.run(query, rels=rels)
            print(f"  ✓ Created {len(rels)} MENTIONS_DRUG relationships")

    def load_paper_disease(self, filepath):
        """Create MENTIONS_DISEASE relationships"""
        if not os.path.exists(filepath):
            return

        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            rels = list(reader)

        query = """
        UNWIND $rels AS rel
        MATCH (p:ResearchPaper {paperId: rel.paper_id})
        MATCH (d:Disease {diseaseId: rel.disease_id})
        CREATE (p)-[r:MENTIONS_DISEASE]->(d)
        """

        with self.driver.session(database=self.database) as session:
            session.run(query, rels=rels)
            print(f"  ✓ Created {len(rels)} MENTIONS_DISEASE relationships")

    def get_statistics(self):
        """Get graph statistics"""
        print("\n" + "=" * 80)
        print("GRAPH STATISTICS")
        print("=" * 80)

        queries = {
            "Drug": "MATCH (n:Drug) RETURN count(n) as count",
            "Disease": "MATCH (n:Disease) RETURN count(n) as count",
            "ClinicalTrial": "MATCH (n:ClinicalTrial) RETURN count(n) as count",
            "Gene": "MATCH (n:Gene) RETURN count(n) as count",
            "Protein": "MATCH (n:Protein) RETURN count(n) as count",
            "Biomarker": "MATCH (n:Biomarker) RETURN count(n) as count",
            "Researcher": "MATCH (n:Researcher) RETURN count(n) as count",
            "Institution": "MATCH (n:Institution) RETURN count(n) as count",
            "ResearchPaper": "MATCH (n:ResearchPaper) RETURN count(n) as count",
            "AdverseEvent": "MATCH (n:AdverseEvent) RETURN count(n) as count",
        }

        print("\nNode Counts:")
        print("-" * 40)

        with self.driver.session(database=self.database) as session:
            for label, query in queries.items():
                result = session.run(query)
                count = result.single()["count"]
                print(f"  {label:20} : {count:5}")

        # Count relationships
        rel_query = "MATCH ()-[r]->() RETURN count(r) as count"
        with self.driver.session(database=self.database) as session:
            result = session.run(rel_query)
            rel_count = result.single()["count"]
            print(f"\n  Total Relationships : {rel_count:5}")


def main():
    """Main execution"""

    loader = BiomedicalNeo4jLoader()

    try:
        # Clear existing data (optional - comment out to append)
        # loader.clear_database()

        # Create constraints
        loader.create_constraints()

        # Load entities
        print("\n" + "=" * 80)
        print("Loading entities...")
        print("=" * 80)

        data_dir = "data/sample"
        loader.load_drugs(f"{data_dir}/drugs.csv")
        loader.load_diseases(f"{data_dir}/diseases.csv")
        loader.load_clinical_trials(f"{data_dir}/clinical_trials.csv")
        loader.load_genes(f"{data_dir}/genes.csv")
        loader.load_proteins(f"{data_dir}/proteins.csv")
        loader.load_biomarkers(f"{data_dir}/biomarkers.csv")
        loader.load_researchers(f"{data_dir}/researchers.csv")
        loader.load_institutions(f"{data_dir}/institutions.csv")
        loader.load_research_papers(f"{data_dir}/research_papers.csv")
        loader.load_adverse_events(f"{data_dir}/adverse_events.csv")

        # Load relationships
        loader.load_relationships(data_dir)

        # Show statistics
        loader.get_statistics()

        print("\n" + "=" * 80)
        print("SUCCESS! Biomedical knowledge graph loaded into Neo4j Aura")
        print("=" * 80)
        print(f"\nYou can now query the graph at: {loader.uri}")
        print("\nExample Cypher queries:")
        print("  MATCH (d:Drug)-[r:TREATS]->(dis:Disease) RETURN d, r, dis LIMIT 10")
        print("  MATCH (d:Drug)-[:TARGETS]->(p:Protein) RETURN d.name, p.name")

    finally:
        loader.close()


if __name__ == "__main__":
    main()
