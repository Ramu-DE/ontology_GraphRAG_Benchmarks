# Use Cases - Quick Reference Card

## 🏥 USE CASE 1: Clinical Safety - Drug Switching

**Scenario:** Patient with EGFR mutation, switching from Nivolumab to Pembrolizumab

**Input:**
```python
{
    "type": "clinical_safety",
    "drug": "Pembrolizumab",
    "patient_context": {
        "genetic_mutation": "EGFR",
        "previous_treatment": "Nivolumab",
        "disease": "Non-Small Cell Lung Cancer"
    }
}
```

**Agents:** ClinicalSafetyAgent → PharmacologyAgent → TrialDataAgent → GeneticsAgent

**Output:** Risk assessment (score, level), adverse events, genetic validation, recommendation

**Key Insight:** Multi-step safety validation with genetic evidence

---

## 💊 USE CASE 2: Drug Repurposing

**Scenario:** Finding NSCLC drugs for Colorectal Cancer

**Input:**
```python
{
    "type": "drug_repurposing",
    "source_disease": "Non-Small Cell Lung Cancer",
    "target_disease": "Colorectal Cancer"
}
```

**Agents:** RepurposingAgent → GeneticsAgent → PharmacologyAgent → EvidenceValidatorAgent

**Output:** Candidate drugs with scores, genetic overlap, pathway analysis, evidence chain

**Key Insight:** Validates repurposing with genetic and pathway evidence

---

## 🔬 USE CASE 3: Research Investment Landscape

**Scenario:** Mapping Alzheimer's research ecosystem

**Input:**
```python
{
    "type": "research_landscape",
    "disease": "Alzheimer's Disease"
}
```

**Agents:** ResearchAnalystAgent → TrialDataAgent → PublicationAgent

**Output:** Top researchers, institutions, trials, funding, collaboration networks

**Key Insight:** Complete picture of research ecosystem and investment

---

## ⚖️ USE CASE 4: Comparative Drug Analysis

**Scenario:** Comparing Pembrolizumab vs Nivolumab

**Input:**
```python
{
    "type": "comparative_analysis",
    "drug1": "Pembrolizumab",
    "drug2": "Nivolumab"
}
```

**Agents:** ComparativeAnalystAgent → PharmacologyAgent → TrialDataAgent → EvidenceValidatorAgent

**Output:** Side-by-side comparison of mechanisms, safety, efficacy with trade-off analysis

**Key Insight:** Clear trade-off guidance (safety vs efficacy)

---

## 🔗 USE CASE 5: Complete Evidence Chain

**Scenario:** Tracing BRCA1 mutation to treatment

**Input:**
```python
{
    "type": "evidence_chain",
    "gene": "BRCA1"
}
```

**Agents:** EvidenceValidatorAgent → GeneticsAgent → PharmacologyAgent → TrialDataAgent → ResearchAnalystAgent

**Output:** Complete chain from gene → disease → treatment → trials → institutions with validation

**Key Insight:** Full evidence trail with confidence scores at each step

---

## Running Use Cases

```bash
# Run all 5 use cases
python strands_agent_implementation.py

# Run specific use case (modify script)
# Change task_type at bottom of file

# Interactive mode
python aws_agent_neo4j.py --interactive
```

---

## Agent Responsibilities

| Agent | Primary Role | Key Queries |
|-------|--------------|-------------|
| ClinicalSafetyAgent | Safety assessment | Risk scoring, adverse events |
| PharmacologyAgent | Drug mechanisms | Targets, pathways, interactions |
| GeneticsAgent | Genetic validation | Gene-disease associations |
| TrialDataAgent | Clinical evidence | Trial results, safety data |
| ResearchAnalystAgent | Research landscape | Researchers, institutions |
| RepurposingAgent | Drug discovery | Candidate identification |
| EvidenceValidatorAgent | Evidence quality | Scoring, validation |

---

## Quick Decision Guide

**Choose Use Case Based On:**

- **Patient-specific decision?** → Use Case 1 (Clinical Safety)
- **Finding new drug applications?** → Use Case 2 (Repurposing)
- **Mapping research field?** → Use Case 3 (Landscape)
- **Comparing drug options?** → Use Case 4 (Comparative)
- **Validating genetic evidence?** → Use Case 5 (Evidence Chain)

---

## Expected Runtimes

| Use Case | Agents | Graph Queries | Approx Time |
|----------|--------|---------------|-------------|
| 1. Clinical Safety | 4 | 4-5 | 15-20 sec |
| 2. Drug Repurposing | 4 | 4-6 | 20-25 sec |
| 3. Research Landscape | 3 | 3-4 | 15-20 sec |
| 4. Comparative | 4 | 5-7 | 20-30 sec |
| 5. Evidence Chain | 5 | 6-8 | 25-35 sec |

---

## Customization Examples

### Add New Patient Context
```python
patient_context = {
    "genetic_mutation": "KRAS",  # Change gene
    "age": 65,                    # Add age
    "comorbidities": ["diabetes"], # Add conditions
    "previous_treatment": "Chemotherapy"
}
```

### Change Target Diseases
```python
{
    "type": "drug_repurposing",
    "source_disease": "Melanoma",      # Different source
    "target_disease": "Renal Cell Carcinoma"  # Different target
}
```

### Focus on Specific Researchers
```python
{
    "type": "research_landscape",
    "disease": "Type 2 Diabetes",
    "min_hindex": 80  # Filter by impact
}
```

---

## Output Formats

All use cases return JSON with:
- ✅ **Primary result** (recommendation, report, comparison)
- ✅ **Evidence** (sources, confidence scores)
- ✅ **Agents involved** (audit trail)
- ✅ **Graph queries executed** (reproducibility)

---

## Production Checklist

Before deploying to production:

- [ ] Load full dataset into Neo4j (not just sample)
- [ ] Configure AWS Bedrock quotas
- [ ] Add authentication/authorization
- [ ] Implement caching for frequent queries
- [ ] Add monitoring and logging
- [ ] Build REST API wrapper
- [ ] Create frontend UI
- [ ] Write automated tests
- [ ] Document API endpoints
- [ ] Set up CI/CD pipeline

---

## Quick Troubleshooting

**Issue:** "Connection to Neo4j failed"
- **Fix:** Check `.env` file, verify Neo4j Aura is running

**Issue:** "AWS Bedrock access denied"
- **Fix:** Run `aws configure`, check IAM permissions

**Issue:** "Agent returned empty results"
- **Fix:** Check if data is loaded: `MATCH (n) RETURN count(n)`

**Issue:** "Slow query performance"
- **Fix:** Add Neo4j indexes on frequently queried properties

---

## Key Takeaways

1. **Multi-agent > Single agent** for complex reasoning
2. **Evidence tracking** enables explainability
3. **Specialized agents** = higher accuracy
4. **Graph database** enables relationship traversal
5. **AWS Strands** orchestrates collaboration

---

**Ready to run:** `python strands_agent_implementation.py` 🚀

**Questions?** Check `STRANDS_README.md` for full documentation
