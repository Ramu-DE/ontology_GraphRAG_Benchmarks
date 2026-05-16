# EC2 Instance Setup for Neptune Benchmark

## Instance Details

**Instance ID:** i-0dc31b1ba71d0bd57  
**Public IP:** 18.236.160.96  
**Private IP:** 172.31.16.211 (same VPC as Neptune ✅)  
**Region:** us-west-2a  
**Status:** Running ✅

---

## Option 1: AWS Systems Manager Session Manager (No SSH Key Needed)

### Connect via AWS Console

1. Go to: https://console.aws.amazon.com/ec2/home?region=us-west-2#Instances:instanceId=i-0dc31b1ba71d0bd57
2. Click "Connect" button
3. Choose "Session Manager" tab
4. Click "Connect"

This opens a browser-based terminal directly on the instance!

### Or via AWS CLI

```bash
aws ssm start-session \
    --target i-0dc31b1ba71d0bd57 \
    --region us-west-2
```

---

## Option 2: Direct Commands via SSM (Run from Sandbox)

Wait 2-3 minutes for SSM agent to register, then:

```bash
# Send installation command
COMMAND_ID=$(aws ssm send-command \
    --instance-ids i-0dc31b1ba71d0bd57 \
    --document-name "AWS-RunShellScript" \
    --parameters 'commands=["sudo yum install -y python3-pip","sudo pip3 install gremlinpython opensearch-py requests-aws4auth boto3"]' \
    --region us-west-2 \
    --query 'Command.CommandId' \
    --output text)

# Check command status
aws ssm get-command-invocation \
    --command-id $COMMAND_ID \
    --instance-id i-0dc31b1ba71d0bd57 \
    --region us-west-2
```

---

## Setup Steps Once Connected

### 1. Install Dependencies

```bash
sudo yum install -y python3-pip git
sudo pip3 install gremlinpython opensearch-py requests-aws4auth boto3
```

### 2. Create neptune_data_loader.py

```bash
cat > neptune_data_loader.py << 'ENDOFFILE'
#!/usr/bin/env python3
"""Load data to AWS Neptune Database"""

from gremlin_python.driver import client
import time

NEPTUNE_ENDPOINT = "wss://graphrag-neptune-cluster.cluster-cracicy0ect3.us-west-2.neptune.amazonaws.com:8182/gremlin"

print("="*80)
print("LOADING DATA TO AWS NEPTUNE DATABASE")
print("="*80)

DRUGS = [
    "Pembrolizumab", "Nivolumab", "Atezolizumab", "Trastuzumab", "Imatinib",
    "Metformin", "Aducanumab", "Lecanemab", "Semaglutide", "Tirzepatide"
]

DISEASES = [
    "Lung Cancer", "Melanoma", "Breast Cancer", "Leukemia", "Diabetes",
    "Alzheimer's Disease", "Heart Disease", "Kidney Disease", "Liver Disease", "COVID-19"
]

GENES = [
    "EGFR", "PD-1", "PD-L1", "HER2", "BCR-ABL",
    "APOE", "TP53", "BRCA1", "KRAS", "ALK"
]

TREATS = [
    ("Pembrolizumab", "Lung Cancer"),
    ("Pembrolizumab", "Melanoma"),
    ("Nivolumab", "Lung Cancer"),
    ("Nivolumab", "Melanoma"),
    ("Atezolizumab", "Lung Cancer"),
    ("Trastuzumab", "Breast Cancer"),
    ("Imatinib", "Leukemia"),
    ("Metformin", "Diabetes"),
    ("Aducanumab", "Alzheimer's Disease"),
    ("Lecanemab", "Alzheimer's Disease"),
]

ASSOCIATED_WITH = [
    ("Lung Cancer", "EGFR"),
    ("Lung Cancer", "KRAS"),
    ("Melanoma", "PD-1"),
    ("Melanoma", "PD-L1"),
    ("Breast Cancer", "HER2"),
    ("Breast Cancer", "BRCA1"),
    ("Leukemia", "BCR-ABL"),
    ("Alzheimer's Disease", "APOE"),
]

try:
    print(f"🔌 Connecting to Neptune...")
    gremlin_client = client.Client(NEPTUNE_ENDPOINT, 'g')
    
    result = gremlin_client.submit("g.V().limit(1).count()").all().result()
    print(f"✅ Connected successfully")
    
    print("🗑️  Clearing existing data...")
    gremlin_client.submit("g.V().drop()").all().result()
    print("✅ Database cleared")
    
    print(f"💊 Loading {len(DRUGS)} drugs...")
    for drug in DRUGS:
        query = f"g.addV('Drug').property('name', '{drug}').property('id', '{drug}')"
        gremlin_client.submit(query).all().result()
        print(f"  ✓ {drug}")
    
    print(f"🏥 Loading {len(DISEASES)} diseases...")
    for disease in DISEASES:
        query = f"g.addV('Disease').property('name', '{disease}').property('id', '{disease}')"
        gremlin_client.submit(query).all().result()
        print(f"  ✓ {disease}")
    
    print(f"🧬 Loading {len(GENES)} genes...")
    for gene in GENES:
        query = f"g.addV('Gene').property('symbol', '{gene}').property('id', '{gene}')"
        gremlin_client.submit(query).all().result()
        print(f"  ✓ {gene}")
    
    print(f"🔗 Creating {len(TREATS)} TREATS relationships...")
    for drug, disease in TREATS:
        query = f"""
        g.V().has('Drug', 'name', '{drug}').as('d')
         .V().has('Disease', 'name', '{disease}').as('dis')
         .addE('TREATS').from('d').to('dis')
        """
        gremlin_client.submit(query).all().result()
        print(f"  ✓ {drug} → {disease}")
    
    print(f"🔗 Creating {len(ASSOCIATED_WITH)} ASSOCIATED_WITH relationships...")
    for disease, gene in ASSOCIATED_WITH:
        query = f"""
        g.V().has('Disease', 'name', '{disease}').as('dis')
         .V().has('Gene', 'symbol', '{gene}').as('g')
         .addE('ASSOCIATED_WITH').from('dis').to('g')
        """
        gremlin_client.submit(query).all().result()
        print(f"  ✓ {disease} → {gene}")
    
    print("="*80)
    print("✅ NEPTUNE DATA LOADING COMPLETE")
    print("="*80)
    
    gremlin_client.close()

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
ENDOFFILE

chmod +x neptune_data_loader.py
```

### 3. Create neptune_opensearch_benchmark.py

```bash
cat > neptune_opensearch_benchmark.py << 'ENDOFFILE'
#!/usr/bin/env python3
"""Two-Layer Benchmark: Neptune + OpenSearch"""

from gremlin_python.driver import client as gremlin_client
from opensearchpy import OpenSearch, RequestsHttpConnection
import hashlib
import time
import json

NEPTUNE_ENDPOINT = "wss://graphrag-neptune-cluster.cluster-cracicy0ect3.us-west-2.neptune.amazonaws.com:8182/gremlin"
OPENSEARCH_ENDPOINT = "search-graphrag-opensearch-cjs5ycirmg65pqvaj2q3w76oy4.us-west-2.es.amazonaws.com"

def generate_embedding(drug_name: str, dimensions: int = 384) -> list:
    """Generate deterministic embedding"""
    seed = int(hashlib.md5(drug_name.encode()).hexdigest(), 16) % (2**32)
    import random
    random.seed(seed)
    embedding = [random.gauss(0, 1) for _ in range(dimensions)]
    magnitude = sum(x**2 for x in embedding) ** 0.5
    return [x / magnitude for x in embedding]

print("="*80)
print("TWO-LAYER BENCHMARK: NEPTUNE + OPENSEARCH")
print("="*80)

try:
    # Connect to OpenSearch
    print("🔌 Connecting to OpenSearch...")
    opensearch = OpenSearch(
        hosts=[{'host': OPENSEARCH_ENDPOINT, 'port': 443}],
        http_auth=('admin', '<your-opensearch-password>'),
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )
    print("✅ OpenSearch connected")
    
    # Connect to Neptune
    print("🔌 Connecting to Neptune...")
    gremlin = gremlin_client.Client(NEPTUNE_ENDPOINT, 'g')
    gremlin.submit("g.V().limit(1).count()").all().result()
    print("✅ Neptune connected")
    
    query_drug = "Pembrolizumab"
    k = 10
    
    print(f"🔍 Query: Find diseases treated by drugs similar to '{query_drug}'")
    
    # Phase 1: OpenSearch Vector Search
    print("\nPhase 1: OpenSearch Vector Search")
    query_vector = generate_embedding(query_drug, 384)
    
    phase1_start = time.time()
    opensearch_result = opensearch.search(
        index="drugs",
        body={
            "size": k,
            "query": {
                "knn": {
                    "embedding": {
                        "vector": query_vector,
                        "k": k
                    }
                }
            }
        }
    )
    phase1_time = (time.time() - phase1_start) * 1000
    candidate_ids = [hit["_id"] for hit in opensearch_result["hits"]["hits"]]
    
    print(f"  ⏱️  Time: {phase1_time:.2f}ms")
    print(f"  📊 Candidates: {len(candidate_ids)} drugs")
    
    # Friction #1: Serialization
    print("\nFriction #1: Serialization")
    serial_start = time.time()
    ids_string = ",".join([f"'{id}'" for id in candidate_ids])
    serial_time = (time.time() - serial_start) * 1000
    print(f"  ⏱️  Time: {serial_time:.2f}ms")
    
    # Phase 2: Neptune Graph Traversal
    print("\nPhase 2: Network + Neptune Graph Traversal")
    phase2_start = time.time()
    query = f"""
    g.V().hasId(within({ids_string}))
         .out('TREATS')
         .project('drug', 'disease')
         .by(values('name'))
         .by(values('name'))
    """
    neptune_result = gremlin.submit(query).all().result()
    phase2_time = (time.time() - phase2_start) * 1000
    
    print(f"  ⏱️  Time: {phase2_time:.2f}ms")
    print(f"  📊 Results: {len(neptune_result)} drug-disease pairs")
    
    # Results
    total_time = phase1_time + serial_time + phase2_time
    
    print("\n" + "="*80)
    print("RESULTS BREAKDOWN")
    print("="*80)
    print(f"  Phase 1 (OpenSearch vector):     {phase1_time:>7.2f}ms")
    print(f"  Friction (serialization):        {serial_time:>7.2f}ms ⚠️")
    print(f"  Phase 2 (network + Neptune):     {phase2_time:>7.2f}ms")
    print(f"  {'─'*40}")
    print(f"  Total (with friction):           {total_time:>7.2f}ms")
    
    print("\nSample Results:")
    for r in neptune_result[:3]:
        print(f"  {r['drug']} treats {r['disease']}")
    
    # Comparison
    neo4j_time = 195.20
    print("\n" + "="*80)
    print("COMPARISON WITH NEO4J")
    print("="*80)
    print(f"  Neptune Two-Layer:       {total_time:>7.2f}ms")
    print(f"  Neo4j Unified:           {neo4j_time:>7.2f}ms")
    print(f"  {'─'*40}")
    print(f"  Slowdown:                {total_time/neo4j_time:>7.2f}×")
    print(f"  Unified Advantage:       {total_time - neo4j_time:>7.2f}ms faster")
    
    # Save results
    results = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "architecture": "Neptune + OpenSearch (Two-Layer)",
        "measurements": {
            "phase1_opensearch_ms": round(phase1_time, 2),
            "serialization_ms": round(serial_time, 2),
            "phase2_neptune_ms": round(phase2_time, 2),
            "total_ms": round(total_time, 2)
        },
        "comparison": {
            "neo4j_unified_ms": neo4j_time,
            "slowdown_factor": round(total_time / neo4j_time, 2),
            "unified_advantage_ms": round(total_time - neo4j_time, 2)
        }
    }
    
    with open('neptune_opensearch_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print("\n📁 Results saved to: neptune_opensearch_results.json")
    print("\n✅ BENCHMARK COMPLETE!")
    
    gremlin.close()

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
ENDOFFILE

chmod +x neptune_opensearch_benchmark.py
```

### 4. Run Benchmark

```bash
# Load Neptune data
python3 neptune_data_loader.py

# Run two-layer benchmark
python3 neptune_opensearch_benchmark.py

# View results
cat neptune_opensearch_results.json
```

---

## Expected Results

```
Phase 1 (OpenSearch vector):     ~200ms
Friction (serialization):         ~10ms  ⚠️
Phase 2 (network + Neptune):     ~220ms
─────────────────────────────────────────
Total (with friction):           ~430ms

Neptune Two-Layer:       430ms
Neo4j Unified:           195ms
─────────────────────────────────────────
Slowdown:                2.2×
Unified Advantage:       235ms faster
```

---

## Retrieve Results Back to Sandbox

After benchmark completes, copy results file:

```bash
# On EC2: Display results
cat neptune_opensearch_results.json

# Copy output and save to sandbox
```

Or use S3:

```bash
# On EC2: Upload to S3
aws s3 cp neptune_opensearch_results.json s3://your-bucket/

# From sandbox: Download
aws s3 cp s3://your-bucket/neptune_opensearch_results.json .
```

---

## Cleanup

After getting results:

```bash
# Terminate EC2 instance
aws ec2 terminate-instances \
    --instance-ids i-0dc31b1ba71d0bd57 \
    --region us-west-2
```

---

## Quick Commands Summary

```bash
# 1. Connect (via AWS Console Session Manager)
https://console.aws.amazon.com/ec2/home?region=us-west-2#Instances:instanceId=i-0dc31b1ba71d0bd57

# 2. Setup
sudo yum install -y python3-pip
sudo pip3 install gremlinpython opensearch-py requests-aws4auth boto3

# 3. Create scripts (see above)

# 4. Run
python3 neptune_data_loader.py
python3 neptune_opensearch_benchmark.py

# 5. Get results
cat neptune_opensearch_results.json
```

---

**Status:** EC2 instance ready at `18.236.160.96` (private: `172.31.16.211`)  
**Next:** Connect via Session Manager and run benchmark!
