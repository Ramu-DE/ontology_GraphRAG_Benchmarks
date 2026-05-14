#!/usr/bin/env python3
"""
Load vector data to AWS OpenSearch
Prepares OpenSearch for two-layer benchmark with Neptune
"""

from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3
import hashlib
import json
import time

print("="*80)
print("LOADING VECTOR DATA TO AWS OPENSEARCH")
print("="*80)
print()

# Drug data (same as Neo4j)
DRUGS = [
    "Pembrolizumab", "Nivolumab", "Atezolizumab", "Trastuzumab", "Imatinib",
    "Metformin", "Aducanumab", "Lecanemab", "Semaglutide", "Tirzepatide"
]

def generate_embedding(drug_name: str, dimensions: int = 384) -> list:
    """Generate deterministic embedding from drug name (same as Neo4j)"""
    seed = int(hashlib.md5(drug_name.encode()).hexdigest(), 16) % (2**32)
    import random
    random.seed(seed)
    embedding = [random.gauss(0, 1) for _ in range(dimensions)]
    # Normalize
    magnitude = sum(x**2 for x in embedding) ** 0.5
    return [x / magnitude for x in embedding]

try:
    # Get OpenSearch endpoint
    print("🔍 Retrieving OpenSearch endpoint...")
    opensearch_info = boto3.client('opensearch', region_name='us-west-2').describe_domain(
        DomainName='graphrag-opensearch'
    )

    endpoint = opensearch_info['DomainStatus']['Endpoint']
    print(f"   Endpoint: {endpoint}")

    # Check if ready
    if opensearch_info['DomainStatus']['Processing']:
        print("❌ OpenSearch is still provisioning. Wait and try again.")
        exit(1)

    print("✅ OpenSearch is available")
    print()

    # Connect to OpenSearch with master user credentials
    print("🔌 Connecting to OpenSearch...")

    # Using master user authentication
    auth = ('admin', 'GraphRAG2024!')

    client = OpenSearch(
        hosts=[{'host': endpoint, 'port': 443}],
        http_auth=auth,
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )

    # Test connection
    info = client.info()
    print(f"✅ Connected to OpenSearch {info['version']['number']}")
    print()

    # Create index with vector mapping
    print("📝 Creating vector index...")

    index_name = "drugs"

    # Delete index if exists
    if client.indices.exists(index=index_name):
        client.indices.delete(index=index_name)
        print(f"   Deleted existing index '{index_name}'")

    # Create index with KNN mapping
    index_body = {
        "settings": {
            "index": {
                "knn": True,
                "knn.algo_param.ef_search": 512
            }
        },
        "mappings": {
            "properties": {
                "name": {"type": "keyword"},
                "embedding": {
                    "type": "knn_vector",
                    "dimension": 384,
                    "method": {
                        "name": "hnsw",
                        "space_type": "cosinesimil",
                        "engine": "nmslib",
                        "parameters": {
                            "ef_construction": 512,
                            "m": 16
                        }
                    }
                }
            }
        }
    }

    client.indices.create(index=index_name, body=index_body)
    print(f"✅ Created index '{index_name}' with KNN/HNSW")
    print()

    # Load drug vectors
    print(f"💊 Loading {len(DRUGS)} drug vectors...")

    for drug in DRUGS:
        embedding = generate_embedding(drug, 384)

        doc = {
            "name": drug,
            "embedding": embedding
        }

        client.index(
            index=index_name,
            id=drug,
            body=doc
        )
        print(f"  ✓ {drug} (384-dim vector)")

    # Force refresh to make documents searchable
    client.indices.refresh(index=index_name)
    print()

    # Verify data
    print("📊 Verifying data...")
    count = client.count(index=index_name)['count']
    print(f"   Documents indexed: {count}")
    print()

    # Test KNN search
    print("🧪 Testing KNN vector search...")

    query_vector = generate_embedding("Pembrolizumab", 384)

    start = time.time()
    result = client.search(
        index=index_name,
        body={
            "size": 3,
            "query": {
                "knn": {
                    "embedding": {
                        "vector": query_vector,
                        "k": 3
                    }
                }
            }
        }
    )
    latency = (time.time() - start) * 1000

    print(f"   Search latency: {latency:.2f}ms")
    print(f"   Results found: {len(result['hits']['hits'])}")
    for hit in result['hits']['hits']:
        print(f"     {hit['_id']} (score: {hit['_score']:.4f})")
    print()

    print("="*80)
    print("✅ OPENSEARCH DATA LOADING COMPLETE")
    print("="*80)
    print()
    print("OpenSearch is ready for benchmarking!")
    print(f"  Endpoint: {endpoint}")
    print(f"  Index: {index_name}")
    print(f"  Vectors: {count} drugs (384-dim)")
    print()
    print("Next: Run two-layer benchmark (Neptune + OpenSearch)")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
