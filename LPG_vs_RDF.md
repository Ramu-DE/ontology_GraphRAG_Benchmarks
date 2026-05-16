# LPG (Neo4j) vs RDF (Neptune) — A Clear Comparison

Two fundamentally different ways to model graph data. Same goal — represent connected knowledge. Different philosophy, different trade-offs.

---

## What is LPG (Labeled Property Graph)?

LPG is the data model used by **Neo4j**, **Neptune Analytics**, and **Neptune DB (Gremlin/openCypher mode)**.

Everything in LPG is one of two things: a **node** or a **relationship**.

### Nodes

Nodes represent entities. They have:

- **Labels** — categorize what the node *is* (a node can have multiple labels)
- **Properties** — key-value pairs storing data about the node

```
(:Drug {name: "Pembrolizumab", mechanism: "PD-1 inhibitor", approval_year: 2014})
(:Disease {name: "Lung Cancer", icd10: "C34.9", category: "Oncology"})
(:Gene {symbol: "EGFR", chromosome: "7"})
```

### Relationships

Relationships connect nodes. They have:

- **Type** — describes what the connection *means* (each relationship has exactly one type)
- **Direction** — relationships always have a start node and end node
- **Properties** — key-value pairs storing data about the connection

```
(:Drug)-[:TREATS {efficacy: 0.85, evidence: "Phase 3"}]->(:Disease)
(:Drug)-[:TARGETS {binding_affinity: "high"}]->(:Protein)
(:Gene)-[:ASSOCIATED_WITH {confidence: 0.92}]->(:Disease)
```

### Important Distinction

| Concept | Belongs To | What It Does | Example |
|---|---|---|---|
| **Label** | Node | Categorizes the node | `:Drug`, `:Disease`, `:Protein` |
| **Type** | Relationship | Names the connection | `:TREATS`, `:TARGETS`, `:ENCODED_BY` |
| **Property** | Both | Stores key-value data | `name: "Pembrolizumab"`, `efficacy: 0.85` |

Labels are NOT the same as Types. Labels go on nodes. Types go on relationships.

### Query Language: Cypher

```cypher
// Find drugs that treat Lung Cancer
MATCH (d:Drug)-[:TREATS]->(dis:Disease {name: "Lung Cancer"})
RETURN d.name, d.mechanism

// Find drugs that share a disease (co-indication)
MATCH (d1:Drug)-[:TREATS]->(dis:Disease)<-[:TREATS]-(d2:Drug)
WHERE d1 <> d2
RETURN d1.name, d2.name, dis.name
```

---

## What is RDF (Resource Description Framework)?

RDF is the data model used by **Neptune DB (SPARQL mode)** and all W3C-compliant triple stores.

Everything in RDF is a **triple**: three parts, always the same structure.

### The Triple

```
Subject  →  Predicate  →  Object
```

That's it. Every fact is one triple. No properties on edges. No labels. Just triples.

```turtle
:Pembrolizumab  rdf:type      :Drug .
:Pembrolizumab  :drugName     "Pembrolizumab" .
:Pembrolizumab  :mechanism    "PD-1 inhibitor" .
:Pembrolizumab  :approvalYear "2014"^^xsd:gYear .
:Pembrolizumab  :treats       :LungCancer .

:LungCancer     rdf:type      :Disease .
:LungCancer     :diseaseName  "Lung Cancer" .
:LungCancer     :icd10Code    "C34.9" .
```

### How RDF Differs From LPG

In LPG, a node is an object with labels and properties attached to it.

In RDF, there are no "nodes with properties." Every fact — including what would be a property in LPG — is a separate triple.

**LPG (one node with 3 properties):**
```
(:Drug {name: "Pembrolizumab", mechanism: "PD-1 inhibitor", year: 2014})
```

**RDF (4 separate triples to say the same thing):**
```turtle
:Pembrolizumab  rdf:type      :Drug .
:Pembrolizumab  :drugName     "Pembrolizumab" .
:Pembrolizumab  :mechanism    "PD-1 inhibitor" .
:Pembrolizumab  :approvalYear "2014"^^xsd:gYear .
```

### The W3C Stack on Top of RDF

RDF alone is just triples. The power comes from the layers built on top:

```
SHACL   →  Validation (enforce constraints on the graph)
OWL     →  Reasoning (infer new facts automatically)
SPARQL  →  Query (pattern matching, traversal, federation)
RDFS    →  Schema (define classes, properties, hierarchies)
RDF     →  Model (subject-predicate-object triples)
```

### Query Language: SPARQL

```sparql
# Find drugs that treat Lung Cancer
SELECT ?drug ?mechanism
WHERE {
    ?drug rdf:type :Drug .
    ?drug :drugName ?name .
    ?drug :mechanism ?mechanism .
    ?drug :treats :LungCancer .
}

# Find drugs that share a disease
SELECT ?drug1 ?drug2 ?disease
WHERE {
    ?drug1 :treats ?disease .
    ?drug2 :treats ?disease .
    FILTER(?drug1 != ?drug2)
}
```

---

## Side-by-Side Comparison

### Same Data, Different Models

**Scenario:** Pembrolizumab treats Lung Cancer with 85% efficacy, based on Phase 3 evidence.

**LPG (Neo4j — 2 nodes, 1 relationship):**
```cypher
CREATE (d:Drug {name: "Pembrolizumab", mechanism: "PD-1 inhibitor"})
CREATE (dis:Disease {name: "Lung Cancer", icd10: "C34.9"})
CREATE (d)-[:TREATS {efficacy: 0.85, evidence: "Phase 3"}]->(dis)
```

Properties on the TREATS relationship store efficacy and evidence directly on the edge. Clean and intuitive.

**RDF (Neptune SPARQL — 9 triples):**
```turtle
:Pembrolizumab  rdf:type     :Drug .
:Pembrolizumab  :drugName    "Pembrolizumab" .
:Pembrolizumab  :mechanism   "PD-1 inhibitor" .
:Pembrolizumab  :treats      :LungCancer .

:LungCancer     rdf:type     :Disease .
:LungCancer     :diseaseName "Lung Cancer" .
:LungCancer     :icd10Code   "C34.9" .

# But where does efficacy: 0.85 go?
# RDF has NO edge properties. You need "reification":
:Treatment001   rdf:type       :TreatmentRecord .
:Treatment001   :hasDrug       :Pembrolizumab .
:Treatment001   :hasDisease    :LungCancer .
:Treatment001   :efficacy      "0.85"^^xsd:decimal .
:Treatment001   :evidence      "Phase 3" .
```

That's 12 triples vs 3 elements in LPG. The reification pattern (creating a new node to represent the relationship) is the standard workaround for RDF's lack of edge properties.

---

## Feature Comparison

| Feature | LPG (Neo4j) | RDF (Neptune SPARQL) |
|---|---|---|
| **Data unit** | Nodes + Relationships | Subject-Predicate-Object triples |
| **Node categorization** | Labels (`:Drug`, `:Disease`) | `rdf:type` triple |
| **Edge categorization** | Relationship Type (`:TREATS`) | Predicate URI (`:treats`) |
| **Properties on nodes** | Native key-value pairs | Separate triple per property |
| **Properties on edges** | Native key-value pairs | Not supported (requires reification) |
| **Schema** | Optional (schema-free) | RDFS/OWL ontology |
| **Validation** | Cypher constraints | SHACL shapes |
| **Inference/Reasoning** | Not built-in | OWL reasoner derives new facts |
| **Query language** | Cypher (Neo4j) / openCypher / Gremlin | SPARQL 1.1 |
| **Vector search** | Native HNSW index on node properties | No native support |
| **Standards body** | Neo4j Inc → now ISO GQL standard | W3C open standard |
| **Interoperability** | Limited (vendor-specific formats) | High (global URIs, linked data, federation) |
| **Federation** | Not native | SPARQL SERVICE clause queries remote endpoints |

---

## When to Use Which

### Choose LPG (Neo4j / Neptune openCypher) When:

- You need **fast application queries** — real-time recommendation, fraud detection, social graphs
- You need **properties on relationships** — weighted edges, timestamps, confidence scores
- You need **native vector search** — GraphRAG, semantic similarity, embedding-based retrieval
- Your team knows **Cypher/SQL** — Cypher is closer to SQL than SPARQL is
- You prioritize **developer experience** — simpler mental model, less boilerplate
- You don't need to share data across organizations using global identifiers

### Choose RDF (Neptune SPARQL) When:

- You need **standards compliance** — government, healthcare, publishing domains that mandate W3C
- You need **reasoning/inference** — OWL can derive "if Drug targets ImmuneCheckpointProtein, then Drug is an Immunotherapy" automatically
- You need **data federation** — SPARQL can query across multiple remote endpoints in one query
- You need **interoperability** — share knowledge graphs across organizations using global URIs
- You need **formal validation** — SHACL shapes enforce structural constraints declaratively
- You're building a **knowledge graph for AI grounding** — RDF's triple model maps naturally to factual assertions

### Choose Both When:

- **Neptune Database** supports both Gremlin/openCypher (LPG) and SPARQL (RDF) on the same engine
- You can load RDF data and query it with SPARQL for reasoning, while also querying the same data with openCypher for application logic
- Our project does exactly this — W3C RDF path (`main.py`) alongside LPG path (`real_neptune_vs_neo4j_benchmark.py`)

---

## How Neptune Supports Both

```
                    Neptune Database
                   /               \
                  /                 \
         SPARQL Endpoint      Gremlin/openCypher
         (RDF triples)        (Property Graph)
              |                      |
           W3C Stack              LPG Model
        RDF/RDFS/OWL/SHACL     Nodes + Relationships
              |                      |
         Reasoning &            Fast traversal &
         Interoperability       Native vectors (Analytics)
```

| Neptune Mode | Data Model | Query Language | Vector Support |
|---|---|---|---|
| **Neptune DB — SPARQL** | RDF triples | SPARQL 1.1 | No |
| **Neptune DB — Gremlin** | LPG | Apache TinkerPop Gremlin | No |
| **Neptune DB — openCypher** | LPG | openCypher | No |
| **Neptune Analytics** | LPG | openCypher | Yes (native) |

Neptune Analytics only supports LPG with openCypher — no RDF/SPARQL. If you need RDF + vectors, you must use Neptune DB (SPARQL) + OpenSearch (kNN) as a two-layer architecture.

---

## In Our Project

We implemented both models on the same biomedical data:

| Path | Data Model | Engine | Script |
|---|---|---|---|
| **W3C Standard** | RDF triples + OWL ontology + SHACL | rdflib/pyshacl (local) | `main.py` |
| **Production Benchmark** | LPG (nodes + relationships) | Neo4j Aura + Neptune Analytics + Neptune DB | `real_neptune_vs_neo4j_benchmark.py` |

Same 10 drugs, same 7 diseases, same 14 TREATS relationships — modeled two different ways to demonstrate the trade-offs.

The benchmark results showed that LPG with native vectors (Neo4j and Neptune Analytics) delivers 34–208ms unified queries. The RDF path gives you standards compliance and reasoning but no native vector search — you need a separate OpenSearch layer (69ms with friction).

---

## Quick Reference

```
LPG:    (Node:Label {property: value})-[:TYPE {property: value}]->(Node:Label)
RDF:    Subject  →  Predicate  →  Object  (everything is a triple)

LPG:    Labels on nodes, Types on relationships, Properties on both
RDF:    No labels, no types, no edge properties — just triples

LPG:    Cypher / openCypher / Gremlin
RDF:    SPARQL

LPG:    Schema-optional, developer-friendly, native vectors
RDF:    W3C standard, reasoning, federation, interoperability
```
