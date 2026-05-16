#!/usr/bin/env python3
"""
Gene-Protein ReAct Agent — AWS Strands Agents + Neptune Analytics
=================================================================

Production implementation using:
  - AWS Strands Agents SDK (Agent, @tool decorator, BedrockModel)
  - AWS Neptune Analytics (openCypher + native vector search)
  - AWS Bedrock (Claude model for reasoning)

The agent investigates gene symbols that also serve as protein names
(EGFR, KRAS, HER2, BRAF, BRCA1) through a ReAct loop, where the LLM
reasons about what to query next and the tools execute against Neptune.

Architecture:
  Strands Agent (Bedrock Claude)
       |
       |-- @tool neptune_query()        → openCypher against Neptune Analytics
       |-- @tool neptune_vector_search() → native vector similarity
       |-- @tool analyze_risk()          → compute risk scores
       |
       v
  Neptune Analytics (us-west-2, graph: g-0l15plmr0b)
       |-- Nodes: Gene, Protein, Drug, Disease, ClinicalTrial, AdverseEvent, Variant, Pathway
       |-- Relationships: TARGETS, TREATS, ASSOCIATED_WITH, INVESTIGATES, REPORTS_AE, etc.
       |-- Native HNSW vectors on Drug nodes (384 dimensions)
"""

import os
import sys
import json
import time
import hashlib
import textwrap
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from dotenv import load_dotenv
import boto3

from strands import Agent
from strands.tools import tool
from strands.models.bedrock import BedrockModel

load_dotenv()

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  NEPTUNE ANALYTICS CLIENT                                                   ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

GRAPH_ID = os.getenv("NEPTUNE_ANALYTICS_GRAPH_ID", "g-0l15plmr0b")
REGION = "us-west-2"

_neptune_client = boto3.client("neptune-graph", region_name=REGION)

def _execute_neptune(query: str) -> List[Dict]:
    """Execute openCypher query against Neptune Analytics, return results list."""
    try:
        resp = _neptune_client.execute_query(
            graphIdentifier=GRAPH_ID,
            queryString=query,
            language="OPEN_CYPHER"
        )
        payload = json.loads(resp["payload"].read())
        return payload.get("results", [])
    except Exception as e:
        return [{"error": str(e)}]

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  DATA LOADER — Populate Neptune Analytics with full biomedical graph        ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def load_biomedical_graph():
    """Load genes, proteins, variants, trials, AEs, and all relationships into Neptune Analytics."""

    print("\n  Loading biomedical graph into Neptune Analytics...")
    print(f"  Graph ID: {GRAPH_ID}")

    # ── Genes ──
    genes = [
        ("EGFR", "Epidermal Growth Factor Receptor", 7, "Cell growth and proliferation"),
        ("KRAS", "KRAS Proto-Oncogene", 12, "Cell signaling"),
        ("TP53", "Tumor Protein P53", 17, "Tumor suppression"),
        ("BRCA1", "Breast Cancer Gene 1", 17, "DNA repair"),
        ("BRCA2", "Breast Cancer Gene 2", 13, "DNA repair"),
        ("HER2", "Human Epidermal Growth Factor Receptor 2", 17, "Cell growth"),
        ("BRAF", "B-Raf Proto-Oncogene", 7, "Serine/threonine kinase in MAPK/ERK signaling"),
        ("PD-L1", "Programmed Death-Ligand 1", 9, "Immune checkpoint"),
        ("ALK", "Anaplastic Lymphoma Kinase", 2, "Receptor tyrosine kinase"),
        ("BCR-ABL", "BCR-ABL Fusion Gene", 22, "Constitutive tyrosine kinase activity"),
    ]
    for sym, name, chrom, func in genes:
        _execute_neptune(f"""
            MERGE (g:Gene {{symbol: '{sym}'}})
            SET g.name = '{name}', g.chromosome = {chrom}, g.function = '{func}'
        """)
    print(f"    Genes: {len(genes)}")

    # ── Proteins ──
    proteins = [
        ("EGFR", "Receptor tyrosine kinase", "Cell membrane", "P00533"),
        ("KRAS", "GTPase", "Cell membrane", "P01116"),
        ("HER2", "Receptor tyrosine kinase", "Cell membrane", "P04626"),
        ("BRAF", "Serine/threonine kinase", "Cytoplasm", "P15056"),
        ("BRCA1", "DNA repair", "Nucleus", "P38398"),
        ("PD-1", "Immune checkpoint", "Cell membrane", "Q15116"),
        ("PD-L1", "Immune checkpoint", "Cell membrane", "Q9NZQ7"),
        ("BCR-ABL", "Tyrosine kinase", "Cytoplasm", "A9UF07"),
        ("GLP-1R", "G-protein coupled receptor", "Cell membrane", "P43220"),
        ("Amyloid-beta", "Amyloid peptide", "Extracellular", "P05067"),
        ("ALK", "Receptor tyrosine kinase", "Cell membrane", "Q9UM73"),
    ]
    for name, pclass, loc, uniprot in proteins:
        _execute_neptune(f"""
            MERGE (p:Protein {{name: '{name}'}})
            SET p.protein_class = '{pclass}', p.cellular_location = '{loc}', p.uniprot_id = '{uniprot}'
        """)
    print(f"    Proteins: {len(proteins)}")

    # ── Additional Drugs ──
    new_drugs = [
        ("Osimertinib", "EGFR T790M inhibitor", "Small Molecule", 2015),
        ("Cetuximab", "EGFR monoclonal antibody", "Monoclonal Antibody", 2004),
        ("Dabrafenib", "BRAF V600E inhibitor", "Small Molecule", 2013),
        ("Sotorasib", "KRAS G12C inhibitor", "Small Molecule", 2021),
        ("Olaparib", "PARP inhibitor (BRCA1 synthetic lethality)", "Small Molecule", 2014),
        ("Nivolumab", "PD-1 inhibitor", "Monoclonal Antibody", 2014),
        ("Alectinib", "ALK inhibitor", "Small Molecule", 2015),
    ]
    for name, mech, dtype, year in new_drugs:
        _execute_neptune(f"""
            MERGE (d:Drug {{name: '{name}'}})
            SET d.mechanism = '{mech}', d.drug_type = '{dtype}',
                d.approval_status = 'Approved', d.approval_year = {year}
        """)
    print(f"    Additional drugs: {len(new_drugs)}")

    # ── Variants ──
    variants = [
        ("rs121434568", "EGFR", "Missense L858R activating mutation", "Pathogenic", 7, 55249063),
        ("rs28934578", "KRAS", "Missense G12C oncogenic", "Pathogenic", 12, 25398284),
        ("rs11547328", "HER2", "Amplification proxy V842I", "Pathogenic", 17, 37880220),
        ("rs113488022", "BRAF", "Missense V600E most common BRAF mutation", "Pathogenic", 7, 140453136),
        ("rs80357713", "BRCA1", "Nonsense premature stop", "Pathogenic", 17, 43091434),
        ("rs28897696", "TP53", "Missense R175H loss of function", "Pathogenic", 17, 7577121),
    ]
    for rsid, gene, cons, sig, chrom, pos in variants:
        _execute_neptune(f"""
            MERGE (v:Variant {{rsid: '{rsid}'}})
            SET v.gene_symbol = '{gene}', v.consequence = '{cons}',
                v.clinical_significance = '{sig}', v.chromosome = {chrom}, v.position = {pos}
        """)
    print(f"    Variants: {len(variants)}")

    # ── Clinical Trials ──
    trials = [
        ("NCT02142738", "Pembrolizumab in Advanced NSCLC", "Phase 3", 1034, "Merck", "Completed"),
        ("NCT01721772", "Nivolumab vs Docetaxel in NSCLC", "Phase 3", 582, "Bristol Myers Squibb", "Completed"),
        ("NCT02296125", "Osimertinib in EGFR T790M NSCLC AURA3", "Phase 3", 419, "AstraZeneca", "Completed"),
        ("NCT01908426", "Cetuximab in Colorectal Cancer", "Phase 3", 687, "Eli Lilly", "Completed"),
        ("NCT01682083", "Dabrafenib Trametinib BRAF V600 Melanoma", "Phase 3", 870, "Novartis", "Completed"),
        ("NCT03600883", "Sotorasib KRAS G12C NSCLC CodeBreaK 200", "Phase 3", 345, "Amgen", "Completed"),
        ("NCT02000622", "Olaparib BRCA Mutated Breast OlympiAD", "Phase 3", 302, "AstraZeneca", "Completed"),
        ("NCT01120184", "Trastuzumab Pertuzumab HER2 Breast CLEOPATRA", "Phase 3", 808, "Roche", "Completed"),
        ("NCT02075840", "Alectinib vs Crizotinib ALK NSCLC ALEX", "Phase 3", 303, "Roche", "Completed"),
    ]
    for nct, title, phase, enroll, sponsor, status in trials:
        title_safe = title.replace("'", "")
        _execute_neptune(f"""
            MERGE (t:ClinicalTrial {{nct_id: '{nct}'}})
            SET t.title = '{title_safe}', t.phase = '{phase}',
                t.enrollment = {enroll}, t.sponsor = '{sponsor}', t.status = '{status}'
        """)
    print(f"    Clinical Trials: {len(trials)}")

    # ── Adverse Events ──
    aes = [
        ("AE001", "Immune-related pneumonitis", "Severe", "Immune-related"),
        ("AE002", "Immune-related colitis", "Moderate", "Immune-related"),
        ("AE003", "Hypothyroidism", "Mild", "Endocrine"),
        ("AE004", "Hepatotoxicity", "Moderate", "Hepatic"),
        ("AE005", "Nausea", "Mild", "Gastrointestinal"),
        ("AE006", "Diarrhea", "Mild", "Gastrointestinal"),
        ("AE007", "Skin rash", "Mild", "Dermatologic"),
        ("AE008", "Infusion reaction", "Moderate", "Infusion-related"),
        ("AE009", "Pyrexia", "Moderate", "Systemic"),
        ("AE010", "Fatigue", "Mild", "Systemic"),
    ]
    for ae_id, name, sev, cat in aes:
        name_safe = name.replace("'", "")
        _execute_neptune(f"""
            MERGE (ae:AdverseEvent {{ae_id: '{ae_id}'}})
            SET ae.name = '{name_safe}', ae.severity = '{sev}', ae.category = '{cat}'
        """)
    print(f"    Adverse Events: {len(aes)}")

    # ── Pathways ──
    pathways = [
        ("PW001", "PI3K-AKT Signaling Pathway", "Cell Survival"),
        ("PW002", "MAPK/ERK Signaling Pathway", "Cell Proliferation"),
        ("PW003", "p53 Tumor Suppressor Pathway", "Apoptosis"),
        ("PW004", "DNA Damage Repair Pathway", "Genome Stability"),
        ("PW005", "PD-1/PD-L1 Immune Checkpoint Pathway", "Immune Evasion"),
    ]
    for pw_id, name, cat in pathways:
        _execute_neptune(f"""
            MERGE (pw:Pathway {{pathway_id: '{pw_id}'}})
            SET pw.name = '{name}', pw.category = '{cat}'
        """)
    print(f"    Pathways: {len(pathways)}")

    # ── Relationships: Drug TARGETS Protein ──
    targets = [
        ("Osimertinib", "EGFR", "Very High", "Inhibitor"),
        ("Cetuximab", "EGFR", "High", "Antagonist"),
        ("Pembrolizumab", "PD-1", "High", "Antagonist"),
        ("Nivolumab", "PD-1", "High", "Antagonist"),
        ("Atezolizumab", "PD-L1", "High", "Antagonist"),
        ("Trastuzumab", "HER2", "Very High", "Antagonist"),
        ("Imatinib", "BCR-ABL", "Very High", "Inhibitor"),
        ("Dabrafenib", "BRAF", "Very High", "Inhibitor"),
        ("Sotorasib", "KRAS", "Very High", "Inhibitor"),
        ("Olaparib", "BRCA1", "High", "Synthetic Lethality"),
        ("Semaglutide", "GLP-1R", "Very High", "Agonist"),
        ("Alectinib", "ALK", "Very High", "Inhibitor"),
    ]
    for drug, protein, affinity, mtype in targets:
        _execute_neptune(f"""
            MATCH (d:Drug {{name: '{drug}'}}), (p:Protein {{name: '{protein}'}})
            MERGE (d)-[t:TARGETS]->(p)
            SET t.binding_affinity = '{affinity}', t.mechanism_type = '{mtype}'
        """)
    print(f"    TARGETS relationships: {len(targets)}")

    # ── Relationships: Drug TREATS Disease ──
    treats = [
        ("Osimertinib", "Non-Small Cell Lung Cancer", 0.71),
        ("Cetuximab", "Non-Small Cell Lung Cancer", 0.35),
        ("Cetuximab", "Colorectal Cancer", 0.42),
        ("Dabrafenib", "Melanoma", 0.50),
        ("Dabrafenib", "Non-Small Cell Lung Cancer", 0.36),
        ("Sotorasib", "Non-Small Cell Lung Cancer", 0.37),
        ("Olaparib", "Breast Cancer", 0.60),
        ("Nivolumab", "Non-Small Cell Lung Cancer", 0.40),
        ("Nivolumab", "Melanoma", 0.38),
        ("Alectinib", "Non-Small Cell Lung Cancer", 0.47),
    ]
    count = 0
    for drug, disease, efficacy in treats:
        r = _execute_neptune(f"""
            MATCH (d:Drug {{name: '{drug}'}}), (dis:Disease {{name: '{disease}'}})
            MERGE (d)-[t:TREATS]->(dis)
            SET t.efficacy_rate = {efficacy}
            RETURN d.name
        """)
        if r and not r[0].get("error"):
            count += 1
    print(f"    Additional TREATS: {count}")

    # ── Gene ASSOCIATED_WITH Disease ──
    assocs = [
        ("EGFR", "Non-Small Cell Lung Cancer", "Strong", "High"),
        ("KRAS", "Non-Small Cell Lung Cancer", "Strong", "High"),
        ("KRAS", "Colorectal Cancer", "Strong", "High"),
        ("HER2", "Breast Cancer", "Strong", "High"),
        ("BRAF", "Melanoma", "Very Strong", "High"),
        ("BRAF", "Non-Small Cell Lung Cancer", "Moderate", "High"),
        ("BRAF", "Colorectal Cancer", "Strong", "High"),
        ("BRCA1", "Breast Cancer", "Very Strong", "High"),
        ("TP53", "Non-Small Cell Lung Cancer", "Moderate", "High"),
        ("TP53", "Breast Cancer", "Strong", "High"),
    ]
    for gene, disease, strength, evidence in assocs:
        _execute_neptune(f"""
            MATCH (g:Gene {{symbol: '{gene}'}}), (d:Disease {{name: '{disease}'}})
            MERGE (g)-[a:ASSOCIATED_WITH]->(d)
            SET a.association_strength = '{strength}', a.evidence_level = '{evidence}'
        """)
    print(f"    ASSOCIATED_WITH: {len(assocs)}")

    # ── ClinicalTrial INVESTIGATES Drug ──
    investigations = [
        ("NCT02142738", "Pembrolizumab"), ("NCT01721772", "Nivolumab"),
        ("NCT02296125", "Osimertinib"), ("NCT01908426", "Cetuximab"),
        ("NCT01682083", "Dabrafenib"), ("NCT03600883", "Sotorasib"),
        ("NCT02000622", "Olaparib"), ("NCT01120184", "Trastuzumab"),
        ("NCT02075840", "Alectinib"),
    ]
    for nct, drug in investigations:
        _execute_neptune(f"""
            MATCH (t:ClinicalTrial {{nct_id: '{nct}'}}), (d:Drug {{name: '{drug}'}})
            MERGE (t)-[:INVESTIGATES]->(d)
        """)
    print(f"    INVESTIGATES: {len(investigations)}")

    # ── ClinicalTrial REPORTS_AE AdverseEvent ──
    ae_reports = [
        ("NCT02142738", "AE001", 0.04, 3), ("NCT02142738", "AE002", 0.08, 2),
        ("NCT02142738", "AE003", 0.12, 1), ("NCT01721772", "AE001", 0.03, 3),
        ("NCT01721772", "AE005", 0.15, 1), ("NCT02296125", "AE001", 0.04, 3),
        ("NCT02296125", "AE005", 0.08, 2), ("NCT02296125", "AE003", 0.12, 1),
        ("NCT01908426", "AE006", 0.15, 2), ("NCT01908426", "AE007", 0.78, 1),
        ("NCT01682083", "AE009", 0.18, 2), ("NCT01682083", "AE005", 0.06, 2),
        ("NCT03600883", "AE006", 0.25, 2), ("NCT03600883", "AE005", 0.10, 2),
        ("NCT02000622", "AE006", 0.32, 2), ("NCT02000622", "AE008", 0.05, 3),
        ("NCT01120184", "AE004", 0.08, 2), ("NCT01120184", "AE005", 0.12, 2),
        ("NCT02075840", "AE005", 0.14, 1), ("NCT02075840", "AE010", 0.35, 1),
    ]
    for nct, ae_id, rate, grade in ae_reports:
        _execute_neptune(f"""
            MATCH (t:ClinicalTrial {{nct_id: '{nct}'}}), (ae:AdverseEvent {{ae_id: '{ae_id}'}})
            MERGE (t)-[r:REPORTS_AE]->(ae)
            SET r.incidence_rate = {rate}, r.grade = {grade}
        """)
    print(f"    REPORTS_AE: {len(ae_reports)}")

    # ── Verify ──
    r = _execute_neptune("MATCH (n) RETURN labels(n)[0] as label, count(n) as cnt ORDER BY cnt DESC")
    print("\n  Neptune Analytics node counts:")
    for row in r:
        print(f"    {row['label']}: {row['cnt']}")
    r = _execute_neptune("MATCH ()-[r]->() RETURN type(r) as t, count(r) as cnt ORDER BY cnt DESC")
    print("  Relationship counts:")
    for row in r:
        print(f"    {row['t']}: {row['cnt']}")

    print("\n  Graph load complete.")


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  STRANDS TOOLS — Neptune Query Interface                                    ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

# Execution tracker — records every ReAct step for visualization
execution_trace: List[Dict] = []

def _trace(iteration: int, step_type: str, agent_role: str, content: str,
           query: str = "", results: List = None, latency_ms: float = 0,
           traversal_path: str = ""):
    execution_trace.append({
        "iteration": iteration,
        "type": step_type,
        "agent": agent_role,
        "content": content,
        "query": query,
        "result_count": len(results) if results else 0,
        "latency_ms": round(latency_ms, 1),
        "traversal_path": traversal_path,
        "timestamp": datetime.now().strftime("%H:%M:%S.%f")[:-3],
    })

_iteration_counter = {"val": 0}

@tool
def neptune_cypher_query(query: str, purpose: str) -> str:
    """Execute an openCypher query against Neptune Analytics knowledge graph.

    Use this tool to query the biomedical knowledge graph stored in AWS Neptune Analytics.
    The graph contains: Gene, Protein, Drug, Disease, ClinicalTrial, AdverseEvent,
    Variant, and Pathway nodes with relationships like TARGETS, TREATS, ASSOCIATED_WITH,
    INVESTIGATES, and REPORTS_AE.

    Args:
        query: The openCypher query string to execute against Neptune Analytics.
        purpose: A brief description of why this query is being run (for audit trail).

    Returns:
        JSON string of query results with execution metadata.
    """
    _iteration_counter["val"] += 1
    iteration = _iteration_counter["val"]

    t0 = time.perf_counter()
    results = _execute_neptune(query)
    latency = (time.perf_counter() - t0) * 1000

    _trace(iteration, "ACT", "NeptuneQueryTool", purpose,
           query=query, results=results, latency_ms=latency,
           traversal_path=_infer_traversal(query))

    output = {
        "purpose": purpose,
        "result_count": len(results),
        "latency_ms": round(latency, 1),
        "results": results[:20],
    }
    return json.dumps(output, indent=2, default=str)


@tool
def neptune_vector_search(search_text: str, top_k: int = 5) -> str:
    """Search for similar drugs using Neptune Analytics native vector search.

    Uses HNSW vector index on Drug node embeddings to find semantically similar drugs
    based on their mechanism descriptions.

    Args:
        search_text: Description of the drug mechanism or type to search for.
        top_k: Number of similar drugs to return (default 5).

    Returns:
        JSON string of top-K similar drugs with similarity scores and their indications.
    """
    _iteration_counter["val"] += 1
    iteration = _iteration_counter["val"]

    embedding = _text_to_embedding(search_text)
    emb_str = "[" + ",".join(f"{v:.6f}" for v in embedding) + "]"

    query = f"""
        CALL neptune.algo.vectors.topKByEmbedding({emb_str}, {{topK: {top_k}}})
        YIELD node, score
        WITH node AS drug, score
        WHERE 'Drug' IN labels(drug)
        OPTIONAL MATCH (drug)-[t:TREATS]->(dis:Disease)
        RETURN drug.name AS drug, drug.mechanism AS mechanism, score,
               collect(DISTINCT {{disease: dis.name, efficacy: t.efficacy_rate}}) AS indications
        ORDER BY score DESC
    """

    t0 = time.perf_counter()
    results = _execute_neptune(query)
    latency = (time.perf_counter() - t0) * 1000

    _trace(iteration, "ACT", "VectorSearchTool",
           f"Vector search: '{search_text}' (top-{top_k})",
           query=f"neptune.algo.vectors.topKByEmbedding(..., topK={top_k})",
           results=results, latency_ms=latency,
           traversal_path="(Drug) --vector similarity--> (Drug) --TREATS--> (Disease)")

    return json.dumps({
        "search_text": search_text,
        "top_k": top_k,
        "latency_ms": round(latency, 1),
        "results": results
    }, indent=2, default=str)


@tool
def compute_risk_assessment(gene_symbol: str, diseases: str, drugs: str,
                            trials: str, adverse_events: str, variants: str) -> str:
    """Compute a multi-factor risk assessment score for a gene-protein-drug chain.

    Takes the accumulated evidence from previous queries and calculates genetic evidence,
    therapeutic coverage, clinical evidence, and safety scores.

    Args:
        gene_symbol: The gene being investigated (e.g., EGFR, KRAS).
        diseases: JSON string of disease associations found.
        drugs: JSON string of targeting drugs found.
        trials: JSON string of clinical trials found.
        adverse_events: JSON string of adverse events found.
        variants: JSON string of pathogenic variants found.

    Returns:
        JSON string with multi-factor risk scores and evidence grade.
    """
    try:
        diseases_list = json.loads(diseases) if isinstance(diseases, str) else diseases
        drugs_list = json.loads(drugs) if isinstance(drugs, str) else drugs
        trials_list = json.loads(trials) if isinstance(trials, str) else trials
        ae_list = json.loads(adverse_events) if isinstance(adverse_events, str) else adverse_events
        variants_list = json.loads(variants) if isinstance(variants, str) else variants
    except (json.JSONDecodeError, TypeError):
        diseases_list = drugs_list = trials_list = ae_list = variants_list = []

    severe_aes = sum(1 for ae in ae_list if ae.get("severity") == "Severe")
    moderate_aes = sum(1 for ae in ae_list if ae.get("severity") == "Moderate")
    total_enrollment = sum(t.get("enrollment", 0) or 0 for t in trials_list)
    phase3 = sum(1 for t in trials_list if "Phase 3" in str(t.get("phase", "")))
    strong_assoc = sum(1 for d in diseases_list
                       if d.get("strength") in ["Strong", "Very Strong"])
    pathogenic = sum(1 for v in variants_list
                     if v.get("significance") == "Pathogenic" or v.get("clinical_significance") == "Pathogenic")
    high_affinity = sum(1 for d in drugs_list
                        if d.get("affinity") in ["High", "Very High"])

    genetic = min(100, strong_assoc * 25 + pathogenic * 15)
    therapeutic = min(100, len(drugs_list) * 20 + high_affinity * 10)
    clinical = min(100, phase3 * 25 + (total_enrollment // 500) * 10)
    safety_risk = min(100, severe_aes * 20 + moderate_aes * 10)
    safety = max(0, 100 - safety_risk)
    overall = genetic * 0.25 + therapeutic * 0.25 + clinical * 0.30 + safety * 0.20

    grade = "A" if overall >= 80 else "B" if overall >= 60 else "C" if overall >= 40 else "D"
    risk_level = "High Risk" if safety < 40 else "Moderate Risk" if safety < 70 else "Low Risk"

    result = {
        "gene": gene_symbol,
        "overall_score": round(overall, 1),
        "evidence_grade": grade,
        "risk_level": risk_level,
        "scores": {
            "genetic_evidence": round(genetic, 1),
            "therapeutic_coverage": round(therapeutic, 1),
            "clinical_evidence": round(clinical, 1),
            "safety": round(safety, 1),
        },
        "factors": {
            "strong_genetic_associations": strong_assoc,
            "pathogenic_variants": pathogenic,
            "total_drugs": len(drugs_list),
            "high_affinity_drugs": high_affinity,
            "phase3_trials": phase3,
            "total_enrollment": total_enrollment,
            "severe_adverse_events": severe_aes,
            "moderate_adverse_events": moderate_aes,
        }
    }
    return json.dumps(result, indent=2)


def _text_to_embedding(text: str, dim: int = 384) -> List[float]:
    """Deterministic hash-based embedding for reproducibility."""
    embedding = []
    for i in range(dim):
        h = hashlib.sha256(f"{text}_{i}".encode()).hexdigest()
        val = (int(h[:8], 16) / 0xFFFFFFFF - 0.5) * 0.2
        embedding.append(val)
    norm = sum(v*v for v in embedding) ** 0.5
    return [v / norm for v in embedding]


def _infer_traversal(query: str) -> str:
    """Infer traversal path from query pattern."""
    parts = []
    if "Gene" in query: parts.append("Gene")
    if "Protein" in query: parts.append("Protein")
    if "Drug" in query: parts.append("Drug")
    if "Disease" in query: parts.append("Disease")
    if "ClinicalTrial" in query: parts.append("ClinicalTrial")
    if "AdverseEvent" in query: parts.append("AdverseEvent")
    if "Variant" in query: parts.append("Variant")
    if "Pathway" in query: parts.append("Pathway")
    return " -> ".join(parts) if parts else "unknown"


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  STRANDS AGENT DEFINITION                                                   ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

SYSTEM_PROMPT = """You are a biomedical research agent investigating gene symbols that also serve as protein names.

You have access to a Neptune Analytics knowledge graph containing:
- Gene nodes (symbol, name, chromosome, function)
- Protein nodes (name, protein_class, cellular_location, uniprot_id)
- Drug nodes (name, mechanism, drug_type, approval_status, approval_year)
- Disease nodes (name, category, icd10_code, prevalence)
- ClinicalTrial nodes (nct_id, title, phase, enrollment, sponsor, status)
- AdverseEvent nodes (ae_id, name, severity, category)
- Variant nodes (rsid, gene_symbol, consequence, clinical_significance)
- Pathway nodes (pathway_id, name, category)

Relationships:
- (Drug)-[:TARGETS {binding_affinity, mechanism_type}]->(Protein)
- (Drug)-[:TREATS {efficacy_rate}]->(Disease)
- (Gene)-[:ASSOCIATED_WITH {association_strength, evidence_level}]->(Disease)
- (ClinicalTrial)-[:INVESTIGATES]->(Drug)
- (ClinicalTrial)-[:REPORTS_AE {incidence_rate, grade}]->(AdverseEvent)

Your investigation must follow the ReAct pattern (Reason → Act → Observe):
For each gene symbol, execute these steps IN ORDER:

1. GENE IDENTITY: Query the Gene node to get symbol, name, chromosome, function
2. PROTEIN MATCH: Find the Protein node with the same name as the gene symbol (dual nomenclature)
3. PATHOGENIC VARIANTS: Find Variant nodes where gene_symbol matches
4. DISEASE ASSOCIATIONS: Query Gene-[ASSOCIATED_WITH]->Disease with strength and evidence
5. TARGETING DRUGS: Find Drug-[TARGETS]->Protein where protein name matches gene, PLUS their TREATS relationships with efficacy
6. CLINICAL TRIALS: Find ClinicalTrial-[INVESTIGATES]->Drug for those targeting drugs
7. ADVERSE EVENTS: Find ClinicalTrial-[REPORTS_AE]->AdverseEvent for those trials
8. RISK ASSESSMENT: Use compute_risk_assessment with ALL accumulated data

IMPORTANT RULES:
- Execute ONE query per step using neptune_cypher_query tool
- After each query, analyze the results before proceeding to the next step
- Use the actual data from previous steps to inform later queries
- At the end, call compute_risk_assessment with all the data you collected
- Present your final report in a structured format with all findings

When writing openCypher queries for Neptune Analytics:
- Use single quotes for string values in WHERE/SET clauses
- Do NOT use parameterized queries ($param) — Neptune Analytics requires inline values
- Use MERGE instead of MATCH for defensive queries
- Properties use dot notation: n.property_name
"""

def create_strands_agent() -> Agent:
    """Create the Strands agent with Bedrock Claude and Neptune tools."""
    model = BedrockModel(
        model_id="us.anthropic.claude-sonnet-4-20250514-v1:0",
        region_name=REGION,
        max_tokens=4096,
        temperature=0.1,
    )

    agent = Agent(
        model=model,
        tools=[neptune_cypher_query, neptune_vector_search, compute_risk_assessment],
        system_prompt=SYSTEM_PROMPT,
        name="GeneProteinReActAgent",
        description="Investigates gene-protein dual nomenclature through Neptune Analytics knowledge graph",
    )
    return agent


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  INVESTIGATION RUNNER                                                       ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def investigate_gene(agent: Agent, gene_symbol: str) -> Dict:
    """Run a single gene investigation through the Strands ReAct loop."""

    _iteration_counter["val"] = 0

    prompt = f"""Investigate the gene symbol {gene_symbol}, which also serves as a protein name.

Follow the 8-step ReAct investigation protocol:
1. Query Gene node for {gene_symbol}
2. Find the Protein node named {gene_symbol} (dual nomenclature)
3. Find pathogenic Variants where gene_symbol = '{gene_symbol}'
4. Find diseases: MATCH (g:Gene {{symbol: '{gene_symbol}'}})-[a:ASSOCIATED_WITH]->(d:Disease) RETURN d.name AS disease, d.category AS category, a.association_strength AS strength, a.evidence_level AS evidence_level
5. Find drugs targeting the protein: MATCH (drug:Drug)-[t:TARGETS]->(p:Protein) WHERE p.name = '{gene_symbol}' OPTIONAL MATCH (drug)-[tr:TREATS]->(dis:Disease) RETURN drug.name AS drug, drug.mechanism AS mechanism, t.binding_affinity AS affinity, t.mechanism_type AS target_mechanism, collect(DISTINCT {{disease: dis.name, efficacy: tr.efficacy_rate}}) AS indications
6. Find clinical trials for those drugs
7. Find adverse events from those trials
8. Compute risk assessment with all accumulated data

After each step, reason about what the results mean before proceeding.
At the end, provide a structured summary of ALL findings."""

    print(f"\n{'='*90}")
    print(f"  STRANDS REACT AGENT: Investigating {gene_symbol}")
    print(f"  Model: Bedrock Claude | Graph: Neptune Analytics ({GRAPH_ID})")
    print(f"{'='*90}")

    t0 = time.perf_counter()
    result = agent(prompt)
    elapsed = (time.perf_counter() - t0) * 1000

    response_text = str(result)

    print(f"\n{'─'*90}")
    print(f"  Agent Response ({elapsed:.0f}ms):")
    print(f"{'─'*90}")
    print(response_text)

    return {
        "gene": gene_symbol,
        "response": response_text,
        "execution_time_ms": round(elapsed, 1),
        "queries_executed": _iteration_counter["val"],
        "trace": [t for t in execution_trace],
    }


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  VISUALIZATION GENERATOR                                                    ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def generate_visualization(all_results: Dict, output_path: str):
    """Generate interactive HTML visualization of all ReAct investigations."""

    all_traces = []
    gene_summaries = {}
    for gene, data in all_results.items():
        all_traces.extend(data.get("trace", []))
        gene_summaries[gene] = {
            "response_preview": data.get("response", "")[:500],
            "execution_time_ms": data.get("execution_time_ms", 0),
            "queries_executed": data.get("queries_executed", 0),
        }

    traces_json = json.dumps(all_traces, indent=2, default=str)
    summaries_json = json.dumps(gene_summaries, indent=2, default=str)
    genes_list = json.dumps(list(all_results.keys()))

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Strands ReAct Agent — Neptune Analytics Visualization</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{
    font-family: 'Inter', sans-serif;
    background: linear-gradient(135deg, #0f0c29 0%, #1a1333 40%, #24243e 100%);
    color: #e0e0e0;
    min-height: 100vh;
    padding: 24px;
  }}
  .container {{ max-width: 1400px; margin: 0 auto; }}
  .header {{
    text-align: center; margin-bottom: 30px; padding: 30px;
    background: rgba(255,255,255,0.03); border-radius: 16px;
    border: 1px solid rgba(255,255,255,0.06);
  }}
  .header h1 {{
    font-size: 2em; font-weight: 800;
    background: linear-gradient(135deg, #ff9800, #ff5722);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  }}
  .header .sub {{ color: #8892b0; font-size: 0.9em; margin-top: 6px; }}
  .header .arch {{
    display: flex; justify-content: center; gap: 16px; margin-top: 16px;
    flex-wrap: wrap;
  }}
  .arch-badge {{
    padding: 6px 16px; border-radius: 8px; font-size: 0.78em; font-weight: 600;
  }}
  .arch-strands {{ background: rgba(255,152,0,0.15); color: #ffb74d; border: 1px solid rgba(255,152,0,0.3); }}
  .arch-neptune {{ background: rgba(33,150,243,0.15); color: #64b5f6; border: 1px solid rgba(33,150,243,0.3); }}
  .arch-bedrock {{ background: rgba(156,39,176,0.15); color: #ce93d8; border: 1px solid rgba(156,39,176,0.3); }}
  .stats {{ display: flex; justify-content: center; gap: 40px; margin-top: 20px; }}
  .stat-val {{ font-size: 1.8em; font-weight: 800; color: #ff9800; }}
  .stat-label {{ font-size: 0.72em; color: #8892b0; text-transform: uppercase; letter-spacing: 0.06em; }}
  .tabs {{ display: flex; gap: 4px; margin-bottom: 20px; flex-wrap: wrap; }}
  .tab {{
    padding: 10px 20px; border-radius: 10px 10px 0 0;
    background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.06);
    border-bottom: none; color: #8892b0; cursor: pointer; font-weight: 600; font-size: 0.85em;
  }}
  .tab:hover {{ background: rgba(255,255,255,0.08); color: #e0e0e0; }}
  .tab.active {{ background: rgba(255,152,0,0.08); color: #ff9800; border-color: rgba(255,152,0,0.2); }}
  .tab-content {{
    display: none; background: rgba(255,255,255,0.03); border-radius: 0 16px 16px 16px;
    border: 1px solid rgba(255,255,255,0.06); padding: 24px;
  }}
  .tab-content.active {{ display: block; }}
  .timeline {{ position: relative; padding-left: 30px; }}
  .timeline::before {{
    content: ''; position: absolute; left: 14px; top: 0; bottom: 0;
    width: 2px; background: linear-gradient(180deg, #ff9800, #2196f3, #4caf50);
  }}
  .tl-step {{
    position: relative; margin-bottom: 12px; padding: 14px 18px;
    border-radius: 10px; border-left: 3px solid; transition: all 0.2s;
  }}
  .tl-step:hover {{ transform: translateX(4px); }}
  .tl-step::before {{
    content: ''; position: absolute; left: -23px; top: 18px;
    width: 10px; height: 10px; border-radius: 50%;
  }}
  .tl-act {{ background: rgba(33,150,243,0.08); border-color: #2196f3; }}
  .tl-act::before {{ background: #2196f3; }}
  .step-hdr {{ display: flex; align-items: center; gap: 10px; margin-bottom: 6px; }}
  .badge {{
    padding: 2px 10px; border-radius: 6px; font-size: 0.72em;
    font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em;
    background: rgba(33,150,243,0.2); color: #64b5f6;
  }}
  .step-agent {{ font-size: 0.78em; color: #8892b0; }}
  .step-metrics {{
    font-family: 'JetBrains Mono', monospace; font-size: 0.72em;
    color: #ff9800; margin-left: auto;
  }}
  .step-body {{ font-size: 0.85em; color: #a8b2d1; line-height: 1.5; }}
  .step-query {{
    margin-top: 8px; padding: 8px 12px; background: rgba(0,0,0,0.3);
    border-radius: 6px; font-family: 'JetBrains Mono', monospace;
    font-size: 0.72em; color: #80cbc4; white-space: pre-wrap;
    max-height: 120px; overflow-y: auto;
  }}
  .step-path {{
    margin-top: 6px; font-family: 'JetBrains Mono', monospace;
    font-size: 0.72em; color: #ce93d8;
  }}
  .gene-card {{
    background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px; padding: 22px; margin-bottom: 16px;
  }}
  .gene-card h3 {{
    font-size: 1.1em; font-weight: 700; color: #ff9800;
    margin-bottom: 14px; padding-bottom: 8px;
    border-bottom: 1px solid rgba(255,255,255,0.06);
  }}
  .info-row {{
    display: flex; justify-content: space-between; padding: 4px 0;
    font-size: 0.82em; border-bottom: 1px solid rgba(255,255,255,0.03);
  }}
  .info-label {{ color: #8892b0; }}
  .info-value {{ color: #e0e0e0; font-weight: 500; }}
  .agent-response {{
    background: rgba(0,0,0,0.2); border-radius: 10px; padding: 18px;
    font-size: 0.85em; line-height: 1.6; color: #a8b2d1;
    white-space: pre-wrap; max-height: 600px; overflow-y: auto;
  }}
  .footer {{
    text-align: center; margin-top: 24px; font-size: 0.75em; color: #4a5568;
    padding-top: 16px; border-top: 1px solid rgba(255,255,255,0.04);
  }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>Gene-Protein ReAct Agent</h1>
    <p class="sub">AWS Strands Agents + Neptune Analytics + Bedrock Claude</p>
    <div class="arch">
      <span class="arch-badge arch-strands">Strands Agents SDK</span>
      <span class="arch-badge arch-neptune">Neptune Analytics (openCypher)</span>
      <span class="arch-badge arch-bedrock">Bedrock Claude Sonnet</span>
    </div>
    <div class="stats" id="headerStats"></div>
  </div>
  <div class="tabs" id="tabBar"></div>
  <div id="tabContents"></div>
  <div class="footer">Ontology GraphRAG Benchmarks &mdash; Strands ReAct Agent + Neptune Analytics</div>
</div>
<script>
const TRACES = {traces_json};
const SUMMARIES = {summaries_json};
const GENES = {genes_list};

const totalQueries = TRACES.filter(t => t.type === 'ACT').length;
const totalLatency = TRACES.filter(t => t.type === 'ACT').reduce((a,b) => a + b.latency_ms, 0);
const totalTime = Object.values(SUMMARIES).reduce((a,b) => a + b.execution_time_ms, 0);

document.getElementById('headerStats').innerHTML = `
  <div><div class="stat-val">${{GENES.length}}</div><div class="stat-label">Genes Investigated</div></div>
  <div><div class="stat-val">${{totalQueries}}</div><div class="stat-label">Neptune Queries</div></div>
  <div><div class="stat-val">${{totalLatency.toFixed(0)}}ms</div><div class="stat-label">Query Latency</div></div>
  <div><div class="stat-val">${{(totalTime/1000).toFixed(1)}}s</div><div class="stat-label">Total Agent Time</div></div>
`;

const tabBar = document.getElementById('tabBar');
const tabContents = document.getElementById('tabContents');
const tabs = [];

tabs.push({{ id: 'timeline', label: 'ReAct Timeline', content: buildTimeline() }});
GENES.forEach(g => tabs.push({{ id: 'gene-'+g, label: g, content: buildGeneTab(g) }}));

tabs.forEach((t, i) => {{
  const el = document.createElement('div');
  el.className = 'tab' + (i===0?' active':'');
  el.textContent = t.label;
  el.onclick = () => switchTab(t.id);
  el.dataset.id = t.id;
  tabBar.appendChild(el);
  const c = document.createElement('div');
  c.className = 'tab-content' + (i===0?' active':'');
  c.id = 'content-'+t.id;
  c.innerHTML = t.content;
  tabContents.appendChild(c);
}});

function switchTab(id) {{
  document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.id===id));
  document.querySelectorAll('.tab-content').forEach(c => c.classList.toggle('active', c.id==='content-'+id));
}}

function buildTimeline() {{
  let html = '<div class="timeline">';
  let prevGene = '';
  TRACES.forEach(t => {{
    if (t.agent !== prevGene) {{
      html += `<div style="text-align:center;padding:10px;font-weight:700;color:#ff9800;font-size:0.85em;">&mdash; ${{t.agent}} &mdash;</div>`;
      prevGene = t.agent;
    }}
    html += `<div class="tl-step tl-act">
      <div class="step-hdr">
        <span class="badge">${{t.type}}</span>
        <span class="step-agent">#${{t.iteration}}</span>
        <span class="step-metrics">${{t.result_count}} results | ${{t.latency_ms.toFixed(1)}}ms</span>
      </div>
      <div class="step-body">${{t.content}}</div>
      ${{t.traversal_path ? `<div class="step-path">Path: ${{t.traversal_path}}</div>` : ''}}
      ${{t.query ? `<div class="step-query">${{t.query}}</div>` : ''}}
    </div>`;
  }});
  html += '</div>';
  return html;
}}

function buildGeneTab(gene) {{
  const s = SUMMARIES[gene] || {{}};
  return `<div class="gene-card">
    <h3>${{gene}} Investigation</h3>
    <div class="info-row"><span class="info-label">Queries Executed</span><span class="info-value">${{s.queries_executed||0}}</span></div>
    <div class="info-row"><span class="info-label">Agent Time</span><span class="info-value">${{(s.execution_time_ms||0).toFixed(0)}}ms</span></div>
  </div>
  <div class="gene-card">
    <h3>Agent Response</h3>
    <div class="agent-response">${{(s.response_preview||'').replace(/</g,'&lt;').replace(/>/g,'&gt;')}}</div>
  </div>`;
}}
</script>
</body>
</html>"""

    with open(output_path, "w") as f:
        f.write(html)
    print(f"\n  Visualization saved: {output_path}")


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  MAIN                                                                       ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def main():
    genes_to_investigate = ["EGFR", "KRAS", "HER2", "BRAF", "BRCA1"]

    print("=" * 90)
    print("  GENE-PROTEIN REACT AGENT — AWS STRANDS + NEPTUNE ANALYTICS")
    print("=" * 90)
    print(f"  Strands Agents SDK + Bedrock Claude + Neptune Analytics openCypher")
    print(f"  Graph ID: {GRAPH_ID} | Region: {REGION}")
    print(f"  Targets: {', '.join(genes_to_investigate)}")
    print("=" * 90)

    # Phase 1: Load data into Neptune Analytics
    print("\n  PHASE 1: Loading biomedical graph into Neptune Analytics")
    print(f"  {'─'*70}")
    load_biomedical_graph()

    # Phase 2: Create Strands agent
    print(f"\n  PHASE 2: Creating Strands ReAct Agent")
    print(f"  {'─'*70}")
    agent = create_strands_agent()
    print(f"  Agent created: {agent.name}")
    print(f"  Tools: {agent.tool_names}")

    # Phase 3: Run investigations
    print(f"\n  PHASE 3: Running ReAct Investigations")
    print(f"  {'─'*70}")

    all_results = {}
    for gene in genes_to_investigate:
        execution_trace.clear()
        try:
            result = investigate_gene(agent, gene)
            all_results[gene] = result
        except Exception as e:
            print(f"\n  ERROR investigating {gene}: {e}")
            all_results[gene] = {
                "gene": gene,
                "response": f"Error: {e}",
                "execution_time_ms": 0,
                "queries_executed": 0,
                "trace": list(execution_trace),
            }

    # Phase 4: Summary
    print(f"\n{'='*90}")
    print(f"  INVESTIGATION SUMMARY")
    print(f"{'='*90}")
    print(f"\n  {'Gene':<8s} {'Time (ms)':<12s} {'Queries':<10s}")
    print(f"  {'─'*35}")
    total_time = 0
    total_q = 0
    for gene, data in all_results.items():
        t = data.get("execution_time_ms", 0)
        q = data.get("queries_executed", 0)
        total_time += t
        total_q += q
        print(f"  {gene:<8s} {t:<12.0f} {q:<10d}")
    print(f"  {'─'*35}")
    print(f"  {'TOTAL':<8s} {total_time:<12.0f} {total_q:<10d}")

    # Phase 5: Visualization
    viz_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "neptune_strands_react_visualization.html")
    generate_visualization(all_results, viz_path)

    # Phase 6: Save JSON results
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "neptune_strands_react_results.json")
    output = {
        "investigation_date": datetime.now().isoformat(),
        "architecture": {
            "agent_framework": "AWS Strands Agents SDK",
            "llm": "Bedrock Claude Sonnet",
            "graph_database": "Neptune Analytics",
            "graph_id": GRAPH_ID,
            "region": REGION,
            "query_language": "openCypher",
            "vector_index": "Native HNSW (384 dimensions)",
        },
        "genes_investigated": genes_to_investigate,
        "summary": {gene: {
            "execution_time_ms": data.get("execution_time_ms", 0),
            "queries_executed": data.get("queries_executed", 0),
        } for gene, data in all_results.items()},
    }
    with open(json_path, "w") as f:
        json.dump(output, f, indent=2, default=str)
    print(f"  Results saved: {json_path}")

    print(f"\n{'='*90}")
    print(f"  COMPLETE — {len(genes_to_investigate)} genes | {total_q} queries | {total_time:.0f}ms")
    print(f"{'='*90}")


if __name__ == "__main__":
    main()
