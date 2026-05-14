#!/usr/bin/env python3
"""
AWS Strands Multi-Agent Framework with Hop-by-Hop Visualization

Integrates the visualizer with the actual Strands implementation
Shows animated traversal for all 5 use cases
"""

import os
import time
from datetime import datetime
from neo4j import GraphDatabase
from dotenv import load_dotenv
from strands_visualizer import StrandsVisualizer, Hop, GraphPathVisualizer


class VisualizedStrandsOrchestrator:
    """Strands orchestrator with built-in visualization"""

    def __init__(self):
        load_dotenv()

        # Neo4j connection
        self.neo4j_driver = GraphDatabase.driver(
            os.getenv('NEO4J_URI'),
            auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
        )

        # Visualizer
        self.visualizer = StrandsVisualizer()

        # Register all agents
        self._register_agents()

        print("✓ Visualized Strands Orchestrator initialized")

    def _register_agents(self):
        """Register all agents with visualizer"""
        agents = [
            ("ClinicalSafetyAgent", "Clinical Safety Specialist"),
            ("PharmacologyAgent", "Pharmacology Specialist"),
            ("GeneticsAgent", "Genetics Specialist"),
            ("TrialDataAgent", "Clinical Trial Specialist"),
            ("ResearchAnalystAgent", "Research Analyst"),
            ("PublicationAgent", "Publication Analyst"),
            ("RepurposingAgent", "Drug Repurposing Specialist"),
            ("ComparativeAnalystAgent", "Comparative Analyst"),
            ("EvidenceValidatorAgent", "Evidence Validator")
        ]

        for name, role in agents:
            self.visualizer.register_agent(name, role)

    def execute_query_with_viz(self, from_agent: str, to_agent: str, action: str,
                                cypher_query: str, parameters: dict,
                                reasoning: str) -> list:
        """Execute a Neo4j query with visualization"""
        start_time = time.time()

        # Execute query
        with self.neo4j_driver.session() as session:
            result = session.run(cypher_query, parameters)
            results = [dict(record) for record in result]

        processing_time = (time.time() - start_time) * 1000  # Convert to ms

        # Record hop
        hop = Hop(
            hop_number=len(self.visualizer.hops) + 1,
            timestamp=datetime.now(),
            from_agent=from_agent,
            to_agent=to_agent,
            action=action,
            cypher_query=cypher_query,
            parameters=parameters,
            results=results,
            processing_time_ms=processing_time,
            data_transferred={"results_count": len(results)},
            reasoning=reasoning
        )

        self.visualizer.record_hop(hop)

        return results

    # ========================================================================
    # USE CASE 1: Clinical Safety Analysis
    # ========================================================================

    def clinical_safety_workflow(self, drug: str, patient_context: dict):
        """Execute clinical safety workflow with visualization"""

        self.visualizer.start_workflow(f"Clinical Safety: {drug}")

        # HOP 1: Get drug mechanism
        results_1 = self.execute_query_with_viz(
            from_agent="ClinicalSafetyAgent",
            to_agent="PharmacologyAgent",
            action="Get drug mechanism and protein targets",
            cypher_query="""
            MATCH (d:Drug {name: $drug})-[t:TARGETS]->(p:Protein)
            RETURN d.mechanism as mechanism, d.approvalStatus as status,
                   collect({protein: p.name, class: p.proteinClass,
                           affinity: t.bindingAffinity}) as targets
            """,
            parameters={"drug": drug},
            reasoning="Need to understand drug mechanism before assessing safety"
        )

        # HOP 2: Get adverse events
        results_2 = self.execute_query_with_viz(
            from_agent="ClinicalSafetyAgent",
            to_agent="TrialDataAgent",
            action="Retrieve adverse events from clinical trials",
            cypher_query="""
            MATCH (d:Drug {name: $drug})<-[:INVESTIGATES]-(t:ClinicalTrial)
                  -[:REPORTS]->(e:AdverseEvent)
            RETURN e.name as event, e.severity as severity,
                   e.frequency as frequency, e.category as category,
                   collect(DISTINCT t.title) as trials
            ORDER BY
                CASE e.severity
                    WHEN 'Severe' THEN 1
                    WHEN 'Moderate' THEN 2
                    WHEN 'Mild' THEN 3
                END
            """,
            parameters={"drug": drug},
            reasoning="Assess adverse event profile from trial data"
        )

        # HOP 3: Check drug interactions
        results_3 = self.execute_query_with_viz(
            from_agent="ClinicalSafetyAgent",
            to_agent="PharmacologyAgent",
            action="Check potential drug interactions",
            cypher_query="""
            MATCH (d1:Drug {name: $drug})-[:TARGETS]->(p:Protein)
                  <-[:TARGETS]-(d2:Drug)
            WHERE d1 <> d2
            RETURN d2.name as interacting_drug, p.name as shared_target,
                   d2.mechanism as mechanism
            """,
            parameters={"drug": drug},
            reasoning="Identify drugs with overlapping targets"
        )

        # HOP 4: Validate genetic evidence (if mutation provided)
        if "genetic_mutation" in patient_context:
            results_4 = self.execute_query_with_viz(
                from_agent="ClinicalSafetyAgent",
                to_agent="GeneticsAgent",
                action=f"Validate {patient_context['genetic_mutation']} mutation match",
                cypher_query="""
                MATCH (g:Gene {symbol: $gene})-[a:ASSOCIATED_WITH]->(d:Disease)
                      <-[tr:TREATS]-(drug:Drug {name: $drug})
                RETURN g.symbol as gene, g.name as geneName,
                       d.name as disease,
                       a.associationStrength as geneticStrength,
                       a.evidenceLevel as evidenceLevel,
                       tr.efficacyRate as efficacy
                """,
                parameters={
                    "drug": drug,
                    "gene": patient_context["genetic_mutation"]
                },
                reasoning="Validate drug efficacy for patient's genetic profile"
            )
        else:
            results_4 = []

        # Synthesize results
        severe_events = [e for e in results_2 if e.get("severity") == "Severe"]
        risk_score = len(severe_events) * 15 + len(results_2) * 3
        risk_level = "HIGH" if risk_score > 50 else "MODERATE" if risk_score > 25 else "LOW"

        report = {
            "drug": drug,
            "patient_context": patient_context,
            "mechanism": results_1[0] if results_1 else {},
            "risk_assessment": {
                "risk_score": risk_score,
                "risk_level": risk_level,
                "severe_events_count": len(severe_events),
                "total_events_count": len(results_2)
            },
            "adverse_events": results_2[:10],
            "drug_interactions": results_3,
            "genetic_validation": results_4[0] if results_4 else None
        }

        self.visualizer.generate_summary()
        return report

    # ========================================================================
    # USE CASE 2: Drug Repurposing
    # ========================================================================

    def drug_repurposing_workflow(self, source_disease: str, target_disease: str):
        """Execute drug repurposing workflow with visualization"""

        self.visualizer.start_workflow(f"Drug Repurposing: {source_disease} → {target_disease}")

        # HOP 1: Find drugs treating source disease
        results_1 = self.execute_query_with_viz(
            from_agent="RepurposingAgent",
            to_agent="PharmacologyAgent",
            action=f"Find drugs treating {source_disease}",
            cypher_query="""
            MATCH (d:Drug)-[t:TREATS]->(dis:Disease)
            WHERE dis.name CONTAINS $source_disease
            RETURN d.name as drug, d.mechanism as mechanism,
                   t.efficacyRate as efficacy, dis.name as disease
            ORDER BY t.efficacyRate DESC
            """,
            parameters={"source_disease": source_disease},
            reasoning="Identify candidate drugs from source disease"
        )

        # HOP 2: Check genetic overlap between diseases
        results_2 = self.execute_query_with_viz(
            from_agent="RepurposingAgent",
            to_agent="GeneticsAgent",
            action="Analyze genetic overlap between diseases",
            cypher_query="""
            MATCH (g:Gene)-[:ASSOCIATED_WITH]->(d1:Disease)
            WHERE d1.name CONTAINS $source_disease

            MATCH (g)-[a:ASSOCIATED_WITH]->(d2:Disease)
            WHERE d2.name CONTAINS $target_disease

            RETURN g.symbol as sharedGene, g.name as geneName,
                   d1.name as sourceDisease, d2.name as targetDisease,
                   a.associationStrength as strength
            """,
            parameters={
                "source_disease": source_disease,
                "target_disease": target_disease
            },
            reasoning="Validate genetic similarity between diseases"
        )

        # Visualize gene-disease paths
        if results_2:
            GraphPathVisualizer.visualize_path(results_2, "gene_to_treatment")
            time.sleep(2)

        # HOP 3: Find drugs targeting relevant pathways
        results_3 = self.execute_query_with_viz(
            from_agent="RepurposingAgent",
            to_agent="PharmacologyAgent",
            action="Map drug targets to disease pathways",
            cypher_query="""
            MATCH (d:Drug)-[:TREATS]->(dis1:Disease)
            WHERE dis1.name CONTAINS $source_disease

            MATCH (d)-[t:TARGETS]->(p:Protein)

            OPTIONAL MATCH (g:Gene)-[:ASSOCIATED_WITH]->(dis2:Disease)
            WHERE dis2.name CONTAINS $target_disease

            RETURN DISTINCT d.name as drug, d.mechanism as mechanism,
                   collect(DISTINCT p.name) as targetProteins,
                   collect(DISTINCT g.symbol) as relevantGenes
            """,
            parameters={
                "source_disease": source_disease,
                "target_disease": target_disease
            },
            reasoning="Validate pathway relevance for target disease"
        )

        # HOP 4: Score candidates
        results_4 = self.execute_query_with_viz(
            from_agent="RepurposingAgent",
            to_agent="EvidenceValidatorAgent",
            action="Score repurposing candidates",
            cypher_query="""
            MATCH (d:Drug)-[t:TREATS]->(dis:Disease)
            WHERE dis.name CONTAINS $source_disease
            RETURN d.name as drug, t.efficacyRate as efficacy
            ORDER BY t.efficacyRate DESC
            LIMIT 5
            """,
            parameters={"source_disease": source_disease},
            reasoning="Rank candidates by evidence strength"
        )

        report = {
            "source_disease": source_disease,
            "target_disease": target_disease,
            "genetic_overlap": {
                "shared_genes": len(results_2),
                "genes": [r["sharedGene"] for r in results_2]
            },
            "candidate_drugs": results_1[:5],
            "pathway_mapping": results_3
        }

        self.visualizer.generate_summary()
        return report

    # ========================================================================
    # USE CASE 3: Research Landscape
    # ========================================================================

    def research_landscape_workflow(self, disease: str):
        """Execute research landscape workflow with visualization"""

        self.visualizer.start_workflow(f"Research Landscape: {disease}")

        # HOP 1: Find top researchers
        results_1 = self.execute_query_with_viz(
            from_agent="ResearchAnalystAgent",
            to_agent="ResearchAnalystAgent",
            action=f"Identify top researchers in {disease}",
            cypher_query="""
            MATCH (r:Researcher)-[:AFFILIATED_WITH]->(i:Institution)
            WHERE r.specialization CONTAINS $disease OR
                  r.specialization CONTAINS $category
            RETURN r.name as researcher, r.hIndex as hIndex,
                   r.totalPublications as publications,
                   r.specialization as specialization,
                   i.name as institution
            ORDER BY r.hIndex DESC
            LIMIT 10
            """,
            parameters={
                "disease": disease,
                "category": disease.split()[-1]
            },
            reasoning="Identify leading researchers by h-index"
        )

        # HOP 2: Map clinical trials
        results_2 = self.execute_query_with_viz(
            from_agent="ResearchAnalystAgent",
            to_agent="TrialDataAgent",
            action="Map clinical trial landscape",
            cypher_query="""
            MATCH (t:ClinicalTrial)-[:STUDIES]->(dis:Disease)
            WHERE dis.name CONTAINS $disease

            MATCH (t)-[:INVESTIGATES]->(d:Drug)

            OPTIONAL MATCH (i:Institution)-[:SPONSORS]->(t)

            RETURN t.title as trial, t.phase as phase, t.status as status,
                   t.enrollment as enrollment, t.sponsor as primarySponsor,
                   d.name as drug, dis.name as disease,
                   i.name as institutionSponsor
            ORDER BY t.enrollment DESC
            """,
            parameters={"disease": disease},
            reasoning="Map institutional investment in clinical trials"
        )

        # Visualize trial network
        if results_2:
            GraphPathVisualizer.visualize_path(results_2, "trial_network")
            time.sleep(2)

        # HOP 3: Analyze publications
        results_3 = self.execute_query_with_viz(
            from_agent="ResearchAnalystAgent",
            to_agent="PublicationAgent",
            action="Analyze research publications",
            cypher_query="""
            MATCH (p:ResearchPaper)-[:MENTIONS_DISEASE]->(dis:Disease)
            WHERE dis.name CONTAINS $disease

            MATCH (p)-[:AUTHORED_BY]->(r:Researcher)-[:AFFILIATED_WITH]->(i:Institution)

            OPTIONAL MATCH (p)-[:MENTIONS_DRUG]->(d:Drug)

            RETURN p.title as paper, p.year as year, p.journal as journal,
                   collect(DISTINCT r.name) as authors,
                   collect(DISTINCT i.name) as institutions,
                   collect(DISTINCT d.name) as drugsDiscussed
            ORDER BY p.year DESC
            """,
            parameters={"disease": disease},
            reasoning="Analyze publication trends and collaboration"
        )

        report = {
            "disease": disease,
            "research_leaders": results_1[:5],
            "clinical_trials": results_2,
            "publications": results_3,
            "institutions": list(set([r["institution"] for r in results_1]))
        }

        self.visualizer.generate_summary()
        return report

    # ========================================================================
    # USE CASE 4: Comparative Analysis
    # ========================================================================

    def comparative_analysis_workflow(self, drug1: str, drug2: str):
        """Execute comparative analysis workflow with visualization"""

        self.visualizer.start_workflow(f"Comparison: {drug1} vs {drug2}")

        # HOP 1: Compare mechanisms and targets
        results_1 = self.execute_query_with_viz(
            from_agent="ComparativeAnalystAgent",
            to_agent="PharmacologyAgent",
            action="Compare drug mechanisms and targets",
            cypher_query="""
            MATCH (d:Drug)-[t:TARGETS]->(p:Protein)
            WHERE d.name IN [$drug1, $drug2]
            RETURN d.name as drug, d.mechanism as mechanism,
                   collect({protein: p.name, class: p.proteinClass,
                           affinity: t.bindingAffinity}) as targets
            """,
            parameters={"drug1": drug1, "drug2": drug2},
            reasoning="Compare molecular mechanisms and protein targets"
        )

        # HOP 2: Compare adverse events
        results_2 = self.execute_query_with_viz(
            from_agent="ComparativeAnalystAgent",
            to_agent="TrialDataAgent",
            action="Compare adverse event profiles",
            cypher_query="""
            MATCH (d:Drug)<-[:INVESTIGATES]-(t:ClinicalTrial)-[:REPORTS]->(e:AdverseEvent)
            WHERE d.name IN [$drug1, $drug2]
            RETURN d.name as drug, e.name as event, e.severity as severity,
                   e.frequency as frequency, count(DISTINCT t) as trialsReporting
            ORDER BY d.name,
                CASE e.severity
                    WHEN 'Severe' THEN 1
                    WHEN 'Moderate' THEN 2
                    WHEN 'Mild' THEN 3
                END
            """,
            parameters={"drug1": drug1, "drug2": drug2},
            reasoning="Compare safety profiles across clinical trials"
        )

        # HOP 3: Compare efficacy
        results_3 = self.execute_query_with_viz(
            from_agent="ComparativeAnalystAgent",
            to_agent="EvidenceValidatorAgent",
            action="Compare efficacy rates",
            cypher_query="""
            MATCH (d:Drug)-[tr:TREATS]->(dis:Disease)
            WHERE d.name IN [$drug1, $drug2]
            RETURN d.name as drug, dis.name as disease,
                   tr.efficacyRate as efficacy
            ORDER BY dis.name, tr.efficacyRate DESC
            """,
            parameters={"drug1": drug1, "drug2": drug2},
            reasoning="Compare treatment efficacy across diseases"
        )

        # Visualize drug-disease paths
        if results_3:
            GraphPathVisualizer.visualize_path(results_3, "drug_to_disease")
            time.sleep(2)

        # Calculate comparison
        drug1_severe = len([e for e in results_2 if e["drug"] == drug1 and e["severity"] == "Severe"])
        drug2_severe = len([e for e in results_2 if e["drug"] == drug2 and e["severity"] == "Severe"])

        report = {
            "drug1": drug1,
            "drug2": drug2,
            "mechanism_comparison": results_1,
            "safety_comparison": {
                "safer_drug": drug1 if drug1_severe < drug2_severe else drug2,
                f"{drug1}_severe_events": drug1_severe,
                f"{drug2}_severe_events": drug2_severe,
                "all_events": results_2
            },
            "efficacy_comparison": results_3
        }

        self.visualizer.generate_summary()
        return report

    # ========================================================================
    # USE CASE 5: Evidence Chain
    # ========================================================================

    def evidence_chain_workflow(self, gene: str):
        """Execute evidence chain workflow with visualization"""

        self.visualizer.start_workflow(f"Evidence Chain: {gene} gene")

        # HOP 1: Get gene information
        results_1 = self.execute_query_with_viz(
            from_agent="EvidenceValidatorAgent",
            to_agent="GeneticsAgent",
            action=f"Retrieve {gene} gene information",
            cypher_query="""
            MATCH (g:Gene {symbol: $gene})
            RETURN g.symbol as symbol, g.name as name,
                   g.chromosome as chromosome, g.function as function
            """,
            parameters={"gene": gene},
            reasoning="Establish genetic foundation"
        )

        # HOP 2: Find disease associations
        results_2 = self.execute_query_with_viz(
            from_agent="EvidenceValidatorAgent",
            to_agent="GeneticsAgent",
            action="Find disease associations",
            cypher_query="""
            MATCH (g:Gene {symbol: $gene})-[a:ASSOCIATED_WITH]->(d:Disease)
            RETURN g.symbol as gene, d.name as disease, d.category as category,
                   d.prevalence as prevalence,
                   a.associationStrength as strength,
                   a.evidenceLevel as evidenceLevel
            ORDER BY
                CASE a.associationStrength
                    WHEN 'Very Strong' THEN 1
                    WHEN 'Strong' THEN 2
                    WHEN 'Moderate' THEN 3
                END
            """,
            parameters={"gene": gene},
            reasoning="Identify diseases with genetic evidence"
        )

        # HOP 3: Find treatments
        results_3 = self.execute_query_with_viz(
            from_agent="EvidenceValidatorAgent",
            to_agent="PharmacologyAgent",
            action="Find treatments for associated diseases",
            cypher_query="""
            MATCH (g:Gene {symbol: $gene})-[:ASSOCIATED_WITH]->(d:Disease)
                  <-[tr:TREATS]-(drug:Drug)
            RETURN g.symbol as gene, d.name as disease,
                   drug.name as drug, drug.mechanism as mechanism,
                   drug.approvalStatus as status,
                   tr.efficacyRate as efficacy
            ORDER BY tr.efficacyRate DESC
            """,
            parameters={"gene": gene},
            reasoning="Map therapeutic interventions"
        )

        # Visualize complete chain
        if results_3:
            GraphPathVisualizer.visualize_path(results_3, "gene_to_treatment")
            time.sleep(2)

        # HOP 4: Find clinical trials
        results_4 = self.execute_query_with_viz(
            from_agent="EvidenceValidatorAgent",
            to_agent="TrialDataAgent",
            action="Find supporting clinical trials",
            cypher_query="""
            MATCH (g:Gene {symbol: $gene})-[:ASSOCIATED_WITH]->(dis:Disease)
                  <-[:STUDIES]-(t:ClinicalTrial)-[:INVESTIGATES]->(d:Drug)
            RETURN g.symbol as gene, dis.name as disease, d.name as drug,
                   t.title as trial, t.phase as phase, t.status as status,
                   t.enrollment as enrollment, t.nctId as nctId
            ORDER BY t.enrollment DESC
            """,
            parameters={"gene": gene},
            reasoning="Validate with clinical evidence"
        )

        # HOP 5: Map institutional investment
        results_5 = self.execute_query_with_viz(
            from_agent="EvidenceValidatorAgent",
            to_agent="ResearchAnalystAgent",
            action="Map institutional investment",
            cypher_query="""
            MATCH (g:Gene {symbol: $gene})-[:ASSOCIATED_WITH]->(dis:Disease)
                  <-[:STUDIES]-(t:ClinicalTrial)<-[:SPONSORS]-(i:Institution)
            RETURN i.name as institution, count(t) as trialsSponsored,
                   collect(DISTINCT dis.name) as diseases,
                   collect(DISTINCT t.phase) as phases
            ORDER BY trialsSponsored DESC
            """,
            parameters={"gene": gene},
            reasoning="Assess research investment"
        )

        report = {
            "gene": gene,
            "gene_info": results_1[0] if results_1 else {},
            "diseases": results_2,
            "treatments": results_3,
            "clinical_trials": results_4,
            "institutions": results_5,
            "chain_complete": len(results_2) > 0 and len(results_3) > 0 and len(results_4) > 0
        }

        self.visualizer.generate_summary()
        return report

    def close(self):
        """Close connections"""
        self.neo4j_driver.close()


# ========================================================================
# MAIN DEMO
# ========================================================================

def main():
    """Run all 5 use cases with visualization"""

    orchestrator = VisualizedStrandsOrchestrator()

    print("\n🎬 Starting Visualized Strands Demonstration")
    print("="*80)

    # USE CASE 1
    print("\n\n[1/5] Clinical Safety Analysis...")
    input("Press Enter to start → ")

    report1 = orchestrator.clinical_safety_workflow(
        drug="Pembrolizumab",
        patient_context={
            "genetic_mutation": "EGFR",
            "previous_treatment": "Nivolumab"
        }
    )

    orchestrator.visualizer.export_trace("trace_clinical_safety.json")
    input("\nPress Enter to continue to next use case → ")

    # USE CASE 2
    print("\n\n[2/5] Drug Repurposing...")
    input("Press Enter to start → ")

    report2 = orchestrator.drug_repurposing_workflow(
        source_disease="Lung Cancer",
        target_disease="Colorectal Cancer"
    )

    orchestrator.visualizer.export_trace("trace_repurposing.json")
    input("\nPress Enter to continue to next use case → ")

    # USE CASE 3
    print("\n\n[3/5] Research Landscape...")
    input("Press Enter to start → ")

    report3 = orchestrator.research_landscape_workflow("Alzheimer")

    orchestrator.visualizer.export_trace("trace_research_landscape.json")
    input("\nPress Enter to continue to next use case → ")

    # USE CASE 4
    print("\n\n[4/5] Comparative Analysis...")
    input("Press Enter to start → ")

    report4 = orchestrator.comparative_analysis_workflow(
        drug1="Pembrolizumab",
        drug2="Nivolumab"
    )

    orchestrator.visualizer.export_trace("trace_comparative.json")
    input("\nPress Enter to continue to next use case → ")

    # USE CASE 5
    print("\n\n[5/5] Evidence Chain...")
    input("Press Enter to start → ")

    report5 = orchestrator.evidence_chain_workflow("BRCA1")

    orchestrator.visualizer.export_trace("trace_evidence_chain.json")

    orchestrator.close()

    print("\n\n" + "="*80)
    print("🎉 ALL USE CASES COMPLETE!")
    print("="*80)
    print("\nTrace files exported:")
    print("  - trace_clinical_safety.json")
    print("  - trace_repurposing.json")
    print("  - trace_research_landscape.json")
    print("  - trace_comparative.json")
    print("  - trace_evidence_chain.json")
    print("\nYou can replay these traces or visualize them in a web interface!")


if __name__ == "__main__":
    main()
