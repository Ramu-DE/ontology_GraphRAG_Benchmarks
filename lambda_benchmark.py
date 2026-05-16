"""
AWS Lambda function to run Neptune + OpenSearch benchmark
This will be deployed to run in the VPC with Neptune access
"""

import json
import time
import hashlib
import sys

# Layer will provide these packages
from gremlin_python.driver import client as gremlin_client
from opensearchpy import OpenSearch, RequestsHttpConnection

NEPTUNE_ENDPOINT = "wss://graphrag-neptune-cluster.cluster-cracicy0ect3.us-west-2.neptune.amazonaws.com:8182/gremlin"
OPENSEARCH_ENDPOINT = "search-graphrag-opensearch-cjs5ycirmg65pqvaj2q3w76oy4.us-west-2.es.amazonaws.com"

def generate_embedding(drug_name, dimensions=384):
    seed = int(hashlib.md5(drug_name.encode()).hexdigest(), 16) % (2**32)
    import random
    random.seed(seed)
    embedding = [random.gauss(0, 1) for _ in range(dimensions)]
    magnitude = sum(x**2 for x in embedding) ** 0.5
    return [x / magnitude for x in embedding]

def load_neptune_data():
    """Load data to Neptune"""
    print("Loading data to Neptune...")

    DRUGS = ["Pembrolizumab", "Nivolumab", "Atezolizumab", "Trastuzumab", "Imatinib",
        "Metformin", "Aducanumab", "Lecanemab", "Semaglutide", "Tirzepatide"]

    DISEASES = ["Lung Cancer", "Melanoma", "Breast Cancer", "Leukemia", "Diabetes",
        "Alzheimer's Disease", "Heart Disease", "Kidney Disease", "Liver Disease", "COVID-19"]

    GENES = ["EGFR", "PD-1", "PD-L1", "HER2", "BCR-ABL", "APOE", "TP53", "BRCA1", "KRAS", "ALK"]

    TREATS = [
        ("Pembrolizumab", "Lung Cancer"), ("Pembrolizumab", "Melanoma"),
        ("Nivolumab", "Lung Cancer"), ("Nivolumab", "Melanoma"),
        ("Atezolizumab", "Lung Cancer"), ("Trastuzumab", "Breast Cancer"),
        ("Imatinib", "Leukemia"), ("Metformin", "Diabetes"),
        ("Aducanumab", "Alzheimer's Disease"), ("Lecanemab", "Alzheimer's Disease"),
    ]

    ASSOCIATED_WITH = [
        ("Lung Cancer", "EGFR"), ("Lung Cancer", "KRAS"),
        ("Melanoma", "PD-1"), ("Melanoma", "PD-L1"),
        ("Breast Cancer", "HER2"), ("Breast Cancer", "BRCA1"),
        ("Leukemia", "BCR-ABL"), ("Alzheimer's Disease", "APOE"),
    ]

    gremlin = gremlin_client.Client(NEPTUNE_ENDPOINT, 'g')

    # Clear existing data
    gremlin.submit("g.V().drop()").all().result()

    # Load drugs
    for drug in DRUGS:
        gremlin.submit(f"g.addV('Drug').property('name', '{drug}').property('id', '{drug}')").all().result()

    # Load diseases
    for disease in DISEASES:
        gremlin.submit(f"g.addV('Disease').property('name', '{disease}').property('id', '{disease}')").all().result()

    # Load genes
    for gene in GENES:
        gremlin.submit(f"g.addV('Gene').property('symbol', '{gene}').property('id', '{gene}')").all().result()

    # Create relationships
    for drug, disease in TREATS:
        gremlin.submit(f"g.V().has('Drug', 'name', '{drug}').as('d').V().has('Disease', 'name', '{disease}').as('dis').addE('TREATS').from('d').to('dis')").all().result()

    for disease, gene in ASSOCIATED_WITH:
        gremlin.submit(f"g.V().has('Disease', 'name', '{disease}').as('dis').V().has('Gene', 'symbol', '{gene}').as('g').addE('ASSOCIATED_WITH').from('dis').to('g')").all().result()

    gremlin.close()
    print("Neptune data loaded!")

def run_benchmark():
    """Run two-layer benchmark"""
    print("Running benchmark...")

    # Connect to OpenSearch
    opensearch = OpenSearch(
        hosts=[{'host': OPENSEARCH_ENDPOINT, 'port': 443}],
        http_auth=('admin', os.getenv('OPENSEARCH_PASS', '')),
        use_ssl=True,
        verify_certs=True,
        connection_class=RequestsHttpConnection
    )

    # Connect to Neptune
    gremlin = gremlin_client.Client(NEPTUNE_ENDPOINT, 'g')
    gremlin.submit("g.V().limit(1).count()").all().result()

    query_drug = "Pembrolizumab"
    k = 10

    # Phase 1: OpenSearch
    query_vector = generate_embedding(query_drug, 384)
    phase1_start = time.time()
    opensearch_result = opensearch.search(
        index="drugs",
        body={"size": k, "query": {"knn": {"embedding": {"vector": query_vector, "k": k}}}}
    )
    phase1_time = (time.time() - phase1_start) * 1000
    candidate_ids = [hit["_id"] for hit in opensearch_result["hits"]["hits"]]

    # Friction: Serialization
    serial_start = time.time()
    ids_string = ",".join([f"'{id}'" for id in candidate_ids])
    serial_time = (time.time() - serial_start) * 1000

    # Phase 2: Neptune
    phase2_start = time.time()
    query = f"g.V().hasId(within({ids_string})).out('TREATS').project('drug', 'disease').by(values('name')).by(values('name'))"
    neptune_result = gremlin.submit(query).all().result()
    phase2_time = (time.time() - phase2_start) * 1000

    total_time = phase1_time + serial_time + phase2_time
    neo4j_time = 195.20

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
        },
        "sample_results": [{"drug": r['drug'], "disease": r['disease']} for r in neptune_result[:3]]
    }

    gremlin.close()
    return results

def lambda_handler(event, context):
    """Lambda handler"""
    try:
        action = event.get('action', 'benchmark')

        if action == 'load_data':
            load_neptune_data()
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Data loaded successfully'})
            }

        elif action == 'benchmark':
            # Load data first
            load_neptune_data()

            # Run benchmark
            results = run_benchmark()

            return {
                'statusCode': 200,
                'body': json.dumps(results, indent=2)
            }

        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Invalid action'})
            }

    except Exception as e:
        import traceback
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e),
                'traceback': traceback.format_exc()
            })
        }
