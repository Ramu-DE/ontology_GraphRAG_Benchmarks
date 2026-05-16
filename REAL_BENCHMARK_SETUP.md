# 🚀 Real GraphRAG Benchmark Setup Guide

This guide shows how to run **ACTUAL performance benchmarks** on real databases, not simulations.

---

## 📋 What We're Benchmarking

### Real Performance Measurements

1. **Neo4j Aura** (Unified Architecture)
   - ✅ We have credentials - READY TO USE
   - Measures actual vector search latency
   - Measures actual graph traversal latency
   - Measures unified query latency (vector + graph in ONE query)

2. **AWS Neptune Database + OpenSearch** (Two-Layer Architecture)
   - ⚠️ Requires AWS account setup
   - Measures two-phase query latency
   - Measures serialization overhead
   - Measures network handover friction

3. **AWS Neptune Analytics** (Unified, Limited)
   - ⚠️ Requires AWS account setup
   - Measures unified query latency
   - Limited HNSW tuning compared to Neo4j

---

## 🎯 Quick Start: Neo4j Aura (We Can Do This NOW!)

### Prerequisites

```bash
# Install required packages
pip install neo4j python-dotenv

# Verify credentials in .env
cat .env
```

Should show:
```
NEO4J_URI=neo4j+s://<your-instance>.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=<your-password>
```

### Step 1: Load Sample Data (Small Scale)

```bash
# Load 10 drugs, 7 diseases, 8 genes with embeddings
python3 neo4j_data_loader.py
```

This will:
- ✅ Create Drug, Disease, Gene nodes
- ✅ Generate embeddings (384-dim vectors)
- ✅ Create TREATS and ASSOCIATED_WITH relationships
- ✅ Create vector index for similarity search
- ✅ Test vector search functionality

### Step 2: Run Real Benchmarks

```bash
# Run actual performance measurements
python3 real_benchmark_implementation.py
```

This measures:
- **Vector search latency:** Time for `db.index.vector.queryNodes()`
- **Graph traversal latency:** Time for `MATCH` patterns
- **Unified query latency:** Vector + graph in ONE Cypher query

Results saved to: `real_benchmark_results.json`

### Step 3: Scale Up (Optional)

```bash
# Generate 10K nodes for larger test
python3 neo4j_data_generator.py --scale 10000

# Generate 100K nodes
python3 neo4j_data_generator.py --scale 100000

# Generate 1M nodes (requires larger Neo4j instance)
python3 neo4j_data_generator.py --scale 1000000
```

---

## 📊 What Gets Measured

### Real Metrics (Not Simulated)

#### 1. Vector Search Latency
```cypher
// This query is actually executed and timed:
CALL db.index.vector.queryNodes('drug_embedding_vector', 10, $vector)
YIELD node, score
RETURN node.name, score
```

**Measured:**
- Query execution time
- Min, max, median, stdev over 10 iterations
- Actual HNSW index performance

#### 2. Graph Traversal Latency
```cypher
// Actual graph pattern matching:
MATCH (drug:Drug {id: $node_id})
MATCH (drug)-[:TREATS]->(disease:Disease)
OPTIONAL MATCH (disease)<-[:ASSOCIATED_WITH]-(gene:Gene)
RETURN drug.name, collect(disease.name), collect(gene.symbol)
```

**Measured:**
- Graph traversal time
- Relationship resolution time
- Aggregation overhead

#### 3. Unified Query Latency (THE KEY METRIC)
```cypher
// Vector + Graph in ONE query (no handover!):
CALL db.index.vector.queryNodes('drug_embedding_vector', 10, $vector)
YIELD node AS drug, score

// Graph traversal in SAME query
MATCH (drug)-[:TREATS]->(disease:Disease)
OPTIONAL MATCH (disease)<-[:ASSOCIATED_WITH]-(gene:Gene)

RETURN drug.name, score, 
       collect(DISTINCT disease.name) as diseases,
       collect(DISTINCT gene.symbol) as genes
ORDER BY score DESC
```

**Measured:**
- **Total latency:** End-to-end query time
- **No handover friction:** Everything in one execution
- **Real-world performance:** Actual database query

---

## 💰 Cost Breakdown

### Neo4j Aura

**Free Tier:**
- 200K nodes, 400K relationships
- Perfect for testing and small-scale benchmarks
- ✅ **We can use this NOW at no cost**

**Professional Tier:**
- Starts at $65/month
- 1M+ nodes
- Required for billion-scale tests

**Enterprise:**
- Custom pricing
- Dedicated cluster
- Full HNSW parameter control

### AWS Neptune + OpenSearch

**Neptune Database:**
- `db.r6g.large`: $0.348/hour (~$250/month)
- `db.r6g.xlarge`: $0.696/hour (~$500/month)
- Storage: $0.10/GB-month
- Data transfer: $0.09/GB

**OpenSearch:**
- `m6g.large.search`: $0.139/hour (~$100/month)
- `m6g.xlarge.search`: $0.278/hour (~$200/month)
- Storage: $0.10/GB-month

**Total for small test:** ~$350-400/month

**Total for billion-scale:** $2,000-5,000/month

### AWS Neptune Analytics

**Pricing:**
- $1.00 per GB-hour (in-memory)
- Example: 100GB graph = $100/hour
- Not billed when stopped

**Total for test:** $50-100 (few hours)

**Total for billion-scale:** Very expensive (hundreds of GB)

---

## 🏗️ AWS Setup (For Neptune Benchmarks)

### Option 1: AWS CLI Setup

```bash
# Install AWS CLI
pip install awscli

# Configure credentials
aws configure

# Create Neptune cluster
aws neptune create-db-cluster \
    --db-cluster-identifier graphrag-benchmark \
    --engine neptune \
    --master-username admin \
    --master-user-password YourSecurePassword123!

# Create Neptune instance
aws neptune create-db-instance \
    --db-instance-identifier graphrag-benchmark-instance \
    --db-instance-class db.r6g.large \
    --engine neptune \
    --db-cluster-identifier graphrag-benchmark

# Create OpenSearch domain
aws opensearch create-domain \
    --domain-name graphrag-vectors \
    --engine-version OpenSearch_2.11 \
    --cluster-config InstanceType=m6g.large.search,InstanceCount=1

# Create Neptune Analytics graph
aws neptune-graph create-graph \
    --graph-name graphrag-benchmark \
    --provisioned-memory 128
```

### Option 2: AWS Console Setup

1. **Neptune Database:**
   - Go to AWS Neptune Console
   - Click "Create database"
   - Choose "Standard create"
   - Instance: db.r6g.large
   - VPC: default or create new
   - Public access: Yes (for testing)

2. **OpenSearch:**
   - Go to AWS OpenSearch Console
   - Click "Create domain"
   - Domain name: graphrag-vectors
   - Instance: m6g.large.search
   - Network: Public access (for testing)

3. **Neptune Analytics:**
   - Go to Neptune Analytics Console
   - Click "Create graph"
   - Memory: 128 GB (minimum)
   - Wait for provisioning (~10 minutes)

### Install Python Clients

```bash
# Neptune client
pip install gremlinpython

# OpenSearch client
pip install opensearch-py

# AWS SDK
pip install boto3
```

### Update Configuration

Add to `.env`:
```bash
# Neptune Database
NEPTUNE_ENDPOINT=your-cluster.us-east-1.neptune.amazonaws.com
NEPTUNE_PORT=8182

# OpenSearch
OPENSEARCH_HOST=search-graphrag-vectors-xxx.us-east-1.es.amazonaws.com
OPENSEARCH_PORT=443

# Neptune Analytics
NEPTUNE_ANALYTICS_ENDPOINT=g-xxxxx.us-east-1.neptune-graph.amazonaws.com
```

---

## 📈 Expected Results

### Small Scale (10K nodes)

**Neo4j Aura:**
```
Vector Search:      15-25ms
Graph Traversal:    5-10ms
Unified Query:      20-30ms
Friction:           NONE
```

**Neptune + OpenSearch:**
```
Vector Search:      20-30ms  (OpenSearch)
Serialization:      2-5ms    (Overhead)
Network:            5-10ms   (Overhead)
Graph Traversal:    10-15ms  (Neptune)
Total:              37-60ms
Friction:           7-15ms (20-25%)
```

### Medium Scale (100K nodes)

**Neo4j Aura:**
```
Vector Search:      25-35ms  (logarithmic scaling)
Unified Query:      30-45ms
```

**Neptune + OpenSearch:**
```
Total:              50-80ms
Friction:           10-20ms (20-25%)
```

### Large Scale (1M nodes)

**Neo4j Aura:**
```
Vector Search:      30-40ms
Unified Query:      40-60ms
```

**Neptune + OpenSearch:**
```
Total:              80-120ms
Friction:           20-30ms (25-30%)
```

### Billion Scale (1B nodes)

**Neo4j Aura (Estimated):**
```
Vector Search:      50-100ms
Unified Query:      70-150ms
```

**Neptune + OpenSearch (Estimated):**
```
Total:              200-400ms
Friction:           50-100ms (25-33%)
```

---

## 🎯 Benchmark Scenarios

### Scenario 1: Small Dataset Comparison
**Goal:** Validate unified architecture advantage
**Scale:** 10K nodes
**Duration:** 30 minutes
**Cost:** $0 (Neo4j free tier)

```bash
# Load data
python3 neo4j_data_loader.py

# Run benchmark
python3 real_benchmark_implementation.py
```

### Scenario 2: Medium Scale Test
**Goal:** Test logarithmic scaling
**Scale:** 100K nodes
**Duration:** 2 hours
**Cost:** $0 (Neo4j free tier)

```bash
# Generate data
python3 neo4j_data_generator.py --scale 100000

# Run benchmark
python3 real_benchmark_implementation.py
```

### Scenario 3: Production Scale Test
**Goal:** Validate billion-scale claims
**Scale:** 1M - 10M nodes
**Duration:** 1 day
**Cost:** $65+ (Neo4j Pro) or $400+ (Neptune)

```bash
# Neo4j Pro required
python3 neo4j_data_generator.py --scale 1000000

# Run comprehensive benchmark
python3 real_benchmark_implementation.py --iterations 100
```

---

## 🔍 Verification Checklist

### Before Running Benchmarks

- [ ] Neo4j credentials configured in `.env`
- [ ] Python packages installed (`neo4j`, `python-dotenv`)
- [ ] Connection verified (`python3 -c "from neo4j import GraphDatabase; print('OK')"`)
- [ ] Data loaded (run `neo4j_data_loader.py`)
- [ ] Vector index created (check in loader output)
- [ ] Vector search working (test query in loader)

### After Running Benchmarks

- [ ] Results file created (`real_benchmark_results.json`)
- [ ] Latency measurements look reasonable (not 0ms or 999999ms)
- [ ] Standard deviation reasonable (< 50% of mean)
- [ ] Multiple iterations completed (default: 10)
- [ ] All queries executed successfully

---

## 🐛 Troubleshooting

### Connection Issues

```python
# Test Neo4j connection
from neo4j import GraphDatabase
driver = GraphDatabase.driver(
    "neo4j+s://<your-instance>.databases.neo4j.io",
    auth=("neo4j", "your-password")
)
with driver.session() as session:
    result = session.run("RETURN 1 as n")
    print(result.single()["n"])  # Should print 1
driver.close()
```

### Vector Index Issues

```cypher
// Check if index exists
SHOW INDEXES;

// Check index status
SHOW INDEXES WHERE name = 'drug_embedding_vector';

// Drop and recreate if needed
DROP INDEX drug_embedding_vector IF EXISTS;
CREATE VECTOR INDEX drug_embedding_vector
FOR (d:Drug) ON d.embedding
OPTIONS {indexConfig: {`vector.dimensions`: 384}};
```

### Memory Issues (Large Scale)

```cypher
// Check memory usage
CALL dbms.listConfig() 
YIELD name, value 
WHERE name STARTS WITH 'dbms.memory';

// Query profile
EXPLAIN
CALL db.index.vector.queryNodes('drug_embedding_vector', 10, $vector)
YIELD node, score
RETURN node;
```

---

## 📊 Comparing Results

### Real vs Simulated

**Simulated (Previous):**
- Based on mathematical models
- HNSW O(log n) complexity
- Estimated overhead
- ⚠️ Not actual measurements

**Real (This Implementation):**
- Actual database queries
- Real network latency
- Measured overhead
- ✅ Production-grade validation

### Expected Differences

Simulated benchmarks may differ from real by:
- ±20-30% due to network variability
- ±10-20% due to database caching
- ±5-10% due to system load

But the **relative differences** should match:
- Unified architectures should be faster
- Two-layer should show friction overhead
- HNSW should scale logarithmically

---

## ✅ Next Steps

### Immediate (Today)

1. Run Neo4j Aura benchmark with sample data
   ```bash
   python3 neo4j_data_loader.py
   python3 real_benchmark_implementation.py
   ```

2. Analyze results
   ```bash
   cat real_benchmark_results.json
   ```

3. Compare with simulated results
   ```bash
   diff real_benchmark_results.json graphrag_benchmark_results.json
   ```

### Short Term (This Week)

1. Scale up to 100K nodes
2. Run multiple benchmark iterations
3. Document performance characteristics
4. Create visualization of real results

### Long Term (This Month)

1. Set up AWS Neptune + OpenSearch
2. Run two-layer benchmarks
3. Measure actual friction overhead
4. Validate billion-scale claims (if budget allows)

---

## 📝 Files Reference

| File | Purpose |
|------|---------|
| `neo4j_data_loader.py` | Load sample biomedical data |
| `neo4j_data_generator.py` | Generate large-scale synthetic data |
| `real_benchmark_implementation.py` | Execute real performance benchmarks |
| `real_benchmark_results.json` | Output with actual measurements |

---

## 🎓 Key Takeaways

1. **We have Neo4j Aura access NOW** - can run real benchmarks immediately
2. **Small-scale tests are FREE** - can validate architecture at no cost
3. **AWS setup is OPTIONAL** - Neo4j alone proves unified architecture advantage
4. **Real measurements matter** - simulations are useful, but actual data is definitive

---

**Status:** ✅ Ready to run real benchmarks on Neo4j Aura  
**Cost:** $0 for initial testing  
**Time:** 30 minutes for first real results  
**Impact:** Production-grade validation of GraphRAG architecture claims
