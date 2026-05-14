# AWS Strands Multi-Agent Framework Implementation

## Overview

This implementation uses **AWS Strands** (https://strandsagents.com/) to orchestrate multiple specialized AI agents for complex biomedical reasoning tasks.

## What is AWS Strands?

AWS Strands is a multi-agent orchestration framework that enables:
- **Multiple specialized agents** working together
- **Agent-to-agent communication** for collaboration
- **Shared memory** for context across agents
- **Parallel execution** for efficiency
- **Tool integration** (Neo4j, AWS Bedrock, custom tools)

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    STRANDS ORCHESTRATOR                         │
│  - Manages agent lifecycle                                      │
│  - Routes messages between agents                               │
│  - Coordinates workflows                                        │
│  - Maintains shared memory                                      │
└─────────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│  Clinical    │   │ Pharmacology │   │  Genetics    │
│  Safety      │   │   Agent      │   │   Agent      │
│  Agent       │   └──────────────┘   └──────────────┘
└──────────────┘            │                   │
        │                   │                   │
        └───────────────────┴───────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │    SHARED MEMORY      │
                │  - Facts              │
                │  - Conversations      │
                │  - Evidence           │
                │  - Decisions          │
                └───────────────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
                ▼                       ▼
        ┌──────────────┐       ┌──────────────┐
        │   Neo4j      │       │ AWS Bedrock  │
        │  Knowledge   │       │   Claude 3   │
        │   Graph      │       │              │
        └──────────────┘       └──────────────┘
```

## Specialized Agents

### 1. ClinicalSafetyAgent
**Role:** Clinical safety analysis and risk assessment

**Tools:**
- Neo4j queries for drug data
- AWS Bedrock for reasoning
- Risk calculation algorithms

**Responsibilities:**
- Analyze drug mechanisms
- Assess adverse events
- Calculate risk scores
- Generate safety recommendations

### 2. PharmacologyAgent
**Role:** Drug mechanism and pharmacology analysis

**Tools:**
- Neo4j queries for drug-protein interactions
- Pathway analysis

**Responsibilities:**
- Analyze drug mechanisms
- Compare molecular targets
- Assess pathway relevance
- Identify drug similarities

### 3. GeneticsAgent
**Role:** Genetic analysis and validation

**Tools:**
- Neo4j queries for gene-disease associations
- Genetic evidence scoring

**Responsibilities:**
- Validate genetic mutations
- Check disease genetic overlap
- Assess association strength
- Provide evidence levels

### 4. TrialDataAgent
**Role:** Clinical trial data analysis

**Tools:**
- Neo4j queries for trial data
- Statistical analysis

**Responsibilities:**
- Retrieve adverse events
- Compare safety profiles
- Map trial landscapes
- Assess trial quality

### 5. ResearchAnalystAgent
**Role:** Research landscape analysis

**Tools:**
- Neo4j queries for researchers, institutions
- Network analysis

**Responsibilities:**
- Identify top researchers
- Map institutional networks
- Analyze funding patterns
- Build collaboration maps

### 6. PublicationAgent
**Role:** Scientific publication analysis

**Tools:**
- Neo4j queries for papers
- Citation analysis

**Responsibilities:**
- Analyze publication trends
- Identify top journals
- Map research topics

### 7. RepurposingAgent
**Role:** Drug repurposing discovery

**Tools:**
- Neo4j pathway queries
- Scoring algorithms

**Responsibilities:**
- Find repurposing candidates
- Score drug-disease matches
- Build evidence chains

### 8. ComparativeAnalystAgent
**Role:** Comparative analysis and synthesis

**Tools:**
- Synthesis algorithms
- Statistical comparison

**Responsibilities:**
- Compare drugs/treatments
- Synthesize multi-source data
- Generate recommendations

### 9. EvidenceValidatorAgent
**Role:** Evidence chain validation

**Tools:**
- Validation rules
- Quality scoring

**Responsibilities:**
- Validate evidence chains
- Score evidence strength
- Identify gaps
- Assess confidence

## Multi-Agent Workflows

### Workflow 1: Clinical Safety Analysis

```
User Request: "Is Pembrolizumab safe for patient with EGFR mutation?"

┌─────────────────────────────────────────────────────────────────┐
│ Step 1: Orchestrator assigns task to ClinicalSafetyAgent       │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 2: ClinicalSafetyAgent → PharmacologyAgent                │
│   Request: "Get drug mechanism and targets"                    │
│   Response: {mechanism: "PD-1 inhibitor", targets: ["PD-1"]}   │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 3: ClinicalSafetyAgent → TrialDataAgent                   │
│   Request: "Get adverse events from trials"                    │
│   Response: {events: [...], severe_count: 2}                   │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 4: ClinicalSafetyAgent → GeneticsAgent                    │
│   Request: "Validate EGFR mutation match"                      │
│   Response: {match: true, quality: "strong", efficacy: 0.45}   │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│ Step 5: ClinicalSafetyAgent synthesizes final report           │
│   - Risk score: 35/100 (MODERATE)                              │
│   - Recommendation: "Acceptable with monitoring"               │
│   - Genetic validation: POSITIVE                               │
└─────────────────────────────────────────────────────────────────┘
```

### Workflow 2: Drug Repurposing

```
User Request: "Can NSCLC drugs be repurposed for Colorectal Cancer?"

Step 1: RepurposingAgent finds candidate drugs from NSCLC
Step 2: GeneticsAgent checks genetic overlap between diseases
Step 3: PharmacologyAgent validates pathway relevance
Step 4: EvidenceValidatorAgent scores candidates
Step 5: RepurposingAgent generates final report with evidence chain
```

### Workflow 3: Research Landscape

```
User Request: "Who's leading Alzheimer's research?"

Step 1: ResearchAnalystAgent finds top researchers
Step 2: TrialDataAgent maps clinical trials
Step 3: PublicationAgent analyzes papers
Step 4: ResearchAnalystAgent builds collaboration network
Step 5: Generate landscape report with institutions and funding
```

### Workflow 4: Comparative Analysis

```
User Request: "Compare Pembrolizumab vs Nivolumab safety"

Step 1: PharmacologyAgent compares mechanisms (parallel)
Step 2: TrialDataAgent compares safety profiles (parallel)
Step 3: EvidenceValidatorAgent compares efficacy (parallel)
Step 4: ComparativeAnalystAgent synthesizes comparison
Step 5: Generate recommendation with trade-offs
```

### Workflow 5: Evidence Chain

```
User Request: "Trace complete BRCA1 mutation story"

Step 1: GeneticsAgent gets gene information
Step 2: GeneticsAgent finds disease associations
Step 3: PharmacologyAgent finds treatments
Step 4: TrialDataAgent validates with clinical data
Step 5: ResearchAnalystAgent maps institutional investment
Step 6: EvidenceValidatorAgent validates complete chain
Step 7: Generate narrative with confidence scores
```

## Key Features

### 1. Agent Communication
Agents communicate via messages:

```python
# Agent A sends message to Agent B
message = agent_a.send_message(
    to_agent="PharmacologyAgent",
    message_type="task",
    content={"action": "analyze_mechanism", "drug": "Pembrolizumab"},
    priority=1  # High priority
)

# Agent B receives and processes
agent_b.receive_message(message)
result = agent_b.process()
```

### 2. Shared Memory
All agents access shared memory:

```python
# Agent writes to shared memory
self.memory.facts['drug_mechanism'] = {
    "mechanism": "PD-1 inhibitor",
    "confidence": 0.95
}

# Another agent reads from shared memory
mechanism = self.memory.facts.get('drug_mechanism')
```

### 3. Parallel Execution
Multiple agents work in parallel:

```python
# Execute 3 agents in parallel
results = orchestrator.execute_parallel([
    {"agent": "PharmacologyAgent", "task": "compare_mechanisms"},
    {"agent": "TrialDataAgent", "task": "compare_safety"},
    {"agent": "EvidenceValidatorAgent", "task": "compare_efficacy"}
])
```

### 4. Evidence Tracking
Evidence is accumulated throughout workflow:

```python
self.memory.evidence.append({
    "source": "TrialDataAgent",
    "type": "clinical_trial",
    "data": {...},
    "strength": "strong",
    "confidence": 0.9
})
```

## Installation

```bash
# Install dependencies
pip install neo4j boto3 python-dotenv

# Your Neo4j credentials are already in .env file
# AWS credentials should be configured via `aws configure`
```

## Running the Demo

```bash
# Make sure Neo4j graph is loaded
python scripts/csv_to_neo4j.py

# Run Strands multi-agent demo
python strands_agent_implementation.py
```

## Use Cases (Refined)

### USE CASE 1: Clinical Safety - Drug Switching
**Scenario:** Patient with EGFR mutation, previously on Nivolumab, considering Pembrolizumab

**Question:** "I'm considering Pembrolizumab for a patient with EGFR mutation who previously used Nivolumab. Check drug interactions, safety profile, and genetic evidence before recommending."

**Agents Involved:**
1. ClinicalSafetyAgent (coordinator)
2. PharmacologyAgent (mechanisms)
3. GeneticsAgent (EGFR validation)
4. TrialDataAgent (safety data)

**Expected Output:**
```json
{
  "drug": "Pembrolizumab",
  "patient_context": {
    "genetic_mutation": "EGFR",
    "previous_treatment": "Nivolumab"
  },
  "risk_assessment": {
    "risk_score": 35,
    "risk_level": "MODERATE",
    "severe_events_count": 2
  },
  "drug_interactions": {
    "with_nivolumab": "Both target PD-1, no direct interaction expected"
  },
  "genetic_validation": {
    "match_found": true,
    "match_quality": "Strong",
    "expected_efficacy": 0.45
  },
  "recommendation": "⚠️ ACCEPTABLE with monitoring. Genetic profile supports use. Switch is safe."
}
```

### USE CASE 2: Drug Repurposing with Evidence Chain
**Question:** "Can drugs used for Non-Small Cell Lung Cancer be repurposed for Colorectal Cancer? Trace the full evidence chain for any candidates."

**Agents Involved:**
1. RepurposingAgent (coordinator)
2. PharmacologyAgent (pathway analysis)
3. GeneticsAgent (genetic overlap)
4. EvidenceValidatorAgent (evidence scoring)

**Expected Output:**
```json
{
  "source_disease": "Non-Small Cell Lung Cancer",
  "target_disease": "Colorectal Cancer",
  "genetic_overlap": {
    "shared_genes": ["KRAS", "TP53"],
    "strongest_association": "KRAS (Very Strong)"
  },
  "candidate_drugs": [
    {
      "drug": "Pembrolizumab",
      "source_efficacy": 0.45,
      "repurposing_score": 78,
      "pathway_support": true,
      "genetic_evidence": "Strong"
    }
  ],
  "evidence_chain": [
    "Step 1: KRAS mutation common in both diseases",
    "Step 2: Pembrolizumab targets PD-1 pathway",
    "Step 3: PD-1 pathway relevant in colorectal cancer",
    "Step 4: Phase 2 trial recommended"
  ],
  "recommendation": "💡 Pembrolizumab shows promise (score: 78/100). Strong genetic link via KRAS. Recommend Phase 2 trial."
}
```

### USE CASE 3: Investment Landscape
**Question:** "Who are the top researchers working on Alzheimer's Disease treatments and which institutions are sponsoring the clinical trials? Give me the full picture."

**Agents Involved:**
1. ResearchAnalystAgent (coordinator)
2. TrialDataAgent (trial mapping)
3. PublicationAgent (paper analysis)

**Expected Output:**
```json
{
  "disease": "Alzheimer's Disease",
  "research_leaders": {
    "top_researchers": [
      {"name": "Dr. Emily Watson", "hIndex": 85, "institution": "Stanford"},
      {"name": "Dr. Jennifer White", "hIndex": 81, "institution": "MIT"}
    ]
  },
  "top_institutions": [
    {
      "name": "Stanford University",
      "researchers": ["Dr. Emily Watson", "..."],
      "trials_sponsored": 5,
      "total_hindex": 425
    }
  ],
  "clinical_trials": {
    "total_trials": 10,
    "by_phase": {"Phase 3": 3, "Phase 2": 7},
    "active_drugs": ["Lecanemab", "Aducanumab", "Metformin"]
  },
  "collaboration_network": {
    "key_clusters": ["Stanford-MIT cluster", "NIH collaborative"],
    "funding_sources": ["NIH", "Eisai", "Private foundations"]
  }
}
```

### USE CASE 4: PD-1 Inhibitor Comparison
**Question:** "Compare the safety profiles of both Pembrolizumab and Nivolumab across their trials. Do they share targets? Which one has fewer severe adverse events?"

**Agents Involved:**
1. ComparativeAnalystAgent (coordinator)
2. PharmacologyAgent (target comparison)
3. TrialDataAgent (safety comparison)

**Expected Output:**
```json
{
  "comparison": "Pembrolizumab vs Nivolumab",
  "shared_characteristics": {
    "shared_targets": ["PD-1"],
    "same_mechanism_class": true,
    "mechanism_similarity": "Both are PD-1 inhibitors"
  },
  "safety_comparison": {
    "safer_drug": "Nivolumab",
    "pembrolizumab_severe_events": 2,
    "nivolumab_severe_events": 1,
    "common_adverse_events": [
      "Immune-related pneumonitis",
      "Hypothyroidism"
    ]
  },
  "efficacy_comparison": {
    "pembrolizumab_avg_efficacy": 0.44,
    "nivolumab_avg_efficacy": 0.39,
    "more_effective": "Pembrolizumab",
    "difference": 0.05
  },
  "recommendation": "⚖️ Trade-off: Nivolumab is safer (fewer severe events), but Pembrolizumab is more effective (+5% efficacy). Choice depends on patient risk profile."
}
```

### USE CASE 5: Complete Evidence Chain Validation
**Question:** "Trace the complete story from BRCA1 mutations through disease, treatment, trials, and institutional investment. Validate the genetic evidence."

**Agents Involved:**
1. EvidenceValidatorAgent (coordinator)
2. GeneticsAgent (genetic evidence)
3. PharmacologyAgent (treatment evidence)
4. TrialDataAgent (clinical evidence)
5. ResearchAnalystAgent (institutional evidence)

**Expected Output:**
```json
{
  "gene": "BRCA1",
  "gene_information": {
    "symbol": "BRCA1",
    "name": "Breast Cancer Gene 1",
    "chromosome": "17",
    "function": "DNA repair"
  },
  "evidence_chain": {
    "step_1_genetic": {
      "diseases_associated": 2,
      "strongest_association": "Breast Cancer (Very Strong)",
      "evidence_quality": ["High", "High"]
    },
    "step_2_therapeutic": {
      "treatments_available": 1,
      "highest_efficacy": 0.52,
      "drugs": ["Trastuzumab"]
    },
    "step_3_clinical": {
      "supporting_trials": 3,
      "phase_3_trials": 2,
      "total_enrollment": 4500
    },
    "step_4_institutional": {
      "sponsoring_institutions": 5,
      "institutions": ["Memorial Sloan Kettering", "Dana-Farber", "..."]
    }
  },
  "chain_validation": {
    "overall_strength": "STRONG",
    "confidence_score": 0.89,
    "gaps": []
  },
  "complete_story": "The BRCA1 gene is strongly associated with Breast Cancer (evidence level: High). Current treatments include Trastuzumab with 52% efficacy. This is supported by 3 clinical trials with 4,500 total participants. Leading institutions include Memorial Sloan Kettering, Dana-Farber."
}
```

## Advantages of Strands Framework

### 1. Specialization
Each agent is expert in one domain:
- Better accuracy than single general-purpose agent
- Agents can be independently improved
- Clear separation of concerns

### 2. Collaboration
Agents work together:
- Complex tasks decomposed automatically
- Agents leverage each other's expertise
- Natural division of labor

### 3. Scalability
Easy to add new agents:
```python
# Add new agent without changing existing code
class ImagingAgent(StrandsAgent):
    def analyze_scans(self, patient_id):
        # New capability
        pass

orchestrator.register_agent(ImagingAgent())
```

### 4. Transparency
Full audit trail:
- All agent communications logged
- Evidence tracked at each step
- Decisions are explainable

### 5. Resilience
Graceful degradation:
- If one agent fails, others continue
- Orchestrator can retry failed operations
- Partial results still useful

## Comparison: Single LLM vs Strands Multi-Agent

| Feature | Single LLM | Strands Multi-Agent |
|---------|------------|---------------------|
| **Accuracy** | Moderate | High (specialized agents) |
| **Explainability** | Limited | Full audit trail |
| **Scalability** | Hard | Easy (add agents) |
| **Specialization** | General | Domain experts |
| **Tool Use** | Limited | Native integration |
| **Parallel Execution** | No | Yes |
| **Evidence Tracking** | Manual | Automatic |
| **Cost** | Lower | Higher (multiple calls) |

## Best Practices

### 1. Agent Design
- **Single Responsibility:** Each agent does one thing well
- **Clear Interfaces:** Well-defined input/output
- **Stateless:** Agents should not hold state (use shared memory)

### 2. Communication
- **Explicit Messages:** Clear message types and content
- **Priority Levels:** Critical tasks get priority
- **Async Where Possible:** Don't block unnecessarily

### 3. Memory Management
- **Structured Facts:** Use consistent schemas
- **Evidence Tracking:** Track source and confidence
- **Cleanup:** Remove stale data

### 4. Error Handling
- **Graceful Degradation:** Continue with partial results
- **Retry Logic:** Retry failed operations
- **Fallbacks:** Have backup strategies

## Next Steps

### 1. Enhance Agents
- Add more specialized agents (imaging, genomics, etc.)
- Improve reasoning with better prompts
- Add learning from past decisions

### 2. Add Capabilities
- Real-time data ingestion
- Integration with external APIs (PubMed, ClinicalTrials.gov)
- Automated literature review

### 3. Production Deployment
- Deploy to AWS Lambda/ECS
- Add monitoring and observability
- Implement caching for performance
- Build REST API for frontend

### 4. Advanced Features
- Agent learning and adaptation
- Dynamic agent creation
- Self-organizing workflows
- Consensus mechanisms for conflicting opinions

## Resources

- **AWS Strands:** https://strandsagents.com/
- **Neo4j:** https://neo4j.com/docs/
- **AWS Bedrock:** https://docs.aws.amazon.com/bedrock/
- **Multi-Agent Systems:** Research papers and frameworks

## Summary

The **AWS Strands multi-agent framework** provides a powerful way to orchestrate specialized AI agents for complex clinical reasoning tasks. By breaking down problems into specialized sub-tasks handled by expert agents, we achieve:

✅ Higher accuracy through specialization  
✅ Better explainability through audit trails  
✅ Greater scalability through modular design  
✅ Improved reliability through distributed processing  

All five use cases demonstrate real-world clinical scenarios where multiple types of evidence must be gathered, validated, and synthesized into actionable recommendations.

**Ready to run:** `python strands_agent_implementation.py`
