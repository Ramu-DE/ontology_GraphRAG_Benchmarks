#!/usr/bin/env python3
"""
ReAct Agent Framework with AWS Bedrock + Neo4j
Multi-agent orchestration for complex biomedical reasoning

ReAct Loop: Reasoning → Acting → Observing → Repeat
"""

import os
import json
from typing import Dict, List, Any, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
from neo4j import GraphDatabase
from dotenv import load_dotenv
import boto3


class AgentRole(Enum):
    """Specialized agent roles"""
    ORCHESTRATOR = "orchestrator"
    CLINICAL_SAFETY = "clinical_safety"
    DRUG_DISCOVERY = "drug_discovery"
    RESEARCH_ANALYST = "research_analyst"
    EVIDENCE_VALIDATOR = "evidence_validator"
    GENETIC_ANALYST = "genetic_analyst"


@dataclass
class Thought:
    """Agent's reasoning step"""
    step: int
    role: AgentRole
    reasoning: str
    next_action: str
    confidence: float  # 0.0 to 1.0


@dataclass
class Action:
    """Action to execute against knowledge graph"""
    agent: AgentRole
    action_type: str  # "query", "validate", "synthesize"
    cypher_query: str
    parameters: Dict[str, Any]
    purpose: str


@dataclass
class Observation:
    """Result from executing an action"""
    action: Action
    results: List[Dict[str, Any]]
    insights: List[str]
    success: bool
    error: str = None


@dataclass
class Evidence:
    """Evidence chain for clinical decision"""
    source: str
    evidence_type: str  # "genetic", "clinical_trial", "adverse_event", "efficacy"
    data: Dict[str, Any]
    strength: str  # "strong", "moderate", "weak"
    confidence: float


class ReActAgentFramework:
    """
    Multi-agent ReAct framework for complex biomedical reasoning

    ReAct Loop:
    1. THINK: Agent reasons about what to do next
    2. ACT: Execute graph query or analysis
    3. OBSERVE: Analyze results
    4. REPEAT: Until task is complete
    """

    def __init__(self):
        load_dotenv()

        # Neo4j connection
        self.neo4j_uri = os.getenv('NEO4J_URI')
        self.neo4j_username = os.getenv('NEO4J_USERNAME')
        self.neo4j_password = os.getenv('NEO4J_PASSWORD')
        self.neo4j_database = os.getenv('NEO4J_DATABASE', 'neo4j')

        self.driver = GraphDatabase.driver(
            self.neo4j_uri,
            auth=(self.neo4j_username, self.neo4j_password)
        )

        # AWS Bedrock
        self.bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')

        # Conversation state
        self.thoughts: List[Thought] = []
        self.actions: List[Action] = []
        self.observations: List[Observation] = []
        self.evidence_chain: List[Evidence] = []

        print("=" * 80)
        print("ReAct AGENT FRAMEWORK - AWS Bedrock + Neo4j")
        print("Multi-Agent Orchestration for Clinical Reasoning")
        print("=" * 80)

    def close(self):
        self.driver.close()

    # ============================================================================
    # CORE ReAct LOOP
    # ============================================================================

    def think(self, role: AgentRole, context: Dict, goal: str) -> Thought:
        """
        THINK step: Agent reasons about what to do next
        """
        prompt = f"""You are a {role.value} agent in a biomedical AI system.

Goal: {goal}

Current context:
{json.dumps(context, indent=2)}

Previous observations:
{json.dumps([obs.insights for obs in self.observations[-3:]], indent=2)}

Think step-by-step:
1. What information do I have?
2. What information do I need?
3. What should I do next?
4. How confident am I?

Respond in JSON format:
{{
    "reasoning": "your step-by-step reasoning",
    "next_action": "specific action to take",
    "confidence": 0.85
}}
"""

        response = self._call_bedrock(prompt)
        thought_data = json.loads(response)

        thought = Thought(
            step=len(self.thoughts) + 1,
            role=role,
            reasoning=thought_data["reasoning"],
            next_action=thought_data["next_action"],
            confidence=thought_data["confidence"]
        )

        self.thoughts.append(thought)
        return thought

    def act(self, action: Action) -> Observation:
        """
        ACT step: Execute action against knowledge graph
        """
        try:
            with self.driver.session(database=self.neo4j_database) as session:
                result = session.run(action.cypher_query, action.parameters)
                results = [dict(record) for record in result]

            # Analyze results to extract insights
            insights = self._extract_insights(action, results)

            observation = Observation(
                action=action,
                results=results,
                insights=insights,
                success=True
            )

        except Exception as e:
            observation = Observation(
                action=action,
                results=[],
                insights=[],
                success=False,
                error=str(e)
            )

        self.observations.append(observation)
        return observation

    def observe(self, observation: Observation) -> Dict[str, Any]:
        """
        OBSERVE step: Analyze results and update state
        """
        if not observation.success:
            return {
                "status": "error",
                "error": observation.error,
                "recommendation": "retry with different query"
            }

        # Extract structured insights
        analysis = {
            "status": "success",
            "data_points": len(observation.results),
            "insights": observation.insights,
            "completeness": self._assess_completeness(observation),
            "next_steps": self._suggest_next_steps(observation)
        }

        return analysis

    def should_continue(self, goal: str, max_iterations: int = 10) -> bool:
        """
        Decide if we should continue the ReAct loop
        """
        if len(self.thoughts) >= max_iterations:
            return False

        # Check if goal is achieved
        if self.thoughts:
            last_thought = self.thoughts[-1]
            if "complete" in last_thought.next_action.lower() or \
               "final" in last_thought.next_action.lower():
                return False

        return True

    # ============================================================================
    # SPECIALIZED AGENTS
    # ============================================================================

    def clinical_safety_agent(self, drug_name: str, patient_context: Dict) -> Dict[str, Any]:
        """
        Clinical Safety Agent: Analyze drug safety for specific patient context

        Steps:
        1. Get drug mechanism and targets
        2. Check adverse events from trials
        3. Analyze drug interactions
        4. Validate against genetic profile
        5. Generate safety recommendation
        """
        print(f"\n{'='*80}")
        print(f"🏥 CLINICAL SAFETY AGENT - Analyzing {drug_name}")
        print(f"{'='*80}")

        goal = f"Assess clinical safety of {drug_name} for patient with context: {patient_context}"
        context = {"drug": drug_name, "patient": patient_context}

        # ReAct Loop
        iteration = 0
        while self.should_continue(goal, max_iterations=5) and iteration < 5:
            iteration += 1
            print(f"\n--- Iteration {iteration} ---")

            # THINK
            thought = self.think(AgentRole.CLINICAL_SAFETY, context, goal)
            print(f"💭 THINK: {thought.reasoning[:150]}...")

            # ACT
            if iteration == 1:
                # Step 1: Get drug mechanism and targets
                action = Action(
                    agent=AgentRole.CLINICAL_SAFETY,
                    action_type="query",
                    cypher_query="""
                    MATCH (d:Drug {name: $drug_name})-[t:TARGETS]->(p:Protein)
                    RETURN d.mechanism as mechanism, d.approvalStatus as status,
                           collect({protein: p.name, class: p.proteinClass,
                                   affinity: t.bindingAffinity}) as targets
                    """,
                    parameters={"drug_name": drug_name},
                    purpose="Get drug mechanism and protein targets"
                )

            elif iteration == 2:
                # Step 2: Get adverse events
                action = Action(
                    agent=AgentRole.CLINICAL_SAFETY,
                    action_type="query",
                    cypher_query="""
                    MATCH (d:Drug {name: $drug_name})<-[:INVESTIGATES]-(t:ClinicalTrial)
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
                    parameters={"drug_name": drug_name},
                    purpose="Identify adverse events and their severity"
                )

            elif iteration == 3:
                # Step 3: Check drug interactions (same protein targets)
                action = Action(
                    agent=AgentRole.CLINICAL_SAFETY,
                    action_type="query",
                    cypher_query="""
                    MATCH (d1:Drug {name: $drug_name})-[:TARGETS]->(p:Protein)
                          <-[:TARGETS]-(d2:Drug)
                    WHERE d1 <> d2
                    RETURN d2.name as interacting_drug, p.name as shared_target,
                           d2.mechanism as mechanism
                    """,
                    parameters={"drug_name": drug_name},
                    purpose="Identify potential drug interactions"
                )

            elif iteration == 4:
                # Step 4: Validate genetic evidence
                if "genetic_mutation" in patient_context:
                    action = Action(
                        agent=AgentRole.GENETIC_ANALYST,
                        action_type="query",
                        cypher_query="""
                        MATCH (g:Gene {symbol: $gene})-[a:ASSOCIATED_WITH]->(d:Disease)
                              <-[tr:TREATS]-(drug:Drug {name: $drug_name})
                        RETURN g.symbol as gene, g.name as geneName,
                               d.name as disease,
                               a.associationStrength as geneticStrength,
                               a.evidenceLevel as evidenceLevel,
                               tr.efficacyRate as efficacy
                        """,
                        parameters={
                            "drug_name": drug_name,
                            "gene": patient_context.get("genetic_mutation", "")
                        },
                        purpose="Validate genetic evidence for drug efficacy"
                    )
                else:
                    break

            else:
                break

            # ACT & OBSERVE
            observation = self.act(action)
            print(f"🎬 ACT: {action.purpose}")
            analysis = self.observe(observation)
            print(f"👁️ OBSERVE: Found {len(observation.results)} results")

            # Update context with findings
            context[f"step_{iteration}"] = {
                "results": observation.results,
                "insights": observation.insights
            }

        # Synthesize final safety assessment
        safety_report = self._synthesize_safety_report(drug_name, context)
        return safety_report

    def drug_repurposing_agent(self, source_disease: str, target_disease: str) -> Dict[str, Any]:
        """
        Drug Repurposing Agent: Find drugs that could be repurposed

        Steps:
        1. Find drugs treating source disease
        2. Check if they target proteins/pathways relevant to target disease
        3. Validate genetic overlap between diseases
        4. Trace evidence chain
        5. Assess repurposing potential
        """
        print(f"\n{'='*80}")
        print(f"💊 DRUG REPURPOSING AGENT")
        print(f"Source: {source_disease} → Target: {target_disease}")
        print(f"{'='*80}")

        goal = f"Identify drugs from {source_disease} that could treat {target_disease}"
        context = {"source": source_disease, "target": target_disease}

        iteration = 0
        candidates = []

        while self.should_continue(goal, max_iterations=4) and iteration < 4:
            iteration += 1
            print(f"\n--- Iteration {iteration} ---")

            # THINK
            thought = self.think(AgentRole.DRUG_DISCOVERY, context, goal)
            print(f"💭 THINK: {thought.reasoning[:150]}...")

            # ACT
            if iteration == 1:
                # Find drugs treating source disease
                action = Action(
                    agent=AgentRole.DRUG_DISCOVERY,
                    action_type="query",
                    cypher_query="""
                    MATCH (d:Drug)-[t:TREATS]->(dis:Disease)
                    WHERE dis.name CONTAINS $source_disease
                    RETURN d.name as drug, d.mechanism as mechanism,
                           t.efficacyRate as efficacy, dis.name as disease
                    ORDER BY t.efficacyRate DESC
                    """,
                    parameters={"source_disease": source_disease},
                    purpose="Find drugs treating source disease"
                )

            elif iteration == 2:
                # Check genetic overlap
                action = Action(
                    agent=AgentRole.GENETIC_ANALYST,
                    action_type="query",
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
                    purpose="Identify shared genetic associations"
                )

            elif iteration == 3:
                # Find drugs targeting shared pathways
                action = Action(
                    agent=AgentRole.DRUG_DISCOVERY,
                    action_type="query",
                    cypher_query="""
                    // Drugs treating source disease
                    MATCH (d:Drug)-[:TREATS]->(dis1:Disease)
                    WHERE dis1.name CONTAINS $source_disease

                    // That target proteins
                    MATCH (d)-[t:TARGETS]->(p:Protein)

                    // Find if target disease has genetic links
                    OPTIONAL MATCH (g:Gene)-[:ASSOCIATED_WITH]->(dis2:Disease)
                    WHERE dis2.name CONTAINS $target_disease

                    RETURN DISTINCT d.name as drug, d.mechanism as mechanism,
                           collect(DISTINCT p.name) as targetProteins,
                           collect(DISTINCT g.symbol) as relevantGenes,
                           dis1.name as sourceDiseaseMatch
                    """,
                    parameters={
                        "source_disease": source_disease,
                        "target_disease": target_disease
                    },
                    purpose="Map drug targets to target disease pathways"
                )

            else:
                break

            observation = self.act(action)
            print(f"🎬 ACT: {action.purpose}")
            print(f"👁️ OBSERVE: Found {len(observation.results)} results")

            if iteration == 1:
                candidates = observation.results

            context[f"step_{iteration}"] = observation.results

        # Build evidence chain
        repurposing_report = self._synthesize_repurposing_report(
            source_disease, target_disease, context, candidates
        )

        return repurposing_report

    def research_landscape_agent(self, disease: str) -> Dict[str, Any]:
        """
        Research Landscape Agent: Map research ecosystem

        Steps:
        1. Find top researchers by h-index
        2. Identify their institutions
        3. Map clinical trials and sponsors
        4. Analyze research papers and citations
        5. Build collaboration network
        """
        print(f"\n{'='*80}")
        print(f"🔬 RESEARCH LANDSCAPE AGENT - {disease}")
        print(f"{'='*80}")

        goal = f"Map research ecosystem for {disease}"
        context = {"disease": disease}

        iteration = 0
        while self.should_continue(goal, max_iterations=4) and iteration < 4:
            iteration += 1
            print(f"\n--- Iteration {iteration} ---")

            thought = self.think(AgentRole.RESEARCH_ANALYST, context, goal)
            print(f"💭 THINK: {thought.reasoning[:150]}...")

            if iteration == 1:
                # Find top researchers
                action = Action(
                    agent=AgentRole.RESEARCH_ANALYST,
                    action_type="query",
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
                        "category": disease.split()[-1]  # e.g., "Disease" from "Alzheimer's Disease"
                    },
                    purpose="Identify top researchers"
                )

            elif iteration == 2:
                # Find clinical trials
                action = Action(
                    agent=AgentRole.RESEARCH_ANALYST,
                    action_type="query",
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
                    purpose="Map clinical trials and sponsors"
                )

            elif iteration == 3:
                # Find research papers
                action = Action(
                    agent=AgentRole.RESEARCH_ANALYST,
                    action_type="query",
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
                    purpose="Analyze research publications"
                )

            else:
                break

            observation = self.act(action)
            print(f"🎬 ACT: {action.purpose}")
            print(f"👁️ OBSERVE: Found {len(observation.results)} results")

            context[f"step_{iteration}"] = observation.results

        landscape_report = self._synthesize_landscape_report(disease, context)
        return landscape_report

    def comparative_safety_agent(self, drug1: str, drug2: str) -> Dict[str, Any]:
        """
        Comparative Safety Agent: Compare two drugs comprehensively

        Steps:
        1. Compare mechanisms and targets
        2. Compare adverse event profiles
        3. Compare efficacy across diseases
        4. Analyze trial data
        5. Generate comparative recommendation
        """
        print(f"\n{'='*80}")
        print(f"⚖️ COMPARATIVE SAFETY AGENT")
        print(f"Comparing: {drug1} vs {drug2}")
        print(f"{'='*80}")

        goal = f"Compare safety and efficacy of {drug1} vs {drug2}"
        context = {"drug1": drug1, "drug2": drug2}

        iteration = 0
        while self.should_continue(goal, max_iterations=5) and iteration < 5:
            iteration += 1
            print(f"\n--- Iteration {iteration} ---")

            thought = self.think(AgentRole.CLINICAL_SAFETY, context, goal)
            print(f"💭 THINK: {thought.reasoning[:150]}...")

            if iteration == 1:
                # Compare targets
                action = Action(
                    agent=AgentRole.CLINICAL_SAFETY,
                    action_type="query",
                    cypher_query="""
                    MATCH (d:Drug)-[t:TARGETS]->(p:Protein)
                    WHERE d.name IN [$drug1, $drug2]
                    RETURN d.name as drug, d.mechanism as mechanism,
                           collect({protein: p.name, class: p.proteinClass,
                                   affinity: t.bindingAffinity}) as targets
                    """,
                    parameters={"drug1": drug1, "drug2": drug2},
                    purpose="Compare molecular targets"
                )

            elif iteration == 2:
                # Compare adverse events
                action = Action(
                    agent=AgentRole.CLINICAL_SAFETY,
                    action_type="query",
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
                    purpose="Compare adverse event profiles"
                )

            elif iteration == 3:
                # Compare efficacy
                action = Action(
                    agent=AgentRole.CLINICAL_SAFETY,
                    action_type="query",
                    cypher_query="""
                    MATCH (d:Drug)-[tr:TREATS]->(dis:Disease)
                    WHERE d.name IN [$drug1, $drug2]
                    RETURN d.name as drug, dis.name as disease,
                           tr.efficacyRate as efficacy
                    ORDER BY dis.name, tr.efficacyRate DESC
                    """,
                    parameters={"drug1": drug1, "drug2": drug2},
                    purpose="Compare efficacy rates"
                )

            elif iteration == 4:
                # Compare trial characteristics
                action = Action(
                    agent=AgentRole.CLINICAL_SAFETY,
                    action_type="query",
                    cypher_query="""
                    MATCH (d:Drug)<-[:INVESTIGATES]-(t:ClinicalTrial)
                    WHERE d.name IN [$drug1, $drug2]
                    RETURN d.name as drug, count(t) as totalTrials,
                           collect(t.phase) as phases,
                           sum(t.enrollment) as totalEnrollment,
                           avg(t.enrollment) as avgEnrollment
                    """,
                    parameters={"drug1": drug1, "drug2": drug2},
                    purpose="Compare clinical trial data"
                )

            else:
                break

            observation = self.act(action)
            print(f"🎬 ACT: {action.purpose}")
            print(f"👁️ OBSERVE: Found {len(observation.results)} results")

            context[f"step_{iteration}"] = observation.results

        comparison_report = self._synthesize_comparison_report(drug1, drug2, context)
        return comparison_report

    def evidence_chain_agent(self, gene: str) -> Dict[str, Any]:
        """
        Evidence Chain Agent: Trace complete story from gene to treatment

        Steps:
        1. Gene function and location
        2. Disease associations with evidence
        3. Drugs treating those diseases
        4. Clinical trials validating treatments
        5. Institutional investment
        6. Validate evidence quality
        """
        print(f"\n{'='*80}")
        print(f"🔗 EVIDENCE CHAIN AGENT - Tracing {gene}")
        print(f"{'='*80}")

        goal = f"Trace complete evidence chain from {gene} gene to treatment"
        context = {"gene": gene}

        iteration = 0
        evidence_chain = []

        while self.should_continue(goal, max_iterations=6) and iteration < 6:
            iteration += 1
            print(f"\n--- Iteration {iteration} ---")

            thought = self.think(AgentRole.EVIDENCE_VALIDATOR, context, goal)
            print(f"💭 THINK: {thought.reasoning[:150]}...")

            if iteration == 1:
                # Gene information
                action = Action(
                    agent=AgentRole.GENETIC_ANALYST,
                    action_type="query",
                    cypher_query="""
                    MATCH (g:Gene {symbol: $gene})
                    RETURN g.symbol as symbol, g.name as name,
                           g.chromosome as chromosome, g.function as function
                    """,
                    parameters={"gene": gene},
                    purpose="Get gene information"
                )

            elif iteration == 2:
                # Disease associations
                action = Action(
                    agent=AgentRole.GENETIC_ANALYST,
                    action_type="query",
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
                    purpose="Identify disease associations"
                )

            elif iteration == 3:
                # Treatments
                action = Action(
                    agent=AgentRole.DRUG_DISCOVERY,
                    action_type="query",
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
                    purpose="Find treatments for associated diseases"
                )

            elif iteration == 4:
                # Clinical trials
                action = Action(
                    agent=AgentRole.EVIDENCE_VALIDATOR,
                    action_type="query",
                    cypher_query="""
                    MATCH (g:Gene {symbol: $gene})-[:ASSOCIATED_WITH]->(dis:Disease)
                          <-[:STUDIES]-(t:ClinicalTrial)-[:INVESTIGATES]->(d:Drug)
                    RETURN g.symbol as gene, dis.name as disease, d.name as drug,
                           t.title as trial, t.phase as phase, t.status as status,
                           t.enrollment as enrollment, t.nctId as nctId
                    ORDER BY t.enrollment DESC
                    """,
                    parameters={"gene": gene},
                    purpose="Find supporting clinical trials"
                )

            elif iteration == 5:
                # Institutional investment
                action = Action(
                    agent=AgentRole.RESEARCH_ANALYST,
                    action_type="query",
                    cypher_query="""
                    MATCH (g:Gene {symbol: $gene})-[:ASSOCIATED_WITH]->(dis:Disease)
                          <-[:STUDIES]-(t:ClinicalTrial)<-[:SPONSORS]-(i:Institution)
                    RETURN i.name as institution, count(t) as trialsSponsored,
                           collect(DISTINCT dis.name) as diseases,
                           collect(DISTINCT t.phase) as phases
                    ORDER BY trialsSponsored DESC
                    """,
                    parameters={"gene": gene},
                    purpose="Map institutional investment"
                )

            else:
                break

            observation = self.act(action)
            print(f"🎬 ACT: {action.purpose}")
            print(f"👁️ OBSERVE: Found {len(observation.results)} results")

            # Build evidence
            for result in observation.results:
                evidence = Evidence(
                    source=f"Step {iteration}: {action.purpose}",
                    evidence_type=action.purpose.split()[0].lower(),
                    data=result,
                    strength=self._assess_evidence_strength(result),
                    confidence=0.85 if observation.success else 0.0
                )
                evidence_chain.append(evidence)

            context[f"step_{iteration}"] = observation.results

        # Validate complete chain
        chain_report = self._synthesize_evidence_chain(gene, context, evidence_chain)
        return chain_report

    # ============================================================================
    # SYNTHESIS & REPORTING
    # ============================================================================

    def _synthesize_safety_report(self, drug: str, context: Dict) -> Dict[str, Any]:
        """Generate comprehensive safety report"""

        # Extract data from context
        mechanism_data = context.get("step_1", {}).get("results", [])
        adverse_events = context.get("step_2", {}).get("results", [])
        interactions = context.get("step_3", {}).get("results", [])
        genetic_validation = context.get("step_4", {}).get("results", [])

        # Categorize adverse events
        severe_events = [e for e in adverse_events if e.get("severity") == "Severe"]
        moderate_events = [e for e in adverse_events if e.get("severity") == "Moderate"]

        # Calculate risk score (0-100)
        risk_score = (len(severe_events) * 10 + len(moderate_events) * 5)
        risk_level = "High" if risk_score > 30 else "Moderate" if risk_score > 15 else "Low"

        report = {
            "drug": drug,
            "mechanism": mechanism_data[0].get("mechanism") if mechanism_data else "Unknown",
            "targets": mechanism_data[0].get("targets", []) if mechanism_data else [],
            "risk_assessment": {
                "risk_score": risk_score,
                "risk_level": risk_level,
                "severe_events": len(severe_events),
                "moderate_events": len(moderate_events)
            },
            "adverse_events": {
                "severe": [{"event": e["event"], "frequency": e.get("frequency")}
                          for e in severe_events],
                "moderate": [{"event": e["event"], "frequency": e.get("frequency")}
                            for e in moderate_events]
            },
            "drug_interactions": [
                {"drug": i["interacting_drug"], "shared_target": i["shared_target"]}
                for i in interactions
            ],
            "genetic_validation": genetic_validation,
            "recommendation": self._generate_safety_recommendation(
                risk_level, severe_events, interactions, genetic_validation
            )
        }

        return report

    def _synthesize_repurposing_report(self, source: str, target: str,
                                       context: Dict, candidates: List[Dict]) -> Dict[str, Any]:
        """Generate drug repurposing report"""

        genetic_overlap = context.get("step_2", {}).get("results", [])
        pathway_mapping = context.get("step_3", {}).get("results", [])

        # Score candidates
        scored_candidates = []
        for candidate in candidates:
            drug_name = candidate["drug"]

            # Check if drug appears in pathway mapping
            pathway_match = any(p["drug"] == drug_name for p in pathway_mapping)
            genetic_support = len([g for g in genetic_overlap
                                  if g.get("strength") in ["Strong", "Very Strong"]])

            score = (
                candidate.get("efficacy", 0) * 40 +  # 40% weight
                (10 if pathway_match else 0) +        # 10 points
                (genetic_support * 10)                 # 10 points per strong gene
            )

            scored_candidates.append({
                **candidate,
                "repurposing_score": score,
                "pathway_support": pathway_match,
                "genetic_evidence": genetic_support
            })

        scored_candidates.sort(key=lambda x: x["repurposing_score"], reverse=True)

        report = {
            "source_disease": source,
            "target_disease": target,
            "genetic_overlap": {
                "shared_genes": len(genetic_overlap),
                "genes": [g["sharedGene"] for g in genetic_overlap],
                "strongest_association": genetic_overlap[0] if genetic_overlap else None
            },
            "candidate_drugs": scored_candidates[:5],  # Top 5
            "evidence_chain": {
                "source_efficacy": "demonstrated",
                "genetic_linkage": "strong" if genetic_support > 2 else "moderate",
                "pathway_relevance": "yes" if pathway_match else "unknown"
            },
            "recommendation": self._generate_repurposing_recommendation(scored_candidates)
        }

        return report

    def _synthesize_landscape_report(self, disease: str, context: Dict) -> Dict[str, Any]:
        """Generate research landscape report"""

        researchers = context.get("step_1", {}).get("results", [])
        trials = context.get("step_2", {}).get("results", [])
        papers = context.get("step_3", {}).get("results", [])

        # Aggregate institutions
        institutions = {}
        for r in researchers:
            inst = r.get("institution")
            if inst:
                if inst not in institutions:
                    institutions[inst] = {"researchers": [], "hindex_sum": 0}
                institutions[inst]["researchers"].append(r["researcher"])
                institutions[inst]["hindex_sum"] += r.get("hIndex", 0)

        # Sort institutions by impact
        top_institutions = sorted(
            institutions.items(),
            key=lambda x: x[1]["hindex_sum"],
            reverse=True
        )[:5]

        report = {
            "disease": disease,
            "research_leaders": {
                "top_researchers": researchers[:5],
                "total_identified": len(researchers),
                "avg_hindex": sum(r.get("hIndex", 0) for r in researchers) / len(researchers) if researchers else 0
            },
            "top_institutions": [
                {
                    "name": inst[0],
                    "researchers": inst[1]["researchers"],
                    "total_hindex": inst[1]["hindex_sum"]
                }
                for inst in top_institutions
            ],
            "clinical_trials": {
                "total_trials": len(trials),
                "by_phase": self._count_by_phase(trials),
                "total_enrollment": sum(t.get("enrollment", 0) for t in trials),
                "active_drugs": list(set(t["drug"] for t in trials if "drug" in t))
            },
            "publications": {
                "total_papers": len(papers),
                "recent_papers": [p for p in papers if p.get("year", 0) >= 2020],
                "top_journals": self._extract_top_journals(papers)
            },
            "collaboration_network": {
                "institutions": list(institutions.keys()),
                "research_clusters": len(institutions)
            }
        }

        return report

    def _synthesize_comparison_report(self, drug1: str, drug2: str,
                                       context: Dict) -> Dict[str, Any]:
        """Generate comparative analysis report"""

        targets = context.get("step_1", {}).get("results", [])
        adverse_events = context.get("step_2", {}).get("results", [])
        efficacy = context.get("step_3", {}).get("results", [])
        trials = context.get("step_4", {}).get("results", [])

        # Separate by drug
        drug1_data = {
            "targets": [t for t in targets if t["drug"] == drug1],
            "adverse_events": [e for e in adverse_events if e["drug"] == drug1],
            "efficacy": [e for e in efficacy if e["drug"] == drug1],
            "trials": [t for t in trials if t["drug"] == drug1]
        }

        drug2_data = {
            "targets": [t for t in targets if t["drug"] == drug2],
            "adverse_events": [e for e in adverse_events if e["drug"] == drug2],
            "efficacy": [e for e in efficacy if e["drug"] == drug2],
            "trials": [t for t in trials if t["drug"] == drug2]
        }

        # Check for shared targets
        shared_targets = self._find_shared_targets(drug1_data["targets"], drug2_data["targets"])

        # Compare safety
        drug1_severe = len([e for e in drug1_data["adverse_events"] if e.get("severity") == "Severe"])
        drug2_severe = len([e for e in drug2_data["adverse_events"] if e.get("severity") == "Severe"])

        safer_drug = drug1 if drug1_severe < drug2_severe else drug2

        # Compare efficacy
        drug1_avg_efficacy = sum(e.get("efficacy", 0) for e in drug1_data["efficacy"]) / len(drug1_data["efficacy"]) if drug1_data["efficacy"] else 0
        drug2_avg_efficacy = sum(e.get("efficacy", 0) for e in drug2_data["efficacy"]) / len(drug2_data["efficacy"]) if drug2_data["efficacy"] else 0

        more_effective = drug1 if drug1_avg_efficacy > drug2_avg_efficacy else drug2

        report = {
            "comparison": f"{drug1} vs {drug2}",
            "shared_characteristics": {
                "shared_targets": shared_targets,
                "same_mechanism_class": self._check_mechanism_similarity(
                    drug1_data["targets"], drug2_data["targets"]
                )
            },
            "safety_comparison": {
                "safer_drug": safer_drug,
                f"{drug1}_severe_events": drug1_severe,
                f"{drug2}_severe_events": drug2_severe,
                "adverse_event_overlap": self._find_common_adverse_events(
                    drug1_data["adverse_events"], drug2_data["adverse_events"]
                )
            },
            "efficacy_comparison": {
                "more_effective": more_effective,
                f"{drug1}_avg_efficacy": round(drug1_avg_efficacy, 3),
                f"{drug2}_avg_efficacy": round(drug2_avg_efficacy, 3),
                "efficacy_difference": abs(drug1_avg_efficacy - drug2_avg_efficacy)
            },
            "trial_comparison": {
                f"{drug1}_trials": drug1_data["trials"][0]["totalTrials"] if drug1_data["trials"] else 0,
                f"{drug2}_trials": drug2_data["trials"][0]["totalTrials"] if drug2_data["trials"] else 0,
                f"{drug1}_enrollment": drug1_data["trials"][0]["totalEnrollment"] if drug1_data["trials"] else 0,
                f"{drug2}_enrollment": drug2_data["trials"][0]["totalEnrollment"] if drug2_data["trials"] else 0
            },
            "recommendation": self._generate_comparison_recommendation(
                safer_drug, more_effective, drug1, drug2
            )
        }

        return report

    def _synthesize_evidence_chain(self, gene: str, context: Dict,
                                    evidence_chain: List[Evidence]) -> Dict[str, Any]:
        """Generate complete evidence chain report"""

        gene_info = context.get("step_1", {}).get("results", [])
        diseases = context.get("step_2", {}).get("results", [])
        treatments = context.get("step_3", {}).get("results", [])
        trials = context.get("step_4", {}).get("results", [])
        institutions = context.get("step_5", {}).get("results", [])

        # Validate evidence chain
        chain_strength = self._validate_evidence_chain(evidence_chain)

        report = {
            "gene": gene,
            "gene_information": gene_info[0] if gene_info else {},
            "evidence_chain": {
                "step_1_genetic": {
                    "diseases_associated": len(diseases),
                    "strongest_association": diseases[0] if diseases else None,
                    "evidence_quality": [d.get("evidenceLevel") for d in diseases]
                },
                "step_2_therapeutic": {
                    "treatments_available": len(treatments),
                    "highest_efficacy": max([t.get("efficacy", 0) for t in treatments]) if treatments else 0,
                    "drugs": [t["drug"] for t in treatments]
                },
                "step_3_clinical": {
                    "supporting_trials": len(trials),
                    "phase_3_trials": len([t for t in trials if t.get("phase") == "Phase 3"]),
                    "total_enrollment": sum(t.get("enrollment", 0) for t in trials)
                },
                "step_4_institutional": {
                    "sponsoring_institutions": len(institutions),
                    "institutions": [i["institution"] for i in institutions]
                }
            },
            "chain_validation": {
                "overall_strength": chain_strength,
                "confidence_score": sum(e.confidence for e in evidence_chain) / len(evidence_chain) if evidence_chain else 0,
                "gaps": self._identify_evidence_gaps(context)
            },
            "complete_story": self._narrative_from_evidence_chain(
                gene, diseases, treatments, trials, institutions
            )
        }

        return report

    # ============================================================================
    # HELPER METHODS
    # ============================================================================

    def _call_bedrock(self, prompt: str) -> str:
        """Call AWS Bedrock Claude model"""
        try:
            response = self.bedrock.invoke_model(
                modelId='anthropic.claude-3-sonnet-20240229-v1:0',
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 2000,
                    "messages": [{"role": "user", "content": prompt}]
                })
            )
            response_body = json.loads(response['body'].read())
            return response_body['content'][0]['text']
        except Exception as e:
            return json.dumps({
                "reasoning": "Error calling Bedrock",
                "next_action": "retry",
                "confidence": 0.0
            })

    def _extract_insights(self, action: Action, results: List[Dict]) -> List[str]:
        """Extract insights from query results"""
        if not results:
            return ["No data found"]

        insights = [f"Found {len(results)} results for: {action.purpose}"]

        # Add specific insights based on action type
        if "adverse" in action.purpose.lower():
            severe = len([r for r in results if r.get("severity") == "Severe"])
            if severe > 0:
                insights.append(f"⚠️ {severe} severe adverse events identified")

        if "efficacy" in action.purpose.lower():
            avg_efficacy = sum(r.get("efficacy", 0) for r in results) / len(results)
            insights.append(f"Average efficacy: {avg_efficacy:.2%}")

        return insights

    def _assess_completeness(self, observation: Observation) -> float:
        """Assess if we have enough data (0.0 to 1.0)"""
        if not observation.results:
            return 0.0
        if len(observation.results) < 3:
            return 0.5
        return 0.9

    def _suggest_next_steps(self, observation: Observation) -> List[str]:
        """Suggest what to do next based on observation"""
        if not observation.success:
            return ["Retry query with different parameters"]
        if len(observation.results) == 0:
            return ["Broaden search criteria", "Check related entities"]
        return ["Continue to next analysis step"]

    def _assess_evidence_strength(self, result: Dict) -> str:
        """Assess strength of evidence from a result"""
        if "evidenceLevel" in result:
            level = result["evidenceLevel"]
            if level == "High":
                return "strong"
            elif level == "Medium":
                return "moderate"
            else:
                return "weak"

        if "efficacy" in result:
            eff = result["efficacy"]
            if eff > 0.5:
                return "strong"
            elif eff > 0.3:
                return "moderate"
            else:
                return "weak"

        return "moderate"

    def _generate_safety_recommendation(self, risk_level: str, severe_events: List,
                                        interactions: List, genetic_validation: List) -> str:
        """Generate safety recommendation"""
        if risk_level == "High":
            return ("⚠️ HIGH RISK: Consider alternative treatments. "
                   f"{len(severe_events)} severe adverse events reported. "
                   "Requires close monitoring if prescribed.")
        elif risk_level == "Moderate":
            return ("⚠️ MODERATE RISK: Acceptable with appropriate monitoring. "
                   f"{len(interactions)} potential drug interactions identified.")
        else:
            return ("✅ LOW RISK: Generally safe profile. Standard monitoring recommended.")

    def _generate_repurposing_recommendation(self, candidates: List[Dict]) -> str:
        """Generate drug repurposing recommendation"""
        if not candidates:
            return "No strong candidates identified for repurposing."

        top = candidates[0]
        return (f"💡 Top candidate: {top['drug']} "
               f"(repurposing score: {top['repurposing_score']:.1f}/100). "
               f"Original efficacy: {top.get('efficacy', 0):.1%}. "
               "Recommend Phase 2 trial for validation.")

    def _generate_comparison_recommendation(self, safer: str, more_effective: str,
                                            drug1: str, drug2: str) -> str:
        """Generate comparison recommendation"""
        if safer == more_effective:
            return f"✅ {safer} is both safer and more effective. Recommended as first-line therapy."
        else:
            return (f"⚖️ Trade-off: {safer} is safer, but {more_effective} is more effective. "
                   "Choice depends on patient risk profile and disease severity.")

    def _count_by_phase(self, trials: List[Dict]) -> Dict[str, int]:
        """Count trials by phase"""
        phases = {}
        for t in trials:
            phase = t.get("phase", "Unknown")
            phases[phase] = phases.get(phase, 0) + 1
        return phases

    def _extract_top_journals(self, papers: List[Dict]) -> List[str]:
        """Extract most common journals"""
        journals = {}
        for p in papers:
            journal = p.get("journal", "Unknown")
            journals[journal] = journals.get(journal, 0) + 1
        return sorted(journals.items(), key=lambda x: x[1], reverse=True)[:5]

    def _find_shared_targets(self, targets1: List[Dict], targets2: List[Dict]) -> List[str]:
        """Find shared protein targets"""
        if not targets1 or not targets2:
            return []

        proteins1 = set()
        for t in targets1:
            for target in t.get("targets", []):
                proteins1.add(target.get("protein"))

        proteins2 = set()
        for t in targets2:
            for target in t.get("targets", []):
                proteins2.add(target.get("protein"))

        return list(proteins1 & proteins2)

    def _check_mechanism_similarity(self, targets1: List[Dict], targets2: List[Dict]) -> bool:
        """Check if mechanisms are similar"""
        if not targets1 or not targets2:
            return False

        mech1 = targets1[0].get("mechanism", "")
        mech2 = targets2[0].get("mechanism", "")

        # Simple similarity check
        common_words = set(mech1.lower().split()) & set(mech2.lower().split())
        return len(common_words) >= 2

    def _find_common_adverse_events(self, events1: List[Dict], events2: List[Dict]) -> List[str]:
        """Find adverse events common to both drugs"""
        events1_set = set(e["event"] for e in events1)
        events2_set = set(e["event"] for e in events2)
        return list(events1_set & events2_set)

    def _validate_evidence_chain(self, chain: List[Evidence]) -> str:
        """Validate strength of evidence chain"""
        if not chain:
            return "weak"

        strong_count = len([e for e in chain if e.strength == "strong"])

        if strong_count >= len(chain) * 0.7:
            return "strong"
        elif strong_count >= len(chain) * 0.4:
            return "moderate"
        else:
            return "weak"

    def _identify_evidence_gaps(self, context: Dict) -> List[str]:
        """Identify gaps in evidence chain"""
        gaps = []

        if not context.get("step_4"):
            gaps.append("Missing clinical trial validation")

        if not context.get("step_2"):
            gaps.append("Genetic evidence not found")

        return gaps if gaps else ["No significant gaps identified"]

    def _narrative_from_evidence_chain(self, gene: str, diseases: List,
                                        treatments: List, trials: List,
                                        institutions: List) -> str:
        """Create narrative story from evidence chain"""
        story = f"The {gene} gene "

        if diseases:
            story += f"is strongly associated with {diseases[0]['disease']} "
            story += f"(evidence level: {diseases[0].get('evidenceLevel', 'unknown')}). "

        if treatments:
            story += f"Current treatments include {treatments[0]['drug']} "
            story += f"with {treatments[0].get('efficacy', 0):.0%} efficacy. "

        if trials:
            story += f"This is supported by {len(trials)} clinical trials "
            story += f"with {sum(t.get('enrollment', 0) for t in trials)} total participants. "

        if institutions:
            story += f"Leading institutions include {', '.join([i['institution'] for i in institutions[:2]])}."

        return story


# ============================================================================
# REFINED USE CASES
# ============================================================================

def run_refined_use_cases():
    """Run all refined use cases"""

    framework = ReActAgentFramework()

    print("\n" + "="*80)
    print("REFINED USE CASES FOR CLINICAL AI AGENTS")
    print("="*80)

    # USE CASE 1: Clinical Safety Analysis
    print("\n" + "="*80)
    print("USE CASE 1: Clinical Safety - Drug Switching")
    print("="*80)
    print("Scenario: Patient with EGFR mutation previously treated with Nivolumab")
    print("Question: Is switching to Pembrolizumab safe?")

    safety_report = framework.clinical_safety_agent(
        drug_name="Pembrolizumab",
        patient_context={
            "genetic_mutation": "EGFR",
            "previous_treatment": "Nivolumab",
            "disease": "Non-Small Cell Lung Cancer"
        }
    )

    print("\n📊 SAFETY REPORT:")
    print(json.dumps(safety_report, indent=2))

    # USE CASE 2: Drug Repurposing
    print("\n\n" + "="*80)
    print("USE CASE 2: Drug Repurposing with Evidence Chain")
    print("="*80)
    print("Question: Can NSCLC drugs be repurposed for Colorectal Cancer?")

    repurposing_report = framework.drug_repurposing_agent(
        source_disease="Lung Cancer",
        target_disease="Colorectal Cancer"
    )

    print("\n📊 REPURPOSING REPORT:")
    print(json.dumps(repurposing_report, indent=2))

    # USE CASE 3: Research Landscape
    print("\n\n" + "="*80)
    print("USE CASE 3: Investment Landscape Analysis")
    print("="*80)
    print("Question: Who's leading Alzheimer's research and which institutions are investing?")

    landscape_report = framework.research_landscape_agent("Alzheimer")

    print("\n📊 RESEARCH LANDSCAPE:")
    print(json.dumps(landscape_report, indent=2))

    # USE CASE 4: Comparative Safety
    print("\n\n" + "="*80)
    print("USE CASE 4: PD-1 Inhibitor Comparison")
    print("="*80)
    print("Question: Compare safety profiles of Pembrolizumab vs Nivolumab")

    comparison_report = framework.comparative_safety_agent(
        "Pembrolizumab",
        "Nivolumab"
    )

    print("\n📊 COMPARISON REPORT:")
    print(json.dumps(comparison_report, indent=2))

    # USE CASE 5: Evidence Chain Tracing
    print("\n\n" + "="*80)
    print("USE CASE 5: Complete Evidence Chain")
    print("="*80)
    print("Question: Trace complete story from BRCA1 mutation to treatment")

    evidence_report = framework.evidence_chain_agent("BRCA1")

    print("\n📊 EVIDENCE CHAIN:")
    print(json.dumps(evidence_report, indent=2))

    framework.close()

    print("\n" + "="*80)
    print("ALL USE CASES COMPLETED!")
    print("="*80)


if __name__ == "__main__":
    run_refined_use_cases()
