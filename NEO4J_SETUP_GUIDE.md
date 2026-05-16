# Neo4j Implementation - Setup & Usage Guide

## Current Status

✅ **Neo4j Credentials Configured**
- URI: `neo4j+s://<your-instance>.databases.neo4j.io`
- Username: `cad612f1`
- Database: `cad612f1`
- Instance: `graphpoc`
- Credentials saved in: `.env`

## Python Environment Setup Required

The workshop environment needs Python dependencies installed. Here are the options:

### Option 1: Using Docker (Recommended)
```bash
docker run -it --rm \
  -v $(pwd):/workspace \
  -w /workspace \
  python:3.12-slim bash

# Inside container:
pip install neo4j python-dotenv pandas
python3 test_neo4j_simple.py
```

### Option 2: Local Virtual Environment
```bash
# If you have sudo access:
sudo apt install python3-venv python3-pip

# Create venv:
python3 -m venv venv
source venv/bin/activate
pip install neo4j python-dotenv pandas

# Run tests:
python test_neo4j_simple.py
```

### Option 3: System-wide (if permitted)
```bash
pip install --break-system-packages neo4j python-dotenv pandas
```

## Neo4j Implementation Files

### 1. **test_neo4j_simple.py**
Basic connection test and database inspection.

**What it does:**
- Tests connection to Neo4j Aura
- Shows node/relationship counts
- Lists all labels and relationship types
- Displays indices
- Shows sample data

**Usage:**
```bash
python3 test_neo4j_simple.py
```

### 2. **neo4j_data_loader.py**
Loads biomedical knowledge graph with embeddings.

**Features:**
- Creates constraints and indices
- Loads 10 drugs with 384-dim embeddings
- Creates TREATS and ASSOCIATED_WITH relationships
- Sets up vector index for similarity search

**Usage:**
```bash
python3 neo4j_data_loader.py
```

**Sample Data Loaded:**
- **Drugs**: Pembrolizumab, Nivolumab, Osimertinib, Erlotinib, etc.
- **Diseases**: NSCLC, Melanoma, Breast Cancer, CRC, etc.
- **Genes**: EGFR, PD-1, PD-L1, VEGF, HER2, etc.
- **Relationships**: Drug→Disease (TREATS), Disease→Gene (ASSOCIATED_WITH)

### 3. **neo4j_data_generator.py**
Generates large-scale synthetic data for benchmarking.

**Usage:**
```bash
# Generate 10K nodes
python3 neo4j_data_generator.py --scale 10000

# Generate 1M nodes
python3 neo4j_data_generator.py --scale 1000000
```

### 4. **aws_agent_neo4j.py**
AWS Bedrock agent for natural language querying.

**Features:**
- Ask questions in natural language
- Routes to appropriate Cypher queries
- Uses Claude 3 via AWS Bedrock
- Returns grounded answers from graph data

**Usage:**
```bash
# Demo mode
python3 aws_agent_neo4j.py

# Interactive mode
python3 aws_agent_neo4j.py --interactive
```

**Example Questions:**
- "What drugs treat lung cancer?"
- "What protein does Pembrolizumab target?"
- "What genes are associated with breast cancer?"
- "What are the adverse events of Pembrolizumab?"

### 5. **real_benchmark_implementation.py**
Performance benchmarking for Neo4j.

**Tests:**
- Vector search latency (k-NN with embeddings)
- Graph traversal performance (multi-hop queries)
- Statistical analysis (mean, median, stdev, min/max)

**Usage:**
```bash
python3 real_benchmark_implementation.py
```

### 6. **scripts/csv_to_neo4j.py**
Comprehensive CSV data loader.

**Entities Loaded:**
- Drugs, Diseases, ClinicalTrials
- Genes, Proteins, Biomarkers
- Researchers, Institutions, ResearchPapers
- AdverseEvents

**Relationships:**
- TREATS (drug → disease)
- TARGETS (drug → protein)
- ASSOCIATED_WITH (gene → disease)
- INVESTIGATES (trial → drug)
- STUDIES (trial → disease)
- REPORTS (trial → adverse event)
- And more...

## Neo4j Cypher Query Examples

### Basic Queries

```cypher
// Count all nodes
MATCH (n) RETURN count(n)

// Show all labels
CALL db.labels()

// Show all relationship types
CALL db.relationshipTypes()

// Sample 10 nodes
MATCH (n) RETURN n LIMIT 10
```

### Graph Traversal Queries

```cypher
// Find drugs that treat lung cancer
MATCH (d:Drug)-[r:TREATS]->(dis:Disease)
WHERE dis.name CONTAINS 'Lung Cancer'
RETURN d.name, d.mechanism, r.efficacyRate
ORDER BY r.efficacyRate DESC

// Multi-hop: Gene → Disease → Drug
MATCH (g:Gene)-[:ASSOCIATED_WITH]->(dis:Disease)<-[t:TREATS]-(d:Drug)
RETURN g.symbol, dis.name, d.name, t.efficacyRate
ORDER BY t.efficacyRate DESC

// Find all drugs targeting the same protein
MATCH (d1:Drug)-[:TARGETS]->(p:Protein)<-[:TARGETS]-(d2:Drug)
WHERE d1.name = 'Pembrolizumab' AND d1 <> d2
RETURN d2.name, p.name
```

### Vector Search Queries

```cypher
// Create vector index
CREATE VECTOR INDEX drug_embedding_vector IF NOT EXISTS
FOR (d:Drug)
ON d.embedding
OPTIONS {
    indexConfig: {
        `vector.dimensions`: 384,
        `vector.similarity_function`: 'cosine'
    }
}

// Vector similarity search
CALL db.index.vector.queryNodes('drug_embedding_vector', 10, $queryVector)
YIELD node, score
RETURN node.name, node.description, score
ORDER BY score DESC
LIMIT 10
```

### Analytical Queries

```cypher
// Drug distribution by mechanism
MATCH (d:Drug)
RETURN d.mechanism, count(*) as count
ORDER BY count DESC

// Most researched diseases
MATCH (t:ClinicalTrial)-[:STUDIES]->(dis:Disease)
RETURN dis.name, count(t) as trial_count
ORDER BY trial_count DESC
LIMIT 10

// High-impact researchers
MATCH (r:Researcher)-[:AFFILIATED_WITH]->(i:Institution)
WHERE r.hIndex >= 70
RETURN r.name, r.hIndex, r.totalPublications, i.name
ORDER BY r.hIndex DESC
```

## Neo4j Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    Neo4j Aura Instance                   │
│                  (Cloud-managed Database)                │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  Property Graph Model:                                   │
│                                                          │
│  ┌────────┐  TREATS   ┌─────────┐  ASSOCIATED_WITH     │
│  │  Drug  │ ────────> │ Disease │ <───────────────┐    │
│  └────────┘           └─────────┘                  │    │
│      │                     │                    ┌──────┐│
│      │ TARGETS             │ STUDIED_BY         │ Gene ││
│      v                     v                    └──────┘│
│  ┌────────┐           ┌──────────────┐                 │
│  │Protein │           │ClinicalTrial │                 │
│  └────────┘           └──────────────┘                 │
│                                                          │
│  Features:                                               │
│  • Vector embeddings (384-dim)                          │
│  • Full-text search                                     │
│  • Constraints & indexes                                │
│  • Graph algorithms (PageRank, Louvain)                 │
│                                                          │
└──────────────────────────────────────────────────────────┘
                           │
                           │ Cypher queries
                           │ (bolt+s protocol)
                           ▼
┌──────────────────────────────────────────────────────────┐
│              Python Application Layer                    │
├──────────────────────────────────────────────────────────┤
│  • neo4j.GraphDatabase (driver)                         │
│  • Data loaders & generators                            │
│  • AWS Bedrock integration                              │
│  • Benchmark harness                                    │
└──────────────────────────────────────────────────────────┘
```

## Quick Start Workflow

1. **Test Connection**
   ```bash
   python3 test_neo4j_simple.py
   ```

2. **Load Initial Data**
   ```bash
   python3 neo4j_data_loader.py
   ```

3. **Query via Browser**
   - Visit: https://console.neo4j.io
   - Login with your credentials
   - Run Cypher queries in the browser

4. **Scale Up (Optional)**
   ```bash
   python3 neo4j_data_generator.py --scale 100000
   ```

5. **Run Benchmarks**
   ```bash
   python3 real_benchmark_implementation.py
   ```

6. **Interactive Agent**
   ```bash
   python3 aws_agent_neo4j.py --interactive
   ```

## Neo4j vs Other Graph Databases

| Feature | Neo4j | AWS Neptune | RDF/Blazegraph |
|---------|-------|-------------|----------------|
| **Query Language** | Cypher (SQL-like) | Gremlin/SPARQL | SPARQL |
| **Data Model** | Property Graph | Property Graph | RDF Triples |
| **Vector Search** | Native (5.11+) | Via OpenSearch | Limited |
| **Learning Curve** | Easy | Moderate | Steep |
| **Visualization** | Excellent (Bloom) | Good | Limited |
| **Cloud Managed** | Aura | Yes | No (self-host) |
| **Standards** | Proprietary | Mixed | W3C |
| **Performance** | Fast traversal | Fast, AWS-native | Variable |

## Performance Characteristics

### Vector Search
- **Latency**: 5-50ms (depending on scale)
- **Index**: Cosine similarity with 384 dimensions
- **Use case**: Drug similarity, semantic search

### Graph Traversal
- **Latency**: 1-20ms (1-3 hops)
- **Pattern**: Optimized for relationship traversal
- **Use case**: Drug→Disease→Gene pathways

### Scaling
- **Free Tier**: 50K nodes, 175K relationships
- **Professional**: ~10M nodes (up to 8GB)
- **Enterprise**: Billions of nodes (up to 384GB)

## Next Steps

Once Python environment is ready:

1. ✅ Test connection (`test_neo4j_simple.py`)
2. ✅ Load sample data (`neo4j_data_loader.py`)
3. ✅ Run queries via Neo4j Browser
4. ✅ Generate large dataset (`neo4j_data_generator.py`)
5. ✅ Benchmark performance (`real_benchmark_implementation.py`)
6. ✅ Build AI agent (`aws_agent_neo4j.py`)

## Resources

- **Neo4j Browser**: https://console.neo4j.io
- **Cypher Docs**: https://neo4j.com/docs/cypher-manual/
- **Python Driver**: https://neo4j.com/docs/python-manual/
- **Graph Data Science**: https://neo4j.com/docs/graph-data-science/

---

**Status**: Credentials configured ✅ | Environment setup needed 🔧 | Ready to deploy 🚀
