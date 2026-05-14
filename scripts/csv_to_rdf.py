#!/usr/bin/env python3
"""
CSV to RDF Converter for Biomedical Knowledge Graph
Transforms CSV data into RDF triples following the W3C semantic stack
"""

import csv
import os
from rdflib import Graph, Namespace, RDF, RDFS, OWL, XSD, Literal, URIRef
from datetime import datetime


class BiomedicalRDFConverter:
    """Converts biomedical CSV data to RDF triples"""

    def __init__(self):
        self.graph = Graph()

        # Define namespaces
        self.BIO = Namespace("http://example.com/biomedical#")
        self.DATA = Namespace("http://example.com/data/")

        # Bind prefixes for readable output
        self.graph.bind("bio", self.BIO)
        self.graph.bind("data", self.DATA)
        self.graph.bind("rdf", RDF)
        self.graph.bind("rdfs", RDFS)
        self.graph.bind("owl", OWL)
        self.graph.bind("xsd", XSD)

    def add_drug(self, row):
        """Convert drug CSV row to RDF triples"""
        drug_uri = self.DATA[f"drug/{row['drug_id']}"]

        # Type assertion
        self.graph.add((drug_uri, RDF.type, self.BIO.Drug))

        # Determine drug subclass
        drug_type = row['drug_type']
        if drug_type == "Monoclonal Antibody":
            self.graph.add((drug_uri, RDF.type, self.BIO.MonoclonalAntibody))
        elif drug_type == "Small Molecule":
            self.graph.add((drug_uri, RDF.type, self.BIO.SmallMolecule))
        elif drug_type == "Peptide":
            self.graph.add((drug_uri, RDF.type, self.BIO.Peptide))

        # Data properties
        self.graph.add((drug_uri, self.BIO.drugId, Literal(row['drug_id'])))
        self.graph.add((drug_uri, self.BIO.drugName, Literal(row['name'])))
        self.graph.add((drug_uri, self.BIO.genericName, Literal(row['generic_name'])))
        self.graph.add((drug_uri, self.BIO.drugType, Literal(row['drug_type'])))
        self.graph.add((drug_uri, self.BIO.approvalStatus, Literal(row['approval_status'])))
        self.graph.add((drug_uri, self.BIO.approvalYear, Literal(row['approval_year'], datatype=XSD.gYear)))
        self.graph.add((drug_uri, self.BIO.mechanism, Literal(row['mechanism'])))
        self.graph.add((drug_uri, RDFS.label, Literal(row['name'])))

        return drug_uri

    def add_disease(self, row):
        """Convert disease CSV row to RDF triples"""
        disease_uri = self.DATA[f"disease/{row['disease_id']}"]

        # Type assertion
        self.graph.add((disease_uri, RDF.type, self.BIO.Disease))

        # Determine disease subclass
        category = row['category']
        if category == "Oncology":
            self.graph.add((disease_uri, RDF.type, self.BIO.OncologyDisease))
        elif category == "Metabolic":
            self.graph.add((disease_uri, RDF.type, self.BIO.MetabolicDisease))
        elif category == "Neurology":
            self.graph.add((disease_uri, RDF.type, self.BIO.NeurologicalDisease))

        # Data properties
        self.graph.add((disease_uri, self.BIO.diseaseId, Literal(row['disease_id'])))
        self.graph.add((disease_uri, self.BIO.diseaseName, Literal(row['name'])))
        self.graph.add((disease_uri, self.BIO.diseaseCategory, Literal(row['category'])))
        self.graph.add((disease_uri, self.BIO.icd10Code, Literal(row['icd10_code'])))
        self.graph.add((disease_uri, self.BIO.prevalence, Literal(row['prevalence'])))
        self.graph.add((disease_uri, RDFS.label, Literal(row['name'])))

        return disease_uri

    def add_clinical_trial(self, row):
        """Convert clinical trial CSV row to RDF triples"""
        trial_uri = self.DATA[f"trial/{row['trial_id']}"]

        # Type assertion
        self.graph.add((trial_uri, RDF.type, self.BIO.ClinicalTrial))

        # Data properties
        self.graph.add((trial_uri, self.BIO.trialId, Literal(row['trial_id'])))
        self.graph.add((trial_uri, self.BIO.nctId, Literal(row['nct_id'])))
        self.graph.add((trial_uri, self.BIO.trialTitle, Literal(row['title'])))
        self.graph.add((trial_uri, self.BIO.phase, Literal(row['phase'])))
        self.graph.add((trial_uri, self.BIO.trialStatus, Literal(row['status'])))
        self.graph.add((trial_uri, self.BIO.startDate, Literal(row['start_date'], datatype=XSD.date)))
        self.graph.add((trial_uri, self.BIO.enrollment, Literal(int(row['enrollment']), datatype=XSD.integer)))
        self.graph.add((trial_uri, self.BIO.sponsor, Literal(row['sponsor'])))
        self.graph.add((trial_uri, RDFS.label, Literal(row['title'])))

        return trial_uri

    def add_gene(self, row):
        """Convert gene CSV row to RDF triples"""
        gene_uri = self.DATA[f"gene/{row['gene_id']}"]

        # Type assertion
        self.graph.add((gene_uri, RDF.type, self.BIO.Gene))

        # Data properties
        self.graph.add((gene_uri, self.BIO.geneId, Literal(row['gene_id'])))
        self.graph.add((gene_uri, self.BIO.geneSymbol, Literal(row['symbol'])))
        self.graph.add((gene_uri, self.BIO.geneName, Literal(row['name'])))
        self.graph.add((gene_uri, self.BIO.chromosome, Literal(row['chromosome'])))
        self.graph.add((gene_uri, self.BIO.geneFunction, Literal(row['function'])))
        self.graph.add((gene_uri, RDFS.label, Literal(row['symbol'])))

        return gene_uri

    def add_protein(self, row):
        """Convert protein CSV row to RDF triples"""
        protein_uri = self.DATA[f"protein/{row['protein_id']}"]

        # Type assertion
        self.graph.add((protein_uri, RDF.type, self.BIO.Protein))

        # Special case: immune checkpoint proteins
        if row['protein_class'] == "Immune checkpoint":
            self.graph.add((protein_uri, RDF.type, self.BIO.ImmuneCheckpointProtein))

        # Data properties
        self.graph.add((protein_uri, self.BIO.proteinId, Literal(row['protein_id'])))
        self.graph.add((protein_uri, self.BIO.proteinName, Literal(row['name'])))
        self.graph.add((protein_uri, self.BIO.uniprotId, Literal(row['uniprot_id'])))
        self.graph.add((protein_uri, self.BIO.proteinClass, Literal(row['protein_class'])))
        self.graph.add((protein_uri, self.BIO.cellularLocation, Literal(row['cellular_location'])))
        self.graph.add((protein_uri, RDFS.label, Literal(row['name'])))

        return protein_uri

    def add_biomarker(self, row):
        """Convert biomarker CSV row to RDF triples"""
        biomarker_uri = self.DATA[f"biomarker/{row['biomarker_id']}"]

        # Type assertion
        self.graph.add((biomarker_uri, RDF.type, self.BIO.Biomarker))

        # Determine biomarker subclass
        bm_type = row['type']
        if bm_type == "Protein":
            self.graph.add((biomarker_uri, RDF.type, self.BIO.ProteinBiomarker))
        elif bm_type == "Genetic":
            self.graph.add((biomarker_uri, RDF.type, self.BIO.GeneticBiomarker))
        elif bm_type == "Metabolic":
            self.graph.add((biomarker_uri, RDF.type, self.BIO.MetabolicBiomarker))

        # Data properties
        self.graph.add((biomarker_uri, RDFS.label, Literal(row['name'])))

        return biomarker_uri

    def add_researcher(self, row):
        """Convert researcher CSV row to RDF triples"""
        researcher_uri = self.DATA[f"researcher/{row['researcher_id']}"]

        # Type assertion
        self.graph.add((researcher_uri, RDF.type, self.BIO.Researcher))

        # Data properties
        self.graph.add((researcher_uri, self.BIO.researcherId, Literal(row['researcher_id'])))
        self.graph.add((researcher_uri, self.BIO.researcherName, Literal(row['name'])))
        self.graph.add((researcher_uri, self.BIO.title, Literal(row['title'])))
        self.graph.add((researcher_uri, self.BIO.specialization, Literal(row['specialization'])))
        self.graph.add((researcher_uri, self.BIO.hIndex, Literal(int(row['h_index']), datatype=XSD.integer)))
        self.graph.add((researcher_uri, self.BIO.totalPublications, Literal(int(row['total_publications']), datatype=XSD.integer)))
        self.graph.add((researcher_uri, RDFS.label, Literal(row['name'])))

        return researcher_uri

    def add_institution(self, row):
        """Convert institution CSV row to RDF triples"""
        institution_uri = self.DATA[f"institution/{row['institution_id']}"]

        # Type assertion
        self.graph.add((institution_uri, RDF.type, self.BIO.Institution))
        self.graph.add((institution_uri, RDFS.label, Literal(row['name'])))

        return institution_uri

    def add_research_paper(self, row):
        """Convert research paper CSV row to RDF triples"""
        paper_uri = self.DATA[f"paper/{row['paper_id']}"]

        # Type assertion
        self.graph.add((paper_uri, RDF.type, self.BIO.ResearchPaper))
        self.graph.add((paper_uri, RDFS.label, Literal(row['title'])))

        return paper_uri

    def add_adverse_event(self, row):
        """Convert adverse event CSV row to RDF triples"""
        event_uri = self.DATA[f"adverse_event/{row['event_id']}"]

        # Type assertion
        self.graph.add((event_uri, RDF.type, self.BIO.AdverseEvent))
        self.graph.add((event_uri, RDFS.label, Literal(row['name'])))

        return event_uri

    def add_drug_treats_disease(self, row):
        """Add drug treats disease relationship"""
        drug_uri = self.DATA[f"drug/{row['drug_id']}"]
        disease_uri = self.DATA[f"disease/{row['disease_id']}"]

        # Object property
        self.graph.add((drug_uri, self.BIO.treats, disease_uri))

        # Reification for additional properties
        treatment_uri = self.DATA[f"treatment/{row['drug_id']}_{row['disease_id']}"]
        self.graph.add((treatment_uri, RDF.type, RDF.Statement))
        self.graph.add((treatment_uri, RDF.subject, drug_uri))
        self.graph.add((treatment_uri, RDF.predicate, self.BIO.treats))
        self.graph.add((treatment_uri, RDF.object, disease_uri))
        self.graph.add((treatment_uri, self.BIO.efficacyRate, Literal(float(row['efficacy_rate']), datatype=XSD.decimal)))
        self.graph.add((treatment_uri, self.BIO.approvalYear, Literal(row['approval_year'], datatype=XSD.gYear)))

    def add_drug_targets_protein(self, row):
        """Add drug targets protein relationship"""
        drug_uri = self.DATA[f"drug/{row['drug_id']}"]
        protein_uri = self.DATA[f"protein/{row['protein_id']}"]

        # Object property
        self.graph.add((drug_uri, self.BIO.targets, protein_uri))

        # Reification for additional properties
        targeting_uri = self.DATA[f"targeting/{row['drug_id']}_{row['protein_id']}"]
        self.graph.add((targeting_uri, RDF.type, RDF.Statement))
        self.graph.add((targeting_uri, RDF.subject, drug_uri))
        self.graph.add((targeting_uri, RDF.predicate, self.BIO.targets))
        self.graph.add((targeting_uri, RDF.object, protein_uri))
        self.graph.add((targeting_uri, self.BIO.bindingAffinity, Literal(row['binding_affinity'])))
        self.graph.add((targeting_uri, self.BIO.mechanismType, Literal(row['mechanism_type'])))

    def add_gene_associated_with_disease(self, row):
        """Add gene associated with disease relationship"""
        disease_uri = self.DATA[f"disease/{row['disease_id']}"]
        gene_uri = self.DATA[f"gene/{row['gene_id']}"]

        # Object property
        self.graph.add((disease_uri, self.BIO.associatedWithGene, gene_uri))

        # Reification for additional properties
        association_uri = self.DATA[f"gene_disease/{row['gene_id']}_{row['disease_id']}"]
        self.graph.add((association_uri, RDF.type, RDF.Statement))
        self.graph.add((association_uri, RDF.subject, disease_uri))
        self.graph.add((association_uri, RDF.predicate, self.BIO.associatedWithGene))
        self.graph.add((association_uri, RDF.object, gene_uri))
        self.graph.add((association_uri, self.BIO.associationStrength, Literal(row['association_strength'])))
        self.graph.add((association_uri, self.BIO.evidenceLevel, Literal(row['evidence_level'])))

    def add_trial_investigates_drug(self, row):
        """Add trial investigates drug relationship"""
        trial_uri = self.DATA[f"trial/{row['trial_id']}"]
        drug_uri = self.DATA[f"drug/{row['drug_id']}"]

        self.graph.add((trial_uri, self.BIO.investigatesDrug, drug_uri))

    def add_trial_studies_disease(self, row):
        """Add trial studies disease relationship"""
        trial_uri = self.DATA[f"trial/{row['trial_id']}"]
        disease_uri = self.DATA[f"disease/{row['disease_id']}"]

        self.graph.add((trial_uri, self.BIO.studiesDisease, disease_uri))

    def add_trial_reports_adverse_event(self, row):
        """Add trial reports adverse event relationship"""
        trial_uri = self.DATA[f"trial/{row['trial_id']}"]
        event_uri = self.DATA[f"adverse_event/{row['event_id']}"]

        self.graph.add((trial_uri, self.BIO.reportsAdverseEvent, event_uri))

    def add_biomarker_predicts_response(self, row):
        """Add biomarker predicts response relationship"""
        biomarker_uri = self.DATA[f"biomarker/{row['biomarker_id']}"]
        drug_uri = self.DATA[f"drug/{row['drug_id']}"]

        self.graph.add((biomarker_uri, self.BIO.predictsResponseTo, drug_uri))

    def add_paper_authored_by(self, row):
        """Add paper authored by researcher relationship"""
        paper_uri = self.DATA[f"paper/{row['paper_id']}"]
        researcher_uri = self.DATA[f"researcher/{row['researcher_id']}"]

        self.graph.add((paper_uri, self.BIO.authoredBy, researcher_uri))

    def add_researcher_affiliated_with(self, row):
        """Add researcher affiliated with institution relationship"""
        researcher_uri = self.DATA[f"researcher/{row['researcher_id']}"]
        institution_uri = self.DATA[f"institution/{row['institution_id']}"]

        self.graph.add((researcher_uri, self.BIO.affiliatedWith, institution_uri))

    def add_institution_sponsors_trial(self, row):
        """Add institution sponsors trial relationship"""
        institution_uri = self.DATA[f"institution/{row['institution_id']}"]
        trial_uri = self.DATA[f"trial/{row['trial_id']}"]

        self.graph.add((institution_uri, self.BIO.sponsoredBy, trial_uri))

    def add_paper_mentions_drug(self, row):
        """Add paper mentions drug relationship"""
        paper_uri = self.DATA[f"paper/{row['paper_id']}"]
        drug_uri = self.DATA[f"drug/{row['drug_id']}"]

        self.graph.add((paper_uri, self.BIO.mentionsDrug, drug_uri))

    def add_paper_mentions_disease(self, row):
        """Add paper mentions disease relationship"""
        paper_uri = self.DATA[f"paper/{row['paper_id']}"]
        disease_uri = self.DATA[f"disease/{row['disease_id']}"]

        self.graph.add((paper_uri, self.BIO.mentionsDisease, disease_uri))

    def load_csv(self, filepath, processor_func):
        """Load CSV and process each row with given function"""
        if not os.path.exists(filepath):
            print(f"Warning: {filepath} not found, skipping...")
            return

        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                processor_func(row)
        print(f"Loaded: {filepath}")

    def convert_all(self, data_dir):
        """Convert all CSV files to RDF"""
        print("Converting CSV data to RDF triples...")
        print("=" * 60)

        # Load entities
        self.load_csv(f"{data_dir}/drugs.csv", self.add_drug)
        self.load_csv(f"{data_dir}/diseases.csv", self.add_disease)
        self.load_csv(f"{data_dir}/clinical_trials.csv", self.add_clinical_trial)
        self.load_csv(f"{data_dir}/genes.csv", self.add_gene)
        self.load_csv(f"{data_dir}/proteins.csv", self.add_protein)
        self.load_csv(f"{data_dir}/biomarkers.csv", self.add_biomarker)
        self.load_csv(f"{data_dir}/researchers.csv", self.add_researcher)
        self.load_csv(f"{data_dir}/institutions.csv", self.add_institution)
        self.load_csv(f"{data_dir}/research_papers.csv", self.add_research_paper)
        self.load_csv(f"{data_dir}/adverse_events.csv", self.add_adverse_event)

        print("\nConverting relationships...")
        print("-" * 60)

        # Load relationships
        rel_dir = f"{data_dir}/relationships"
        self.load_csv(f"{rel_dir}/drug_treats_disease.csv", self.add_drug_treats_disease)
        self.load_csv(f"{rel_dir}/drug_targets_protein.csv", self.add_drug_targets_protein)
        self.load_csv(f"{rel_dir}/gene_associated_with_disease.csv", self.add_gene_associated_with_disease)
        self.load_csv(f"{rel_dir}/trial_investigates_drug.csv", self.add_trial_investigates_drug)
        self.load_csv(f"{rel_dir}/trial_studies_disease.csv", self.add_trial_studies_disease)
        self.load_csv(f"{rel_dir}/trial_reports_adverse_event.csv", self.add_trial_reports_adverse_event)
        self.load_csv(f"{rel_dir}/biomarker_predicts_response.csv", self.add_biomarker_predicts_response)
        self.load_csv(f"{rel_dir}/paper_authored_by.csv", self.add_paper_authored_by)
        self.load_csv(f"{rel_dir}/researcher_affiliated_with.csv", self.add_researcher_affiliated_with)
        self.load_csv(f"{rel_dir}/institution_sponsors_trial.csv", self.add_institution_sponsors_trial)
        self.load_csv(f"{rel_dir}/paper_mentions_drug.csv", self.add_paper_mentions_drug)
        self.load_csv(f"{rel_dir}/paper_mentions_disease.csv", self.add_paper_mentions_disease)

        print("=" * 60)
        print(f"Conversion complete! Total triples: {len(self.graph)}")

    def save(self, output_file, format='turtle'):
        """Save RDF graph to file"""
        self.graph.serialize(destination=output_file, format=format)
        print(f"\nRDF data saved to: {output_file}")
        print(f"Format: {format}")


def main():
    """Main conversion function"""
    converter = BiomedicalRDFConverter()

    # Convert all data
    data_directory = "data/sample"
    converter.convert_all(data_directory)

    # Save as Turtle (most readable)
    converter.save("output/biomedical_data.ttl", format='turtle')

    # Also save as RDF/XML (more widely supported)
    converter.save("output/biomedical_data.rdf", format='xml')

    # Also save as N-Triples (simplest format)
    converter.save("output/biomedical_data.nt", format='nt')

    print("\n" + "=" * 60)
    print("SUCCESS: RDF knowledge graph created!")
    print("=" * 60)


if __name__ == "__main__":
    main()
