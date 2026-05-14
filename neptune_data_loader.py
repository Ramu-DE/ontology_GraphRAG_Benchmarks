#!/usr/bin/env python3
"""
Load data to AWS Neptune Database
Prepares Neptune for two-layer benchmark with OpenSearch
"""

from gremlin_python.driver import client
from gremlin_python.driver.protocol import GremlinServerError
import time

# Neptune connection
NEPTUNE_ENDPOINT = "wss://graphrag-neptune-cluster.cluster-cracicy0ect3.us-west-2.neptune.amazonaws.com:8182/gremlin"

print("="*80)
print("LOADING DATA TO AWS NEPTUNE DATABASE")
print("="*80)
print()

# Sample biomedical data (same as Neo4j)
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

# Drug-Disease relationships
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

# Disease-Gene relationships
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
    # Connect to Neptune
    print(f"🔌 Connecting to Neptune...")
    print(f"   Endpoint: {NEPTUNE_ENDPOINT}")

    gremlin_client = client.Client(NEPTUNE_ENDPOINT, 'g')

    # Test connection
    result = gremlin_client.submit("g.V().limit(1).count()").all().result()
    print(f"✅ Connected successfully")
    print()

    # Clear existing data (optional - for clean test)
    print("🗑️  Clearing existing data...")
    gremlin_client.submit("g.V().drop()").all().result()
    print("✅ Database cleared")
    print()

    # Load Drugs
    print(f"💊 Loading {len(DRUGS)} drugs...")
    for drug in DRUGS:
        query = f"g.addV('Drug').property('name', '{drug}').property('id', '{drug}')"
        gremlin_client.submit(query).all().result()
        print(f"  ✓ {drug}")
    print()

    # Load Diseases
    print(f"🏥 Loading {len(DISEASES)} diseases...")
    for disease in DISEASES:
        query = f"g.addV('Disease').property('name', '{disease}').property('id', '{disease}')"
        gremlin_client.submit(query).all().result()
        print(f"  ✓ {disease}")
    print()

    # Load Genes
    print(f"🧬 Loading {len(GENES)} genes...")
    for gene in GENES:
        query = f"g.addV('Gene').property('symbol', '{gene}').property('id', '{gene}')"
        gremlin_client.submit(query).all().result()
        print(f"  ✓ {gene}")
    print()

    # Create TREATS relationships
    print(f"🔗 Creating {len(TREATS)} TREATS relationships...")
    for drug, disease in TREATS:
        query = f"""
        g.V().has('Drug', 'name', '{drug}').as('d')
         .V().has('Disease', 'name', '{disease}').as('dis')
         .addE('TREATS').from('d').to('dis')
        """
        gremlin_client.submit(query).all().result()
        print(f"  ✓ {drug} → {disease}")
    print()

    # Create ASSOCIATED_WITH relationships
    print(f"🔗 Creating {len(ASSOCIATED_WITH)} ASSOCIATED_WITH relationships...")
    for disease, gene in ASSOCIATED_WITH:
        query = f"""
        g.V().has('Disease', 'name', '{disease}').as('dis')
         .V().has('Gene', 'symbol', '{gene}').as('g')
         .addE('ASSOCIATED_WITH').from('dis').to('g')
        """
        gremlin_client.submit(query).all().result()
        print(f"  ✓ {disease} → {gene}")
    print()

    # Verify data
    print("📊 Verifying data...")
    drug_count = gremlin_client.submit("g.V().hasLabel('Drug').count()").all().result()[0]
    disease_count = gremlin_client.submit("g.V().hasLabel('Disease').count()").all().result()[0]
    gene_count = gremlin_client.submit("g.V().hasLabel('Gene').count()").all().result()[0]
    treats_count = gremlin_client.submit("g.E().hasLabel('TREATS').count()").all().result()[0]
    assoc_count = gremlin_client.submit("g.E().hasLabel('ASSOCIATED_WITH').count()").all().result()[0]

    print(f"  Drugs: {drug_count}")
    print(f"  Diseases: {disease_count}")
    print(f"  Genes: {gene_count}")
    print(f"  TREATS: {treats_count}")
    print(f"  ASSOCIATED_WITH: {assoc_count}")
    print()

    # Test query
    print("🧪 Testing graph traversal query...")
    query = """
    g.V().hasLabel('Drug').has('name', 'Pembrolizumab')
     .out('TREATS')
     .project('drug', 'disease')
     .by(constant('Pembrolizumab'))
     .by(values('name'))
    """
    result = gremlin_client.submit(query).all().result()
    print(f"  Found {len(result)} treatments")
    for r in result:
        print(f"    {r['drug']} treats {r['disease']}")
    print()

    print("="*80)
    print("✅ NEPTUNE DATA LOADING COMPLETE")
    print("="*80)
    print()
    print("Neptune is ready for benchmarking!")
    print("  Endpoint: graphrag-neptune-cluster.cluster-cracicy0ect3.us-west-2.neptune.amazonaws.com:8182")
    print()
    print("Next: Wait for OpenSearch to complete, then load vectors")

    gremlin_client.close()

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
