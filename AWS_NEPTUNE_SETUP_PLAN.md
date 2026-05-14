# AWS Neptune + OpenSearch Setup Plan

## Access Verification ✅

**AWS Account:** 210999745354  
**Region:** us-west-2  
**VPC:** vpc-097a149637cc1b2e5 (default)  
**Subnets:** 4 subnets across us-west-2a/b/c/d  

**Services Accessible:**
- ✅ Neptune Database
- ✅ Neptune Analytics  
- ✅ OpenSearch
- ✅ EC2 (for networking)

---

## Architecture Options

### Option 1: Neptune Analytics (Recommended for Quick Start)
**Pros:**
- Native vector search built-in
- Unified queries (no OpenSearch needed)
- Fastest to set up (10-15 minutes)
- Best for validating unified architecture

**Cons:**
- Expensive ($1/GB-hour in-memory)
- Cannot compare two-layer friction
- Limited HNSW tuning

**Cost:** ~$10-50 for testing session

### Option 2: Neptune Database + OpenSearch (Full Comparison)
**Pros:**
- Can measure two-layer friction
- Direct comparison with Neo4j
- More production-like
- Better cost control

**Cons:**
- More complex setup (30-45 minutes)
- Requires both services
- More expensive for long-term

**Cost:** ~$0.50/hour (Neptune db.t3.medium + OpenSearch t3.small)

### Option 3: Both (Complete Validation)
**Pros:**
- Full comparison: Neptune DB, Neptune Analytics, Neo4j
- Validates all architecture claims
- Complete benchmark suite

**Cons:**
- Most expensive
- Longest setup time

**Cost:** ~$1.50-2.00/hour combined

---

## Recommended Approach

**Start with Neptune Analytics** (Option 1):
1. Quick setup (10 minutes)
2. Validates unified architecture
3. Can compare with Neo4j results we just got
4. Lower cost for testing

**Then add Neptune DB + OpenSearch** (Option 2) if needed:
1. Measure two-layer friction
2. Complete comparison
3. Full validation

---

## Setup Steps

### Neptune Analytics Setup

```bash
# 1. Create Neptune Analytics graph
aws neptune-graph create-graph \
    --graph-name graphrag-benchmark \
    --provisioned-memory 8 \
    --region us-west-2 \
    --tags Key=Project,Value=GraphRAG

# Wait for provisioning (~5-10 minutes)
aws neptune-graph get-graph \
    --graph-identifier <graph-id> \
    --region us-west-2

# 2. Load data via CSV import or SDK
# 3. Run benchmark queries
# 4. Compare with Neo4j results
```

**Estimated time:** 15-20 minutes  
**Cost:** ~$8/hour (8GB memory)

### Neptune Database + OpenSearch Setup

```bash
# 1. Create Neptune subnet group
aws neptune create-db-subnet-group \
    --db-subnet-group-name graphrag-subnet \
    --db-subnet-group-description "GraphRAG benchmark" \
    --subnet-ids subnet-0611e4c21f24ec7b6 subnet-0511317f09d952d33 \
    --region us-west-2

# 2. Create Neptune cluster
aws neptune create-db-cluster \
    --db-cluster-identifier graphrag-neptune \
    --engine neptune \
    --db-subnet-group-name graphrag-subnet \
    --vpc-security-group-ids <sg-id> \
    --region us-west-2

# 3. Create Neptune instance
aws neptune create-db-instance \
    --db-instance-identifier graphrag-neptune-1 \
    --db-instance-class db.t3.medium \
    --engine neptune \
    --db-cluster-identifier graphrag-neptune \
    --region us-west-2

# 4. Create OpenSearch domain
aws opensearch create-domain \
    --domain-name graphrag-opensearch \
    --engine-version OpenSearch_2.11 \
    --cluster-config InstanceType=t3.small.search,InstanceCount=1 \
    --ebs-options EBSEnabled=true,VolumeType=gp3,VolumeSize=10 \
    --region us-west-2

# 5. Load data
# 6. Run benchmarks
# 7. Compare results
```

**Estimated time:** 45-60 minutes  
**Cost:** ~$0.50/hour

---

## Data Loading Plan

### For Neptune Analytics
```python
# Use CSV bulk loader
drugs.csv
diseases.csv
genes.csv
relationships.csv

# Or use openCypher
CREATE (d:Drug {name: 'Pembrolizumab', embedding: [...]})
```

### For Neptune Database
```python
# Use Gremlin
g.addV('Drug').property('name', 'Pembrolizumab')
```

### For OpenSearch
```python
# Index vectors
PUT /drugs/_doc/1
{
  "name": "Pembrolizumab",
  "embedding": [0.1, 0.2, ...]
}
```

---

## Benchmark Queries

### Neptune Analytics (Unified)
```cypher
// Vector + Graph in ONE query
CALL neptune.algo.vectors.topKByNode('Drug', 'embedding', $vector, 10)
YIELD node, score
MATCH (node)-[:TREATS]->(disease:Disease)
RETURN node, score, disease
```

### Neptune Database + OpenSearch (Two-Layer)
```python
# Phase 1: OpenSearch vector search
opensearch.search(index="drugs", body={"query": {"knn": {...}}})

# Phase 2: Neptune graph traversal
g.V(candidate_ids).out('TREATS').values()
```

---

## Cost Estimate

### Neptune Analytics (8GB, 1 hour)
- Instance: $8.00
- **Total: $8.00/hour**

### Neptune Database + OpenSearch (1 hour)
- Neptune db.t3.medium: $0.082
- OpenSearch t3.small: $0.036
- Storage: $0.01
- Data transfer: $0.01
- **Total: ~$0.13/hour**

### For 4-hour test session
- Neptune Analytics: $32
- Neptune DB + OpenSearch: $0.52
- **Both: $32.52**

---

## Decision

Which setup would you like?

1. **Neptune Analytics only** ($8/hour, 20 min setup)
2. **Neptune DB + OpenSearch** ($0.13/hour, 60 min setup)  
3. **Both for complete comparison** ($8.13/hour, 90 min setup)

I can start immediately with any option.
