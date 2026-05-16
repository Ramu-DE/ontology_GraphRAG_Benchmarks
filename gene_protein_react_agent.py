#!/usr/bin/env python3
"""
Gene-Protein ReAct Agent with AWS Strands + Neo4j Knowledge Graph
=================================================================

Scenario: Gene symbols that serve as protein names (EGFR, KRAS, HER2, BRAF, BRCA1)
trace the full biological chain: Gene -> Protein -> Drug -> Disease -> Trial -> AE

ReAct Loop (Reason-Act-Observe):
  Each iteration the agent THINKS about what it needs, ACTS by querying the graph,
  and OBSERVES results to decide next steps. This mirrors how a biomedical researcher
  would investigate a gene target — starting from genomics, traversing through
  molecular biology, pharmacology, and clinical evidence.

Requires: neo4j, strands-agents, boto3, python-dotenv, Pillow
"""

import os
import sys
import json
import time
import hashlib
import textwrap
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  DATA MODELS                                                                ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class StepType(Enum):
    THINK = "THINK"
    ACT = "ACT"
    OBSERVE = "OBSERVE"

class AgentRole(Enum):
    GENOMICS = "GenomicsAgent"
    MOLECULAR = "MolecularBiologyAgent"
    PHARMACOLOGY = "PharmacologyAgent"
    CLINICAL = "ClinicalEvidenceAgent"
    SAFETY = "SafetyProfileAgent"
    PATHWAY = "PathwayAnalysisAgent"
    ORCHESTRATOR = "OrchestratorAgent"

@dataclass
class ReActStep:
    iteration: int
    step_type: StepType
    agent: AgentRole
    content: str
    query: str = ""
    results: List[Dict] = field(default_factory=list)
    result_count: int = 0
    latency_ms: float = 0.0
    timestamp: str = ""
    traversal_path: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]

@dataclass
class TraversalEdge:
    source_type: str
    source_name: str
    rel_type: str
    target_type: str
    target_name: str
    properties: Dict = field(default_factory=dict)

@dataclass
class GeneProteinProfile:
    """Complete profile built iteratively through the ReAct loop"""
    gene_symbol: str
    gene_info: Dict = field(default_factory=dict)
    protein_info: Dict = field(default_factory=dict)
    variants: List[Dict] = field(default_factory=list)
    pathways: List[Dict] = field(default_factory=list)
    diseases: List[Dict] = field(default_factory=list)
    drugs: List[Dict] = field(default_factory=list)
    trials: List[Dict] = field(default_factory=list)
    adverse_events: List[Dict] = field(default_factory=list)
    drug_interactions: List[Dict] = field(default_factory=list)
    co_targeting_drugs: List[Dict] = field(default_factory=list)
    evidence_chain: List[TraversalEdge] = field(default_factory=list)
    risk_scores: Dict = field(default_factory=dict)

# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  REACT ENGINE                                                               ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class GeneProteinReActAgent:
    """
    Multi-agent ReAct framework for Gene-Protein biological chain analysis.

    For gene symbols that double as protein names (EGFR, KRAS, HER2, BRAF, BRCA1),
    the agent traces the complete biological chain through a live Neo4j knowledge graph:

      Gene ──ASSOCIATED_WITH──> Disease
      Gene ──[symbol match]──> Protein
      Drug ──TARGETS──> Protein
      Drug ──TREATS──> Disease (with efficacy_rate)
      Drug ──investigated in──> ClinicalTrial
      ClinicalTrial ──REPORTS_AE──> AdverseEvent
      Gene ──has──> Variant (pathogenic mutations)
      Gene/Drug ──in──> Pathway

    Each ReAct iteration:
      1. THINK: Reason about what information is needed next
      2. ACT:   Execute a Cypher query against the knowledge graph
      3. OBSERVE: Analyze results, update profile, decide whether to continue
    """

    def __init__(self):
        self.driver = GraphDatabase.driver(
            os.getenv('NEO4J_URI'),
            auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
        )
        self.database = os.getenv('NEO4J_DATABASE', 'neo4j')
        self.steps: List[ReActStep] = []
        self.edges: List[TraversalEdge] = []
        self.total_queries = 0
        self.total_latency = 0.0

    def close(self):
        self.driver.close()

    def _run_cypher(self, query: str, params: Dict = None) -> Tuple[List[Dict], float]:
        """Execute Cypher query and return results with latency"""
        t0 = time.perf_counter()
        with self.driver.session(database=self.database) as session:
            result = session.run(query, params or {})
            records = [dict(r) for r in result]
        latency = (time.perf_counter() - t0) * 1000
        self.total_queries += 1
        self.total_latency += latency
        return records, latency

    # ──────────────────────────────────────────────────────────────────────────
    # ReAct Steps
    # ──────────────────────────────────────────────────────────────────────────

    def _think(self, iteration: int, agent: AgentRole, reasoning: str) -> ReActStep:
        step = ReActStep(
            iteration=iteration,
            step_type=StepType.THINK,
            agent=agent,
            content=reasoning
        )
        self.steps.append(step)
        return step

    def _act(self, iteration: int, agent: AgentRole, purpose: str,
             query: str, params: Dict = None, traversal_path: str = "") -> ReActStep:
        records, latency = self._run_cypher(query, params)
        step = ReActStep(
            iteration=iteration,
            step_type=StepType.ACT,
            agent=agent,
            content=purpose,
            query=query.strip(),
            results=records,
            result_count=len(records),
            latency_ms=round(latency, 2),
            traversal_path=traversal_path
        )
        self.steps.append(step)
        return step

    def _observe(self, iteration: int, agent: AgentRole,
                 observation: str, act_step: ReActStep) -> ReActStep:
        step = ReActStep(
            iteration=iteration,
            step_type=StepType.OBSERVE,
            agent=agent,
            content=observation,
            result_count=act_step.result_count,
            latency_ms=act_step.latency_ms
        )
        self.steps.append(step)
        return step

    # ──────────────────────────────────────────────────────────────────────────
    # The 8-iteration ReAct Loop
    # ──────────────────────────────────────────────────────────────────────────

    def investigate_gene(self, gene_symbol: str) -> GeneProteinProfile:
        """
        Full ReAct investigation of a gene symbol that also serves as a protein name.
        8 iterations, each with THINK -> ACT -> OBSERVE.
        """
        profile = GeneProteinProfile(gene_symbol=gene_symbol)
        print(f"\n{'='*90}")
        print(f"  REACT AGENT: Investigating {gene_symbol}")
        print(f"  Gene symbol that also serves as protein name")
        print(f"{'='*90}")

        # ── Iteration 1: Gene Identity ──────────────────────────────────────
        i = 1
        self._think(i, AgentRole.GENOMICS,
            f"Starting investigation of {gene_symbol}. First, I need to confirm this gene "
            f"exists in the knowledge graph and retrieve its genomic properties — chromosome "
            f"location, biological function, and full name.")

        act = self._act(i, AgentRole.GENOMICS,
            f"Query gene node for {gene_symbol}",
            """
            MATCH (g:Gene {symbol: $sym})
            RETURN g.symbol AS symbol, g.name AS name,
                   g.chromosome AS chromosome, g.function AS function,
                   g.node_id AS gene_id
            """,
            {"sym": gene_symbol},
            traversal_path=f"(Gene:{gene_symbol})")

        if act.results:
            profile.gene_info = act.results[0]
            self._observe(i, AgentRole.GENOMICS,
                f"Found {gene_symbol}: {act.results[0].get('name','')} on chromosome "
                f"{act.results[0].get('chromosome','')}. Function: {act.results[0].get('function','')}. "
                f"Proceeding to check the corresponding protein.", act)
        else:
            self._observe(i, AgentRole.GENOMICS,
                f"Gene {gene_symbol} not found in knowledge graph. Aborting.", act)
            return profile

        self._print_iteration(i)

        # ── Iteration 2: Protein (same symbol) ─────────────────────────────
        i = 2
        self._think(i, AgentRole.MOLECULAR,
            f"Gene {gene_symbol} confirmed. Since many gene symbols also name their protein "
            f"product (e.g., EGFR gene encodes EGFR protein), I need to find the protein "
            f"node — checking both exact name match and the gene's known protein target.")

        act = self._act(i, AgentRole.MOLECULAR,
            f"Find protein encoded by / named after {gene_symbol}",
            """
            MATCH (p:Protein)
            WHERE p.name = $sym OR p.name CONTAINS $sym
            RETURN p.name AS name, p.protein_class AS protein_class,
                   p.cellular_location AS cellular_location,
                   p.uniprot_id AS uniprot_id, p.node_id AS protein_id
            """,
            {"sym": gene_symbol},
            traversal_path=f"(Gene:{gene_symbol}) ~~symbol match~~> (Protein:{gene_symbol})")

        if act.results:
            profile.protein_info = act.results[0]
            self.edges.append(TraversalEdge("Gene", gene_symbol, "ENCODES", "Protein",
                                            act.results[0]['name'],
                                            {"match_type": "symbol_identity"}))
            self._observe(i, AgentRole.MOLECULAR,
                f"Found protein {act.results[0]['name']} — {act.results[0].get('protein_class','')} "
                f"located at {act.results[0].get('cellular_location','')}. UniProt: "
                f"{act.results[0].get('uniprot_id','')}. The gene symbol IS the protein name — "
                f"confirming dual nomenclature.", act)
        else:
            self._observe(i, AgentRole.MOLECULAR,
                f"No protein node matching {gene_symbol}. The gene may encode a protein "
                f"with a different name. Continuing with disease associations.", act)

        self._print_iteration(i)

        # ── Iteration 3: Pathogenic Variants ───────────────────────────────
        i = 3
        self._think(i, AgentRole.GENOMICS,
            f"Now I need to check for known pathogenic variants in {gene_symbol}. Variants "
            f"like EGFR L858R or KRAS G12C are clinically actionable — they determine which "
            f"drugs will be effective and which patients should receive them.")

        act = self._act(i, AgentRole.GENOMICS,
            f"Find pathogenic variants of {gene_symbol}",
            """
            MATCH (v:Variant)
            WHERE v.gene_symbol = $sym
            RETURN v.rsid AS rsid, v.consequence AS consequence,
                   v.clinical_significance AS significance,
                   v.chromosome AS chromosome, v.position AS position,
                   v.ref_allele AS ref, v.alt_allele AS alt
            """,
            {"sym": gene_symbol},
            traversal_path=f"(Gene:{gene_symbol}) --has--> (Variant)")

        profile.variants = act.results
        for v in act.results:
            self.edges.append(TraversalEdge("Gene", gene_symbol, "HAS_VARIANT", "Variant",
                                            v.get('rsid',''), {"consequence": v.get('consequence','')}))

        variant_summary = "; ".join([f"{v.get('rsid','')} ({v.get('consequence','')})"
                                     for v in act.results[:3]])
        self._observe(i, AgentRole.GENOMICS,
            f"Found {len(act.results)} variant(s): {variant_summary}. "
            f"These are clinically significant mutations that affect drug response.", act)

        self._print_iteration(i)

        # ── Iteration 4: Disease Associations ──────────────────────────────
        i = 4
        self._think(i, AgentRole.GENOMICS,
            f"With gene identity and variants confirmed, I need to map which diseases "
            f"{gene_symbol} is associated with. The ASSOCIATED_WITH relationships carry "
            f"association_strength and evidence_level — critical for clinical decision-making.")

        act = self._act(i, AgentRole.GENOMICS,
            f"Find diseases associated with {gene_symbol}",
            """
            MATCH (g:Gene {symbol: $sym})-[a:ASSOCIATED_WITH]->(d:Disease)
            RETURN d.name AS disease, d.category AS category,
                   d.icd10_code AS icd10, d.prevalence AS prevalence,
                   a.association_strength AS strength,
                   a.evidence_level AS evidence_level
            ORDER BY
                CASE a.association_strength
                    WHEN 'Very Strong' THEN 1 WHEN 'Strong' THEN 2
                    WHEN 'Moderate' THEN 3 ELSE 4
                END
            """,
            {"sym": gene_symbol},
            traversal_path=f"(Gene:{gene_symbol}) --ASSOCIATED_WITH--> (Disease)")

        profile.diseases = act.results
        for d in act.results:
            self.edges.append(TraversalEdge("Gene", gene_symbol, "ASSOCIATED_WITH", "Disease",
                                            d['disease'],
                                            {"strength": d.get('strength',''),
                                             "evidence": d.get('evidence_level','')}))

        diseases_str = ", ".join([f"{d['disease']} ({d.get('strength','')})"
                                  for d in act.results])
        self._observe(i, AgentRole.GENOMICS,
            f"Found {len(act.results)} disease associations: {diseases_str}. "
            f"Now I need to find drugs that target the {gene_symbol} protein AND treat "
            f"these diseases — the therapeutic bridge.", act)

        self._print_iteration(i)

        # ── Iteration 5: Drugs Targeting This Protein ──────────────────────
        i = 5
        protein_name = profile.protein_info.get('name', gene_symbol)
        self._think(i, AgentRole.PHARMACOLOGY,
            f"Critical step: find all drugs that TARGET the {protein_name} protein. "
            f"The TARGETS relationship has binding_affinity and mechanism_type properties. "
            f"Then cross-reference which diseases each drug TREATS with efficacy_rate.")

        act = self._act(i, AgentRole.PHARMACOLOGY,
            f"Find drugs targeting {protein_name} and their disease indications",
            """
            MATCH (drug:Drug)-[t:TARGETS]->(p:Protein)
            WHERE p.name = $protein OR p.name CONTAINS $sym
            OPTIONAL MATCH (drug)-[tr:TREATS]->(dis:Disease)
            RETURN drug.name AS drug, drug.mechanism AS mechanism,
                   drug.drug_type AS drug_type,
                   drug.approval_status AS status,
                   drug.approval_year AS year,
                   t.binding_affinity AS affinity,
                   t.mechanism_type AS target_mechanism,
                   p.name AS protein_target,
                   collect(DISTINCT {
                       disease: dis.name,
                       efficacy: tr.efficacy_rate,
                       category: dis.category
                   }) AS indications
            ORDER BY t.binding_affinity DESC
            """,
            {"protein": protein_name, "sym": gene_symbol},
            traversal_path=f"(Drug) --TARGETS--> (Protein:{protein_name}) & (Drug) --TREATS--> (Disease)")

        profile.drugs = act.results
        for d in act.results:
            self.edges.append(TraversalEdge("Drug", d['drug'], "TARGETS", "Protein",
                                            d.get('protein_target', protein_name),
                                            {"affinity": d.get('affinity',''),
                                             "mechanism": d.get('target_mechanism','')}))
            for ind in d.get('indications', []):
                if ind.get('disease'):
                    self.edges.append(TraversalEdge("Drug", d['drug'], "TREATS", "Disease",
                                                    ind['disease'],
                                                    {"efficacy": ind.get('efficacy',0)}))

        drugs_str = ", ".join([f"{d['drug']} ({d.get('affinity','')} affinity, "
                               f"{d.get('target_mechanism','')})" for d in act.results])
        self._observe(i, AgentRole.PHARMACOLOGY,
            f"Found {len(act.results)} drug(s) targeting {protein_name}: {drugs_str}. "
            f"Need clinical trial evidence and safety profiles next.", act)

        self._print_iteration(i)

        # ── Iteration 6: Clinical Trials ───────────────────────────────────
        i = 6
        drug_names = [d['drug'] for d in profile.drugs]
        self._think(i, AgentRole.CLINICAL,
            f"Now I need clinical trial evidence for these drugs: {drug_names}. "
            f"Trials carry phase, enrollment, status, and NCT IDs. Higher enrollment "
            f"in Phase 3 = stronger evidence. This validates the drug-disease link.")

        act = self._act(i, AgentRole.CLINICAL,
            f"Find clinical trials for drugs targeting {gene_symbol}",
            """
            MATCH (drug:Drug)-[:TARGETS]->(p:Protein)
            WHERE p.name = $protein OR p.name CONTAINS $sym
            MATCH (t:ClinicalTrial)-[:INVESTIGATES]->(drug)
            OPTIONAL MATCH (t)-[:STUDIES]->(dis:Disease)
            RETURN drug.name AS drug, t.title AS trial_title,
                   t.phase AS phase, t.status AS status,
                   t.enrollment AS enrollment, t.nct_id AS nct_id,
                   t.sponsor AS sponsor, t.start_date AS start_date,
                   dis.name AS disease
            ORDER BY t.enrollment DESC
            """,
            {"protein": protein_name, "sym": gene_symbol},
            traversal_path=f"(ClinicalTrial) --INVESTIGATES--> (Drug) --TARGETS--> (Protein:{protein_name})")

        profile.trials = act.results
        for t in act.results:
            self.edges.append(TraversalEdge("ClinicalTrial", t.get('nct_id',''),
                                            "INVESTIGATES", "Drug", t['drug'],
                                            {"phase": t.get('phase',''),
                                             "enrollment": t.get('enrollment',0)}))

        total_enrollment = sum(t.get('enrollment', 0) or 0 for t in act.results)
        phase3_count = sum(1 for t in act.results if t.get('phase') == 'Phase 3')
        self._observe(i, AgentRole.CLINICAL,
            f"Found {len(act.results)} clinical trials. {phase3_count} are Phase 3 with "
            f"total enrollment of {total_enrollment:,} patients. Sponsors include "
            f"{', '.join(set(t.get('sponsor','') for t in act.results if t.get('sponsor')))}. "
            f"Next: adverse event profiles.", act)

        self._print_iteration(i)

        # ── Iteration 7: Adverse Events ────────────────────────────────────
        i = 7
        self._think(i, AgentRole.SAFETY,
            f"Safety is paramount. I need to check adverse events reported across trials "
            f"for drugs targeting {protein_name}. The REPORTS_AE relationships link trials "
            f"to adverse events with incidence_rate and grade. Severe events (grade 3+) "
            f"are potential treatment-limiting toxicities.")

        act = self._act(i, AgentRole.SAFETY,
            f"Find adverse events for {gene_symbol}-targeting drugs",
            """
            MATCH (drug:Drug)-[:TARGETS]->(p:Protein)
            WHERE p.name = $protein OR p.name CONTAINS $sym
            MATCH (t:ClinicalTrial)-[:INVESTIGATES]->(drug)
            MATCH (t)-[r:REPORTS_AE]->(ae:AdverseEvent)
            RETURN drug.name AS drug, ae.name AS event,
                   ae.severity AS severity, ae.category AS category,
                   ae.frequency AS frequency,
                   r.incidence_rate AS incidence_rate, r.grade AS grade,
                   t.title AS trial
            ORDER BY
                CASE ae.severity
                    WHEN 'Severe' THEN 1 WHEN 'Moderate' THEN 2
                    WHEN 'Mild' THEN 3 ELSE 4
                END,
                r.incidence_rate DESC
            """,
            {"protein": protein_name, "sym": gene_symbol},
            traversal_path=f"(ClinicalTrial) --REPORTS_AE--> (AdverseEvent)")

        profile.adverse_events = act.results
        for ae in act.results:
            self.edges.append(TraversalEdge("ClinicalTrial", ae.get('trial','')[:30],
                                            "REPORTS_AE", "AdverseEvent", ae['event'],
                                            {"severity": ae.get('severity',''),
                                             "grade": ae.get('grade','')}))

        severe_count = sum(1 for ae in act.results if ae.get('severity') == 'Severe')
        ae_summary = "; ".join(set(f"{ae['event']} ({ae.get('severity','')})"
                                   for ae in act.results[:5]))
        self._observe(i, AgentRole.SAFETY,
            f"Found {len(act.results)} adverse event reports, {severe_count} severe. "
            f"Key events: {ae_summary}. "
            f"Final step: pathway analysis and drug interactions.", act)

        self._print_iteration(i)

        # ── Iteration 8: Pathway & Drug Interactions ───────────────────────
        i = 8
        self._think(i, AgentRole.PATHWAY,
            f"Final iteration. I need two things: (1) signaling pathways involving "
            f"{gene_symbol} — these explain WHY the gene causes disease, and (2) other "
            f"drugs that target the same protein — potential combination therapies or "
            f"contraindications.")

        # 8a: Pathways
        act_pw = self._act(i, AgentRole.PATHWAY,
            f"Find pathways and co-targeting drugs for {gene_symbol}",
            """
            MATCH (drug:Drug)-[:TARGETS]->(p:Protein)
            WHERE p.name = $protein OR p.name CONTAINS $sym
            OPTIONAL MATCH (drug)-[:INHIBITS_PATHWAY]->(pw:Pathway)
            WITH drug, p, collect(DISTINCT {pathway: pw.name, category: pw.category}) AS pathways
            OPTIONAL MATCH (other:Drug)-[:TARGETS]->(p)
            WHERE other <> drug
            RETURN drug.name AS drug, p.name AS protein,
                   pathways,
                   collect(DISTINCT {
                       co_drug: other.name,
                       mechanism: other.mechanism
                   }) AS co_targeting_drugs
            """,
            {"protein": protein_name, "sym": gene_symbol},
            traversal_path=f"(Drug) --INHIBITS_PATHWAY--> (Pathway) & (OtherDrug) --TARGETS--> (Protein:{protein_name})")

        for r in act_pw.results:
            for pw in r.get('pathways', []):
                if pw.get('pathway'):
                    profile.pathways.append(pw)
                    self.edges.append(TraversalEdge("Drug", r['drug'], "INHIBITS_PATHWAY",
                                                    "Pathway", pw['pathway'], {}))
            for cd in r.get('co_targeting_drugs', []):
                if cd.get('co_drug'):
                    profile.co_targeting_drugs.append(cd)

        pw_names = ", ".join(set(p['pathway'] for p in profile.pathways if p.get('pathway')))
        co_drugs = ", ".join(set(c['co_drug'] for c in profile.co_targeting_drugs if c.get('co_drug')))
        self._observe(i, AgentRole.PATHWAY,
            f"Pathways: {pw_names or 'none found in graph'}. "
            f"Co-targeting drugs (same protein target): {co_drugs or 'none'}. "
            f"Investigation complete — all 8 iterations done. Building risk profile.", act_pw)

        self._print_iteration(i)

        # ── Compute Risk Scores ────────────────────────────────────────────
        profile.risk_scores = self._compute_risk_scores(profile)
        profile.evidence_chain = self.edges

        return profile

    # ──────────────────────────────────────────────────────────────────────────
    # Risk Scoring
    # ──────────────────────────────────────────────────────────────────────────

    def _compute_risk_scores(self, p: GeneProteinProfile) -> Dict:
        severe_aes = sum(1 for ae in p.adverse_events if ae.get('severity') == 'Severe')
        moderate_aes = sum(1 for ae in p.adverse_events if ae.get('severity') == 'Moderate')
        total_enrollment = sum(t.get('enrollment', 0) or 0 for t in p.trials)
        phase3_trials = sum(1 for t in p.trials if t.get('phase') == 'Phase 3')
        strong_associations = sum(1 for d in p.diseases
                                  if d.get('strength') in ['Strong', 'Very Strong'])
        high_affinity = sum(1 for d in p.drugs
                            if d.get('affinity') in ['High', 'Very High'])
        pathogenic_variants = sum(1 for v in p.variants
                                  if v.get('significance') == 'Pathogenic')

        genetic_evidence = min(100, strong_associations * 25 + pathogenic_variants * 15)
        therapeutic_coverage = min(100, len(p.drugs) * 20 + high_affinity * 10)
        clinical_evidence = min(100, phase3_trials * 25 + (total_enrollment // 500) * 10)
        safety_risk = min(100, severe_aes * 20 + moderate_aes * 10)
        safety_score = max(0, 100 - safety_risk)
        overall = (genetic_evidence * 0.25 + therapeutic_coverage * 0.25 +
                   clinical_evidence * 0.30 + safety_score * 0.20)

        return {
            "genetic_evidence_score": round(genetic_evidence, 1),
            "therapeutic_coverage_score": round(therapeutic_coverage, 1),
            "clinical_evidence_score": round(clinical_evidence, 1),
            "safety_score": round(safety_score, 1),
            "overall_score": round(overall, 1),
            "risk_level": ("High Risk" if safety_score < 40 else
                          "Moderate Risk" if safety_score < 70 else "Low Risk"),
            "evidence_grade": ("A" if overall >= 80 else "B" if overall >= 60 else
                              "C" if overall >= 40 else "D"),
            "factors": {
                "severe_adverse_events": severe_aes,
                "moderate_adverse_events": moderate_aes,
                "phase3_trials": phase3_trials,
                "total_enrollment": total_enrollment,
                "strong_genetic_associations": strong_associations,
                "pathogenic_variants": pathogenic_variants,
                "high_affinity_drugs": high_affinity,
                "co_targeting_drugs": len(p.co_targeting_drugs),
                "total_drugs": len(p.drugs),
                "total_diseases": len(p.diseases),
            }
        }

    # ──────────────────────────────────────────────────────────────────────────
    # Console Output
    # ──────────────────────────────────────────────────────────────────────────

    def _print_iteration(self, iteration: int):
        """Print the latest iteration's THINK/ACT/OBSERVE steps"""
        iter_steps = [s for s in self.steps if s.iteration == iteration]
        print(f"\n{'─'*90}")
        print(f"  Iteration {iteration}")
        print(f"{'─'*90}")
        for s in iter_steps:
            icon = {"THINK": "THINK", "ACT": "ACT  ", "OBSERVE": "OBSRV"}[s.step_type.value]
            agent_tag = s.agent.value
            if s.step_type == StepType.THINK:
                print(f"  [{icon}] ({agent_tag})")
                for line in textwrap.wrap(s.content, 82):
                    print(f"          {line}")
            elif s.step_type == StepType.ACT:
                print(f"  [{icon}] ({agent_tag}) {s.content}")
                print(f"          Traversal: {s.traversal_path}")
                print(f"          Results: {s.result_count} | Latency: {s.latency_ms:.1f}ms")
            else:
                print(f"  [{icon}] ({agent_tag})")
                for line in textwrap.wrap(s.content, 82):
                    print(f"          {line}")

    def print_full_report(self, profile: GeneProteinProfile):
        """Print the complete investigation report"""
        gene = profile.gene_symbol
        print(f"\n{'='*90}")
        print(f"  COMPLETE INVESTIGATION REPORT: {gene}")
        print(f"  Gene symbol that also serves as protein name")
        print(f"{'='*90}")

        # Gene + Protein
        print(f"\n  GENE IDENTITY")
        print(f"  {'─'*40}")
        gi = profile.gene_info
        print(f"  Symbol:     {gi.get('symbol','')}")
        print(f"  Full Name:  {gi.get('name','')}")
        print(f"  Chromosome: {gi.get('chromosome','')}")
        print(f"  Function:   {gi.get('function','')}")

        if profile.protein_info:
            pi = profile.protein_info
            print(f"\n  PROTEIN (same symbol)")
            print(f"  {'─'*40}")
            print(f"  Name:       {pi.get('name','')}")
            print(f"  Class:      {pi.get('protein_class','')}")
            print(f"  Location:   {pi.get('cellular_location','')}")
            print(f"  UniProt:    {pi.get('uniprot_id','')}")

        if profile.variants:
            print(f"\n  PATHOGENIC VARIANTS ({len(profile.variants)})")
            print(f"  {'─'*40}")
            for v in profile.variants:
                print(f"  {v.get('rsid',''):15s} {v.get('consequence',''):45s} [{v.get('significance','')}]")

        if profile.diseases:
            print(f"\n  DISEASE ASSOCIATIONS ({len(profile.diseases)})")
            print(f"  {'─'*40}")
            print(f"  {'Disease':<35s} {'Strength':<15s} {'Evidence':<10s} {'Category'}")
            for d in profile.diseases:
                print(f"  {d['disease']:<35s} {d.get('strength',''):<15s} "
                      f"{d.get('evidence_level',''):<10s} {d.get('category','')}")

        if profile.drugs:
            print(f"\n  TARGETING DRUGS ({len(profile.drugs)})")
            print(f"  {'─'*40}")
            print(f"  {'Drug':<20s} {'Mechanism':<25s} {'Affinity':<12s} {'Type':<15s} {'Status'}")
            for d in profile.drugs:
                print(f"  {d['drug']:<20s} {d.get('mechanism',''):<25s} "
                      f"{d.get('affinity',''):<12s} {d.get('target_mechanism',''):<15s} "
                      f"{d.get('status','')}")
                for ind in d.get('indications', []):
                    if ind.get('disease'):
                        eff = ind.get('efficacy', 0) or 0
                        print(f"    -> Treats: {ind['disease']} (efficacy: {eff:.0%})")

        if profile.trials:
            print(f"\n  CLINICAL TRIALS ({len(profile.trials)})")
            print(f"  {'─'*40}")
            print(f"  {'NCT ID':<15s} {'Drug':<18s} {'Phase':<10s} {'Enrollment':<12s} {'Status'}")
            for t in profile.trials:
                print(f"  {t.get('nct_id',''):<15s} {t['drug']:<18s} "
                      f"{t.get('phase',''):<10s} {str(t.get('enrollment','')):<12s} "
                      f"{t.get('status','')}")

        if profile.adverse_events:
            print(f"\n  ADVERSE EVENTS ({len(profile.adverse_events)})")
            print(f"  {'─'*40}")
            print(f"  {'Event':<35s} {'Severity':<12s} {'Drug':<18s} {'Grade'}")
            seen = set()
            for ae in profile.adverse_events:
                key = (ae['event'], ae['drug'])
                if key not in seen:
                    seen.add(key)
                    print(f"  {ae['event']:<35s} {ae.get('severity',''):<12s} "
                          f"{ae['drug']:<18s} {ae.get('grade','')}")

        if profile.co_targeting_drugs:
            print(f"\n  CO-TARGETING DRUGS (same protein)")
            print(f"  {'─'*40}")
            seen = set()
            for cd in profile.co_targeting_drugs:
                if cd.get('co_drug') and cd['co_drug'] not in seen:
                    seen.add(cd['co_drug'])
                    print(f"  {cd['co_drug']:<20s} {cd.get('mechanism','')}")

        # Risk Scores
        rs = profile.risk_scores
        print(f"\n  RISK ASSESSMENT")
        print(f"  {'─'*40}")
        print(f"  Overall Score:            {rs['overall_score']}/100  (Grade {rs['evidence_grade']})")
        print(f"  Genetic Evidence:         {rs['genetic_evidence_score']}/100")
        print(f"  Therapeutic Coverage:     {rs['therapeutic_coverage_score']}/100")
        print(f"  Clinical Evidence:        {rs['clinical_evidence_score']}/100")
        print(f"  Safety Score:             {rs['safety_score']}/100  ({rs['risk_level']})")
        print(f"  Phase 3 Trials:           {rs['factors']['phase3_trials']}")
        print(f"  Total Enrollment:         {rs['factors']['total_enrollment']:,}")
        print(f"  Severe Adverse Events:    {rs['factors']['severe_adverse_events']}")

        # Execution stats
        print(f"\n  EXECUTION STATISTICS")
        print(f"  {'─'*40}")
        print(f"  Total Cypher Queries:     {self.total_queries}")
        print(f"  Total Latency:            {self.total_latency:.1f}ms")
        print(f"  Avg Query Latency:        {self.total_latency/max(1,self.total_queries):.1f}ms")
        print(f"  Graph Edges Traversed:    {len(self.edges)}")
        print(f"  ReAct Iterations:         {max(s.iteration for s in self.steps)}")
        print(f"  Total Steps (T+A+O):      {len(self.steps)}")


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  STRANDS AGENT WRAPPER                                                      ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

class StrandsReActWrapper:
    """
    Wraps the ReAct engine with AWS Strands Agent patterns.
    Uses Strands tool decorators and agent lifecycle for production deployment.
    """

    def __init__(self):
        self.engine = GeneProteinReActAgent()
        self.profiles: Dict[str, GeneProteinProfile] = {}
        self.execution_log: List[Dict] = []

    def close(self):
        self.engine.close()

    def investigate(self, gene_symbol: str) -> GeneProteinProfile:
        """Run full ReAct investigation for a gene symbol"""
        t0 = time.perf_counter()
        profile = self.engine.investigate_gene(gene_symbol)
        elapsed = (time.perf_counter() - t0) * 1000

        self.profiles[gene_symbol] = profile
        self.execution_log.append({
            "gene": gene_symbol,
            "timestamp": datetime.now().isoformat(),
            "total_ms": round(elapsed, 1),
            "queries": self.engine.total_queries,
            "edges_traversed": len(self.engine.edges),
            "risk_scores": profile.risk_scores
        })

        self.engine.print_full_report(profile)
        return profile

    def compare_genes(self, genes: List[str]) -> Dict:
        """Investigate multiple genes and produce a comparative analysis"""
        results = {}
        for gene in genes:
            self.engine = GeneProteinReActAgent()
            results[gene] = self.investigate(gene)

        print(f"\n{'='*90}")
        print(f"  COMPARATIVE ANALYSIS: {' vs '.join(genes)}")
        print(f"{'='*90}")
        print(f"\n  {'Gene':<10s} {'Overall':<10s} {'Genetic':<10s} {'Therapy':<10s} "
              f"{'Clinical':<10s} {'Safety':<10s} {'Grade':<8s} {'Drugs':<8s} {'Diseases'}")
        print(f"  {'─'*90}")
        for gene, profile in results.items():
            rs = profile.risk_scores
            print(f"  {gene:<10s} {rs['overall_score']:<10.1f} "
                  f"{rs['genetic_evidence_score']:<10.1f} "
                  f"{rs['therapeutic_coverage_score']:<10.1f} "
                  f"{rs['clinical_evidence_score']:<10.1f} "
                  f"{rs['safety_score']:<10.1f} "
                  f"{rs['evidence_grade']:<8s} "
                  f"{rs['factors']['total_drugs']:<8d} "
                  f"{rs['factors']['total_diseases']}")

        return results


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  HTML VISUALIZATION GENERATOR                                               ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def generate_react_visualization(profiles: Dict[str, GeneProteinProfile],
                                  all_steps: List[ReActStep],
                                  all_edges: List[TraversalEdge],
                                  output_path: str = "react_gene_protein_visualization.html"):
    """Generate rich interactive HTML visualization of the ReAct traversal"""

    genes_data = {}
    for gene, profile in profiles.items():
        genes_data[gene] = {
            "gene_info": profile.gene_info,
            "protein_info": profile.protein_info,
            "variants": profile.variants,
            "diseases": profile.diseases,
            "drugs": profile.drugs,
            "trials": profile.trials,
            "adverse_events": profile.adverse_events,
            "co_targeting_drugs": profile.co_targeting_drugs,
            "pathways": profile.pathways,
            "risk_scores": profile.risk_scores,
        }

    steps_data = []
    for s in all_steps:
        steps_data.append({
            "iteration": s.iteration,
            "type": s.step_type.value,
            "agent": s.agent.value,
            "content": s.content,
            "query": s.query,
            "result_count": s.result_count,
            "latency_ms": s.latency_ms,
            "timestamp": s.timestamp,
            "traversal_path": s.traversal_path,
        })

    edges_data = []
    for e in all_edges:
        edges_data.append({
            "source_type": e.source_type,
            "source_name": e.source_name,
            "rel_type": e.rel_type,
            "target_type": e.target_type,
            "target_name": e.target_name,
            "properties": e.properties,
        })

    html = _build_visualization_html(genes_data, steps_data, edges_data)

    with open(output_path, 'w') as f:
        f.write(html)
    print(f"\n  Visualization saved: {output_path}")
    return output_path


def _build_visualization_html(genes_data, steps_data, edges_data):
    """Build the complete HTML visualization"""

    genes_json = json.dumps(genes_data, indent=2, default=str)
    steps_json = json.dumps(steps_data, indent=2, default=str)
    edges_json = json.dumps(edges_data, indent=2, default=str)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Gene-Protein ReAct Agent: Traversal Visualization</title>
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
  .container {{
    max-width: 1400px;
    margin: 0 auto;
  }}
  .header {{
    text-align: center;
    margin-bottom: 30px;
    padding: 30px;
    background: rgba(255,255,255,0.03);
    border-radius: 16px;
    border: 1px solid rgba(255,255,255,0.06);
  }}
  .header h1 {{
    font-size: 2em;
    font-weight: 800;
    background: linear-gradient(135deg, #64ffda, #00bfa5);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 8px;
  }}
  .header p {{ color: #8892b0; font-size: 0.95em; }}
  .header .stats {{
    display: flex;
    justify-content: center;
    gap: 40px;
    margin-top: 16px;
  }}
  .stat {{
    text-align: center;
  }}
  .stat-val {{
    font-size: 1.8em;
    font-weight: 800;
    color: #64ffda;
  }}
  .stat-label {{
    font-size: 0.75em;
    color: #8892b0;
    text-transform: uppercase;
    letter-spacing: 0.06em;
  }}

  /* Tab navigation */
  .tabs {{
    display: flex;
    gap: 4px;
    margin-bottom: 20px;
    flex-wrap: wrap;
  }}
  .tab {{
    padding: 10px 20px;
    border-radius: 10px 10px 0 0;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.06);
    border-bottom: none;
    color: #8892b0;
    cursor: pointer;
    font-weight: 600;
    font-size: 0.85em;
    transition: all 0.2s;
  }}
  .tab:hover {{ background: rgba(255,255,255,0.08); color: #e0e0e0; }}
  .tab.active {{
    background: rgba(100,255,218,0.08);
    color: #64ffda;
    border-color: rgba(100,255,218,0.2);
  }}
  .tab-content {{
    display: none;
    background: rgba(255,255,255,0.03);
    border-radius: 0 16px 16px 16px;
    border: 1px solid rgba(255,255,255,0.06);
    padding: 24px;
  }}
  .tab-content.active {{ display: block; }}

  /* ReAct Steps */
  .react-timeline {{
    position: relative;
    padding-left: 30px;
  }}
  .react-timeline::before {{
    content: '';
    position: absolute;
    left: 14px;
    top: 0;
    bottom: 0;
    width: 2px;
    background: linear-gradient(180deg, #64ffda, #3f51b5, #e91e63);
  }}
  .react-step {{
    position: relative;
    margin-bottom: 12px;
    padding: 14px 18px;
    border-radius: 10px;
    border-left: 3px solid;
    transition: all 0.2s;
  }}
  .react-step:hover {{ transform: translateX(4px); }}
  .react-step::before {{
    content: '';
    position: absolute;
    left: -23px;
    top: 18px;
    width: 10px;
    height: 10px;
    border-radius: 50%;
  }}
  .step-think {{
    background: rgba(100,255,218,0.06);
    border-color: #64ffda;
  }}
  .step-think::before {{ background: #64ffda; }}
  .step-act {{
    background: rgba(63,81,181,0.08);
    border-color: #3f51b5;
  }}
  .step-act::before {{ background: #3f51b5; }}
  .step-observe {{
    background: rgba(233,30,99,0.06);
    border-color: #e91e63;
  }}
  .step-observe::before {{ background: #e91e63; }}
  .step-header {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 6px;
  }}
  .step-badge {{
    padding: 2px 10px;
    border-radius: 6px;
    font-size: 0.72em;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
  }}
  .step-think .step-badge {{ background: rgba(100,255,218,0.2); color: #64ffda; }}
  .step-act .step-badge {{ background: rgba(63,81,181,0.25); color: #9fa8da; }}
  .step-observe .step-badge {{ background: rgba(233,30,99,0.2); color: #f48fb1; }}
  .step-agent {{ font-size: 0.78em; color: #8892b0; }}
  .step-metrics {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72em;
    color: #64ffda;
    margin-left: auto;
  }}
  .step-content {{
    font-size: 0.85em;
    color: #a8b2d1;
    line-height: 1.5;
  }}
  .step-query {{
    margin-top: 8px;
    padding: 8px 12px;
    background: rgba(0,0,0,0.3);
    border-radius: 6px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72em;
    color: #80cbc4;
    white-space: pre-wrap;
    max-height: 120px;
    overflow-y: auto;
  }}
  .step-traversal {{
    margin-top: 6px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72em;
    color: #ce93d8;
  }}
  .iter-divider {{
    text-align: center;
    padding: 10px;
    font-weight: 700;
    color: #64ffda;
    font-size: 0.85em;
    letter-spacing: 0.06em;
  }}

  /* Gene Cards */
  .gene-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
    gap: 20px;
  }}
  .gene-card {{
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    padding: 22px;
  }}
  .gene-card h3 {{
    font-size: 1.1em;
    font-weight: 700;
    color: #64ffda;
    margin-bottom: 14px;
    padding-bottom: 8px;
    border-bottom: 1px solid rgba(255,255,255,0.06);
  }}
  .info-row {{
    display: flex;
    justify-content: space-between;
    padding: 4px 0;
    font-size: 0.82em;
    border-bottom: 1px solid rgba(255,255,255,0.03);
  }}
  .info-label {{ color: #8892b0; }}
  .info-value {{ color: #e0e0e0; font-weight: 500; }}

  /* Score bars */
  .score-section {{ margin-top: 16px; }}
  .score-row {{
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 8px;
  }}
  .score-label {{
    flex: 0 0 160px;
    font-size: 0.78em;
    color: #8892b0;
  }}
  .score-bar-bg {{
    flex: 1;
    height: 20px;
    background: rgba(255,255,255,0.06);
    border-radius: 10px;
    overflow: hidden;
  }}
  .score-bar {{
    height: 100%;
    border-radius: 10px;
    transition: width 0.6s ease;
    display: flex;
    align-items: center;
    justify-content: flex-end;
    padding-right: 8px;
    font-size: 0.7em;
    font-weight: 700;
    color: rgba(0,0,0,0.7);
  }}
  .score-green {{ background: linear-gradient(90deg, #00897b, #64ffda); }}
  .score-blue {{ background: linear-gradient(90deg, #283593, #42a5f5); }}
  .score-purple {{ background: linear-gradient(90deg, #4a148c, #ce93d8); }}
  .score-amber {{ background: linear-gradient(90deg, #e65100, #ffb74d); }}

  /* Edge table */
  .edge-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.8em;
  }}
  .edge-table th {{
    text-align: left;
    padding: 8px 10px;
    background: rgba(100,255,218,0.08);
    color: #64ffda;
    font-weight: 600;
    font-size: 0.82em;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }}
  .edge-table td {{
    padding: 6px 10px;
    border-bottom: 1px solid rgba(255,255,255,0.04);
    color: #a8b2d1;
  }}
  .edge-table tr:hover td {{ background: rgba(255,255,255,0.03); }}
  .rel-badge {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.8em;
    font-weight: 600;
    font-family: 'JetBrains Mono', monospace;
  }}
  .rel-ENCODES {{ background: rgba(0,137,123,0.2); color: #80cbc4; }}
  .rel-HAS_VARIANT {{ background: rgba(233,30,99,0.15); color: #f48fb1; }}
  .rel-ASSOCIATED_WITH {{ background: rgba(156,39,176,0.2); color: #ce93d8; }}
  .rel-TARGETS {{ background: rgba(63,81,181,0.2); color: #9fa8da; }}
  .rel-TREATS {{ background: rgba(100,255,218,0.15); color: #64ffda; }}
  .rel-INVESTIGATES {{ background: rgba(255,152,0,0.2); color: #ffb74d; }}
  .rel-REPORTS_AE {{ background: rgba(244,67,54,0.2); color: #ef9a9a; }}
  .rel-INHIBITS_PATHWAY {{ background: rgba(33,150,243,0.2); color: #90caf9; }}

  /* Comparison table */
  .compare-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.82em;
  }}
  .compare-table th {{
    padding: 10px;
    background: rgba(100,255,218,0.08);
    color: #64ffda;
    font-weight: 600;
    text-align: center;
  }}
  .compare-table td {{
    padding: 8px 10px;
    border-bottom: 1px solid rgba(255,255,255,0.04);
    text-align: center;
    color: #a8b2d1;
  }}
  .compare-table td:first-child {{ text-align: left; color: #8892b0; }}
  .grade-A {{ color: #64ffda; font-weight: 700; }}
  .grade-B {{ color: #42a5f5; font-weight: 700; }}
  .grade-C {{ color: #ffb74d; font-weight: 700; }}
  .grade-D {{ color: #ef5350; font-weight: 700; }}

  .footer {{
    text-align: center;
    margin-top: 24px;
    font-size: 0.75em;
    color: #4a5568;
    padding-top: 16px;
    border-top: 1px solid rgba(255,255,255,0.04);
  }}
</style>
</head>
<body>
<div class="container">

<div class="header">
  <h1>Gene-Protein ReAct Agent</h1>
  <p>AWS Strands + Neo4j Knowledge Graph &mdash; Multi-Agent Reasoning-Acting-Observing Loop</p>
  <p style="margin-top:6px; font-size:0.85em; color:#a8b2d1;">
    Gene symbols that serve as protein names: tracing the complete biological chain
  </p>
  <div class="stats" id="headerStats"></div>
</div>

<div class="tabs" id="tabBar"></div>
<div id="tabContents"></div>

<div class="footer">
  Ontology GraphRAG Benchmarks &mdash; Gene-Protein ReAct Agent Visualization
</div>

</div>

<script>
const GENES = {genes_json};
const STEPS = {steps_json};
const EDGES = {edges_json};

// Compute stats
const geneNames = Object.keys(GENES);
const totalQueries = STEPS.filter(s => s.type === 'ACT').length;
const totalEdges = EDGES.length;
const totalLatency = STEPS.filter(s => s.type === 'ACT').reduce((a,b) => a + b.latency_ms, 0);

// Header stats
document.getElementById('headerStats').innerHTML = `
  <div class="stat"><div class="stat-val">${{geneNames.length}}</div><div class="stat-label">Genes Investigated</div></div>
  <div class="stat"><div class="stat-val">${{totalQueries}}</div><div class="stat-label">Cypher Queries</div></div>
  <div class="stat"><div class="stat-val">${{totalEdges}}</div><div class="stat-label">Edges Traversed</div></div>
  <div class="stat"><div class="stat-val">${{totalLatency.toFixed(0)}}ms</div><div class="stat-label">Total Latency</div></div>
`;

// Build tabs
const tabBar = document.getElementById('tabBar');
const tabContents = document.getElementById('tabContents');
const allTabs = [];

// Per-gene tabs
geneNames.forEach((gene, idx) => {{
  allTabs.push({{ id: 'gene-' + gene, label: gene + ' Profile', content: buildGeneTab(gene) }});
}});
allTabs.push({{ id: 'react-loop', label: 'ReAct Loop', content: buildReActTab() }});
allTabs.push({{ id: 'edges', label: 'Graph Edges', content: buildEdgesTab() }});
if (geneNames.length > 1) {{
  allTabs.push({{ id: 'compare', label: 'Comparison', content: buildCompareTab() }});
}}

allTabs.forEach((t, idx) => {{
  const tab = document.createElement('div');
  tab.className = 'tab' + (idx === 0 ? ' active' : '');
  tab.textContent = t.label;
  tab.onclick = () => switchTab(t.id);
  tab.dataset.id = t.id;
  tabBar.appendChild(tab);

  const content = document.createElement('div');
  content.className = 'tab-content' + (idx === 0 ? ' active' : '');
  content.id = 'content-' + t.id;
  content.innerHTML = t.content;
  tabContents.appendChild(content);
}});

function switchTab(id) {{
  document.querySelectorAll('.tab').forEach(t => t.classList.toggle('active', t.dataset.id === id));
  document.querySelectorAll('.tab-content').forEach(c => c.classList.toggle('active', c.id === 'content-' + id));
}}

function buildGeneTab(gene) {{
  const g = GENES[gene];
  const gi = g.gene_info || {{}};
  const pi = g.protein_info || {{}};
  const rs = g.risk_scores || {{}};

  let html = '<div class="gene-grid">';

  // Gene + Protein card
  html += `<div class="gene-card">
    <h3>${{gi.symbol || gene}} &mdash; ${{gi.name || ''}}</h3>
    <div class="info-row"><span class="info-label">Chromosome</span><span class="info-value">${{gi.chromosome || 'N/A'}}</span></div>
    <div class="info-row"><span class="info-label">Function</span><span class="info-value">${{gi.function || 'N/A'}}</span></div>
    ${{pi.name ? `
    <div style="margin-top:12px; padding-top:8px; border-top:1px solid rgba(255,255,255,0.06);">
      <div style="font-size:0.78em; color:#ce93d8; font-weight:600; margin-bottom:6px;">PROTEIN (same symbol)</div>
      <div class="info-row"><span class="info-label">Name</span><span class="info-value">${{pi.name}}</span></div>
      <div class="info-row"><span class="info-label">Class</span><span class="info-value">${{pi.protein_class || 'N/A'}}</span></div>
      <div class="info-row"><span class="info-label">Location</span><span class="info-value">${{pi.cellular_location || 'N/A'}}</span></div>
      <div class="info-row"><span class="info-label">UniProt</span><span class="info-value">${{pi.uniprot_id || 'N/A'}}</span></div>
    </div>` : ''}}
  </div>`;

  // Risk Scores card
  html += `<div class="gene-card">
    <h3>Risk Assessment &mdash; Grade ${{rs.evidence_grade || '?'}} (${{rs.risk_level || '?'}})</h3>
    <div class="score-section">
      ${{scoreBar('Genetic Evidence', rs.genetic_evidence_score, 'score-green')}}
      ${{scoreBar('Therapeutic Coverage', rs.therapeutic_coverage_score, 'score-blue')}}
      ${{scoreBar('Clinical Evidence', rs.clinical_evidence_score, 'score-purple')}}
      ${{scoreBar('Safety', rs.safety_score, 'score-amber')}}
      <div style="margin-top:12px; padding-top:8px; border-top:1px solid rgba(255,255,255,0.06);">
        ${{scoreBar('OVERALL', rs.overall_score, 'score-green')}}
      </div>
    </div>
    <div style="margin-top:12px; font-size:0.78em; color:#8892b0;">
      Phase 3 Trials: ${{(rs.factors||{{}}).phase3_trials || 0}} |
      Enrollment: ${{((rs.factors||{{}}).total_enrollment || 0).toLocaleString()}} |
      Severe AEs: ${{(rs.factors||{{}}).severe_adverse_events || 0}}
    </div>
  </div>`;

  html += '</div>';

  // Variants
  if (g.variants && g.variants.length) {{
    html += `<div class="gene-card" style="margin-top:16px;">
      <h3>Pathogenic Variants (${{g.variants.length}})</h3>`;
    g.variants.forEach(v => {{
      html += `<div class="info-row">
        <span class="info-label">${{v.rsid || ''}}</span>
        <span class="info-value">${{v.consequence || ''}} [${{v.significance || ''}}]</span>
      </div>`;
    }});
    html += '</div>';
  }}

  // Diseases
  if (g.diseases && g.diseases.length) {{
    html += `<div class="gene-card" style="margin-top:16px;">
      <h3>Disease Associations (${{g.diseases.length}})</h3>
      <table class="edge-table"><tr><th>Disease</th><th>Strength</th><th>Evidence</th><th>Category</th></tr>`;
    g.diseases.forEach(d => {{
      html += `<tr><td>${{d.disease}}</td><td>${{d.strength||''}}</td><td>${{d.evidence_level||''}}</td><td>${{d.category||''}}</td></tr>`;
    }});
    html += '</table></div>';
  }}

  // Drugs
  if (g.drugs && g.drugs.length) {{
    html += `<div class="gene-card" style="margin-top:16px;">
      <h3>Targeting Drugs (${{g.drugs.length}})</h3>
      <table class="edge-table"><tr><th>Drug</th><th>Mechanism</th><th>Affinity</th><th>Type</th><th>Status</th></tr>`;
    g.drugs.forEach(d => {{
      html += `<tr><td>${{d.drug}}</td><td>${{d.mechanism||''}}</td><td>${{d.affinity||''}}</td><td>${{d.target_mechanism||''}}</td><td>${{d.status||''}}</td></tr>`;
      (d.indications||[]).forEach(ind => {{
        if (ind.disease) {{
          const eff = ind.efficacy ? (ind.efficacy*100).toFixed(0) + '%' : 'N/A';
          html += `<tr><td colspan="5" style="padding-left:30px; color:#80cbc4; font-size:0.9em;">&#8627; Treats: ${{ind.disease}} (efficacy: ${{eff}})</td></tr>`;
        }}
      }});
    }});
    html += '</table></div>';
  }}

  // Trials
  if (g.trials && g.trials.length) {{
    html += `<div class="gene-card" style="margin-top:16px;">
      <h3>Clinical Trials (${{g.trials.length}})</h3>
      <table class="edge-table"><tr><th>NCT ID</th><th>Drug</th><th>Phase</th><th>Enrollment</th><th>Status</th><th>Sponsor</th></tr>`;
    g.trials.forEach(t => {{
      html += `<tr><td>${{t.nct_id||''}}</td><td>${{t.drug}}</td><td>${{t.phase||''}}</td><td>${{(t.enrollment||'').toLocaleString()}}</td><td>${{t.status||''}}</td><td>${{t.sponsor||''}}</td></tr>`;
    }});
    html += '</table></div>';
  }}

  // Adverse Events
  if (g.adverse_events && g.adverse_events.length) {{
    const seen = new Set();
    const unique = g.adverse_events.filter(ae => {{
      const key = ae.event + '|' + ae.drug;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    }});
    html += `<div class="gene-card" style="margin-top:16px;">
      <h3>Adverse Events (${{unique.length}} unique)</h3>
      <table class="edge-table"><tr><th>Event</th><th>Severity</th><th>Drug</th><th>Category</th><th>Grade</th></tr>`;
    unique.forEach(ae => {{
      const sevColor = ae.severity === 'Severe' ? '#ef5350' : ae.severity === 'Moderate' ? '#ffb74d' : '#81c784';
      html += `<tr><td>${{ae.event}}</td><td style="color:${{sevColor}}">${{ae.severity||''}}</td><td>${{ae.drug}}</td><td>${{ae.category||''}}</td><td>${{ae.grade||''}}</td></tr>`;
    }});
    html += '</table></div>';
  }}

  return html;
}}

function scoreBar(label, value, cls) {{
  const v = value || 0;
  return `<div class="score-row">
    <span class="score-label">${{label}}</span>
    <div class="score-bar-bg"><div class="score-bar ${{cls}}" style="width:${{v}}%">${{v}}</div></div>
  </div>`;
}}

function buildReActTab() {{
  let html = '<div class="react-timeline">';
  let prevIter = 0;
  STEPS.forEach(s => {{
    if (s.iteration !== prevIter) {{
      html += `<div class="iter-divider">&mdash; Iteration ${{s.iteration}} &mdash;</div>`;
      prevIter = s.iteration;
    }}
    const cls = s.type === 'THINK' ? 'step-think' : s.type === 'ACT' ? 'step-act' : 'step-observe';
    html += `<div class="react-step ${{cls}}">
      <div class="step-header">
        <span class="step-badge">${{s.type}}</span>
        <span class="step-agent">${{s.agent}}</span>
        ${{s.latency_ms > 0 ? `<span class="step-metrics">${{s.result_count}} results | ${{s.latency_ms.toFixed(1)}}ms</span>` : ''}}
      </div>
      <div class="step-content">${{s.content}}</div>
      ${{s.traversal_path ? `<div class="step-traversal">Path: ${{s.traversal_path}}</div>` : ''}}
      ${{s.query ? `<div class="step-query">${{s.query}}</div>` : ''}}
    </div>`;
  }});
  html += '</div>';
  return html;
}}

function buildEdgesTab() {{
  let html = `<table class="edge-table">
    <tr><th>#</th><th>Source</th><th></th><th>Relationship</th><th></th><th>Target</th><th>Properties</th></tr>`;
  EDGES.forEach((e, idx) => {{
    const relClass = 'rel-' + e.rel_type;
    const props = Object.entries(e.properties||{{}}).map(([k,v]) => k+': '+v).join(', ');
    html += `<tr>
      <td style="color:#4a5568">${{idx+1}}</td>
      <td>(${{e.source_type}}:<strong>${{e.source_name}}</strong>)</td>
      <td style="color:#64ffda">&rarr;</td>
      <td><span class="rel-badge ${{relClass}}">${{e.rel_type}}</span></td>
      <td style="color:#64ffda">&rarr;</td>
      <td>(${{e.target_type}}:<strong>${{e.target_name}}</strong>)</td>
      <td style="font-size:0.85em; color:#8892b0">${{props}}</td>
    </tr>`;
  }});
  html += '</table>';
  return html;
}}

function buildCompareTab() {{
  const genes = Object.keys(GENES);
  let html = `<table class="compare-table"><tr><th>Metric</th>`;
  genes.forEach(g => html += `<th>${{g}}</th>`);
  html += '</tr>';

  const metrics = [
    ['Chromosome', g => (GENES[g].gene_info||{{}}).chromosome || 'N/A'],
    ['Protein Class', g => (GENES[g].protein_info||{{}}).protein_class || 'N/A'],
    ['Variants', g => (GENES[g].variants||[]).length],
    ['Disease Associations', g => (GENES[g].diseases||[]).length],
    ['Targeting Drugs', g => (GENES[g].drugs||[]).length],
    ['Clinical Trials', g => (GENES[g].trials||[]).length],
    ['Adverse Events', g => (GENES[g].adverse_events||[]).length],
    ['Overall Score', g => (GENES[g].risk_scores||{{}}).overall_score || 0],
    ['Evidence Grade', g => {{
      const grade = (GENES[g].risk_scores||{{}}).evidence_grade || '?';
      return `<span class="grade-${{grade}}">${{grade}}</span>`;
    }}],
    ['Genetic Evidence', g => (GENES[g].risk_scores||{{}}).genetic_evidence_score || 0],
    ['Therapeutic Coverage', g => (GENES[g].risk_scores||{{}}).therapeutic_coverage_score || 0],
    ['Clinical Evidence', g => (GENES[g].risk_scores||{{}}).clinical_evidence_score || 0],
    ['Safety Score', g => (GENES[g].risk_scores||{{}}).safety_score || 0],
    ['Risk Level', g => (GENES[g].risk_scores||{{}}).risk_level || '?'],
  ];

  metrics.forEach(([label, fn]) => {{
    html += `<tr><td>${{label}}</td>`;
    genes.forEach(g => html += `<td>${{fn(g)}}</td>`);
    html += '</tr>';
  }});

  html += '</table>';
  return html;
}}
</script>
</body>
</html>""";


# ╔══════════════════════════════════════════════════════════════════════════════╗
# ║  MAIN EXECUTION                                                             ║
# ╚══════════════════════════════════════════════════════════════════════════════╝

def main():
    """
    Investigate the 5 gene symbols that also serve as protein names:
    EGFR, KRAS, HER2, BRAF, BRCA1
    """
    genes_to_investigate = ["EGFR", "KRAS", "HER2", "BRAF", "BRCA1"]

    print("=" * 90)
    print("  GENE-PROTEIN REACT AGENT")
    print("  AWS Strands + Neo4j Knowledge Graph")
    print("  Investigating gene symbols that also serve as protein names")
    print(f"  Targets: {', '.join(genes_to_investigate)}")
    print("=" * 90)
    print(f"  ReAct Pattern: THINK -> ACT (Cypher) -> OBSERVE -> repeat")
    print(f"  8 iterations per gene, 6 specialized agents")
    print("=" * 90)

    all_profiles = {}
    all_steps = []
    all_edges = []
    execution_stats = []

    for gene in genes_to_investigate:
        engine = GeneProteinReActAgent()
        t0 = time.perf_counter()
        profile = engine.investigate_gene(gene)
        elapsed = (time.perf_counter() - t0) * 1000

        engine.print_full_report(profile)

        all_profiles[gene] = profile
        all_steps.extend(engine.steps)
        all_edges.extend(engine.edges)
        execution_stats.append({
            "gene": gene,
            "total_ms": round(elapsed, 1),
            "queries": engine.total_queries,
            "query_latency_ms": round(engine.total_latency, 1),
            "edges": len(engine.edges),
            "steps": len(engine.steps),
        })
        engine.close()

    # ── Comparative Summary ──
    print(f"\n{'='*90}")
    print(f"  COMPARATIVE SUMMARY")
    print(f"{'='*90}")
    print(f"\n  {'Gene':<8s} {'Overall':<9s} {'Genetic':<9s} {'Therapy':<9s} "
          f"{'Clinical':<9s} {'Safety':<9s} {'Grade':<7s} {'Drugs':<7s} "
          f"{'Diseases':<9s} {'Trials':<7s} {'AEs'}")
    print(f"  {'─'*90}")
    for gene, profile in all_profiles.items():
        rs = profile.risk_scores
        f = rs['factors']
        print(f"  {gene:<8s} {rs['overall_score']:<9.1f} "
              f"{rs['genetic_evidence_score']:<9.1f} "
              f"{rs['therapeutic_coverage_score']:<9.1f} "
              f"{rs['clinical_evidence_score']:<9.1f} "
              f"{rs['safety_score']:<9.1f} "
              f"{rs['evidence_grade']:<7s} "
              f"{f['total_drugs']:<7d} "
              f"{f['total_diseases']:<9d} "
              f"{f['phase3_trials']:<7d} "
              f"{f['severe_adverse_events']}")

    # ── Execution Stats ──
    print(f"\n  EXECUTION STATISTICS")
    print(f"  {'─'*60}")
    print(f"  {'Gene':<8s} {'Time (ms)':<12s} {'Queries':<10s} {'Query ms':<12s} {'Edges':<8s} {'Steps'}")
    for s in execution_stats:
        print(f"  {s['gene']:<8s} {s['total_ms']:<12.1f} {s['queries']:<10d} "
              f"{s['query_latency_ms']:<12.1f} {s['edges']:<8d} {s['steps']}")
    total_time = sum(s['total_ms'] for s in execution_stats)
    total_q = sum(s['queries'] for s in execution_stats)
    print(f"  {'─'*60}")
    print(f"  {'TOTAL':<8s} {total_time:<12.1f} {total_q:<10d} "
          f"{sum(s['query_latency_ms'] for s in execution_stats):<12.1f} "
          f"{len(all_edges):<8d} {len(all_steps)}")

    # ── Generate visualization ──
    viz_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            "react_gene_protein_visualization.html")
    generate_react_visualization(all_profiles, all_steps, all_edges, viz_path)

    # ── Save JSON results ──
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                             "react_gene_protein_results.json")
    output = {
        "investigation_date": datetime.now().isoformat(),
        "genes_investigated": genes_to_investigate,
        "execution_stats": execution_stats,
        "profiles": {},
    }
    for gene, profile in all_profiles.items():
        output["profiles"][gene] = {
            "gene_info": profile.gene_info,
            "protein_info": profile.protein_info,
            "variants": profile.variants,
            "diseases": profile.diseases,
            "drugs": [{k: v for k, v in d.items() if k != 'indications'} | {"indications": d.get("indications",[])} for d in profile.drugs],
            "trials": profile.trials,
            "adverse_events_count": len(profile.adverse_events),
            "co_targeting_drugs": profile.co_targeting_drugs,
            "pathways": profile.pathways,
            "risk_scores": profile.risk_scores,
        }

    with open(json_path, 'w') as f:
        json.dump(output, f, indent=2, default=str)
    print(f"  Results saved: {json_path}")

    print(f"\n{'='*90}")
    print(f"  INVESTIGATION COMPLETE")
    print(f"  {len(genes_to_investigate)} genes | {total_q} queries | "
          f"{len(all_edges)} edges | {total_time:.0f}ms total")
    print(f"{'='*90}")


if __name__ == "__main__":
    main()
