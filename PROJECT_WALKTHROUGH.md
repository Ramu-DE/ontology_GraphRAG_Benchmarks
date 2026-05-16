# Project Walkthrough: What We Built and Why

This document explains everything we did in this project, step by step, from understanding the W3C semantic stack through building real benchmarks against live cloud infrastructure.

---

## Phase 1: Understanding the W3C Semantic Web Stack

We started by studying the RDF (Resource Description Framework) stack — a layered architecture defined by the W3C that turns raw data into machine-understandable knowledge.

### The Stack (Bottom to Top)

| Layer | What It Does |
|---|---|
| **RDF** | Foundation data model. Everything is a triple: `Subject → Predicate → Object`. Chain triples to form a directed labeled graph. |
| **RDFS** | Adds schema vocabulary — classes, properties, domains, ranges, hierarchies. Gives structure to raw triples. |
| **SPARQL** | Query language for RDF graphs. Supports traversal, pattern matching, and federation across multiple endpoints. |
| **OWL** | Web Ontology Language. Defines rich ontologies with classes, properties, axioms. Enables inference — deriving new facts from existing ones. |
| **SHACL** | Shapes Constraint Language. Validates that graph data conforms to expected shapes and constraints. Quality enforcement. |

### What We Built

- **Biomedical ontology** (`ontology/biomedical_ontology.ttl`) — 19 classes, 17 object properties, 22 datatype properties, 5 OWL reasoning rules covering drugs, diseases, genes, proteins, clinical trials, researchers, biomarkers, and adverse events
- **Sample data** (`data/sample/`) — 10 drugs, 10 diseases, 10 clinical trials, 10 genes, 10 proteins, 10 biomarkers, 10 researchers, with 12 relationship CSV files
- **SHACL validation shapes** (`validation/shacl_shapes.ttl`) — Constraints for every entity type (Drug IDs must match `D###`, disease categories must be one of 5 values, Phase 3 trials need enrollment >= 100, etc.)
- **29 SPARQL queries** (`queries/sparql_queries.sparql`) — From simple lookups to complex multi-hop traversals
- **W3C demo script** (`main.py`) — Loads ontology, validates data against SHACL shapes, runs SPARQL queries, demonstrates AI use cases

### Diagram

We created a redesigned W3C RDF Stack diagram (`Graph/w3c_rdf_stack.png`) with a dark gradient theme, color-coded layers, 3D depth effects, triple flow visualization, and key takeaways. An interactive HTML version (`Graph/w3c_rdf_stack.html`) is also included.

---

## Phase 2: Loading Data into Neo4j Aura

We loaded the biomedical knowledge graph into a live **Neo4j Aura** cloud instance.

### What We Did

1. Connected to Neo4j Aura (cloud-hosted graph database)
2. Loaded all 10 drugs, 7 diseases, and 14 TREATS relationships using Cypher
3. Created a native **HNSW vector index** on drug nodes for embedding-based similarity search
4. Generated 384-dimensional embeddings for each drug (deterministic hash-based for reproducibility)
5. Stored embeddings as node properties — no external vector database needed

### Key Script: `scripts/csv_to_neo4j.py`
Converts CSV data files into Cypher import statements for Neo4j.

---

## Phase 3: HNSW Tuning and Sparse Matrix Analysis

We built a dedicated demo (`hnsw_sparse_matrix_demo.py`) to explore how HNSW (Hierarchical Navigable Small World) vector index parameters affect search performance.

### Three HNSW Configurations Tested

| Config | M (connectivity) | efConstruction | efRuntime | Purpose |
|---|---|---|---|---|
| **Fast / Low Memory** | 4 | 32 | 32 | Prototyping, small datasets, low latency |
| **Balanced** | 16 | 100 | 100 | Production default — good recall with reasonable memory |
| **Max Recall** | 48 | 256 | 256 | Clinical-grade accuracy where missing a result is dangerous |

### What These Parameters Mean

- **M** = how many neighbors each node connects to in the HNSW graph. Higher M = better recall but more memory
- **efConstruction** = how many candidates to explore when building the index. Higher = better quality index
- **efRuntime** = how many candidates to explore during search. Higher = better recall at query time

### Sparse Matrix Analysis

We demonstrated how graph adjacency (which drug treats which disease) and vector similarity (how semantically close two drugs are) combine into a unified structure. This shows why native vector support inside the graph DB eliminates the need for a separate vector database — both the graph structure and vector similarity live in the same query engine.

### Unified Query (The "Holy Grail")

```cypher
CALL db.index.vector.queryNodes('drug_embedding_vector', 5, $queryVector)
YIELD node AS drug, score
OPTIONAL MATCH (drug)-[:TREATS]->(disease:Disease)
RETURN drug.name, score, collect(disease.name) AS diseases
ORDER BY score DESC
```

One query does vector similarity search AND graph traversal. No serialization, no network hop, no friction.

---

## Phase 4: Provisioning AWS Infrastructure

To do a real comparison, we provisioned three AWS services from scratch:

### Services Created

| Service | Type | Region | Purpose |
|---|---|---|---|
| **Neptune Analytics** | Graph + native vectors | us-west-2 | Unified architecture (like Neo4j) |
| **Neptune Database** | Graph only (Gremlin) | us-west-2 | Traditional graph DB for two-layer test |
| **OpenSearch** | Vector search (kNN HNSW) | us-west-2 | Separate vector layer for two-layer test |

### Why Three Services?

We wanted to test three distinct architectures:

1. **Neo4j Aura** — Already running. Unified vector + graph in one engine
2. **Neptune Analytics** — AWS's answer to unified GraphRAG. Native vector search via `neptune.algo.vectors.topKByEmbedding()` combined with openCypher graph traversal in one query
3. **Neptune DB + OpenSearch** — The traditional "two-layer" approach where vector search happens in one service and graph traversal in another, with serialization friction in between

---

## Phase 5: Real Benchmarks Against Live Infrastructure

This is the core of the project. Every number is a real measurement — no simulations, no mathematical models, no `time.sleep()` calls.

### Script: `real_neptune_vs_neo4j_benchmark.py`

### Architecture 1: Neo4j Aura (Unified)

```
+------------------------------+
|        Neo4j Aura            |
|  +--------+  +------------+ |
|  |  HNSW  |  |   Cypher   | |
|  | Vector |--|   Graph    | |
|  | Index  |  | Traversal  | |
|  +--------+  +------------+ |
|     ONE query, ZERO friction |
+------------------------------+
```

- Vector index: `drug_embedding_vector` (HNSW, 384 dimensions, cosine similarity)
- Query: `CALL db.index.vector.queryNodes()` → `MATCH (drug)-[:TREATS]->(disease)`
- **Result: 208.1 ms average** (dominated by cross-region network latency to Aura cloud)

### Architecture 2: Neptune Analytics (Unified)

```
+------------------------------+
|    Neptune Analytics         |
|  +--------+  +------------+ |
|  | Native |  | openCypher | |
|  | Vector |--|   Graph    | |
|  | Search |  | Traversal  | |
|  +--------+  +------------+ |
|     ONE query, ZERO friction |
+------------------------------+
```

- Embedding storage: `CALL neptune.algo.vectors.upsert(node, [embedding])`
- Vector search: `CALL neptune.algo.vectors.topKByEmbedding([vec], {topK: 5})`
- Combined with `MATCH (node)-[:TREATS]->(disease)` in one query
- **Result: 34.8 ms average** (same-region AWS, no network penalty)

### Architecture 3: Neptune DB + OpenSearch (Two-Layer)

```
+--------------+    serialize    +--------------+
|  OpenSearch   |----- IDs ----->|  Neptune DB   |
|  (kNN HNSW)  |    (friction)   |  (Gremlin)   |
+--------------+                 +--------------+
     Step 1            Step 2          Step 3
```

- Step 1: OpenSearch kNN returns top-K drug IDs by vector similarity
- Step 2: Serialize candidate IDs into Gremlin query format (the "friction")
- Step 3: Neptune DB Gremlin traverses `g.V(ids).out('TREATS').values('name')`
- **Result: 69.1 ms average** (high variance: 32–180ms due to cold starts)

### Final Benchmark Results

| Architecture | Mean | Min | Max | Friction |
|---|---|---|---|---|
| **Neptune Analytics** (unified) | **34.8 ms** | 32.6 ms | 37.1 ms | 0 ms |
| **Neptune DB + OpenSearch** (two-layer) | **69.1 ms** | 32.3 ms | 180.5 ms | ~0.04 ms |
| **Neo4j Aura** (unified) | **208.1 ms** | 175.1 ms | 261.2 ms | 0 ms |

### Per-Query Results

| Query | Neo4j Aura | Neptune Analytics | Neptune DB + OpenSearch |
|---|---|---|---|
| PD-1 inhibitor (Immuno) | 249.6 ms | 34.4 ms | 180.5 ms |
| HER2 antibody (HER2) | 175.1 ms | 37.1 ms | 39.2 ms |
| Kinase inhibitor (TKI) | 175.2 ms | 32.6 ms | 32.3 ms |
| GLP-1 peptide (GLP1) | 179.3 ms | 37.0 ms | 56.9 ms |
| Amyloid-beta Ab (Amyloid) | 261.2 ms | 33.0 ms | 36.5 ms |

### Key Insights

1. **Neptune Analytics is ~6x faster than Neo4j Aura** — but this is largely a same-region vs cross-region comparison. Neo4j's architecture is equally unified; the latency penalty is geographic, not architectural.

2. **Unified beats two-layer** — Neptune Analytics (34.8ms) is 2x faster than Neptune DB + OpenSearch (69.1ms), even though both are same-region. The two-layer approach pays for an extra network hop and query serialization.

3. **Two-layer friction is real but small at this scale** — The serialization cost was ~0.04ms (negligible), but the second network hop to Neptune DB adds 30–150ms depending on cold/warm state. At scale with thousands of candidate IDs, serialization friction would grow significantly.

4. **Both Neo4j and Neptune Analytics solve the same problem** — native vector search inside the graph engine. The choice between them is about ecosystem (AWS vs Neo4j), query language (openCypher vs Cypher), and pricing model.

---

## Phase 6: Technical Challenges We Solved

### Neptune Analytics Parameter Format
Neptune Analytics openCypher does NOT support parameterized queries (`$param` syntax). All values must be inline in the query string.

**Failed:** `MERGE (d:Drug {id: $id})` with `parameters={"id": {"value": "D001"}}`
**Fixed:** `CREATE (d:Drug {node_id: 'D001', name: 'Pembrolizumab'})`

### Neptune Analytics Embedding Storage
Standard property assignment doesn't work for vectors.

**Failed:** `SET d.embedding = [0.1, 0.2, ...]` (error: "Unsupported property value")
**Fixed:** `CALL neptune.algo.vectors.upsert(d, [0.1, 0.2, ...]) YIELD success`

### Neptune DB Gremlin Bindings
Neptune DB does not support Gremlin parameter bindings.

**Failed:** `g.addV('Drug').property(id, did)` with `{"did": "D001"}`
**Fixed:** `g.addV('Drug').property(id, 'D001')`

### Neptune DB Edge Creation
The `g.V().addE().to(g.V())` pattern fails on Neptune.

**Failed:** `g.V('D001').addE('TREATS').to(g.V('DIS001'))`
**Fixed:** `g.addE('TREATS').from(V('D001')).to(V('DIS001'))`

### OpenSearch Connection
AWS OpenSearch with fine-grained access control requires `RequestsHttpConnection` class, not the default urllib3 connection.

---

## Phase 7: Graph Visualizations

We generated four interactive HTML visualizations from the live Neptune graph data using PyVis:

| Visualization | File | What It Shows |
|---|---|---|
| **Full Drug-Disease Graph** | `neptune_graph_full.html` | All 10 drugs → 7 diseases with 14 TREATS edges. Drugs colored by mechanism (PD-1 = red, GLP-1 = green, etc). |
| **Co-Indication Network** | `neptune_graph_coindication.html` | Drug-to-drug connections through shared diseases. Shows combination therapy candidates (e.g., Nivolumab + Pembrolizumab + Atezolizumab all treat Lung Cancer). |
| **Mechanism Clusters** | `neptune_graph_mechanisms.html` | Star hub nodes per mechanism type with drugs radiating outward, dashed lines to diseases. |
| **Vector Search + Graph** | `neptune_vector_search_graph.html` | Gold star = search query "PD-1 immune checkpoint inhibitor for lung cancer". Lines to drugs sized by Neptune Analytics similarity score, then TREATS edges to diseases. |

All visualizations feature drag-and-drop nodes, zoom, hover tooltips, and physics-based layouts.

### Jupyter Notebook

`neptune_graph_visualization.ipynb` — Uses AWS `graph-notebook` magic commands (`%%gremlin`, `%%oc`) to query Neptune DB and Neptune Analytics directly from Jupyter cells with built-in Graph tab rendering.

---

## Phase 8: Multi-Agent Clinical Risk Assessment

We built a multi-agent system using the AWS Strands Agent Framework (`strands_production_grade.py`) with five specialized agents:

| Agent | What It Does |
|---|---|
| **PharmacologyAgent** | Analyzes drug mechanisms, evaluates efficacy based on graph relationships |
| **ClinicalSafetyAgent** | Assesses adverse event profiles, computes safety scores from trial data |
| **GeneticsAgent** | Evaluates genomic markers, mutation impacts, gene-drug associations |
| **DrugInteractionAgent** | Checks multi-drug interactions using graph path analysis |
| **PatientProfileAgent** | Integrates patient-specific risk factors (comorbidities, age, genetics) |

These agents compute a **7-factor risk score**: drug efficacy, adverse event severity, genetic compatibility, drug interactions, trial evidence strength, biomarker predictiveness, and patient comorbidities. Every answer is grounded in graph triples — no hallucination.

---

## Phase 9: Cleanup and GitHub Push

Before pushing to GitHub (`Ramu-DE/ontology_GraphRAG_Benchmarks`):

1. **Scrubbed all credentials** — moved hardcoded Neo4j passwords, OpenSearch credentials, and Neptune endpoint IDs to environment variables loaded from `.env` (gitignored)
2. **Updated `.env.example`** — template with all required environment variables
3. **Wrote comprehensive README** — architecture diagrams, benchmark tables, project structure, quick start guide
4. **Created redesigned W3C diagram** — dark theme PNG replacing the original

---

## Summary of Files We Created or Modified

### Core Scripts
| File | Purpose |
|---|---|
| `real_neptune_vs_neo4j_benchmark.py` | Real 3-architecture benchmark (the main deliverable) |
| `hnsw_sparse_matrix_demo.py` | HNSW parameter tuning + sparse matrix analysis |
| `main.py` | W3C semantic stack demo (RDF, SHACL, SPARQL) |
| `strands_production_grade.py` | Multi-agent clinical risk assessment |

### Data and Ontology
| File | Purpose |
|---|---|
| `ontology/biomedical_ontology.ttl` | OWL ontology (19 classes) |
| `validation/shacl_shapes.ttl` | SHACL validation shapes |
| `queries/sparql_queries.sparql` | 29 SPARQL query examples |
| `data/sample/*.csv` | Sample biomedical data |

### Visualizations
| File | Purpose |
|---|---|
| `neptune_graph_full.html` | Drug-Disease interactive graph |
| `neptune_graph_coindication.html` | Co-indication network |
| `neptune_graph_mechanisms.html` | Mechanism cluster visualization |
| `neptune_vector_search_graph.html` | Vector search results on graph |
| `Graph/w3c_rdf_stack.png` | Redesigned W3C RDF Stack diagram |

### Results
| File | Purpose |
|---|---|
| `real_benchmark_comparison.json` | Raw benchmark data (all 3 architectures) |

---

## Technologies Used

| Category | Technologies |
|---|---|
| Ontology and Validation | RDF, RDFS, OWL, SHACL (W3C standards) |
| Query Languages | SPARQL, Cypher, openCypher, Gremlin |
| Graph Databases | Neo4j Aura, AWS Neptune Database, Neptune Analytics |
| Vector Search | Neo4j HNSW index, Neptune native vectors, OpenSearch kNN |
| AI Agents | AWS Strands Agent Framework, AWS Bedrock |
| Visualization | PyVis (interactive HTML graphs), graph-notebook (Jupyter) |
| Infrastructure | AWS (Neptune, OpenSearch, IAM), Neo4j Aura Cloud |
| Languages | Python, Turtle (RDF), SPARQL, Cypher, Gremlin |
