#!/bin/bash
# Complete Neptune + OpenSearch Benchmark Script
# Run this on EC2 instance i-0dc31b1ba71d0bd57

set -e

echo "=========================================="
echo "Installing dependencies..."
echo "=========================================="
sudo yum install -y python3-pip git
sudo pip3 install gremlinpython opensearch-py requests-aws4auth boto3

echo ""
echo "=========================================="
echo "Creating Neptune data loader..."
echo "=========================================="
cat > ~/load_neptune.py << 'EOF'
from gremlin_python.driver import client
NEPTUNE_ENDPOINT = "wss://graphrag-neptune-cluster.cluster-cracicy0ect3.us-west-2.neptune.amazonaws.com:8182/gremlin"
print("Connecting to Neptune...")
g = client.Client(NEPTUNE_ENDPOINT, 'g')
g.submit("g.V().drop()").all().result()
for drug in ["Pembrolizumab", "Nivolumab", "Atezolizumab", "Trastuzumab", "Imatinib", "Metformin", "Aducanumab", "Lecanemab", "Semaglutide", "Tirzepatide"]:
    g.submit(f"g.addV('Drug').property('name', '{drug}').property('id', '{drug}')").all().result()
    print(f"  ✓ {drug}")
for disease in ["Lung Cancer", "Melanoma", "Breast Cancer", "Leukemia", "Diabetes", "Alzheimer's Disease", "Heart Disease", "Kidney Disease", "Liver Disease", "COVID-19"]:
    g.submit(f"g.addV('Disease').property('name', '{disease}').property('id', '{disease}')").all().result()
    print(f"  ✓ {disease}")
for gene in ["EGFR", "PD-1", "PD-L1", "HER2", "BCR-ABL", "APOE", "TP53", "BRCA1", "KRAS", "ALK"]:
    g.submit(f"g.addV('Gene').property('symbol', '{gene}').property('id', '{gene}')").all().result()
    print(f"  ✓ {gene}")
for drug, disease in [("Pembrolizumab", "Lung Cancer"), ("Pembrolizumab", "Melanoma"), ("Nivolumab", "Lung Cancer"), ("Nivolumab", "Melanoma"), ("Atezolizumab", "Lung Cancer"), ("Trastuzumab", "Breast Cancer"), ("Imatinib", "Leukemia"), ("Metformin", "Diabetes"), ("Aducanumab", "Alzheimer's Disease"), ("Lecanemab", "Alzheimer's Disease")]:
    g.submit(f"g.V().has('Drug', 'name', '{drug}').as('d').V().has('Disease', 'name', '{disease}').as('dis').addE('TREATS').from('d').to('dis')").all().result()
print("✅ Neptune data loaded!")
g.close()
EOF

echo ""
echo "=========================================="
echo "Creating benchmark script..."
echo "=========================================="
cat > ~/benchmark.py << 'EOF'
from gremlin_python.driver import client as gremlin_client
from opensearchpy import OpenSearch, RequestsHttpConnection
import hashlib, time, json

def generate_embedding(drug_name, dimensions=384):
    seed = int(hashlib.md5(drug_name.encode()).hexdigest(), 16) % (2**32)
    import random
    random.seed(seed)
    embedding = [random.gauss(0, 1) for _ in range(dimensions)]
    magnitude = sum(x**2 for x in embedding) ** 0.5
    return [x / magnitude for x in embedding]

print("="*80)
print("TWO-LAYER BENCHMARK: NEPTUNE + OPENSEARCH")
print("="*80)

opensearch = OpenSearch(hosts=[{'host': 'search-graphrag-opensearch-cjs5ycirmg65pqvaj2q3w76oy4.us-west-2.es.amazonaws.com', 'port': 443}], http_auth=('admin', 'GraphRAG2024!'), use_ssl=True, verify_certs=True, connection_class=RequestsHttpConnection)
gremlin = gremlin_client.Client("wss://graphrag-neptune-cluster.cluster-cracicy0ect3.us-west-2.neptune.amazonaws.com:8182/gremlin", 'g')

query_drug = "Pembrolizumab"
print(f"\nQuery: Find diseases treated by drugs similar to '{query_drug}'\n")

# Phase 1: OpenSearch
print("Phase 1: OpenSearch Vector Search")
query_vector = generate_embedding(query_drug, 384)
phase1_start = time.time()
opensearch_result = opensearch.search(index="drugs", body={"size": 10, "query": {"knn": {"embedding": {"vector": query_vector, "k": 10}}}})
phase1_time = (time.time() - phase1_start) * 1000
candidate_ids = [hit["_id"] for hit in opensearch_result["hits"]["hits"]]
print(f"  ⏱️  Time: {phase1_time:.2f}ms")
print(f"  📊 Candidates: {len(candidate_ids)} drugs\n")

# Friction: Serialization
print("Friction #1: Serialization")
serial_start = time.time()
ids_string = ",".join([f"'{id}'" for id in candidate_ids])
serial_time = (time.time() - serial_start) * 1000
print(f"  ⏱️  Time: {serial_time:.2f}ms\n")

# Phase 2: Neptune
print("Phase 2: Network + Neptune Graph Traversal")
phase2_start = time.time()
query = f"g.V().hasId(within({ids_string})).out('TREATS').project('drug', 'disease').by(values('name')).by(values('name'))"
neptune_result = gremlin.submit(query).all().result()
phase2_time = (time.time() - phase2_start) * 1000
print(f"  ⏱️  Time: {phase2_time:.2f}ms")
print(f"  📊 Results: {len(neptune_result)} drug-disease pairs\n")

total_time = phase1_time + serial_time + phase2_time
neo4j_time = 195.20

print("="*80)
print("RESULTS BREAKDOWN")
print("="*80)
print(f"  Phase 1 (OpenSearch vector):     {phase1_time:>7.2f}ms")
print(f"  Friction (serialization):        {serial_time:>7.2f}ms ⚠️")
print(f"  Phase 2 (network + Neptune):     {phase2_time:>7.2f}ms")
print(f"  {'─'*40}")
print(f"  Total (with friction):           {total_time:>7.2f}ms\n")

print("Sample Results:")
for r in neptune_result[:3]:
    print(f"  {r['drug']} treats {r['disease']}")

print("\n" + "="*80)
print("COMPARISON WITH NEO4J")
print("="*80)
print(f"  Neptune Two-Layer:       {total_time:>7.2f}ms")
print(f"  Neo4j Unified:           {neo4j_time:>7.2f}ms")
print(f"  {'─'*40}")
print(f"  Slowdown:                {total_time/neo4j_time:>7.2f}×")
print(f"  Unified Advantage:       {total_time - neo4j_time:>7.2f}ms faster\n")

results = {
    "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    "architecture": "Neptune + OpenSearch (Two-Layer)",
    "measurements": {"phase1_opensearch_ms": round(phase1_time, 2), "serialization_ms": round(serial_time, 2), "phase2_neptune_ms": round(phase2_time, 2), "total_ms": round(total_time, 2)},
    "comparison": {"neo4j_unified_ms": neo4j_time, "slowdown_factor": round(total_time / neo4j_time, 2), "unified_advantage_ms": round(total_time - neo4j_time, 2)}
}

with open('results.json', 'w') as f:
    json.dump(results, f, indent=2)

print("📁 Results saved to: results.json\n✅ BENCHMARK COMPLETE!")
gremlin.close()
EOF

echo ""
echo "=========================================="
echo "Loading data to Neptune..."
echo "=========================================="
python3 ~/load_neptune.py

echo ""
echo "=========================================="
echo "Running benchmark..."
echo "=========================================="
python3 ~/benchmark.py

echo ""
echo "=========================================="
echo "FINAL RESULTS:"
echo "=========================================="
cat ~/results.json

echo ""
echo "✅ DONE! Copy the results above."
