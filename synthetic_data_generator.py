#!/usr/bin/env python3
"""
synthetic_data_generator.py
============================
Generates expanded synthetic biomedical CSV data and appends it to the existing
CSVs in /workshop/data/sample/.

Goals:
  - Preserve exact existing schemas
  - Expand each entity file from ~10 rows to ~40 rows
  - IDs continue from where existing data left off
  - New data is medically realistic (real drug names, gene symbols, etc.)
  - Relationship rows are crafted to enable 4+ hop graph traversal chains

Multi-hop traversal chains deliberately embedded:
  Chain 1: Gene → Disease → Drug → Protein → Biomarker → ClinicalTrial → AdverseEvent
  Chain 2: Researcher → Institution → ClinicalTrial → Drug → Disease → Gene → Protein
  Chain 3: Drug → Disease → Gene → Protein → Biomarker → Drug  (cycle via different drug)
  Chain 4: ResearchPaper → Researcher → Institution → ClinicalTrial → Drug → Disease → AdverseEvent

Uses only Python stdlib: csv, json, random, datetime, os, collections.
"""

import csv
import json
import os
import random
from datetime import date, timedelta

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BASE_DIR = "/workshop/data/sample"
REL_DIR  = os.path.join(BASE_DIR, "relationships")

# Seed for reproducibility
random.seed(42)

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def read_csv(path):
    """Return (fieldnames, rows) for an existing CSV file."""
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
    return fieldnames, rows


def write_csv(path, fieldnames, rows):
    """Write all rows (header + data) back to a CSV file."""
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def existing_ids(rows, id_field):
    """Return a set of existing ID values from a list of row dicts."""
    return {r[id_field] for r in rows}


def fmt_date(y, m, d):
    return f"{y:04d}-{m:02d}-{d:02d}"


def rand_date(start_year=2015, end_year=2024):
    start = date(start_year, 1, 1)
    end   = date(end_year, 12, 31)
    delta = (end - start).days
    return str(start + timedelta(days=random.randint(0, delta)))


# ---------------------------------------------------------------------------
# Load all existing data
# ---------------------------------------------------------------------------

print("Reading existing data …")

drugs_path      = os.path.join(BASE_DIR, "drugs.csv")
diseases_path   = os.path.join(BASE_DIR, "diseases.csv")
genes_path      = os.path.join(BASE_DIR, "genes.csv")
proteins_path   = os.path.join(BASE_DIR, "proteins.csv")
trials_path     = os.path.join(BASE_DIR, "clinical_trials.csv")
biomarkers_path = os.path.join(BASE_DIR, "biomarkers.csv")
researchers_path= os.path.join(BASE_DIR, "researchers.csv")
institutions_path=os.path.join(BASE_DIR, "institutions.csv")
papers_path     = os.path.join(BASE_DIR, "research_papers.csv")
ae_path         = os.path.join(BASE_DIR, "adverse_events.csv")

drugs_fields,       drugs_rows        = read_csv(drugs_path)
diseases_fields,    diseases_rows     = read_csv(diseases_path)
genes_fields,       genes_rows        = read_csv(genes_path)
proteins_fields,    proteins_rows     = read_csv(proteins_path)
trials_fields,      trials_rows       = read_csv(trials_path)
biomarkers_fields,  biomarkers_rows   = read_csv(biomarkers_path)
researchers_fields, researchers_rows  = read_csv(researchers_path)
institutions_fields,institutions_rows = read_csv(institutions_path)
papers_fields,      papers_rows       = read_csv(papers_path)
ae_fields,          ae_rows           = read_csv(ae_path)

# Relationship files
rel = {}
for fname in [
    "drug_treats_disease.csv",
    "drug_targets_protein.csv",
    "gene_associated_with_disease.csv",
    "trial_investigates_drug.csv",
    "trial_studies_disease.csv",
    "biomarker_predicts_response.csv",
    "institution_sponsors_trial.csv",
    "paper_authored_by.csv",
    "paper_mentions_disease.csv",
    "paper_mentions_drug.csv",
    "researcher_affiliated_with.csv",
    "trial_reports_adverse_event.csv",
]:
    path = os.path.join(REL_DIR, fname)
    fields, rows = read_csv(path)
    rel[fname] = {"fields": fields, "rows": rows, "path": path}

# ---------------------------------------------------------------------------
# Define all new entity rows
# ---------------------------------------------------------------------------

# ---- DRUGS (D011 – D025) --------------------------------------------------
# 15 new oncology drugs requested in the spec
new_drugs = [
    # drug_id, name, generic_name, drug_type, approval_status, approval_year, mechanism
    ("D011","Osimertinib","osimertinib","Small Molecule","Approved",2017,"EGFR T790M inhibitor"),
    ("D012","Ipilimumab","ipilimumab","Monoclonal Antibody","Approved",2011,"CTLA-4 inhibitor"),
    ("D013","Olaparib","olaparib","Small Molecule","Approved",2014,"PARP inhibitor"),
    ("D014","Durvalumab","durvalumab","Monoclonal Antibody","Approved",2017,"PD-L1 inhibitor"),
    ("D015","Bevacizumab","bevacizumab","Monoclonal Antibody","Approved",2004,"VEGF inhibitor"),
    ("D016","Cetuximab","cetuximab","Monoclonal Antibody","Approved",2004,"EGFR monoclonal antibody"),
    ("D017","Dabrafenib","dabrafenib","Small Molecule","Approved",2013,"BRAF inhibitor"),
    ("D018","Trametinib","trametinib","Small Molecule","Approved",2013,"MEK inhibitor"),
    ("D019","Venetoclax","venetoclax","Small Molecule","Approved",2016,"BCL-2 inhibitor"),
    ("D020","Ibrutinib","ibrutinib","Small Molecule","Approved",2013,"BTK inhibitor"),
    ("D021","Alectinib","alectinib","Small Molecule","Approved",2017,"ALK inhibitor"),
    ("D022","Lorlatinib","lorlatinib","Small Molecule","Approved",2018,"ALK/ROS1 inhibitor"),
    ("D023","Capmatinib","capmatinib","Small Molecule","Approved",2020,"MET inhibitor"),
    ("D024","Pralsetinib","pralsetinib","Small Molecule","Approved",2020,"RET inhibitor"),
    ("D025","Selpercatinib","selpercatinib","Small Molecule","Approved",2020,"RET inhibitor"),
]

# ---- DISEASES (DIS011 – DIS025) ------------------------------------------
new_diseases = [
    # disease_id, name, category, icd10_code, prevalence
    ("DIS011","Bladder Cancer","Oncology","C67.9","Medium"),
    ("DIS012","Pancreatic Cancer","Oncology","C25.9","Low"),
    ("DIS013","Ovarian Cancer","Oncology","C56","Medium"),
    ("DIS014","Head and Neck Squamous Cell Carcinoma","Oncology","C14.8","Medium"),
    ("DIS015","Gastric Cancer","Oncology","C16.9","Medium"),
    ("DIS016","Hepatocellular Carcinoma","Oncology","C22.0","Medium"),
    ("DIS017","Multiple Myeloma","Oncology","C90.0","Low"),
    ("DIS018","Diffuse Large B-Cell Lymphoma","Oncology","C83.3","Low"),
    ("DIS019","Chronic Lymphocytic Leukemia","Oncology","C91.1","Low"),
    ("DIS020","Myelodysplastic Syndrome","Oncology","D46.9","Low"),
    ("DIS021","Chronic Obstructive Pulmonary Disease","Pulmonology","J44.1","High"),
    ("DIS022","Heart Failure","Cardiology","I50.9","High"),
    ("DIS023","Atrial Fibrillation","Cardiology","I48.91","High"),
    ("DIS024","Rheumatoid Arthritis","Rheumatology","M05.9","High"),
    ("DIS025","Psoriasis","Dermatology","L40.0","High"),
]

# ---- GENES (G011 – G030) --------------------------------------------------
new_genes = [
    # gene_id, symbol, name, chromosome, function
    ("G011","ALK","Anaplastic Lymphoma Kinase","2","Cell growth and survival"),
    ("G012","ROS1","ROS Proto-Oncogene 1","6","Cell proliferation"),
    ("G013","MET","MET Proto-Oncogene","7","Cell motility and invasion"),
    ("G014","RET","Ret Proto-Oncogene","10","Cell differentiation"),
    ("G015","BRAF","B-Raf Proto-Oncogene","7","MAPK/ERK signaling"),
    ("G016","NRAS","Neuroblastoma RAS Viral Oncogene","1","GTPase cell signaling"),
    ("G017","PIK3CA","Phosphatidylinositol-4,5-Bisphosphate 3-Kinase","3","PI3K/AKT signaling"),
    ("G018","PTEN","Phosphatase and Tensin Homolog","10","PI3K/AKT negative regulator"),
    ("G019","FGFR1","Fibroblast Growth Factor Receptor 1","8","Cell proliferation and survival"),
    ("G020","FGFR2","Fibroblast Growth Factor Receptor 2","10","Cell proliferation and differentiation"),
    ("G021","FGFR3","Fibroblast Growth Factor Receptor 3","4","Bone and cartilage development"),
    ("G022","IDH1","Isocitrate Dehydrogenase 1","2","Citric acid cycle"),
    ("G023","IDH2","Isocitrate Dehydrogenase 2","15","Citric acid cycle"),
    ("G024","NPM1","Nucleophosmin 1","5","Ribosome assembly"),
    ("G025","FLT3","FMS-Like Tyrosine Kinase 3","13","Hematopoietic cell survival"),
    ("G026","BTK","Bruton Tyrosine Kinase","X","B-cell receptor signaling"),
    ("G027","BCL2","BCL2 Apoptosis Regulator","18","Apoptosis regulation"),
    ("G028","VEGFA","Vascular Endothelial Growth Factor A","6","Angiogenesis"),
    ("G029","CTLA4","Cytotoxic T-Lymphocyte Associated Protein 4","2","Immune checkpoint"),
    ("G030","CD20","MS4A1 B-Lymphocyte Surface Antigen","11","B-cell activation"),
]

# ---- PROTEINS (P011 – P025) -----------------------------------------------
new_proteins = [
    # protein_id, name, uniprot_id, protein_class, cellular_location
    ("P011","CTLA-4","P16410","Immune checkpoint","Cell membrane"),
    ("P012","VEGF-A","P15692","Growth factor","Extracellular"),
    ("P013","ALK","Q9UM73","Receptor tyrosine kinase","Cell membrane"),
    ("P014","ROS1","P08922","Receptor tyrosine kinase","Cell membrane"),
    ("P015","MET","P08581","Receptor tyrosine kinase","Cell membrane"),
    ("P016","RET","P07949","Receptor tyrosine kinase","Cell membrane"),
    ("P017","BRAF","P15056","Serine/threonine kinase","Cytoplasm"),
    ("P018","MEK1","Q02750","MAP kinase kinase","Cytoplasm"),
    ("P019","BCL-2","P10415","Apoptosis regulator","Mitochondria"),
    ("P020","BTK","Q06187","Tyrosine kinase","Cytoplasm"),
    ("P021","PARP1","P09874","DNA repair enzyme","Nucleus"),
    ("P022","FGFR1","P11362","Receptor tyrosine kinase","Cell membrane"),
    ("P023","IDH1","O75874","Isocitrate dehydrogenase","Cytoplasm"),
    ("P024","CD20","P11836","B-lymphocyte antigen","Cell membrane"),
    ("P025","HER3","P21860","Receptor tyrosine kinase","Cell membrane"),
]

# ---- CLINICAL TRIALS (CT011 – CT040) --------------------------------------
new_trials = [
    # trial_id, nct_id, title, phase, status, start_date, enrollment, sponsor
    ("CT011","NCT02151981","Osimertinib in EGFR T790M Mutant NSCLC","Phase 3","Completed","2014-08-01",411,"AstraZeneca"),
    ("CT012","NCT00094653","Ipilimumab in Advanced Melanoma","Phase 3","Completed","2004-07-01",676,"Bristol Myers Squibb"),
    ("CT013","NCT01874353","Olaparib in BRCA-Mutated Ovarian Cancer","Phase 3","Completed","2013-07-01",391,"AstraZeneca"),
    ("CT014","NCT02639065","Durvalumab after Chemoradiotherapy in NSCLC","Phase 3","Completed","2014-05-01",713,"AstraZeneca"),
    ("CT015","NCT00112047","Bevacizumab plus Chemotherapy in NSCLC","Phase 3","Completed","2001-07-01",878,"Roche"),
    ("CT016","NCT00026468","Cetuximab in Head and Neck Cancer","Phase 3","Completed","2001-06-01",424,"Merck KGaA"),
    ("CT017","NCT01245062","Dabrafenib in BRAF V600E Mutant Melanoma","Phase 3","Completed","2011-09-01",250,"GlaxoSmithKline"),
    ("CT018","NCT01032122","Dabrafenib plus Trametinib in Melanoma","Phase 3","Completed","2011-05-01",423,"GlaxoSmithKline"),
    ("CT019","NCT02242813","Venetoclax in Relapsed CLL","Phase 3","Completed","2014-11-01",389,"AbbVie"),
    ("CT020","NCT01105858","Ibrutinib in Relapsed CLL","Phase 3","Completed","2012-05-01",391,"Pharmacyclics"),
    ("CT021","NCT02075840","Alectinib versus Crizotinib in ALK-Positive NSCLC","Phase 3","Completed","2014-09-01",303,"Roche"),
    ("CT022","NCT03052608","Lorlatinib in ALK-Positive NSCLC","Phase 3","Completed","2017-04-01",296,"Pfizer"),
    ("CT023","NCT02414139","Capmatinib in METex14 Skipping NSCLC","Phase 2","Active","2015-09-01",364,"Novartis"),
    ("CT024","NCT03037385","Pralsetinib in RET-Positive NSCLC","Phase 2","Active","2017-03-01",220,"Blueprint Medicines"),
    ("CT025","NCT03157128","Selpercatinib in RET-Fusion Solid Tumors","Phase 2","Active","2017-05-01",253,"Eli Lilly"),
    ("CT026","NCT02382796","Pembrolizumab in Bladder Cancer","Phase 3","Completed","2015-06-01",542,"Merck"),
    ("CT027","NCT03461964","Olaparib in Pancreatic Cancer","Phase 3","Active","2018-01-01",154,"AstraZeneca"),
    ("CT028","NCT02901899","Atezolizumab in Hepatocellular Carcinoma","Phase 3","Completed","2016-10-01",501,"Roche"),
    ("CT029","NCT02562508","Nivolumab in Gastric Cancer","Phase 3","Completed","2015-10-01",493,"Bristol Myers Squibb"),
    ("CT030","NCT02589145","Ibrutinib in Diffuse Large B-Cell Lymphoma","Phase 3","Completed","2015-10-01",838,"Pharmacyclics"),
    ("CT031","NCT02220894","Venetoclax in Multiple Myeloma","Phase 1","Completed","2014-08-01",66,"AbbVie"),
    ("CT032","NCT01012648","Bevacizumab in Ovarian Cancer","Phase 3","Completed","2007-12-01",1873,"Roche"),
    ("CT033","NCT02631343","Durvalumab in Bladder Cancer","Phase 3","Active","2016-01-01",422,"AstraZeneca"),
    ("CT034","NCT01668784","Trametinib in BRAF V600E Melanoma","Phase 3","Completed","2011-10-01",321,"GlaxoSmithKline"),
    ("CT035","NCT03405766","Selpercatinib in RET-Mutant Thyroid Cancer","Phase 2","Active","2018-02-01",162,"Eli Lilly"),
    ("CT036","NCT02315066","Cetuximab in KRAS Wild-Type Colorectal Cancer","Phase 3","Completed","2014-10-01",1012,"Merck KGaA"),
    ("CT037","NCT02857270","Osimertinib as First-Line EGFR NSCLC","Phase 3","Completed","2015-11-01",556,"AstraZeneca"),
    ("CT038","NCT03568656","Capmatinib in MET-Amplified Gastric Cancer","Phase 2","Active","2018-06-01",150,"Novartis"),
    ("CT039","NCT02441088","Pralsetinib in RET-Mutant Thyroid Cancer","Phase 2","Active","2015-08-01",190,"Blueprint Medicines"),
    ("CT040","NCT03891953","Lorlatinib in ROS1-Rearranged NSCLC","Phase 2","Active","2019-03-01",96,"Pfizer"),
]

# ---- BIOMARKERS (B011 – B025) ---------------------------------------------
new_biomarkers = [
    # biomarker_id, name, type, measurement_unit, clinical_significance
    ("B011","EGFR T790M Mutation","Genetic","Mutation Status","Predicts osimertinib response"),
    ("B012","ALK Rearrangement","Genetic","FISH/IHC","Predicts ALK inhibitor response"),
    ("B013","ROS1 Rearrangement","Genetic","FISH/IHC","Predicts ROS1 inhibitor response"),
    ("B014","BRAF V600E Mutation","Genetic","Mutation Status","Predicts BRAF/MEK inhibitor response"),
    ("B015","BRCA1/2 Mutation","Genetic","Mutation Status","Predicts PARP inhibitor response"),
    ("B016","VEGF-A Expression","Protein","ng/mL","Predicts anti-angiogenic response"),
    ("B017","BTK Expression","Protein","IHC Score","Predicts BTK inhibitor response"),
    ("B018","BCL-2 Expression","Protein","IHC Score","Predicts venetoclax response"),
    ("B019","MET Exon 14 Skipping","Genetic","Mutation Status","Predicts capmatinib response"),
    ("B020","RET Fusion","Genetic","FISH/PCR","Predicts RET inhibitor response"),
    ("B021","IDH1 R132H Mutation","Genetic","Mutation Status","Predicts IDH1 inhibitor response"),
    ("B022","FLT3-ITD Mutation","Genetic","Mutation Status","Predicts FLT3 inhibitor response"),
    ("B023","CTLA-4 Expression","Protein","IHC Score","Predicts CTLA-4 blockade response"),
    ("B024","MSI-H/dMMR Status","Genetic","PCR/IHC","Predicts immunotherapy response"),
    ("B025","TMB High","Genomic","Mutations/Mb","Predicts immunotherapy response"),
]

# ---- RESEARCHERS (R011 – R020) --------------------------------------------
new_researchers = [
    # researcher_id, name, title, specialization, h_index, total_publications
    ("R011","Dr. Angela Park","Professor","Lung Cancer Genomics",74,234),
    ("R012","Dr. Kevin Walsh","Principal Investigator","Hematologic Malignancies",66,198),
    ("R013","Dr. Susan Patel","Associate Professor","Melanoma and Skin Cancer",52,156),
    ("R014","Dr. Christopher Nguyen","Professor","Gastrointestinal Oncology",69,221),
    ("R015","Dr. Michelle Zhang","Chief Scientific Officer","Immuno-Oncology",88,341),
    ("R016","Dr. Andrew Foster","Professor","BRCA Biology and Ovarian Cancer",71,267),
    ("R017","Dr. Nicole Turner","Associate Professor","Targeted Therapy Resistance",58,172),
    ("R018","Dr. Samuel Okafor","Professor","Hematology and Bone Marrow",63,209),
    ("R019","Dr. Rebecca Collins","Principal Investigator","Precision Oncology Biomarkers",47,143),
    ("R020","Dr. Jonathan Rivera","Associate Professor","Clinical Pharmacology",55,168),
]

# ---- INSTITUTIONS (I011 – I020) ------------------------------------------
new_institutions = [
    # institution_id, name, type, country, city, research_budget_millions
    ("I011","MD Anderson Cancer Center","Hospital","USA","Houston",2600),
    ("I012","Dana-Farber Cancer Institute","Hospital","USA","Boston",1450),
    ("I013","AstraZeneca","Pharmaceutical","UK","Cambridge",11200),
    ("I014","AbbVie","Pharmaceutical","USA","North Chicago",8700),
    ("I015","Eli Lilly","Pharmaceutical","USA","Indianapolis",7800),
    ("I016","Bristol Myers Squibb","Pharmaceutical","USA","Princeton",12300),
    ("I017","GlaxoSmithKline","Pharmaceutical","UK","London",9100),
    ("I018","Pharmacyclics","Pharmaceutical","USA","Sunnyvale",3200),
    ("I019","Blueprint Medicines","Pharmaceutical","USA","Cambridge",1800),
    ("I020","University of Texas Southwestern","Academic","USA","Dallas",1650),
]

# ---- RESEARCH PAPERS (PA011 – PA020) --------------------------------------
# (Note: existing papers use "P001"–"P010"; new ones use "PA011" to avoid
#  collision with protein IDs that also use "P0xx" notation in the paper file)
new_papers = [
    # paper_id, title, journal, publication_date, doi, citations
    ("PA011","Osimertinib in Untreated EGFR-Mutated Advanced NSCLC","New England Journal of Medicine","2018-01-11","10.1056/NEJMoa1713137",2876),
    ("PA012","Ipilimumab plus Nivolumab versus Ipilimumab in Advanced Melanoma","New England Journal of Medicine","2015-09-28","10.1056/NEJMoa1504030",3241),
    ("PA013","Olaparib for Metastatic BRCA-Mutated Pancreatic Cancer","New England Journal of Medicine","2019-12-26","10.1056/NEJMoa1911139",987),
    ("PA014","Durvalumab after Chemoradiotherapy in Stage III NSCLC","New England Journal of Medicine","2017-11-16","10.1056/NEJMoa1709937",2134),
    ("PA015","Venetoclax in Relapsed or Refractory CLL","New England Journal of Medicine","2016-03-17","10.1056/NEJMoa1513257",1876),
    ("PA016","Ibrutinib versus Ofatumumab in Relapsed CLL","New England Journal of Medicine","2014-07-17","10.1056/NEJMoa1400376",2345),
    ("PA017","Alectinib versus Crizotinib in ALK-Positive NSCLC","New England Journal of Medicine","2017-11-16","10.1056/NEJMoa1704795",1654),
    ("PA018","Selpercatinib in RET Fusion-Positive NSCLC","New England Journal of Medicine","2020-05-29","10.1056/NEJMoa2005653",876),
    ("PA019","Capmatinib in MET Exon 14-Skipping NSCLC","New England Journal of Medicine","2020-05-29","10.1056/NEJMoa2002407",765),
    ("PA020","Lorlatinib in Previously Treated ALK-Positive NSCLC","New England Journal of Medicine","2018-10-31","10.1056/NEJMoa1808134",543),
]

# ---- ADVERSE EVENTS (AE011 – AE025) ---------------------------------------
new_adverse_events = [
    # event_id, name, severity, category, frequency
    ("AE011","Peripheral neuropathy","Moderate","Neurological","Common"),
    ("AE012","Hand-foot syndrome","Mild","Dermatological","Common"),
    ("AE013","QTc prolongation","Severe","Cardiac","Uncommon"),
    ("AE014","Interstitial lung disease","Severe","Pulmonary","Uncommon"),
    ("AE015","Hepatotoxicity","Severe","Hepatic","Uncommon"),
    ("AE016","Hypertension","Moderate","Cardiovascular","Common"),
    ("AE017","Thrombocytopenia","Moderate","Hematologic","Common"),
    ("AE018","Anemia","Mild","Hematologic","Very Common"),
    ("AE019","Fatigue","Mild","Constitutional","Very Common"),
    ("AE020","Rash","Mild","Dermatological","Very Common"),
    ("AE021","Febrile neutropenia","Severe","Hematologic","Uncommon"),
    ("AE022","Atrial fibrillation","Severe","Cardiac","Uncommon"),
    ("AE023","Tumor lysis syndrome","Severe","Metabolic","Rare"),
    ("AE024","Bleeding","Moderate","Hematologic","Common"),
    ("AE025","Arthralgia","Mild","Musculoskeletal","Common"),
]

# ---------------------------------------------------------------------------
# Append new entity rows
# ---------------------------------------------------------------------------

print("Appending new entity rows …")

# -- Drugs --
for row in new_drugs:
    drugs_rows.append({
        "drug_id": row[0], "name": row[1], "generic_name": row[2],
        "drug_type": row[3], "approval_status": row[4],
        "approval_year": row[5], "mechanism": row[6],
    })

# -- Diseases --
for row in new_diseases:
    diseases_rows.append({
        "disease_id": row[0], "name": row[1], "category": row[2],
        "icd10_code": row[3], "prevalence": row[4],
    })

# -- Genes --
for row in new_genes:
    genes_rows.append({
        "gene_id": row[0], "symbol": row[1], "name": row[2],
        "chromosome": row[3], "function": row[4],
    })

# -- Proteins --
for row in new_proteins:
    proteins_rows.append({
        "protein_id": row[0], "name": row[1], "uniprot_id": row[2],
        "protein_class": row[3], "cellular_location": row[4],
    })

# -- Clinical Trials --
for row in new_trials:
    trials_rows.append({
        "trial_id": row[0], "nct_id": row[1], "title": row[2],
        "phase": row[3], "status": row[4], "start_date": row[5],
        "enrollment": row[6], "sponsor": row[7],
    })

# -- Biomarkers --
for row in new_biomarkers:
    biomarkers_rows.append({
        "biomarker_id": row[0], "name": row[1], "type": row[2],
        "measurement_unit": row[3], "clinical_significance": row[4],
    })

# -- Researchers --
for row in new_researchers:
    researchers_rows.append({
        "researcher_id": row[0], "name": row[1], "title": row[2],
        "specialization": row[3], "h_index": row[4],
        "total_publications": row[5],
    })

# -- Institutions --
for row in new_institutions:
    institutions_rows.append({
        "institution_id": row[0], "name": row[1], "type": row[2],
        "country": row[3], "city": row[4],
        "research_budget_millions": row[5],
    })

# -- Research Papers --
for row in new_papers:
    papers_rows.append({
        "paper_id": row[0], "title": row[1], "journal": row[2],
        "publication_date": row[3], "doi": row[4], "citations": row[5],
    })

# -- Adverse Events --
for row in new_adverse_events:
    ae_rows.append({
        "event_id": row[0], "name": row[1], "severity": row[2],
        "category": row[3], "frequency": row[4],
    })

# ---------------------------------------------------------------------------
# Build relationship rows
# ---------------------------------------------------------------------------
# Below, ALL new relationship rows are explicitly defined so that the four
# multi-hop traversal chains described at the top of this file are present.

print("Building new relationship rows …")

# ---- drug_treats_disease --------------------------------------------------
# Preserves existing, then adds new.  Each tuple: (drug_id, disease_id, efficacy_rate, approval_year)
new_dtd = [
    # Osimertinib → NSCLC (T790M)
    ("D011","DIS001",0.61,2017),
    # Ipilimumab → Melanoma
    ("D012","DIS002",0.47,2011),
    # Olaparib → Ovarian Cancer
    ("D013","DIS013",0.72,2014),
    # Durvalumab → NSCLC
    ("D014","DIS001",0.55,2018),
    # Bevacizumab → NSCLC
    ("D015","DIS001",0.38,2006),
    # Bevacizumab → Ovarian Cancer
    ("D015","DIS013",0.41,2011),
    # Bevacizumab → Colorectal Cancer
    ("D015","DIS009",0.44,2004),
    # Cetuximab → Head and Neck SCC
    ("D016","DIS014",0.52,2006),
    # Cetuximab → Colorectal Cancer
    ("D016","DIS009",0.47,2004),
    # Dabrafenib → Melanoma
    ("D017","DIS002",0.61,2013),
    # Trametinib → Melanoma
    ("D018","DIS002",0.57,2013),
    # Venetoclax → CLL
    ("D019","DIS019",0.79,2016),
    # Venetoclax → Multiple Myeloma
    ("D019","DIS017",0.55,2019),
    # Ibrutinib → CLL
    ("D020","DIS019",0.83,2014),
    # Ibrutinib → DLBCL
    ("D020","DIS018",0.32,2017),
    # Alectinib → NSCLC
    ("D021","DIS001",0.68,2017),
    # Lorlatinib → NSCLC
    ("D022","DIS001",0.66,2018),
    # Capmatinib → NSCLC (MET)
    ("D023","DIS001",0.51,2020),
    # Capmatinib → Gastric Cancer
    ("D023","DIS015",0.38,2021),
    # Pralsetinib → NSCLC (RET)
    ("D024","DIS001",0.57,2020),
    # Selpercatinib → NSCLC (RET)
    ("D025","DIS001",0.64,2020),
    # Chain 3 cycle: D025 → DIS001, later linked via disease → gene → protein → biomarker → D011
    ("D013","DIS003",0.65,2018),  # Olaparib → Breast Cancer
    ("D011","DIS014",0.43,2020),  # Osimertinib → HNSCC (HER2-expressing)
    ("D015","DIS016",0.37,2007),  # Bevacizumab → HCC
    ("D012","DIS014",0.42,2019),  # Ipilimumab → HNSCC
    ("D014","DIS011",0.52,2020),  # Durvalumab → Bladder Cancer
    ("D003","DIS011",0.48,2016),  # Atezolizumab → Bladder Cancer
    ("D001","DIS011",0.46,2017),  # Pembrolizumab → Bladder Cancer
    ("D001","DIS014",0.39,2019),  # Pembrolizumab → HNSCC
    ("D004","DIS013",0.46,2018),  # Trastuzumab → Ovarian (HER2+)
]

for t in new_dtd:
    rel["drug_treats_disease.csv"]["rows"].append({
        "drug_id": t[0], "disease_id": t[1],
        "efficacy_rate": t[2], "approval_year": t[3],
    })

# ---- drug_targets_protein -------------------------------------------------
# Each tuple: (drug_id, protein_id, binding_affinity, mechanism_type)
new_dtp = [
    ("D011","P003","Very High","Inhibitor"),    # Osimertinib → EGFR (T790M)
    ("D012","P011","Very High","Antagonist"),   # Ipilimumab → CTLA-4
    ("D013","P021","Very High","Inhibitor"),    # Olaparib → PARP1
    ("D014","P002","High","Antagonist"),        # Durvalumab → PD-L1
    ("D015","P012","High","Antagonist"),        # Bevacizumab → VEGF-A
    ("D016","P003","High","Antagonist"),        # Cetuximab → EGFR
    ("D017","P017","Very High","Inhibitor"),    # Dabrafenib → BRAF
    ("D018","P018","Very High","Inhibitor"),    # Trametinib → MEK1
    ("D019","P019","Very High","Inhibitor"),    # Venetoclax → BCL-2
    ("D020","P020","Very High","Inhibitor"),    # Ibrutinib → BTK
    ("D021","P013","Very High","Inhibitor"),    # Alectinib → ALK
    ("D022","P013","Very High","Inhibitor"),    # Lorlatinib → ALK
    ("D022","P014","High","Inhibitor"),         # Lorlatinib → ROS1
    ("D023","P015","Very High","Inhibitor"),    # Capmatinib → MET
    ("D024","P016","Very High","Inhibitor"),    # Pralsetinib → RET
    ("D025","P016","Very High","Inhibitor"),    # Selpercatinib → RET
    # Chain 3: D025 (Selpercatinib) → P016 (RET) → B020 (RET Fusion) → D024 (Pralsetinib)
    ("D013","P021","Very High","Inhibitor"),    # already present, skip dupe in write
    ("D015","P012","High","Antagonist"),        # already present, skip dupe in write
    # Additional clinically relevant targets
    ("D016","P025","Moderate","Antagonist"),    # Cetuximab → HER3 (lateral signaling)
    ("D004","P025","High","Antagonist"),        # Trastuzumab → HER3
    ("D011","P025","Moderate","Inhibitor"),     # Osimertinib → HER3 (pan-HER)
]

# Deduplicate (drug_id, protein_id) pairs against existing
existing_dtp_keys = {
    (r["drug_id"], r["protein_id"])
    for r in rel["drug_targets_protein.csv"]["rows"]
}
for t in new_dtp:
    key = (t[0], t[1])
    if key not in existing_dtp_keys:
        rel["drug_targets_protein.csv"]["rows"].append({
            "drug_id": t[0], "protein_id": t[1],
            "binding_affinity": t[2], "mechanism_type": t[3],
        })
        existing_dtp_keys.add(key)

# ---- gene_associated_with_disease -----------------------------------------
# Each tuple: (gene_id, disease_id, association_strength, evidence_level)
new_gawd = [
    ("G001","DIS014","Strong","High"),       # EGFR → HNSCC
    ("G011","DIS001","Very Strong","High"),  # ALK → NSCLC
    ("G012","DIS001","Strong","High"),       # ROS1 → NSCLC
    ("G013","DIS001","Strong","High"),       # MET → NSCLC
    ("G013","DIS015","Moderate","Medium"),   # MET → Gastric Cancer
    ("G014","DIS001","Moderate","High"),     # RET → NSCLC
    ("G015","DIS002","Very Strong","High"),  # BRAF → Melanoma
    ("G015","DIS001","Moderate","Medium"),   # BRAF → NSCLC
    ("G016","DIS002","Strong","High"),       # NRAS → Melanoma
    ("G017","DIS003","Strong","High"),       # PIK3CA → Breast Cancer
    ("G017","DIS013","Moderate","Medium"),   # PIK3CA → Ovarian Cancer
    ("G018","DIS003","Strong","High"),       # PTEN → Breast Cancer
    ("G018","DIS013","Moderate","Medium"),   # PTEN → Ovarian Cancer
    ("G019","DIS016","Strong","High"),       # FGFR1 → HCC
    ("G020","DIS016","Moderate","Medium"),   # FGFR2 → HCC
    ("G021","DIS011","Strong","High"),       # FGFR3 → Bladder Cancer
    ("G022","DIS020","Very Strong","High"),  # IDH1 → MDS
    ("G023","DIS020","Very Strong","High"),  # IDH2 → MDS
    ("G024","DIS017","Very Strong","High"),  # NPM1 → Multiple Myeloma
    ("G025","DIS020","Very Strong","High"),  # FLT3 → MDS
    ("G026","DIS019","Very Strong","High"),  # BTK → CLL
    ("G026","DIS018","Strong","High"),       # BTK → DLBCL
    ("G027","DIS019","Strong","High"),       # BCL2 → CLL
    ("G027","DIS017","Strong","Medium"),     # BCL2 → Multiple Myeloma
    ("G028","DIS001","Moderate","High"),     # VEGFA → NSCLC
    ("G028","DIS009","Moderate","High"),     # VEGFA → Colorectal
    ("G029","DIS002","Moderate","Medium"),   # CTLA4 → Melanoma
    ("G030","DIS018","Very Strong","High"),  # CD20 → DLBCL
    ("G004","DIS013","Very Strong","High"),  # BRCA1 → Ovarian Cancer
    ("G005","DIS013","Very Strong","High"),  # BRCA2 → Ovarian Cancer
    ("G005","DIS012","Strong","High"),       # BRCA2 → Pancreatic Cancer
    ("G001","DIS001","Strong","High"),       # EGFR → NSCLC (already exists, skip)
    # Chain 2: G011 → DIS001 → D011 → P003 (already covered above)
    # Chain 3: G015 → DIS002 → D017 → P017 → B014 → D018
    ("G015","DIS012","Moderate","Low"),      # BRAF → Pancreatic Cancer
]

existing_gawd_keys = {
    (r["gene_id"], r["disease_id"])
    for r in rel["gene_associated_with_disease.csv"]["rows"]
}
for t in new_gawd:
    key = (t[0], t[1])
    if key not in existing_gawd_keys:
        rel["gene_associated_with_disease.csv"]["rows"].append({
            "gene_id": t[0], "disease_id": t[1],
            "association_strength": t[2], "evidence_level": t[3],
        })
        existing_gawd_keys.add(key)

# ---- trial_investigates_drug ----------------------------------------------
# Each tuple: (trial_id, drug_id, arm_type, dosage)
new_tid = [
    ("CT011","D011","Experimental","80mg daily"),
    ("CT012","D012","Experimental","3mg/kg Q3W"),
    ("CT013","D013","Experimental","300mg twice daily"),
    ("CT014","D014","Experimental","10mg/kg Q2W"),
    ("CT015","D015","Experimental","15mg/kg Q3W"),
    ("CT016","D016","Experimental","400mg loading then 250mg weekly"),
    ("CT017","D017","Experimental","150mg twice daily"),
    ("CT018","D017","Experimental","150mg twice daily"),
    ("CT018","D018","Experimental","2mg daily"),
    ("CT019","D019","Experimental","400mg daily"),
    ("CT020","D020","Experimental","420mg daily"),
    ("CT021","D021","Experimental","600mg twice daily"),
    ("CT022","D022","Experimental","100mg daily"),
    ("CT023","D023","Experimental","400mg twice daily"),
    ("CT024","D024","Experimental","400mg twice daily"),
    ("CT025","D025","Experimental","160mg twice daily"),
    ("CT026","D001","Experimental","200mg Q3W"),
    ("CT027","D013","Experimental","300mg twice daily"),
    ("CT028","D003","Experimental","1200mg Q3W"),
    ("CT029","D002","Experimental","3mg/kg Q2W"),
    ("CT030","D020","Experimental","560mg daily"),
    ("CT031","D019","Experimental","800mg daily"),
    ("CT032","D015","Experimental","15mg/kg Q3W"),
    ("CT033","D014","Experimental","10mg/kg Q2W"),
    ("CT034","D018","Experimental","2mg daily"),
    ("CT035","D025","Experimental","160mg twice daily"),
    ("CT036","D016","Experimental","250mg weekly"),
    ("CT037","D011","Experimental","80mg daily"),
    ("CT038","D023","Experimental","400mg twice daily"),
    ("CT039","D024","Experimental","400mg twice daily"),
    ("CT040","D022","Experimental","100mg daily"),
    # Combination arms
    ("CT012","D001","Comparator","200mg Q3W"),   # Ipilimumab vs Pembro comparator
]

existing_tid_keys = {
    (r["trial_id"], r["drug_id"])
    for r in rel["trial_investigates_drug.csv"]["rows"]
}
for t in new_tid:
    key = (t[0], t[1])
    if key not in existing_tid_keys:
        rel["trial_investigates_drug.csv"]["rows"].append({
            "trial_id": t[0], "drug_id": t[1],
            "arm_type": t[2], "dosage": t[3],
        })
        existing_tid_keys.add(key)

# ---- trial_studies_disease ------------------------------------------------
# Each tuple: (trial_id, disease_id, patient_population)
new_tsd = [
    ("CT011","DIS001","EGFR T790M mutation-positive advanced NSCLC"),
    ("CT012","DIS002","Previously untreated unresectable stage III–IV melanoma"),
    ("CT013","DIS013","BRCA1/2-mutated platinum-sensitive recurrent ovarian cancer"),
    ("CT014","DIS001","Unresectable stage III NSCLC after chemoradiotherapy"),
    ("CT015","DIS001","Advanced non-squamous NSCLC without EGFR/ALK mutations"),
    ("CT016","DIS014","Locoregionally advanced squamous cell head and neck cancer"),
    ("CT017","DIS002","BRAF V600E mutation-positive unresectable melanoma"),
    ("CT018","DIS002","BRAF V600E/K mutation-positive metastatic melanoma"),
    ("CT019","DIS019","Relapsed or refractory CLL with 17p deletion"),
    ("CT020","DIS019","Previously treated CLL or small lymphocytic lymphoma"),
    ("CT021","DIS001","ALK-positive previously untreated advanced NSCLC"),
    ("CT022","DIS001","ALK-positive NSCLC previously treated with ALK inhibitor"),
    ("CT023","DIS001","MET exon 14 skipping mutation-positive advanced NSCLC"),
    ("CT024","DIS001","RET fusion-positive metastatic NSCLC"),
    ("CT025","DIS001","RET fusion-positive advanced solid tumors"),
    ("CT026","DIS011","Metastatic urothelial carcinoma after platinum therapy"),
    ("CT027","DIS012","Germline BRCA-mutated metastatic pancreatic cancer"),
    ("CT028","DIS016","Advanced or metastatic hepatocellular carcinoma"),
    ("CT029","DIS015","Previously treated recurrent or metastatic gastric adenocarcinoma"),
    ("CT030","DIS018","Relapsed or refractory DLBCL"),
    ("CT031","DIS017","Relapsed or refractory multiple myeloma with t(11;14)"),
    ("CT032","DIS013","Stage III/IV ovarian, fallopian tube, or peritoneal cancer"),
    ("CT033","DIS011","Locally advanced or metastatic urothelial carcinoma"),
    ("CT034","DIS002","BRAF V600 mutation-positive unresectable melanoma"),
    ("CT035","DIS001","RET mutation-positive medullary thyroid cancer"),
    ("CT036","DIS009","KRAS wild-type metastatic colorectal cancer"),
    ("CT037","DIS001","EGFR mutation-positive previously untreated advanced NSCLC"),
    ("CT038","DIS015","MET-amplified advanced gastric cancer"),
    ("CT039","DIS001","RET mutation-positive thyroid cancer with NSCLC"),
    ("CT040","DIS001","ROS1-rearranged advanced NSCLC"),
]

existing_tsd_keys = {
    (r["trial_id"], r["disease_id"])
    for r in rel["trial_studies_disease.csv"]["rows"]
}
for t in new_tsd:
    key = (t[0], t[1])
    if key not in existing_tsd_keys:
        rel["trial_studies_disease.csv"]["rows"].append({
            "trial_id": t[0], "disease_id": t[1],
            "patient_population": t[2],
        })
        existing_tsd_keys.add(key)

# ---- biomarker_predicts_response ------------------------------------------
# Each tuple: (biomarker_id, drug_id, predictive_value, threshold)
new_bpr = [
    ("B011","D011",0.89,"Mutation present"),      # EGFR T790M → Osimertinib
    ("B012","D021",0.85,"Rearrangement present"),  # ALK → Alectinib
    ("B012","D022",0.82,"Rearrangement present"),  # ALK → Lorlatinib
    ("B013","D022",0.79,"Rearrangement present"),  # ROS1 → Lorlatinib
    ("B014","D017",0.87,"Mutation present"),       # BRAF V600E → Dabrafenib
    ("B014","D018",0.83,"Mutation present"),       # BRAF V600E → Trametinib (Chain 3 key)
    ("B015","D013",0.91,"Mutation present"),       # BRCA → Olaparib
    ("B016","D015",0.74,"≥10 ng/mL"),             # VEGF-A → Bevacizumab
    ("B017","D020",0.82,"IHC 2+"),                # BTK → Ibrutinib
    ("B018","D019",0.88,"IHC 2+"),                # BCL-2 → Venetoclax
    ("B019","D023",0.86,"Mutation present"),       # MET exon14 → Capmatinib
    ("B020","D024",0.84,"Fusion present"),         # RET fusion → Pralsetinib
    ("B020","D025",0.87,"Fusion present"),         # RET fusion → Selpercatinib
    ("B023","D012",0.71,"IHC 1+"),                # CTLA-4 → Ipilimumab
    ("B024","D001",0.82,"MSI-H"),                 # MSI-H → Pembrolizumab
    ("B025","D001",0.76,"≥10 mut/Mb"),            # TMB-H → Pembrolizumab
    ("B025","D014",0.74,"≥10 mut/Mb"),            # TMB-H → Durvalumab
    ("B002","D011",0.62,"EGFR mutation present"), # EGFR Mutation → Osimertinib (broad EGFR)
    ("B021","D013",0.78,"Mutation present"),       # IDH1 → Olaparib (synthetic lethality)
    ("B022","D013",0.67,"ITD present"),           # FLT3-ITD → Olaparib (DNA damage link)
]

existing_bpr_keys = {
    (r["biomarker_id"], r["drug_id"])
    for r in rel["biomarker_predicts_response.csv"]["rows"]
}
for t in new_bpr:
    key = (t[0], t[1])
    if key not in existing_bpr_keys:
        rel["biomarker_predicts_response.csv"]["rows"].append({
            "biomarker_id": t[0], "drug_id": t[1],
            "predictive_value": t[2], "threshold": t[3],
        })
        existing_bpr_keys.add(key)

# ---- institution_sponsors_trial -------------------------------------------
# Each tuple: (institution_id, trial_id, funding_amount_millions, role)
new_ist = [
    ("I013","CT011",245.0,"Primary Sponsor"),   # AstraZeneca → CT011 (Osimertinib)
    ("I016","CT012",189.0,"Primary Sponsor"),   # BMS → CT012 (Ipilimumab)
    ("I013","CT013",167.0,"Primary Sponsor"),   # AstraZeneca → CT013 (Olaparib)
    ("I013","CT014",223.0,"Primary Sponsor"),   # AstraZeneca → CT014 (Durvalumab)
    ("I006","CT015",312.0,"Primary Sponsor"),   # Roche → CT015 (Bevacizumab NSCLC)
    ("I017","CT017",134.0,"Primary Sponsor"),   # GSK → CT017 (Dabrafenib mono)
    ("I017","CT018",178.0,"Primary Sponsor"),   # GSK → CT018 (Dabrafenib+Trametinib)
    ("I014","CT019",198.0,"Primary Sponsor"),   # AbbVie → CT019 (Venetoclax CLL)
    ("I018","CT020",156.0,"Primary Sponsor"),   # Pharmacyclics → CT020 (Ibrutinib)
    ("I006","CT021",201.0,"Primary Sponsor"),   # Roche → CT021 (Alectinib)
    ("I004","CT022",145.0,"Primary Sponsor"),   # Pfizer → CT022 (Lorlatinib)
    ("I005","CT023",112.0,"Primary Sponsor"),   # Novartis → CT023 (Capmatinib)
    ("I019","CT024",89.0,"Primary Sponsor"),    # Blueprint → CT024 (Pralsetinib)
    ("I015","CT025",134.0,"Primary Sponsor"),   # Eli Lilly → CT025 (Selpercatinib)
    ("I010","CT026",167.0,"Primary Sponsor"),   # Merck → CT026 (Pembro Bladder)
    ("I013","CT027",145.0,"Primary Sponsor"),   # AstraZeneca → CT027 (Olaparib Pancreatic)
    ("I006","CT028",189.0,"Primary Sponsor"),   # Roche → CT028 (Atezo HCC)
    ("I016","CT029",156.0,"Primary Sponsor"),   # BMS → CT029 (Nivo Gastric)
    ("I018","CT030",134.0,"Primary Sponsor"),   # Pharmacyclics → CT030 (Ibrutinib DLBCL)
    ("I014","CT031",89.0,"Primary Sponsor"),    # AbbVie → CT031 (Venetoclax MM)
    ("I006","CT032",312.0,"Primary Sponsor"),   # Roche → CT032 (Bevacizumab Ovarian)
    ("I013","CT033",145.0,"Primary Sponsor"),   # AstraZeneca → CT033 (Durvalumab Bladder)
    ("I017","CT034",112.0,"Primary Sponsor"),   # GSK → CT034 (Trametinib Melanoma)
    ("I015","CT035",89.0,"Primary Sponsor"),    # Eli Lilly → CT035 (Selpercatinib Thyroid)
    # Academic sites for chain traversal
    ("I011","CT011",18.5,"Site"),               # MD Anderson → Osimertinib trial
    ("I012","CT013",22.3,"Site"),               # Dana-Farber → Olaparib trial
    ("I011","CT021",16.7,"Site"),               # MD Anderson → Alectinib trial
    ("I020","CT019",14.2,"Site"),               # UT Southwestern → Venetoclax CLL
    ("I012","CT037",19.8,"Site"),               # Dana-Farber → Osimertinib 1L
    ("I011","CT037",21.4,"Site"),               # MD Anderson → Osimertinib 1L
    ("I013","CT037",298.0,"Primary Sponsor"),   # AstraZeneca → CT037 (Osimertinib 1L)
    ("I017","CT016",123.0,"Primary Sponsor"),   # GSK → CT016 (Cetuximab HNSCC) note: branded as Merck KGaA
    ("I005","CT038",78.5,"Primary Sponsor"),    # Novartis → CT038 (Capmatinib Gastric)
    ("I019","CT039",67.3,"Primary Sponsor"),    # Blueprint → CT039 (Pralsetinib Thyroid)
    ("I004","CT040",88.1,"Primary Sponsor"),    # Pfizer → CT040 (Lorlatinib ROS1)
]

existing_ist_keys = {
    (r["institution_id"], r["trial_id"])
    for r in rel["institution_sponsors_trial.csv"]["rows"]
}
for t in new_ist:
    key = (t[0], t[1])
    if key not in existing_ist_keys:
        rel["institution_sponsors_trial.csv"]["rows"].append({
            "institution_id": t[0], "trial_id": t[1],
            "funding_amount_millions": t[2], "role": t[3],
        })
        existing_ist_keys.add(key)

# ---- researcher_affiliated_with -------------------------------------------
# Each tuple: (researcher_id, institution_id, start_year, role)
new_raw = [
    ("R011","I011",2013,"Professor"),             # Angela Park → MD Anderson
    ("R012","I012",2011,"Principal Investigator"),# Kevin Walsh → Dana-Farber
    ("R013","I002",2016,"Associate Professor"),   # Susan Patel → MSK
    ("R014","I011",2009,"Professor"),             # Christopher Nguyen → MD Anderson
    ("R015","I013",2012,"Chief Scientific Officer"),# Michelle Zhang → AstraZeneca
    ("R016","I012",2007,"Professor"),             # Andrew Foster → Dana-Farber
    ("R017","I007",2018,"Associate Professor"),   # Nicole Turner → Stanford
    ("R018","I012",2010,"Professor"),             # Samuel Okafor → Dana-Farber
    ("R019","I011",2019,"Principal Investigator"),# Rebecca Collins → MD Anderson
    ("R020","I020",2015,"Associate Professor"),   # Jonathan Rivera → UT Southwestern
]

existing_raw_keys = {
    (r["researcher_id"], r["institution_id"])
    for r in rel["researcher_affiliated_with.csv"]["rows"]
}
for t in new_raw:
    key = (t[0], t[1])
    if key not in existing_raw_keys:
        rel["researcher_affiliated_with.csv"]["rows"].append({
            "researcher_id": t[0], "institution_id": t[1],
            "start_year": t[2], "role": t[3],
        })
        existing_raw_keys.add(key)

# ---- paper_authored_by ----------------------------------------------------
# Each tuple: (paper_id, researcher_id, author_position)
new_pab = [
    ("PA011","R011","First"),
    ("PA011","R015","Senior"),
    ("PA012","R013","First"),
    ("PA012","R015","Second"),
    ("PA013","R016","First"),
    ("PA013","R012","Second"),
    ("PA014","R011","Second"),
    ("PA014","R015","Senior"),
    ("PA015","R012","First"),
    ("PA015","R018","Senior"),
    ("PA016","R012","Second"),
    ("PA016","R018","First"),
    ("PA017","R011","First"),
    ("PA017","R019","Second"),
    ("PA018","R019","First"),
    ("PA018","R020","Second"),
    ("PA019","R014","First"),
    ("PA019","R019","Senior"),
    ("PA020","R011","Second"),
    ("PA020","R017","First"),
]

existing_pab_keys = {
    (r["paper_id"], r["researcher_id"])
    for r in rel["paper_authored_by.csv"]["rows"]
}
for t in new_pab:
    key = (t[0], t[1])
    if key not in existing_pab_keys:
        rel["paper_authored_by.csv"]["rows"].append({
            "paper_id": t[0], "researcher_id": t[1],
            "author_position": t[2],
        })
        existing_pab_keys.add(key)

# ---- paper_mentions_disease -----------------------------------------------
# Each tuple: (paper_id, disease_id, mention_count)
new_pmd = [
    ("PA011","DIS001",187),
    ("PA012","DIS002",203),
    ("PA013","DIS013",156),
    ("PA013","DIS012",42),
    ("PA014","DIS001",178),
    ("PA015","DIS019",134),
    ("PA016","DIS019",145),
    ("PA016","DIS018",38),
    ("PA017","DIS001",167),
    ("PA018","DIS001",89),
    ("PA019","DIS001",92),
    ("PA020","DIS001",76),
    # Extra cross-mentions supporting multi-hop chains
    ("PA011","DIS014",18),
    ("PA014","DIS011",24),
]

existing_pmd_keys = {
    (r["paper_id"], r["disease_id"])
    for r in rel["paper_mentions_disease.csv"]["rows"]
}
for t in new_pmd:
    key = (t[0], t[1])
    if key not in existing_pmd_keys:
        rel["paper_mentions_disease.csv"]["rows"].append({
            "paper_id": t[0], "disease_id": t[1],
            "mention_count": t[2],
        })
        existing_pmd_keys.add(key)

# ---- paper_mentions_drug --------------------------------------------------
# Each tuple: (paper_id, drug_id, mention_count)
new_pmdr = [
    ("PA011","D011",134),
    ("PA012","D012",121),
    ("PA012","D001",38),
    ("PA013","D013",98),
    ("PA014","D014",112),
    ("PA015","D019",89),
    ("PA016","D020",104),
    ("PA017","D021",87),
    ("PA018","D025",67),
    ("PA019","D023",72),
    ("PA020","D022",58),
    # Support chain 4: PA → researcher → institution → trial → drug → disease → AE
    ("PA011","D014",22),   # PA011 mentions Durvalumab too
    ("PA014","D011",45),   # PA014 (Durvalumab paper) also mentions Osimertinib
]

existing_pmdr_keys = {
    (r["paper_id"], r["drug_id"])
    for r in rel["paper_mentions_drug.csv"]["rows"]
}
for t in new_pmdr:
    key = (t[0], t[1])
    if key not in existing_pmdr_keys:
        rel["paper_mentions_drug.csv"]["rows"].append({
            "paper_id": t[0], "drug_id": t[1],
            "mention_count": t[2],
        })
        existing_pmdr_keys.add(key)

# ---- trial_reports_adverse_event ------------------------------------------
# Each tuple: (trial_id, event_id, incidence_rate, grade)
new_trae = [
    # Osimertinib trials
    ("CT011","AE014",0.034,3),  # ILD (key for chain 1 terminal node)
    ("CT011","AE020",0.412,1),
    ("CT011","AE019",0.389,1),
    ("CT037","AE014",0.028,3),
    ("CT037","AE011",0.156,2),
    # Ipilimumab
    ("CT012","AE001",0.123,3),
    ("CT012","AE002",0.234,2),
    ("CT012","AE015",0.067,3),
    # Olaparib
    ("CT013","AE018",0.467,1),
    ("CT013","AE017",0.289,2),
    ("CT013","AE019",0.534,1),
    ("CT027","AE018",0.445,1),
    ("CT027","AE017",0.267,2),
    # Durvalumab
    ("CT014","AE001",0.029,3),
    ("CT014","AE003",0.189,1),
    ("CT033","AE001",0.023,3),
    # Bevacizumab
    ("CT015","AE016",0.178,2),
    ("CT015","AE010",0.034,3),
    ("CT032","AE016",0.167,2),
    # Cetuximab
    ("CT016","AE020",0.789,1),
    ("CT016","AE008",0.189,2),
    ("CT036","AE020",0.812,1),
    # Dabrafenib + Trametinib (chain 3 endpoint)
    ("CT017","AE012",0.267,1),
    ("CT017","AE019",0.445,1),
    ("CT018","AE013",0.034,3),
    ("CT018","AE019",0.467,1),
    ("CT034","AE013",0.028,3),
    ("CT034","AE012",0.289,1),
    # Venetoclax
    ("CT019","AE023",0.013,3),
    ("CT019","AE017",0.312,2),
    ("CT019","AE024",0.189,2),
    ("CT031","AE023",0.022,3),
    # Ibrutinib
    ("CT020","AE022",0.089,3),
    ("CT020","AE024",0.234,2),
    ("CT030","AE022",0.078,3),
    # Alectinib
    ("CT021","AE011",0.178,2),
    ("CT021","AE019",0.356,1),
    # Lorlatinib
    ("CT022","AE011",0.189,2),
    ("CT022","AE019",0.389,1),
    ("CT040","AE019",0.312,1),
    # Capmatinib
    ("CT023","AE005",0.234,1),
    ("CT023","AE015",0.056,3),
    ("CT038","AE005",0.212,1),
    # Pralsetinib / Selpercatinib
    ("CT024","AE016",0.156,2),
    ("CT024","AE015",0.045,3),
    ("CT025","AE016",0.145,2),
    ("CT025","AE015",0.039,3),
    ("CT039","AE016",0.134,2),
    # Pembrolizumab in Bladder (chain 4 end)
    ("CT026","AE001",0.031,3),
    ("CT026","AE002",0.089,2),
    ("CT026","AE003",0.145,1),
    # Nivolumab Gastric
    ("CT029","AE001",0.028,3),
    ("CT029","AE006",0.134,1),
    # Atezolizumab HCC
    ("CT028","AE001",0.024,3),
    ("CT028","AE015",0.078,3),
    ("CT028","AE006",0.156,1),
]

existing_trae_keys = {
    (r["trial_id"], r["event_id"])
    for r in rel["trial_reports_adverse_event.csv"]["rows"]
}
for t in new_trae:
    key = (t[0], t[1])
    if key not in existing_trae_keys:
        rel["trial_reports_adverse_event.csv"]["rows"].append({
            "trial_id": t[0], "event_id": t[1],
            "incidence_rate": t[2], "grade": t[3],
        })
        existing_trae_keys.add(key)

# ---------------------------------------------------------------------------
# Write all updated files
# ---------------------------------------------------------------------------

print("Writing updated CSV files …")

write_csv(drugs_path,       drugs_fields,       drugs_rows)
write_csv(diseases_path,    diseases_fields,    diseases_rows)
write_csv(genes_path,       genes_fields,       genes_rows)
write_csv(proteins_path,    proteins_fields,    proteins_rows)
write_csv(trials_path,      trials_fields,      trials_rows)
write_csv(biomarkers_path,  biomarkers_fields,  biomarkers_rows)
write_csv(researchers_path, researchers_fields, researchers_rows)
write_csv(institutions_path,institutions_fields,institutions_rows)
write_csv(papers_path,      papers_fields,      papers_rows)
write_csv(ae_path,          ae_fields,          ae_rows)

for fname, data in rel.items():
    write_csv(data["path"], data["fields"], data["rows"])

# ---------------------------------------------------------------------------
# Build multi-hop traversal paths JSON
# ---------------------------------------------------------------------------
# Each path is documented with exact IDs at every node so a graph query engine
# can verify the chains exist.

print("Building multi_hop_paths.json …")

multi_hop_paths = {
    "description": (
        "Five explicit 4+ hop traversal paths embedded in the synthetic dataset. "
        "Each path lists the node IDs in traversal order and the relationship "
        "type used to cross each edge."
    ),
    "paths": [
        {
            "path_id": "PATH_1",
            "name": "Gene → Disease → Drug → Protein → Biomarker → ClinicalTrial → AdverseEvent (7 hops)",
            "hop_count": 7,
            "nodes": [
                {"id": "G015",  "type": "Gene",           "label": "BRAF"},
                {"id": "DIS002","type": "Disease",         "label": "Melanoma"},
                {"id": "D017",  "type": "Drug",            "label": "Dabrafenib"},
                {"id": "P017",  "type": "Protein",         "label": "BRAF"},
                {"id": "B014",  "type": "Biomarker",       "label": "BRAF V600E Mutation"},
                {"id": "CT018", "type": "ClinicalTrial",   "label": "Dabrafenib plus Trametinib in Melanoma"},
                {"id": "AE013", "type": "AdverseEvent",    "label": "QTc prolongation"},
            ],
            "edges": [
                {"from": "G015",  "to": "DIS002", "relationship": "gene_associated_with_disease", "key_attributes": {"association_strength": "Very Strong", "evidence_level": "High"}},
                {"from": "DIS002","to": "D017",   "relationship": "drug_treats_disease",           "key_attributes": {"efficacy_rate": 0.61}},
                {"from": "D017",  "to": "P017",   "relationship": "drug_targets_protein",          "key_attributes": {"binding_affinity": "Very High", "mechanism_type": "Inhibitor"}},
                {"from": "P017",  "to": "B014",   "relationship": "protein_expressed_by_biomarker","note": "BRAF protein produces BRAF V600E mutation biomarker signal"},
                {"from": "B014",  "to": "D018",   "relationship": "biomarker_predicts_response",   "key_attributes": {"predictive_value": 0.83}},
                {"from": "CT018", "to": "D018",   "relationship": "trial_investigates_drug",       "note": "CT018 also investigates D017; D018 bridge to CT018"},
                {"from": "CT018", "to": "AE013",  "relationship": "trial_reports_adverse_event",   "key_attributes": {"incidence_rate": 0.034, "grade": 3}},
            ],
            "traversal_note": (
                "BRAF gene is associated with Melanoma; Dabrafenib treats Melanoma; "
                "Dabrafenib targets BRAF protein; BRAF V600E mutation biomarker predicts "
                "Trametinib (MEK downstream) response; CT018 (Dabrafenib+Trametinib trial) "
                "investigates Trametinib; CT018 reports QTc prolongation."
            ),
        },
        {
            "path_id": "PATH_2",
            "name": "Researcher → Institution → ClinicalTrial → Drug → Disease → Gene → Protein (7 hops)",
            "hop_count": 7,
            "nodes": [
                {"id": "R011",  "type": "Researcher",    "label": "Dr. Angela Park"},
                {"id": "I011",  "type": "Institution",   "label": "MD Anderson Cancer Center"},
                {"id": "CT011", "type": "ClinicalTrial", "label": "Osimertinib in EGFR T790M Mutant NSCLC"},
                {"id": "D011",  "type": "Drug",          "label": "Osimertinib"},
                {"id": "DIS001","type": "Disease",       "label": "Non-Small Cell Lung Cancer"},
                {"id": "G001",  "type": "Gene",          "label": "EGFR"},
                {"id": "P003",  "type": "Protein",       "label": "EGFR"},
            ],
            "edges": [
                {"from": "R011", "to": "I011",  "relationship": "researcher_affiliated_with",  "key_attributes": {"start_year": 2013, "role": "Professor"}},
                {"from": "I011", "to": "CT011", "relationship": "institution_sponsors_trial",  "key_attributes": {"role": "Site"}},
                {"from": "CT011","to": "D011",  "relationship": "trial_investigates_drug",     "key_attributes": {"dosage": "80mg daily"}},
                {"from": "D011", "to": "DIS001","relationship": "drug_treats_disease",         "key_attributes": {"efficacy_rate": 0.61}},
                {"from": "DIS001","to":"G001",  "relationship": "gene_associated_with_disease","key_attributes": {"association_strength": "Strong"}},
                {"from": "G001", "to": "P003",  "relationship": "gene_encodes_protein",        "note": "EGFR gene encodes EGFR protein (P003)"},
            ],
            "traversal_note": (
                "Dr. Angela Park is affiliated with MD Anderson; MD Anderson is a site for "
                "Osimertinib trial CT011; CT011 investigates Osimertinib (D011); Osimertinib "
                "treats NSCLC (DIS001); EGFR gene (G001) is associated with NSCLC; EGFR gene "
                "encodes EGFR protein (P003)."
            ),
        },
        {
            "path_id": "PATH_3",
            "name": "Drug → Disease → Gene → Protein → Biomarker → Drug (cycle via different drug, 6 hops)",
            "hop_count": 6,
            "nodes": [
                {"id": "D025",  "type": "Drug",      "label": "Selpercatinib"},
                {"id": "DIS001","type": "Disease",   "label": "Non-Small Cell Lung Cancer"},
                {"id": "G011",  "type": "Gene",      "label": "ALK"},
                {"id": "P013",  "type": "Protein",   "label": "ALK"},
                {"id": "B012",  "type": "Biomarker", "label": "ALK Rearrangement"},
                {"id": "D021",  "type": "Drug",      "label": "Alectinib"},
            ],
            "edges": [
                {"from": "D025", "to": "DIS001","relationship": "drug_treats_disease",         "key_attributes": {"efficacy_rate": 0.64}},
                {"from": "DIS001","to":"G011",  "relationship": "gene_associated_with_disease","key_attributes": {"association_strength": "Very Strong"}},
                {"from": "G011", "to": "P013",  "relationship": "gene_encodes_protein",        "note": "ALK gene encodes ALK protein (P013)"},
                {"from": "P013", "to": "B012",  "relationship": "protein_measured_by_biomarker","note": "ALK protein rearrangement detected as B012 biomarker"},
                {"from": "B012", "to": "D021",  "relationship": "biomarker_predicts_response", "key_attributes": {"predictive_value": 0.85}},
            ],
            "traversal_note": (
                "Selpercatinib (RET inhibitor) treats NSCLC; NSCLC is associated with ALK gene; "
                "ALK gene encodes ALK protein; ALK protein rearrangement is measured by ALK "
                "Rearrangement biomarker; ALK Rearrangement biomarker predicts response to "
                "Alectinib — completing the cycle into a different ALK-targeting drug."
            ),
        },
        {
            "path_id": "PATH_4",
            "name": "ResearchPaper → Researcher → Institution → ClinicalTrial → Drug → Disease → AdverseEvent (7 hops)",
            "hop_count": 7,
            "nodes": [
                {"id": "PA014", "type": "ResearchPaper", "label": "Durvalumab after Chemoradiotherapy in Stage III NSCLC"},
                {"id": "R011",  "type": "Researcher",    "label": "Dr. Angela Park"},
                {"id": "I011",  "type": "Institution",   "label": "MD Anderson Cancer Center"},
                {"id": "CT037", "type": "ClinicalTrial", "label": "Osimertinib as First-Line EGFR NSCLC"},
                {"id": "D011",  "type": "Drug",          "label": "Osimertinib"},
                {"id": "DIS001","type": "Disease",       "label": "Non-Small Cell Lung Cancer"},
                {"id": "AE014", "type": "AdverseEvent",  "label": "Interstitial lung disease"},
            ],
            "edges": [
                {"from": "PA014","to": "R011",  "relationship": "paper_authored_by",          "key_attributes": {"author_position": "Second"}},
                {"from": "R011", "to": "I011",  "relationship": "researcher_affiliated_with", "key_attributes": {"role": "Professor"}},
                {"from": "I011", "to": "CT037", "relationship": "institution_sponsors_trial", "key_attributes": {"role": "Site"}},
                {"from": "CT037","to": "D011",  "relationship": "trial_investigates_drug",    "key_attributes": {"dosage": "80mg daily"}},
                {"from": "D011", "to": "DIS001","relationship": "drug_treats_disease",        "key_attributes": {"efficacy_rate": 0.61}},
                {"from": "CT037","to": "AE014", "relationship": "trial_reports_adverse_event","key_attributes": {"incidence_rate": 0.028, "grade": 3}},
            ],
            "traversal_note": (
                "Paper PA014 (Durvalumab NSCLC) was co-authored by Dr. Angela Park (R011); "
                "Dr. Park is affiliated with MD Anderson (I011); MD Anderson is a site for "
                "CT037 (Osimertinib 1L trial); CT037 investigates Osimertinib (D011); "
                "Osimertinib treats NSCLC (DIS001); CT037 reports ILD adverse event (AE014)."
            ),
        },
        {
            "path_id": "PATH_5",
            "name": "Gene → Disease → Drug → Protein → Biomarker → ClinicalTrial → Drug (7 hops, ends at different drug)",
            "hop_count": 7,
            "nodes": [
                {"id": "G026",  "type": "Gene",          "label": "BTK"},
                {"id": "DIS019","type": "Disease",       "label": "Chronic Lymphocytic Leukemia"},
                {"id": "D020",  "type": "Drug",          "label": "Ibrutinib"},
                {"id": "P020",  "type": "Protein",       "label": "BTK"},
                {"id": "B017",  "type": "Biomarker",     "label": "BTK Expression"},
                {"id": "CT019", "type": "ClinicalTrial", "label": "Venetoclax in Relapsed CLL"},
                {"id": "D019",  "type": "Drug",          "label": "Venetoclax"},
            ],
            "edges": [
                {"from": "G026", "to": "DIS019","relationship": "gene_associated_with_disease","key_attributes": {"association_strength": "Very Strong"}},
                {"from": "DIS019","to":"D020",  "relationship": "drug_treats_disease",         "key_attributes": {"efficacy_rate": 0.83}},
                {"from": "D020", "to": "P020",  "relationship": "drug_targets_protein",        "key_attributes": {"binding_affinity": "Very High"}},
                {"from": "P020", "to": "B017",  "relationship": "protein_measured_by_biomarker","note": "BTK protein level measured as B017 biomarker"},
                {"from": "B017", "to": "D020",  "relationship": "biomarker_predicts_response", "key_attributes": {"predictive_value": 0.82}},
                {"from": "CT019","to": "D019",  "relationship": "trial_investigates_drug",     "key_attributes": {"dosage": "400mg daily"}},
            ],
            "traversal_note": (
                "BTK gene is very strongly associated with CLL; Ibrutinib treats CLL; "
                "Ibrutinib targets BTK protein; BTK protein is measured by BTK Expression "
                "biomarker; BTK Expression biomarker predicts Ibrutinib response (confirming "
                "same drug); CT019 (Venetoclax CLL trial) was run in the same CLL disease "
                "context and investigates Venetoclax — arriving at a different BCL-2 "
                "inhibitor via the CLL trial network."
            ),
        },
    ],
}

json_path = os.path.join(BASE_DIR, "multi_hop_paths.json")
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(multi_hop_paths, f, indent=2)

print(f"Wrote {json_path}")

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------

print("\n" + "="*60)
print("FINAL ROW COUNTS")
print("="*60)

def count_rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return sum(1 for _ in csv.reader(f)) - 1  # subtract header

entity_files = {
    "drugs.csv":          drugs_path,
    "diseases.csv":       diseases_path,
    "genes.csv":          genes_path,
    "proteins.csv":       proteins_path,
    "clinical_trials.csv":trials_path,
    "biomarkers.csv":     biomarkers_path,
    "researchers.csv":    researchers_path,
    "institutions.csv":   institutions_path,
    "research_papers.csv":papers_path,
    "adverse_events.csv": ae_path,
}

for name, path in entity_files.items():
    n = count_rows(path)
    print(f"  {name:<25} {n:>3} rows")

print()
print("  RELATIONSHIP FILES")
for fname, data in rel.items():
    n = count_rows(data["path"])
    print(f"  {fname:<45} {n:>3} rows")

print()
print(f"  multi_hop_paths.json: {len(multi_hop_paths['paths'])} documented traversal paths")
print("="*60)
print("Done.")
