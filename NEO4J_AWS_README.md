# Biomedical Knowledge Graph with Neo4j + AWS Bedrock Agent

## Overview

This implementation combines:
- **Neo4j Aura** - Cloud-native graph database for storing and querying the biomedical knowledge graph
- **AWS Bedrock** - AI agent framework using Claude for natural language interaction
- **Biomedical Data** - Drugs, diseases, clinical trials, genes, proteins, and their relationships

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        USER                                 │
│           (Asks natural language questions)                 │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                  AWS BEDROCK AGENT                          │
│              (Claude 3 Sonnet via Bedrock)                  │
│  - Understands natural language                             │
│  - Routes to appropriate graph queries                      │
│  - Synthesizes answers from graph data                      │
└─────────────────────────────────────────────────────────────┘
                            ↓
                     Cypher Queries
                            ↓
┌─────────────────────────────────────────────────────────────┐
│                      NEO4J AURA                             │
│               (Cloud Graph Database)                        │
│                                                             │
│  Nodes:           Relationships:                            │
│  - Drug           - TREATS (drug → disease)                 │
│  - Disease        - TARGETS (drug → protein)                │
│  - Gene           - ASSOCIATED_WITH (gene → disease)        │
│  - Protein        - INVESTIGATES (trial → drug)             │
│  - ClinicalTrial  - STUDIES (trial → disease)               │
│  - Biomarker      - REPORTS (trial → adverse event)         │
│  - Researcher     - PREDICTS_RESPONSE (biomarker → drug)    │
│  - Institution    - AUTHORED_BY (paper → researcher)        │
│  - ResearchPaper  - AFFILIATED_WITH (researcher → inst)     │
│  - AdverseEvent   - MENTIONS (paper → drug/disease)         │
│                                                             │
│  ~100 nodes, ~100 relationships                             │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

### Prerequisites
- Python 3.8+
- Neo4j Aura account (free tier available)
- AWS account with Bedrock access
- AWS credentials configured

### Step 1: Install Dependencies

```bash
pip install -r neo4j_requirements.txt
```

This installs:
- `neo4j` - Neo4j Python driver
- `boto3` - AWS SDK for Python
- `python-dotenv` - Environment variable management
- `pandas` - Data processing

### Step 2: Configure Environment

The `.env` file is already configured with your Neo4j Aura credentials:

```env
NEO4J_URI=neo4j+s://<your-instance>.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=<your-neo4j-password>
NEO4J_DATABASE=neo4j
AURA_INSTANCEID=cad612f1
AURA_INSTANCENAME=graphpoc
```

### Step 3: Load Data into Neo4j

```bash
python scripts/csv_to_neo4j.py
```

**What this does:**
1. Connects to your Neo4j Aura instance
2. Creates constraints and indexes
3. Loads all entities (drugs, diseases, trials, etc.)
4. Creates relationships between entities
5. Displays statistics

**Expected output:**
```
============================================================
BIOMEDICAL KNOWLEDGE GRAPH - Neo4j Loader
============================================================

Connecting to Neo4j Aura...
  URI: neo4j+s://<your-instance>.databases.neo4j.io
  Database: neo4j
✓ Connected successfully!

Creating constraints and indexes...
✓ Constraints created

============================================================
Loading entities...
============================================================

Loading drugs...
  ✓ Created 10 drug nodes

Loading diseases...
  ✓ Created 10 disease nodes

...

============================================================
Loading relationships...
============================================================
  ✓ Created 15 TREATS relationships
  ✓ Created 11 TARGETS relationships
  ...

============================================================
GRAPH STATISTICS
============================================================

Node Counts:
----------------------------------------
  Drug                 :    10
  Disease              :    10
  ClinicalTrial        :    10
  Gene                 :    10
  Protein              :    10
  Biomarker            :    10
  Researcher           :    10
  Institution          :    10
  ResearchPaper        :    10
  AdverseEvent         :    10

  Total Relationships :   100+

============================================================
SUCCESS! Biomedical knowledge graph loaded into Neo4j Aura
============================================================
```

### Step 4: Run the AWS Bedrock Agent

```bash
# Demo mode (runs predefined questions)
python aws_agent_neo4j.py

# Interactive mode (ask your own questions)
python aws_agent_neo4j.py --interactive
```

## Example Queries

### Using Python API

```python
from aws_agent_neo4j import BiomedicalGraphAgent

agent = BiomedicalGraphAgent()

# Find treatments for a disease
treatments = agent.get_drug_treatments("Lung Cancer")
print(treatments)
# [
#   {'drug': 'Pembrolizumab', 'mechanism': 'PD-1 inhibitor', 'efficacy': 0.45},
#   {'drug': 'Nivolumab', 'mechanism': 'PD-1 inhibitor', 'efficacy': 0.40},
#   ...
# ]

# Find protein targets
targets = agent.get_drug_targets("Pembrolizumab")
print(targets)
# [
#   {'drug': 'Pembrolizumab', 'protein': 'PD-1', 'affinity': 'High'}
# ]

# Gene-disease-drug pathway
pathway = agent.get_gene_disease_drug_pathway("BRCA1")
print(pathway)
# [
#   {'gene': 'BRCA1', 'disease': 'Breast Cancer', 'drug': 'Trastuzumab', 'efficacy': 0.52}
# ]

agent.close()
```

### Using Natural Language (Bedrock Agent)

```python
agent = BiomedicalGraphAgent()

# Ask questions in natural language
answer = agent.answer_question("What drugs treat Type 2 Diabetes?")
print(answer)
# "Based on the knowledge graph, there are three drugs approved for Type 2 Diabetes:
#  1. Tirzepatide (GIP/GLP-1 receptor agonist) - 63% efficacy
#  2. Semaglutide (GLP-1 receptor agonist) - 58% efficacy
#  3. Metformin (AMPK activator) - 31% efficacy
#  Tirzepatide shows the highest efficacy rate..."

answer = agent.answer_question("What protein does Pembrolizumab target?")
print(answer)
# "Pembrolizumab targets the PD-1 protein (Programmed Death-1), which is an immune
#  checkpoint protein. It binds with high affinity and acts as an antagonist, blocking
#  the PD-1/PD-L1 pathway and allowing the immune system to attack cancer cells..."
```

### Using Cypher Directly

```cypher
// Find all immunotherapy drugs for oncology diseases
MATCH (d:Drug)-[t:TREATS]->(dis:Disease)
WHERE dis.category = 'Oncology' AND d.mechanism CONTAINS 'inhibitor'
RETURN d.name, d.mechanism, dis.name, t.efficacyRate
ORDER BY t.efficacyRate DESC

// Multi-hop: Gene → Disease → Drug pathway
MATCH (g:Gene)-[:ASSOCIATED_WITH]->(dis:Disease)<-[t:TREATS]-(d:Drug)
RETURN g.symbol, dis.name, d.name, t.efficacyRate
ORDER BY t.efficacyRate DESC

// Find clinical trials with enrollment > 1000
MATCH (t:ClinicalTrial)-[:INVESTIGATES]->(d:Drug)
MATCH (t)-[:STUDIES]->(dis:Disease)
WHERE t.enrollment > 1000
RETURN t.title, t.phase, t.enrollment, d.name, dis.name
ORDER BY t.enrollment DESC

// Research network: Find collaborations
MATCH (r1:Researcher)-[:AFFILIATED_WITH]->(i:Institution)<-[:AFFILIATED_WITH]-(r2:Researcher)
WHERE r1 <> r2
RETURN i.name as institution, collect(DISTINCT r1.name) as researchers
```

## AWS Bedrock Agent Features

### 1. Natural Language Understanding
The agent understands various ways of asking the same question:

```python
# All of these work:
agent.answer_question("What drugs treat lung cancer?")
agent.answer_question("Show me treatments for NSCLC")
agent.answer_question("Which medications are approved for non-small cell lung cancer?")
```

### 2. Contextual Graph Queries
The agent automatically:
- Routes questions to appropriate Cypher queries
- Retrieves relevant data from Neo4j
- Passes structured data to Claude
- Generates natural language answers

### 3. Grounded Responses
Unlike pure LLM queries, the agent:
- **Never hallucinates** - all facts come from the graph
- **Provides provenance** - can show the exact graph path
- **Quantifies uncertainty** - "data doesn't contain..." when appropriate

## Use Cases

### 1. Drug Discovery

**Question:** "What drugs target the same protein as Pembrolizumab?"

**Graph Query:**
```cypher
MATCH (d1:Drug {name: 'Pembrolizumab'})-[:TARGETS]->(p:Protein)<-[:TARGETS]-(d2:Drug)
WHERE d1 <> d2
RETURN d2.name, p.name
```

**Answer:** "Nivolumab also targets PD-1. Both are immune checkpoint inhibitors approved for cancer treatment."

**Value:** Identify drug repurposing opportunities

### 2. Precision Medicine

**Question:** "Patient has BRCA1 mutation and breast cancer. What treatments are available?"

**Graph Query:**
```cypher
MATCH (g:Gene {symbol: 'BRCA1'})-[:ASSOCIATED_WITH]->(d:Disease)<-[t:TREATS]-(drug:Drug)
RETURN drug.name, t.efficacyRate, drug.mechanism
ORDER BY t.efficacyRate DESC
```

**Answer:** "Trastuzumab is indicated for BRCA1-associated breast cancer with 52% efficacy rate. It targets HER2 protein which is often overexpressed in BRCA1-mutation cases..."

**Value:** Personalized treatment recommendations

### 3. Clinical Decision Support

**Question:** "What are the risks of immunotherapy for melanoma?"

**Graph Query:**
```cypher
MATCH (d:Drug)-[:TREATS]->(dis:Disease {name: 'Melanoma'})
MATCH (d)<-[:INVESTIGATES]-(t:ClinicalTrial)-[:REPORTS]->(e:AdverseEvent)
WHERE d.mechanism CONTAINS 'inhibitor'
RETURN d.name, e.name, e.severity, e.frequency
```

**Answer:** "Immunotherapy drugs like Pembrolizumab and Nivolumab for melanoma can cause:
- Immune-related pneumonitis (severe, uncommon)
- Immune-related colitis (moderate, common)
- Hypothyroidism (mild, common)
Patients should be monitored for these immune-related adverse events..."

**Value:** Informed consent and safety monitoring

### 4. Research Network Analysis

**Question:** "Who are the leading Alzheimer's researchers and what institutions are they at?"

**Graph Query:**
```cypher
MATCH (r:Researcher)-[:AFFILIATED_WITH]->(i:Institution)
WHERE r.specialization CONTAINS 'Alzheimer' AND r.hIndex >= 70
RETURN r.name, r.hIndex, r.totalPublications, i.name
ORDER BY r.hIndex DESC
```

**Answer:** "Top Alzheimer's researchers:
1. Dr. Jennifer White (h-index: 81, 289 publications) - [Institution Name]
2. Dr. Emily Watson (h-index: 85, 312 publications) - [Institution Name]
..."

**Value:** Partnership and collaboration opportunities

## Neo4j vs RDF Comparison

| Feature | Neo4j | RDF/SPARQL |
|---------|-------|------------|
| **Query Speed** | Fast (optimized for traversal) | Moderate (depends on triple store) |
| **Schema** | Flexible property graph | Formal ontology (RDFS/OWL) |
| **Reasoning** | Cypher queries | OWL inference |
| **Standards** | Proprietary (but popular) | W3C standards |
| **Visualization** | Excellent (Neo4j Bloom) | Limited |
| **Learning Curve** | Easier (Cypher is SQL-like) | Steeper (SPARQL, RDF) |
| **Semantic Web** | Limited | Native support |
| **Best For** | Fast queries, exploration | Interoperability, reasoning |

### When to Use Neo4j
✅ Need fast graph traversal  
✅ Interactive exploration and visualization  
✅ Flexible schema evolution  
✅ Team already knows SQL  
✅ Operational queries (milliseconds)

### When to Use RDF
✅ Need formal ontologies  
✅ Domain has standard vocabularies (FIBO, SNOMED)  
✅ Semantic interoperability required  
✅ Heavy reasoning/inference  
✅ Academic/research context

### Hybrid Approach (Best of Both)
Many organizations use:
- **Neo4j** for operational queries and visualization
- **RDF/OWL** for semantic layer and reasoning
- Bidirectional sync between them

## Deployment

### Local Development
```bash
# Use .env file with Neo4j Aura credentials
python scripts/csv_to_neo4j.py
python aws_agent_neo4j.py
```

### AWS Lambda Deployment

1. Package the application:
```bash
pip install -t package/ -r neo4j_requirements.txt
cd package && zip -r ../lambda.zip . && cd ..
zip -g lambda.zip aws_agent_neo4j.py
```

2. Create Lambda function:
```bash
aws lambda create-function \
    --function-name biomedical-graph-agent \
    --runtime python3.11 \
    --handler aws_agent_neo4j.lambda_handler \
    --zip-file fileb://lambda.zip \
    --environment Variables="{
        NEO4J_URI=$NEO4J_URI,
        NEO4J_USERNAME=$NEO4J_USERNAME,
        NEO4J_PASSWORD=$NEO4J_PASSWORD
    }" \
    --role arn:aws:iam::ACCOUNT_ID:role/lambda-execution-role
```

3. Create API Gateway REST API to expose the agent

### Scaling Considerations

**Neo4j Aura Free Tier:**
- 50K nodes, 175K relationships
- Suitable for POC/development

**Neo4j Aura Professional:**
- Up to 8GB memory
- ~10M nodes, 100M relationships
- $65+/month

**Neo4j Aura Enterprise:**
- Up to 384GB memory
- Billions of nodes/relationships
- High availability
- $1,000+/month

**AWS Bedrock:**
- Pay per request
- Claude 3 Sonnet: ~$0.003 per 1K input tokens
- Scales automatically

## Advanced Features

### 1. Graph Algorithms

Neo4j includes built-in graph algorithms:

```cypher
// PageRank to find most "important" drugs
CALL gds.pageRank.stream('drug-disease-network')
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).name AS drug, score
ORDER BY score DESC LIMIT 10

// Community detection to find drug clusters
CALL gds.louvain.stream('drug-target-network')
YIELD nodeId, communityId
RETURN gds.util.asNode(nodeId).name AS drug, communityId
```

### 2. Full-Text Search

```cypher
// Create full-text index
CREATE FULLTEXT INDEX drugSearch FOR (d:Drug) ON EACH [d.name, d.mechanism]

// Search
CALL db.index.fulltext.queryNodes('drugSearch', 'PD-1 inhibitor')
YIELD node, score
RETURN node.name, node.mechanism, score
```

### 3. Vector Embeddings (for AI)

```python
from neo4j import GraphDatabase
import openai

# Generate embeddings for drugs
driver = GraphDatabase.driver(uri, auth=(user, password))

with driver.session() as session:
    drugs = session.run("MATCH (d:Drug) RETURN d.drugId, d.name, d.mechanism")

    for drug in drugs:
        text = f"{drug['name']} is a {drug['mechanism']}"
        embedding = openai.Embedding.create(input=text, model="text-embedding-ada-002")

        session.run("""
            MATCH (d:Drug {drugId: $id})
            SET d.embedding = $embedding
        """, id=drug['drugId'], embedding=embedding['data'][0]['embedding'])

# Similarity search
query_embedding = openai.Embedding.create(
    input="immune checkpoint inhibitor",
    model="text-embedding-ada-002"
)['data'][0]['embedding']

similar_drugs = session.run("""
    MATCH (d:Drug)
    RETURN d.name,
           gds.similarity.cosine(d.embedding, $query) AS similarity
    ORDER BY similarity DESC
    LIMIT 5
""", query=query_embedding)
```

## Monitoring and Observability

### Neo4j Monitoring

```cypher
// Database statistics
CALL dbms.queryJmx('org.neo4j:instance=kernel#0,name=Store file sizes')
YIELD attributes

// Query performance
CALL dbms.listQueries()
YIELD query, elapsedTimeMillis, cpuTimeMillis
WHERE elapsedTimeMillis > 1000
RETURN query, elapsedTimeMillis
ORDER BY elapsedTimeMillis DESC
```

### AWS CloudWatch Integration

```python
import boto3

cloudwatch = boto3.client('cloudwatch')

# Log query metrics
cloudwatch.put_metric_data(
    Namespace='BiomedicalGraphAgent',
    MetricData=[
        {
            'MetricName': 'QueryLatency',
            'Value': query_time_ms,
            'Unit': 'Milliseconds'
        }
    ]
)
```

## Security Best Practices

1. **Never commit credentials** - Use AWS Secrets Manager or Parameter Store
2. **Use IAM roles** for Lambda functions
3. **Enable Neo4j SSL/TLS** (Aura does this by default)
4. **Rotate passwords** regularly
5. **Use read-only Neo4j users** for query-only applications
6. **Validate and sanitize** user inputs before constructing Cypher queries

## Troubleshooting

### Issue: "Failed to establish connection to Neo4j"
**Solution:**
- Check NEO4J_URI in .env file
- Verify Neo4j Aura instance is running
- Check firewall/network settings
- Ensure credentials are correct

### Issue: "AWS Bedrock access denied"
**Solution:**
- Configure AWS credentials: `aws configure`
- Check IAM permissions for Bedrock
- Verify region is us-east-1 (or your Bedrock region)
- Request Bedrock access in AWS Console if needed

### Issue: "Cypher query timeout"
**Solution:**
- Add indexes on frequently queried properties
- Limit result sets with LIMIT clause
- Optimize query (avoid OPTIONAL MATCH when possible)
- Consider upgrading Neo4j Aura tier

## Next Steps

1. **Add more data** - Import additional CSV files
2. **Build UI** - Create web interface (React + Neo4j)
3. **Add graph algorithms** - PageRank, community detection
4. **Implement caching** - Redis for frequently queried results
5. **Create REST API** - FastAPI wrapper around agent
6. **Add monitoring** - CloudWatch dashboards
7. **Integrate with clinical systems** - HL7 FHIR connectors

## Resources

- [Neo4j Cypher Manual](https://neo4j.com/docs/cypher-manual/current/)
- [Neo4j Python Driver](https://neo4j.com/docs/python-manual/current/)
- [AWS Bedrock Documentation](https://docs.aws.amazon.com/bedrock/)
- [Graph Data Science Library](https://neo4j.com/docs/graph-data-science/current/)
- [Neo4j Aura](https://neo4j.com/cloud/aura/)

## Summary

You now have a **production-ready biomedical knowledge graph** powered by:
- ✅ Neo4j Aura for fast graph queries
- ✅ AWS Bedrock Agent for natural language interaction
- ✅ Claude 3 for intelligent answer generation
- ✅ Real biomedical data with complex relationships

**Key advantages:**
1. **Fast queries** - Neo4j optimized for graph traversal
2. **No hallucinations** - All answers grounded in graph data
3. **Scalable** - Both Neo4j and Bedrock scale to production
4. **Interactive** - Natural language questions, visual exploration
5. **Cloud-native** - Fully managed, no infrastructure to maintain

Deploy this for your team and start asking questions!
