#!/usr/bin/env python3
"""
AWS Strands Multi-Agent Framework Implementation
https://strandsagents.com/

Strands provides multi-agent orchestration with:
- Autonomous agents with specialized roles
- Agent-to-agent communication
- Shared memory and state
- Parallel execution
- Tool integration (Neo4j queries)
"""

import os
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
from neo4j import GraphDatabase
from dotenv import load_dotenv
import boto3


# ============================================================================
# STRANDS AGENT FRAMEWORK COMPONENTS
# ============================================================================

@dataclass
class StrandsMessage:
    """Message passed between agents in Strands"""
    from_agent: str
    to_agent: str
    message_type: str  # "task", "result", "question", "answer"
    content: Dict[str, Any]
    priority: int = 1  # 1=high, 2=medium, 3=low


@dataclass
class StrandsMemory:
    """Shared memory accessible to all agents"""
    facts: Dict[str, Any]
    conversations: List[StrandsMessage]
    evidence: List[Dict[str, Any]]
    decisions: List[Dict[str, Any]]


class StrandsAgent:
    """
    Base class for Strands autonomous agents

    Each agent has:
    - Role and specialization
    - Access to shared memory
    - Tools (Neo4j queries, AWS Bedrock)
    - Ability to communicate with other agents
    """

    def __init__(self, name: str, role: str, tools: List[str]):
        self.name = name
        self.role = role
        self.tools = tools
        self.memory: Optional[StrandsMemory] = None
        self.inbox: List[StrandsMessage] = []

    def attach_memory(self, memory: StrandsMemory):
        """Attach shared memory"""
        self.memory = memory

    def send_message(self, to_agent: str, message_type: str,
                     content: Dict[str, Any], priority: int = 1):
        """Send message to another agent"""
        msg = StrandsMessage(
            from_agent=self.name,
            to_agent=to_agent,
            message_type=message_type,
            content=content,
            priority=priority
        )
        if self.memory:
            self.memory.conversations.append(msg)
        return msg

    def receive_message(self, message: StrandsMessage):
        """Receive message from another agent"""
        self.inbox.append(message)

    def get_pending_messages(self) -> List[StrandsMessage]:
        """Get messages for this agent"""
        if not self.memory:
            return []

        pending = [msg for msg in self.memory.conversations
                  if msg.to_agent == self.name]
        return pending

    def process(self) -> Optional[StrandsMessage]:
        """Process next task - implemented by subclasses"""
        raise NotImplementedError


class StrandsOrchestrator:
    """
    Orchestrates multiple agents in the Strands framework

    Responsibilities:
    - Manages agent lifecycle
    - Routes messages between agents
    - Coordinates parallel execution
    - Maintains shared memory
    """

    def __init__(self):
        self.agents: Dict[str, StrandsAgent] = {}
        self.memory = StrandsMemory(
            facts={},
            conversations=[],
            evidence=[],
            decisions=[]
        )

        # Neo4j connection
        load_dotenv()
        self.neo4j_driver = GraphDatabase.driver(
            os.getenv('NEO4J_URI'),
            auth=(os.getenv('NEO4J_USERNAME'), os.getenv('NEO4J_PASSWORD'))
        )

        # AWS Bedrock
        self.bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

        print("="*80)
        print("AWS STRANDS MULTI-AGENT FRAMEWORK")
        print("Orchestrating Specialized AI Agents for Clinical Reasoning")
        print("="*80)

    def register_agent(self, agent: StrandsAgent):
        """Register an agent with the orchestrator"""
        agent.attach_memory(self.memory)
        self.agents[agent.name] = agent
        print(f"✓ Registered agent: {agent.name} ({agent.role})")

    def route_message(self, message: StrandsMessage):
        """Route message to destination agent"""
        if message.to_agent in self.agents:
            self.agents[message.to_agent].receive_message(message)

    def execute_workflow(self, initial_task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute multi-agent workflow

        Strands workflow:
        1. Orchestrator assigns task to appropriate agent
        2. Agent processes task, queries tools
        3. Agent may request help from other agents
        4. Agents communicate results
        5. Orchestrator synthesizes final answer
        """
        print(f"\n{'='*80}")
        print(f"EXECUTING WORKFLOW: {initial_task.get('type', 'unknown')}")
        print(f"{'='*80}")

        # Store initial task
        self.memory.facts['initial_task'] = initial_task

        # Route to appropriate agent based on task type
        task_type = initial_task['type']

        if task_type == "clinical_safety":
            result = self._execute_clinical_safety_workflow(initial_task)
        elif task_type == "drug_repurposing":
            result = self._execute_repurposing_workflow(initial_task)
        elif task_type == "research_landscape":
            result = self._execute_research_workflow(initial_task)
        elif task_type == "comparative_analysis":
            result = self._execute_comparative_workflow(initial_task)
        elif task_type == "evidence_chain":
            result = self._execute_evidence_workflow(initial_task)
        else:
            result = {"error": f"Unknown task type: {task_type}"}

        return result

    def _execute_clinical_safety_workflow(self, task: Dict) -> Dict[str, Any]:
        """
        Workflow: Clinical Safety Analysis

        Agents involved:
        1. ClinicalSafetyAgent - Coordinates analysis
        2. PharmacologyAgent - Analyzes drug mechanism
        3. GeneticsAgent - Validates genetic evidence
        4. TrialDataAgent - Retrieves trial safety data
        """
        print("\n🏥 Clinical Safety Workflow")
        print("-"*80)

        drug = task['drug']
        patient_context = task.get('patient_context', {})

        # Step 1: Clinical Safety Agent queries drug mechanism
        print("\n[Step 1] ClinicalSafetyAgent → PharmacologyAgent")
        pharma_result = self.agents['PharmacologyAgent'].analyze_mechanism(drug)
        print(f"  Found: {pharma_result.get('mechanism')}")

        # Step 2: Get trial safety data
        print("\n[Step 2] ClinicalSafetyAgent → TrialDataAgent")
        trial_result = self.agents['TrialDataAgent'].get_adverse_events(drug)
        print(f"  Found: {len(trial_result.get('events', []))} adverse events")

        # Step 3: Validate genetic evidence
        if 'genetic_mutation' in patient_context:
            print("\n[Step 3] ClinicalSafetyAgent → GeneticsAgent")
            genetic_result = self.agents['GeneticsAgent'].validate_genetic_match(
                patient_context['genetic_mutation'], drug
            )
            print(f"  Genetic match: {genetic_result.get('match_quality')}")
        else:
            genetic_result = None

        # Step 4: Clinical Safety Agent synthesizes
        print("\n[Step 4] ClinicalSafetyAgent synthesizes final report")
        safety_report = self.agents['ClinicalSafetyAgent'].synthesize_safety_report(
            drug, pharma_result, trial_result, genetic_result, patient_context
        )

        return safety_report

    def _execute_repurposing_workflow(self, task: Dict) -> Dict[str, Any]:
        """
        Workflow: Drug Repurposing

        Agents involved:
        1. RepurposingAgent - Coordinates search
        2. PharmacologyAgent - Analyzes mechanisms
        3. GeneticsAgent - Checks genetic overlap
        4. EvidenceValidatorAgent - Validates evidence chain
        """
        print("\n💊 Drug Repurposing Workflow")
        print("-"*80)

        source = task['source_disease']
        target = task['target_disease']

        # Step 1: Find candidate drugs
        print("\n[Step 1] RepurposingAgent finds candidates")
        candidates = self.agents['RepurposingAgent'].find_candidates(source)
        print(f"  Found: {len(candidates)} candidates")

        # Step 2: Check genetic overlap
        print("\n[Step 2] GeneticsAgent checks genetic overlap")
        genetic_overlap = self.agents['GeneticsAgent'].check_disease_overlap(source, target)
        print(f"  Shared genes: {len(genetic_overlap)}")

        # Step 3: Validate pathway relevance
        print("\n[Step 3] PharmacologyAgent validates pathways")
        pathway_analysis = self.agents['PharmacologyAgent'].analyze_pathway_overlap(
            candidates, target
        )

        # Step 4: Evidence validator scores candidates
        print("\n[Step 4] EvidenceValidatorAgent scores candidates")
        scored_candidates = self.agents['EvidenceValidatorAgent'].score_repurposing_candidates(
            candidates, genetic_overlap, pathway_analysis
        )

        # Step 5: RepurposingAgent generates final report
        print("\n[Step 5] RepurposingAgent generates report")
        repurposing_report = self.agents['RepurposingAgent'].generate_report(
            source, target, scored_candidates, genetic_overlap
        )

        return repurposing_report

    def _execute_research_workflow(self, task: Dict) -> Dict[str, Any]:
        """
        Workflow: Research Landscape Analysis

        Agents involved:
        1. ResearchAnalystAgent - Coordinates analysis
        2. TrialDataAgent - Analyzes trials
        3. PublicationAgent - Analyzes papers
        """
        print("\n🔬 Research Landscape Workflow")
        print("-"*80)

        disease = task['disease']

        # Step 1: Find researchers
        print("\n[Step 1] ResearchAnalystAgent finds researchers")
        researchers = self.agents['ResearchAnalystAgent'].find_researchers(disease)
        print(f"  Found: {len(researchers)} researchers")

        # Step 2: Map trials
        print("\n[Step 2] TrialDataAgent maps trials")
        trials = self.agents['TrialDataAgent'].map_trials(disease)
        print(f"  Found: {len(trials)} trials")

        # Step 3: Analyze publications
        print("\n[Step 3] PublicationAgent analyzes papers")
        publications = self.agents['PublicationAgent'].analyze_publications(disease)

        # Step 4: Build network
        print("\n[Step 4] ResearchAnalystAgent builds collaboration network")
        landscape = self.agents['ResearchAnalystAgent'].build_landscape(
            disease, researchers, trials, publications
        )

        return landscape

    def _execute_comparative_workflow(self, task: Dict) -> Dict[str, Any]:
        """
        Workflow: Comparative Drug Analysis

        Agents involved:
        1. ComparativeAnalystAgent - Coordinates comparison
        2. PharmacologyAgent - Compares mechanisms
        3. TrialDataAgent - Compares safety profiles
        4. EvidenceValidatorAgent - Validates comparison
        """
        print("\n⚖️ Comparative Analysis Workflow")
        print("-"*80)

        drug1 = task['drug1']
        drug2 = task['drug2']

        # Step 1: Compare mechanisms
        print("\n[Step 1] PharmacologyAgent compares mechanisms")
        mechanism_comparison = self.agents['PharmacologyAgent'].compare_mechanisms(drug1, drug2)

        # Step 2: Compare safety
        print("\n[Step 2] TrialDataAgent compares safety profiles")
        safety_comparison = self.agents['TrialDataAgent'].compare_safety(drug1, drug2)

        # Step 3: Compare efficacy
        print("\n[Step 3] EvidenceValidatorAgent compares efficacy")
        efficacy_comparison = self.agents['EvidenceValidatorAgent'].compare_efficacy(drug1, drug2)

        # Step 4: Generate recommendation
        print("\n[Step 4] ComparativeAnalystAgent generates recommendation")
        comparison_report = self.agents['ComparativeAnalystAgent'].generate_comparison(
            drug1, drug2, mechanism_comparison, safety_comparison, efficacy_comparison
        )

        return comparison_report

    def _execute_evidence_workflow(self, task: Dict) -> Dict[str, Any]:
        """
        Workflow: Complete Evidence Chain

        Agents involved:
        1. EvidenceValidatorAgent - Coordinates chain
        2. GeneticsAgent - Genetic evidence
        3. PharmacologyAgent - Drug evidence
        4. TrialDataAgent - Clinical evidence
        5. ResearchAnalystAgent - Institutional evidence
        """
        print("\n🔗 Evidence Chain Workflow")
        print("-"*80)

        gene = task['gene']

        # Step 1: Gene information
        print("\n[Step 1] GeneticsAgent retrieves gene info")
        gene_info = self.agents['GeneticsAgent'].get_gene_info(gene)

        # Step 2: Disease associations
        print("\n[Step 2] GeneticsAgent finds disease associations")
        diseases = self.agents['GeneticsAgent'].find_associated_diseases(gene)

        # Step 3: Treatments
        print("\n[Step 3] PharmacologyAgent finds treatments")
        treatments = self.agents['PharmacologyAgent'].find_treatments_for_gene(gene)

        # Step 4: Clinical validation
        print("\n[Step 4] TrialDataAgent validates with trials")
        trials = self.agents['TrialDataAgent'].find_gene_related_trials(gene)

        # Step 5: Institutional investment
        print("\n[Step 5] ResearchAnalystAgent maps investment")
        institutions = self.agents['ResearchAnalystAgent'].map_institutional_investment(gene)

        # Step 6: Validate chain
        print("\n[Step 6] EvidenceValidatorAgent validates complete chain")
        evidence_chain = self.agents['EvidenceValidatorAgent'].validate_complete_chain(
            gene, gene_info, diseases, treatments, trials, institutions
        )

        return evidence_chain

    def close(self):
        """Close all connections"""
        self.neo4j_driver.close()


# ============================================================================
# SPECIALIZED STRANDS AGENTS
# ============================================================================

class ClinicalSafetyAgent(StrandsAgent):
    """Agent specialized in clinical safety analysis"""

    def __init__(self, neo4j_driver, bedrock_client):
        super().__init__("ClinicalSafetyAgent", "Clinical Safety Specialist",
                        ["neo4j_query", "bedrock_reasoning"])
        self.neo4j = neo4j_driver
        self.bedrock = bedrock_client

    def synthesize_safety_report(self, drug: str, pharma_result: Dict,
                                  trial_result: Dict, genetic_result: Optional[Dict],
                                  patient_context: Dict) -> Dict[str, Any]:
        """Synthesize final safety report"""

        # Calculate risk score
        adverse_events = trial_result.get('events', [])
        severe_count = len([e for e in adverse_events if e.get('severity') == 'Severe'])
        risk_score = min(100, severe_count * 15 + len(adverse_events) * 3)

        if risk_score > 50:
            risk_level = "HIGH"
            recommendation = "⚠️ Consider alternative treatments"
        elif risk_score > 25:
            risk_level = "MODERATE"
            recommendation = "⚠️ Acceptable with monitoring"
        else:
            risk_level = "LOW"
            recommendation = "✅ Generally safe profile"

        report = {
            "drug": drug,
            "patient_context": patient_context,
            "mechanism": pharma_result.get('mechanism'),
            "targets": pharma_result.get('targets', []),
            "risk_assessment": {
                "risk_score": risk_score,
                "risk_level": risk_level,
                "severe_events_count": severe_count,
                "total_events_count": len(adverse_events)
            },
            "adverse_events": adverse_events[:10],  # Top 10
            "genetic_validation": genetic_result,
            "recommendation": recommendation,
            "requires_monitoring": risk_level != "LOW"
        }

        return report


class PharmacologyAgent(StrandsAgent):
    """Agent specialized in drug mechanisms and pharmacology"""

    def __init__(self, neo4j_driver):
        super().__init__("PharmacologyAgent", "Pharmacology Specialist",
                        ["neo4j_query"])
        self.neo4j = neo4j_driver

    def analyze_mechanism(self, drug: str) -> Dict[str, Any]:
        """Analyze drug mechanism and targets"""
        with self.neo4j.session() as session:
            result = session.run("""
                MATCH (d:Drug {name: $drug})-[t:TARGETS]->(p:Protein)
                RETURN d.mechanism as mechanism, d.approvalStatus as status,
                       collect({protein: p.name, class: p.proteinClass,
                               affinity: t.bindingAffinity}) as targets
            """, drug=drug)

            record = result.single()
            if record:
                return dict(record)
            return {}

    def compare_mechanisms(self, drug1: str, drug2: str) -> Dict[str, Any]:
        """Compare mechanisms of two drugs"""
        with self.neo4j.session() as session:
            result = session.run("""
                MATCH (d:Drug)-[t:TARGETS]->(p:Protein)
                WHERE d.name IN [$drug1, $drug2]
                RETURN d.name as drug, d.mechanism as mechanism,
                       collect(p.name) as targets
            """, drug1=drug1, drug2=drug2)

            records = [dict(r) for r in result]

            if len(records) == 2:
                shared_targets = set(records[0]['targets']) & set(records[1]['targets'])
                return {
                    "drug1": records[0],
                    "drug2": records[1],
                    "shared_targets": list(shared_targets),
                    "mechanism_similarity": len(shared_targets) > 0
                }
            return {}

    def analyze_pathway_overlap(self, candidates: List[Dict], target_disease: str) -> Dict:
        """Analyze if candidate drugs target relevant pathways"""
        # Simplified for demo
        return {"relevant_candidates": len(candidates)}

    def find_treatments_for_gene(self, gene: str) -> List[Dict]:
        """Find treatments for diseases associated with gene"""
        with self.neo4j.session() as session:
            result = session.run("""
                MATCH (g:Gene {symbol: $gene})-[:ASSOCIATED_WITH]->(d:Disease)
                      <-[tr:TREATS]-(drug:Drug)
                RETURN gene.symbol as gene, d.name as disease,
                       drug.name as drug, tr.efficacyRate as efficacy
                ORDER BY tr.efficacyRate DESC
            """, gene=gene)

            return [dict(r) for r in result]


class GeneticsAgent(StrandsAgent):
    """Agent specialized in genetic analysis"""

    def __init__(self, neo4j_driver):
        super().__init__("GeneticsAgent", "Genetics Specialist", ["neo4j_query"])
        self.neo4j = neo4j_driver

    def validate_genetic_match(self, mutation: str, drug: str) -> Dict[str, Any]:
        """Validate if drug is appropriate for genetic mutation"""
        with self.neo4j.session() as session:
            result = session.run("""
                MATCH (g:Gene {symbol: $mutation})-[a:ASSOCIATED_WITH]->(d:Disease)
                      <-[tr:TREATS]-(drug:Drug {name: $drug})
                RETURN g.symbol as gene, d.name as disease,
                       a.associationStrength as strength,
                       a.evidenceLevel as evidence,
                       tr.efficacyRate as efficacy
            """, mutation=mutation, drug=drug)

            records = [dict(r) for r in result]

            if records:
                return {
                    "match_found": True,
                    "match_quality": records[0].get('strength', 'Unknown'),
                    "evidence_level": records[0].get('evidence', 'Unknown'),
                    "expected_efficacy": records[0].get('efficacy', 0),
                    "details": records
                }
            return {"match_found": False}

    def check_disease_overlap(self, disease1: str, disease2: str) -> List[Dict]:
        """Check genetic overlap between two diseases"""
        with self.neo4j.session() as session:
            result = session.run("""
                MATCH (g:Gene)-[:ASSOCIATED_WITH]->(d1:Disease)
                WHERE d1.name CONTAINS $disease1

                MATCH (g)-[a:ASSOCIATED_WITH]->(d2:Disease)
                WHERE d2.name CONTAINS $disease2

                RETURN g.symbol as gene, g.name as geneName,
                       a.associationStrength as strength
            """, disease1=disease1, disease2=disease2)

            return [dict(r) for r in result]

    def get_gene_info(self, gene: str) -> Dict:
        """Get gene information"""
        with self.neo4j.session() as session:
            result = session.run("""
                MATCH (g:Gene {symbol: $gene})
                RETURN g.symbol, g.name, g.chromosome, g.function
            """, gene=gene)

            record = result.single()
            return dict(record) if record else {}

    def find_associated_diseases(self, gene: str) -> List[Dict]:
        """Find diseases associated with gene"""
        with self.neo4j.session() as session:
            result = session.run("""
                MATCH (g:Gene {symbol: $gene})-[a:ASSOCIATED_WITH]->(d:Disease)
                RETURN d.name as disease, a.associationStrength as strength,
                       a.evidenceLevel as evidence
                ORDER BY a.associationStrength DESC
            """, gene=gene)

            return [dict(r) for r in result]


class TrialDataAgent(StrandsAgent):
    """Agent specialized in clinical trial data"""

    def __init__(self, neo4j_driver):
        super().__init__("TrialDataAgent", "Clinical Trial Specialist", ["neo4j_query"])
        self.neo4j = neo4j_driver

    def get_adverse_events(self, drug: str) -> Dict[str, Any]:
        """Get adverse events for a drug"""
        with self.neo4j.session() as session:
            result = session.run("""
                MATCH (d:Drug {name: $drug})<-[:INVESTIGATES]-(t:ClinicalTrial)
                      -[:REPORTS]->(e:AdverseEvent)
                RETURN e.name as event, e.severity as severity,
                       e.frequency as frequency, e.category as category
                ORDER BY
                    CASE e.severity
                        WHEN 'Severe' THEN 1
                        WHEN 'Moderate' THEN 2
                        ELSE 3
                    END
            """, drug=drug)

            events = [dict(r) for r in result]
            return {"events": events}

    def compare_safety(self, drug1: str, drug2: str) -> Dict:
        """Compare safety profiles of two drugs"""
        with self.neo4j.session() as session:
            result = session.run("""
                MATCH (d:Drug)<-[:INVESTIGATES]-(t:ClinicalTrial)-[:REPORTS]->(e:AdverseEvent)
                WHERE d.name IN [$drug1, $drug2]
                RETURN d.name as drug, e.severity as severity, count(*) as count
            """, drug1=drug1, drug2=drug2)

            return {"comparison": [dict(r) for r in result]}

    def map_trials(self, disease: str) -> List[Dict]:
        """Map clinical trials for a disease"""
        with self.neo4j.session() as session:
            result = session.run("""
                MATCH (t:ClinicalTrial)-[:STUDIES]->(d:Disease)
                WHERE d.name CONTAINS $disease
                MATCH (t)-[:INVESTIGATES]->(drug:Drug)
                RETURN t.title, t.phase, t.enrollment, drug.name as drug
                ORDER BY t.enrollment DESC
            """, disease=disease)

            return [dict(r) for r in result]

    def find_gene_related_trials(self, gene: str) -> List[Dict]:
        """Find trials related to a gene"""
        with self.neo4j.session() as session:
            result = session.run("""
                MATCH (g:Gene {symbol: $gene})-[:ASSOCIATED_WITH]->(d:Disease)
                      <-[:STUDIES]-(t:ClinicalTrial)
                RETURN t.title, t.phase, t.enrollment
                ORDER BY t.enrollment DESC
            """, gene=gene)

            return [dict(r) for r in result]


class ResearchAnalystAgent(StrandsAgent):
    """Agent specialized in research landscape analysis"""

    def __init__(self, neo4j_driver):
        super().__init__("ResearchAnalystAgent", "Research Analyst", ["neo4j_query"])
        self.neo4j = neo4j_driver

    def find_researchers(self, disease: str) -> List[Dict]:
        """Find researchers working on disease"""
        with self.neo4j.session() as session:
            result = session.run("""
                MATCH (r:Researcher)-[:AFFILIATED_WITH]->(i:Institution)
                WHERE r.specialization CONTAINS $disease
                RETURN r.name, r.hIndex, i.name as institution
                ORDER BY r.hIndex DESC
                LIMIT 10
            """, disease=disease)

            return [dict(r) for r in result]

    def build_landscape(self, disease: str, researchers: List, trials: List,
                        publications: List) -> Dict:
        """Build complete research landscape"""
        return {
            "disease": disease,
            "top_researchers": researchers[:5],
            "total_trials": len(trials),
            "key_institutions": list(set([r.get('institution') for r in researchers]))
        }

    def map_institutional_investment(self, gene: str) -> List[Dict]:
        """Map institutional investment related to gene"""
        with self.neo4j.session() as session:
            result = session.run("""
                MATCH (g:Gene {symbol: $gene})-[:ASSOCIATED_WITH]->(d:Disease)
                      <-[:STUDIES]-(t:ClinicalTrial)<-[:SPONSORS]-(i:Institution)
                RETURN i.name as institution, count(t) as trials
                ORDER BY trials DESC
            """, gene=gene)

            return [dict(r) for r in result]


class PublicationAgent(StrandsAgent):
    """Agent specialized in publication analysis"""

    def __init__(self, neo4j_driver):
        super().__init__("PublicationAgent", "Publication Analyst", ["neo4j_query"])
        self.neo4j = neo4j_driver

    def analyze_publications(self, disease: str) -> List[Dict]:
        """Analyze publications about disease"""
        with self.neo4j.session() as session:
            result = session.run("""
                MATCH (p:ResearchPaper)-[:MENTIONS_DISEASE]->(d:Disease)
                WHERE d.name CONTAINS $disease
                RETURN p.title, p.year, p.journal
                ORDER BY p.year DESC
                LIMIT 10
            """, disease=disease)

            return [dict(r) for r in result]


class RepurposingAgent(StrandsAgent):
    """Agent specialized in drug repurposing"""

    def __init__(self, neo4j_driver):
        super().__init__("RepurposingAgent", "Drug Repurposing Specialist", ["neo4j_query"])
        self.neo4j = neo4j_driver

    def find_candidates(self, source_disease: str) -> List[Dict]:
        """Find drugs treating source disease"""
        with self.neo4j.session() as session:
            result = session.run("""
                MATCH (d:Drug)-[t:TREATS]->(dis:Disease)
                WHERE dis.name CONTAINS $disease
                RETURN d.name as drug, d.mechanism, t.efficacyRate as efficacy
                ORDER BY t.efficacyRate DESC
            """, disease=source_disease)

            return [dict(r) for r in result]

    def generate_report(self, source: str, target: str, candidates: List,
                        genetic_overlap: List) -> Dict:
        """Generate repurposing report"""
        return {
            "source_disease": source,
            "target_disease": target,
            "candidate_drugs": candidates[:5],
            "genetic_evidence": len(genetic_overlap),
            "recommendation": candidates[0] if candidates else None
        }


class ComparativeAnalystAgent(StrandsAgent):
    """Agent specialized in comparative analysis"""

    def __init__(self):
        super().__init__("ComparativeAnalystAgent", "Comparative Analyst", ["synthesis"])

    def generate_comparison(self, drug1: str, drug2: str, mechanism: Dict,
                            safety: Dict, efficacy: Dict) -> Dict:
        """Generate comparison report"""
        return {
            "drug1": drug1,
            "drug2": drug2,
            "mechanism_comparison": mechanism,
            "safety_comparison": safety,
            "efficacy_comparison": efficacy,
            "recommendation": "Detailed comparison complete"
        }


class EvidenceValidatorAgent(StrandsAgent):
    """Agent specialized in evidence validation"""

    def __init__(self):
        super().__init__("EvidenceValidatorAgent", "Evidence Validator", ["validation"])

    def score_repurposing_candidates(self, candidates: List, genetic: List,
                                      pathway: Dict) -> List[Dict]:
        """Score repurposing candidates"""
        scored = []
        for c in candidates:
            score = c.get('efficacy', 0) * 100
            c['repurposing_score'] = score
            scored.append(c)
        return sorted(scored, key=lambda x: x['repurposing_score'], reverse=True)

    def compare_efficacy(self, drug1: str, drug2: str) -> Dict:
        """Compare efficacy of two drugs"""
        return {"comparison": "efficacy_analysis"}

    def validate_complete_chain(self, gene: str, gene_info: Dict, diseases: List,
                                 treatments: List, trials: List, institutions: List) -> Dict:
        """Validate complete evidence chain"""
        return {
            "gene": gene,
            "chain_strength": "strong" if len(trials) > 3 else "moderate",
            "evidence_summary": {
                "genetic": len(diseases),
                "therapeutic": len(treatments),
                "clinical": len(trials),
                "institutional": len(institutions)
            }
        }


# ============================================================================
# MAIN DEMO
# ============================================================================

def main():
    """Main demo of Strands multi-agent framework"""

    # Initialize orchestrator
    orchestrator = StrandsOrchestrator()

    # Register agents
    orchestrator.register_agent(ClinicalSafetyAgent(
        orchestrator.neo4j_driver, orchestrator.bedrock
    ))
    orchestrator.register_agent(PharmacologyAgent(orchestrator.neo4j_driver))
    orchestrator.register_agent(GeneticsAgent(orchestrator.neo4j_driver))
    orchestrator.register_agent(TrialDataAgent(orchestrator.neo4j_driver))
    orchestrator.register_agent(ResearchAnalystAgent(orchestrator.neo4j_driver))
    orchestrator.register_agent(PublicationAgent(orchestrator.neo4j_driver))
    orchestrator.register_agent(RepurposingAgent(orchestrator.neo4j_driver))
    orchestrator.register_agent(ComparativeAnalystAgent())
    orchestrator.register_agent(EvidenceValidatorAgent())

    print(f"\n✓ All agents registered and ready!\n")

    # USE CASE 1: Clinical Safety
    print("\n" + "="*80)
    print("USE CASE 1: Clinical Safety Analysis")
    print("="*80)

    result1 = orchestrator.execute_workflow({
        "type": "clinical_safety",
        "drug": "Pembrolizumab",
        "patient_context": {
            "genetic_mutation": "EGFR",
            "previous_treatment": "Nivolumab",
            "disease": "Non-Small Cell Lung Cancer"
        }
    })

    print("\n📊 RESULT:")
    print(json.dumps(result1, indent=2))

    # USE CASE 2: Drug Repurposing
    print("\n\n" + "="*80)
    print("USE CASE 2: Drug Repurposing")
    print("="*80)

    result2 = orchestrator.execute_workflow({
        "type": "drug_repurposing",
        "source_disease": "Lung Cancer",
        "target_disease": "Colorectal Cancer"
    })

    print("\n📊 RESULT:")
    print(json.dumps(result2, indent=2))

    # USE CASE 3: Research Landscape
    print("\n\n" + "="*80)
    print("USE CASE 3: Research Landscape")
    print("="*80)

    result3 = orchestrator.execute_workflow({
        "type": "research_landscape",
        "disease": "Alzheimer"
    })

    print("\n📊 RESULT:")
    print(json.dumps(result3, indent=2))

    # USE CASE 4: Comparative Analysis
    print("\n\n" + "="*80)
    print("USE CASE 4: Comparative Analysis")
    print("="*80)

    result4 = orchestrator.execute_workflow({
        "type": "comparative_analysis",
        "drug1": "Pembrolizumab",
        "drug2": "Nivolumab"
    })

    print("\n📊 RESULT:")
    print(json.dumps(result4, indent=2))

    # USE CASE 5: Evidence Chain
    print("\n\n" + "="*80)
    print("USE CASE 5: Complete Evidence Chain")
    print("="*80)

    result5 = orchestrator.execute_workflow({
        "type": "evidence_chain",
        "gene": "BRCA1"
    })

    print("\n📊 RESULT:")
    print(json.dumps(result5, indent=2))

    orchestrator.close()

    print("\n" + "="*80)
    print("ALL USE CASES COMPLETED!")
    print("="*80)


if __name__ == "__main__":
    main()
