# Biomedical Knowledge Graph — W3C Semantic Stack + AWS Neptune + GraphRAG

> A production-grade biomedical knowledge graph demonstrating the full W3C semantic web stack, AWS Neptune graph database, GraphRAG architecture benchmarks, and multi-agent clinical risk assessment using AWS Strands.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Repository Structure](#repository-structure)
4. [Quick Start](#quick-start)
5. [Modules](#modules)
   - [Ontology (RDF/OWL)](#1-ontology--rdfs--owl)
   - [Data Layer (CSV → RDF)](#2-data-layer-csv--rdf)
   - [SHACL Validation](#3-shacl-validation)
   - [SPARQL Queries](#4-sparql-queries)
   - [AWS Neptune Setup](#5-aws-neptune-setup)
   - [GraphRAG Benchmarks](#6-graphrag-benchmarks)
   - [AWS Strands Agents](#7-aws-strands-agents)
6. [Benchmark Results](#benchmark-results)
7. [Jupyter Notebook](#jupyter-notebook)
8. [Excel Reference](#excel-reference)
9. [Setup & Installation](#setup--installation)
10. [Environment Variables](#environment-variables)

---

## Project Overview

This project demonstrates how to build a **semantically rich biomedical knowledge graph** that enables AI systems to reason over pharmaceutical data without hallucinating.

### What's Covered

| Domain | Technology | Purpose |
|--------|-----------|---------|
| Knowledge Representation | RDF (Turtle) | Subject-Predicate-Object triples |
| Schema / Vocabulary | RDFS | Classes, subclasses, property domains & ranges |
| Logic & Reasoning | OWL 2 | Auto-classification inference rules |
| Graph Queries | SPARQL | Multi-hop traversal, aggregation |
| Data Validation | SHACL | Constraints enforced at write time |
| Graph Database | AWS Neptune | Production graph store (Gremlin + SPARQL) |
| Vector Search | OpenSearch | Semantic similarity via kNN embeddings |
| Unified GraphRAG | Neo4j / Neptune Analytics | Native vectors + graph in one query |
| Multi-Agent AI | AWS Strands | 5 specialized clinical risk agents |

### Domain

Pharmaceutical research, clinical trials, drug discovery:
- **10 Drugs** — Pembrolizumab, Nivolumab, Atezolizumab, Erlotinib, Tirzepatide, and more
- **10 Diseases** — NSCLC, Melanoma, Breast Cancer, Type 2 Diabetes, Alzheimer's, and more
- **10 Clinical Trials** — KEYNOTE-024, CheckMate-214, FLAURA, LEADER, CLARITY AD, and more
- **10 Genes** — EGFR, KRAS, TP53, BRCA1, BRAF, HER2, ALK, RET, MET, PTEN
- **10 Proteins** — PD-1, PD-L1, HER2, EGFR protein, VEGFR, mTOR, CDK4/6
- **10 Biomarkers**, **10 Researchers**, **10+ Institutions**, **10 Adverse Events**
- **~500+ RDF triples**, **13 relationship types**

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                      DATA SOURCES                                   │
│  CSV Files (drugs, diseases, trials, genes, proteins, biomarkers)  │
└──────────────────────────┬──────────────────────────────────────────┘
                           │ scripts/csv_to_rdf.py
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   W3C SEMANTIC STACK                                 │
│                                                                     │
│  ┌──────────┐  ┌──────────┐  ┌────────┐  ┌─────────┐  ┌────────┐ │
│  │  SHACL   │  │  SPARQL  │  │  OWL   │  │  RDFS   │  │  RDF   │ │
│  │Validation│  │ Queries  │  │Reasoning│  │ Schema  │  │ Triples│ │
│  └──────────┘  └──────────┘  └────────┘  └─────────┘  └────────┘ │
│                                                                     │
│  output/biomedical_data.ttl   ontology/biomedical_ontology.ttl     │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
┌─────────────────────┐    ┌────────────────────────┐
│    AWS NEPTUNE      │    │       NEO4J             │
│   (Graph Store)     │    │  (Unified GraphRAG)     │
│                     │    │                         │
│  Neptune DB         │    │  Native Vector Index    │
│    + OpenSearch     │    │  (HNSW M=32)            │
│  (Two-Layer)        │    │  + Cypher queries       │
│                     │    │  One query, no friction │
│  Gremlin / SPARQL   │    │                         │
└──────────┬──────────┘    └───────────┬─────────────┘
           │                           │
           └──────────┬────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    GRAPHRAG QUERY LAYER                              │
│                                                                     │
│  Two-Layer (Neptune+OpenSearch):  31.5ms @ 1B nodes  ❌ 11.8% friction│
│  Unified (Neo4j/FalkorDB):        23.6ms @ 1B nodes  ✅ 0% friction │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  AWS STRANDS MULTI-AGENT SYSTEM                      │
│                                                                     │
│  PharmacologyAgent ──→ ClinicalSafetyAgent ──→ GeneticsAgent       │
│       │                                               │             │
│       └───→ DrugInteractionAgent ←──→ PatientProfileAgent          │
│                                                                     │
│  7 Risk Factors → Weighted Score → Clinical Decision                │
│  Simple: 0.250 (LOW)  →  Production: 0.485 (MODERATE)  [+94%]     │
└─────────────────────────────────────────────────────────────────────┘
```

See [`architecture_diagram.ipynb`](architecture_diagram.ipynb) for the full interactive notebook.

---

## Repository Structure

```
Ontology/
│
├── 📓 architecture_diagram.ipynb    ← JUPYTER NOTEBOOK (start here)
├── 📊 Biomedical_KG_Workshop_Reference.xlsx  ← Full Excel reference
├── 📄 README.md                     ← This file
├── 🔑 .env.example                  ← Copy to .env and fill credentials
│
├── ontology/
│   ├── biomedical_ontology.ttl      ← OWL ontology (classes, properties, rules)
│   ├── biomedical_ontology.dot      ← Graphviz source for relationship diagram
│   └── biomedical_ontology_diagram.html  ← Interactive HTML diagram (open in browser)
│
├── validation/
│   └── shacl_shapes.ttl             ← SHACL constraint shapes per entity
│
├── queries/
│   └── sparql_queries.sparql        ← 29 SPARQL query examples
│
├── data/sample/
│   ├── drugs.csv
│   ├── diseases.csv
│   ├── clinical_trials.csv
│   ├── genes.csv
│   ├── proteins.csv
│   ├── biomarkers.csv
│   ├── researchers.csv
│   ├── institutions.csv
│   ├── research_papers.csv
│   ├── adverse_events.csv
│   └── relationships/               ← 13 relationship CSV files
│       ├── drug_treats_disease.csv
│       ├── drug_targets_protein.csv
│       ├── gene_associated_with_disease.csv
│       └── ...
│
├── scripts/
│   ├── csv_to_rdf.py                ← Converts CSVs → RDF Turtle triples
│   └── csv_to_neo4j.py              ← Converts CSVs → Neo4j Cypher import
│
├── main.py                          ← Demo: load → validate → query → show AI
├── requirements.txt                 ← Python dependencies
├── create_excel.py                  ← Generates the Excel reference workbook
│
│   ── AWS Neptune ──
├── neptune_data_loader.py           ← Loads data into Neptune via Gremlin
├── neptune_opensearch_benchmark.py  ← Two-layer benchmark (Neptune + OpenSearch)
├── neptune_analytics_unified_benchmark.py  ← Neptune Analytics unified queries
├── neptune_analytics_simple_benchmark.py
├── neptune_graphrag_comparison.py   ← Neptune vs Neo4j comparison
├── test_neptune_connection.py       ← Test Neptune / OpenSearch connectivity
├── opensearch_data_loader.py        ← Load embeddings into OpenSearch kNN index
├── neptune_infrastructure_status.sh ← Check AWS resource status
│
│   ── GraphRAG & Neo4j ──
├── graphrag_benchmark.py            ← Full 3-arch × 7-scale HNSW benchmark
├── graphrag_native_vectors.py       ← Neo4j native vector index + unified queries
├── graphrag_benchmark_results.json  ← Raw benchmark output
├── real_benchmark_implementation.py ← Live benchmark vs simulated
├── real_benchmark_results.json
├── neo4j_data_generator.py          ← Generates synthetic biomedical data
├── neo4j_data_loader.py             ← Loads into Neo4j via Bolt
├── lambda_benchmark.py              ← AWS Lambda-based benchmark runner
├── demo_real_benchmark_connection.py
│
│   ── AWS Strands Agents ──
├── strands_production_grade.py      ← Main: 5 agents + 7 risk factors
├── strands_official_implementation.py ← Official Strands SDK patterns
├── strands_official_simple.py
├── strands_demo_standalone.py       ← Standalone demo (no dependencies)
├── strands_agent_implementation.py  ← Agent framework base
├── strands_visual_demo.py           ← HTML generator for workflow viz
├── strands_with_visualization.py
├── strands_visualizer.py
├── react_agent_framework.py         ← ReAct (Reason+Act) agent base
├── aws_agent_neo4j.py               ← AWS agent connecting to Neo4j
├── generate_production_visualization.py  ← HTML risk comparison generator
├── show_production_comparison.py    ← ASCII comparison display
├── show_visualization.py            ← ASCII workflow display
├── production_risk_assessment.json  ← Sample output from production agents
│
│   ── Visualizations ──
├── production_visualization.html    ← Side-by-side risk comparison (open in browser)
├── strands_visualization.html       ← Agent workflow visualization
├── graphrag_benchmark_visualization.html  ← Benchmark dashboard
├── web_visualizer.html              ← Knowledge graph web visualizer
│
│   ── Documentation (Markdown) ──
├── AWS_NEPTUNE_SETUP_PLAN.md
├── BENCHMARK_SUMMARY.md
├── COMPLETE_BENCHMARK_SUMMARY.md
├── GRAPHRAG_BENCHMARK_RESULTS.md
├── GRAPHRAG_UNIFIED_ARCHITECTURE.md
├── IMPLEMENTATION_GUIDE.md
├── NEPTUNE_CONNECTION_INFO.md        ← ⚠️  Contains placeholder endpoints only
├── NEPTUNE_VECTOR_SEARCH_ANALYSIS.md
├── PRODUCTION_IMPLEMENTATION_SUMMARY.md
├── QUICK_START.md
├── RDF_Team_Presentation.md
├── RISK_CALCULATION_EXPLAINED.md
├── STRANDS_README.md
└── USE_CASES_QUICK_REFERENCE.md
```

---

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/Ramu-DE/Ontology.git
cd Ontology
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 3. Convert CSV Data to RDF

```bash
python scripts/csv_to_rdf.py
# → output/biomedical_data.ttl (~500 triples)
```

### 4. Run the Main Demo

```bash
python main.py
# Loads ontology → validates SHACL → executes SPARQL → shows AI examples
```

### 5. Open the Jupyter Notebook

```bash
pip install jupyter
jupyter notebook architecture_diagram.ipynb
```

### 6. Open the Interactive HTML Diagram

```
ontology/biomedical_ontology_diagram.html  ← open in any browser
production_visualization.html              ← agent risk comparison
graphrag_benchmark_visualization.html      ← benchmark dashboard
```

---

## Modules

### 1. Ontology — RDFS + OWL

**File:** `ontology/biomedical_ontology.ttl`

Defines the schema and reasoning rules for the entire knowledge graph.

**Classes (19 total):**

| Type | Classes |
|------|---------|
| Core | Drug, Disease, ClinicalTrial, Gene, Protein, Biomarker, Researcher, Institution, ResearchPaper, AdverseEvent |
| Drug subtypes | MonoclonalAntibody, SmallMolecule, Peptide |
| Disease subtypes | OncologyDisease, MetabolicDisease, NeurologicalDisease |
| Biomarker subtypes | ProteinBiomarker, GeneticBiomarker, MetabolicBiomarker |
| Protein subtype | ImmuneCheckpointProtein |

**OWL Inference Rules:**

```turtle
# Auto-classify drugs targeting immune checkpoints as Immunotherapy
:Immunotherapy owl:equivalentClass [
    owl:intersectionOf (
        :Drug
        [ owl:onProperty :targets ;
          owl:someValuesFrom :ImmuneCheckpointProtein ]
    )
] .
```

| Rule | Condition | Result |
|------|-----------|--------|
| ApprovedTreatment | Drug + treats Disease + status="Approved" | Auto-labeled |
| Immunotherapy | Drug + targets ImmuneCheckpointProtein | Auto-labeled |
| HighImpactResearcher | Researcher + hIndex ≥ 70 | Auto-labeled |
| DefinitiveEvidence | Trial + Phase 3 + Completed | Auto-labeled |
| EpidemicDisease | Disease + prevalence="Very High" | Auto-labeled |

---

### 2. Data Layer (CSV → RDF)

**File:** `scripts/csv_to_rdf.py`

Converts all CSV source files into RDF Turtle triples.

```bash
python scripts/csv_to_rdf.py
# Output: output/biomedical_data.ttl, .rdf, .nt
```

**W3C Stack Layers:**

```
SHACL (Validation)     ← data/quality constraints
SPARQL (Query)         ← graph traversal & pattern matching
OWL (Reasoning)        ← logical inference
RDFS (Schema)          ← classes, properties, hierarchy
RDF (Data Model)       ← Subject → Predicate → Object
```

---

### 3. SHACL Validation

**File:** `validation/shacl_shapes.ttl`

Enforces data quality before any data reaches the graph:

```turtle
:DrugShape a sh:NodeShape ;
    sh:targetClass :Drug ;
    sh:property [
        sh:path :drugId ;
        sh:minCount 1 ; sh:maxCount 1 ;
        sh:pattern "^D[0-9]{3}$" ;        # Must be D001, D002, etc.
    ] ;
    sh:property [
        sh:path :approvalStatus ;
        sh:in ("Approved" "Experimental" "Withdrawn") ;
    ] .
```

---

### 4. SPARQL Queries

**File:** `queries/sparql_queries.sparql`  — 29 examples

```sparql
# Multi-hop: Gene → Disease → Drug pathway
SELECT ?geneSymbol ?diseaseName ?drugName ?efficacy
WHERE {
    ?gene bio:geneSymbol ?geneSymbol .
    ?disease bio:associatedWithGene ?gene ;
             bio:diseaseName ?diseaseName .
    ?drug bio:treats ?disease ;
          bio:drugName ?drugName .
    FILTER(?efficacy > 0.50)
}
```

---

### 5. AWS Neptune Setup

**Cluster:** `graphrag-neptune-cluster.cluster-cracicy0ect3.us-west-2.neptune.amazonaws.com:8182`  
**Region:** `us-west-2`

```bash
# Create Neptune cluster
aws neptune create-db-cluster \
    --db-cluster-identifier graphrag-neptune \
    --engine neptune \
    --db-subnet-group-name graphrag-subnet \
    --region us-west-2

# Load data
python neptune_data_loader.py

# Run two-layer benchmark (Neptune + OpenSearch)
python neptune_opensearch_benchmark.py
```

Key files:
- `neptune_data_loader.py` — Gremlin bulk loader
- `opensearch_data_loader.py` — Vector index loader
- `neptune_opensearch_benchmark.py` — Two-layer latency benchmark
- `neptune_analytics_unified_benchmark.py` — Unified query benchmark

---

### 6. GraphRAG Benchmarks

**File:** `graphrag_benchmark.py`

Tests three architectures at 7 scales (1K → 1B nodes):

```
Architecture                Latency @ 1B nodes   Friction
─────────────────────────────────────────────────────────
Neptune DB + OpenSearch     31.5ms               11.8% (3.7ms)
Neptune Analytics           31.9ms               0% (unified)
Neo4j / FalkorDB            23.6ms               0% (unified + optimized)
```

**The Holy Grail — Unified Query:**

```cypher
// Vector search + graph traversal in ONE query — zero context switching
CALL db.index.vector.queryNodes('Drug_embedding_vector', 10, $query_vector)
YIELD node AS drug, score
MATCH (drug)-[:TREATS]->(disease:Disease)
OPTIONAL MATCH (disease)<-[:ASSOCIATED_WITH]-(gene:Gene)
RETURN drug.name, score, collect(disease.name), collect(gene.symbol)
ORDER BY score DESC
```

---

### 7. AWS Strands Agents

**File:** `strands_production_grade.py`

Five specialized agents collaborate to compute a 7-factor clinical risk score:

| Agent | Role | Risk Factor |
|-------|------|------------|
| PharmacologyAgent | Drug mechanisms | Severity, Frequency baseline |
| ClinicalSafetyAgent | Adverse events | +15% (High severity) |
| GeneticsAgent | Genetic validation | Confidence scoring |
| DrugInteractionAgent ⭐ | Drug-drug interactions | +15% |
| PatientProfileAgent ⭐ | Demographics | +20% age, +20% comorbidities |

**Test case — 68-year-old, EGFR mutation, switching from Nivolumab:**

| Algorithm | Score | Level | Factors |
|-----------|-------|-------|---------|
| Simple | 0.250 | LOW 🟢 | 1 |
| **Production** | **0.485** | **MODERATE 🟡** | **7** |

**Improvement: +94% more accurate** — clinical decision changed from standard to enhanced monitoring.

---

## Benchmark Results

### Performance at 1 Billion Nodes

```
Architecture             Vector Search  Graph Traversal  Overhead   Total
──────────────────────────────────────────────────────────────────────────
Neptune DB + OpenSearch  17.8ms         5.6ms            3.7ms      31.5ms
Neptune Analytics        25.4ms         5.4ms            0ms        31.9ms
Neo4j / FalkorDB         17.6ms         5.2ms            0ms        23.6ms  ✅ WINNER
```

**Key findings:**
- Two-layer friction is real: 3.7ms (11.8%) overhead from serialization + network
- Unified architecture eliminates this entirely (0ms handover)
- Full HNSW tuning (M=32, efConstruction=128, efRuntime=100) gives 30% boost
- Sparse matrix representation gives additional 20% graph traversal gain
- All architectures scale logarithmically O(log n) — 1B nodes stays under 35ms

---

## Jupyter Notebook

**File:** [`architecture_diagram.ipynb`](architecture_diagram.ipynb)

Covers everything in one interactive notebook:
1. W3C Semantic Stack visual explanation
2. Ontology class hierarchy diagram
3. Entity relationship diagram (SVG)
4. SPARQL query examples with live execution
5. SHACL validation walkthrough
6. AWS Neptune architecture comparison
7. GraphRAG benchmark visualization
8. Strands agent workflow diagram
9. Risk factor calculation walkthrough
10. End-to-end data flow

---

## Excel Reference

**File:** [`Biomedical_KG_Workshop_Reference.xlsx`](Biomedical_KG_Workshop_Reference.xlsx)

14-sheet comprehensive reference workbook:

| Sheet | Content |
|-------|---------|
| 📋 Overview | TOC + workshop summary |
| 🏗️ W3C Stack | All 5 layers explained |
| 🧬 Ontology Classes | 19 classes with attributes |
| 🔗 Properties | 17 object + 22 datatype properties |
| 🤖 OWL Rules | 5 reasoning rules |
| ☁️ AWS Neptune | Setup, endpoints, commands |
| 📊 Benchmarks | Results table 1K→1B |
| 🚀 GraphRAG | Two-layer vs unified |
| 🤖 Strands Agents | 5 agents, 7 factors, results |
| 📁 Project Files | Every file explained |
| 💡 SPARQL Queries | 12 key patterns |
| 🔐 SHACL Validation | 17 constraint rules |
| 📈 Data Summary | Entity/relationship counts |
| 🗺️ Flow Diagram | 14-step end-to-end flow |

---

## Setup & Installation

### Prerequisites

- Python 3.8+
- AWS CLI configured (`aws configure`)
- Neo4j (optional, for Neo4j benchmarks)
- Jupyter (optional, for notebook)

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Core Dependencies (`requirements.txt`)

```
rdflib>=6.0.0          # RDF/SPARQL processing
pyshacl>=0.20.0        # SHACL validation
boto3>=1.26.0          # AWS SDK
opensearch-py          # OpenSearch client
gremlinpython          # Neptune Gremlin client
neo4j                  # Neo4j driver
sentence-transformers  # Embedding generation
openpyxl               # Excel generation
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

| Variable | Description |
|----------|-------------|
| `NEO4J_URI` | Neo4j Aura connection URI |
| `NEO4J_PASSWORD` | Neo4j password |
| `AWS_REGION` | AWS region (default: us-west-2) |
| `NEPTUNE_CLUSTER_ENDPOINT` | Neptune cluster hostname |
| `OPENSEARCH_ENDPOINT` | OpenSearch HTTPS endpoint |
| `OPENSEARCH_PASSWORD` | OpenSearch admin password |
| `ANTHROPIC_API_KEY` | Anthropic Claude API key |

> **Security:** Never commit `.env` — it is in `.gitignore`. Only `.env.example` is committed.

---

## Key Concepts

### RDF Triple
The fundamental unit: **Subject → Predicate → Object**
```
Pembrolizumab  treats  Non-Small-Cell-Lung-Cancer
Drug:D001      targets Protein:PD-1
```

### OWL Reasoning
Logic rules that auto-classify instances:
```
IF Drug + targets ImmuneCheckpointProtein
THEN → Drug is automatically an Immunotherapy
```

### HNSW (Hierarchical Navigable Small World)
The vector index algorithm enabling O(log n) search at billion scale:
- **M=32** — optimal connectivity for billion-scale
- **efConstruction=128** — index build quality
- **efRuntime=100** — search speed/accuracy trade-off

### GraphRAG Holy Grail
> "If we want to reach the holy grail of GraphRAG at scale, we have to stop thinking of vectors as a separate add-on to a graph engine. When vectors and edges share the same sparse matrix representation, there is no friction."

---

## License

Educational and research use. See individual file headers.

---

## Acknowledgements

- W3C Semantic Web standards: RDF, RDFS, OWL, SPARQL, SHACL
- AWS Neptune, OpenSearch, Strands, Bedrock
- Neo4j native vector indices
- FalkorDB sparse matrix architecture
- Biomedical ontologies: SNOMED CT, Gene Ontology, UniProt
