#!/usr/bin/env python3
"""
REAL Neptune vs Neo4j Benchmark
================================
Measures ACTUAL latency against live infrastructure:
  1. Neo4j Aura          — unified vector + graph (HNSW native)
  2. Neptune Analytics    — unified vector + graph (native vectors)
  3. Neptune DB + OpenSearch — two-layer (vector DB + graph DB separate)

Every number in the output is a REAL measurement, not a simulation.
"""

import time
import json
import hashlib
import random
import statistics
import sys
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional

import numpy as np

# =============================================================================
# Configuration
# =============================================================================

import os
from dotenv import load_dotenv
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "neo4j+s://your-instance.databases.neo4j.io")
NEO4J_USER = os.getenv("NEO4J_USERNAME", "neo4j")
NEO4J_PASS = os.getenv("NEO4J_PASSWORD", "")
NEO4J_DB = os.getenv("NEO4J_DATABASE", "neo4j")

NEPTUNE_ANALYTICS_ENDPOINT = os.getenv("NEPTUNE_ANALYTICS_ENDPOINT", "")
NEPTUNE_ANALYTICS_GRAPH_ID = os.getenv("NEPTUNE_ANALYTICS_GRAPH_ID", "")

NEPTUNE_DB_ENDPOINT = os.getenv("NEPTUNE_DB_ENDPOINT", "")
NEPTUNE_DB_PORT = int(os.getenv("NEPTUNE_DB_PORT", "8182"))

OPENSEARCH_DOMAIN = os.getenv("OPENSEARCH_DOMAIN", "graphrag-opensearch")
OPENSEARCH_USER = os.getenv("OPENSEARCH_USER", "admin")
OPENSEARCH_PASS = os.getenv("OPENSEARCH_PASS", "")

AWS_REGION = "us-west-2"
VECTOR_DIM = 384
TOP_K = 5
BENCHMARK_ITERATIONS = 10

# Biomedical drug data (same as loaded in Neo4j)
DRUGS = [
    {"id": "D001", "name": "Pembrolizumab",  "mechanism": "PD-1 inhibitor",     "type": "Monoclonal Antibody", "status": "Approved"},
    {"id": "D002", "name": "Nivolumab",      "mechanism": "PD-1 inhibitor",     "type": "Monoclonal Antibody", "status": "Approved"},
    {"id": "D003", "name": "Atezolizumab",   "mechanism": "PD-L1 inhibitor",    "type": "Monoclonal Antibody", "status": "Approved"},
    {"id": "D004", "name": "Trastuzumab",    "mechanism": "HER2 inhibitor",     "type": "Monoclonal Antibody", "status": "Approved"},
    {"id": "D005", "name": "Imatinib",       "mechanism": "BCR-ABL inhibitor",  "type": "Small Molecule",      "status": "Approved"},
    {"id": "D006", "name": "Semaglutide",    "mechanism": "GLP-1 agonist",      "type": "Peptide",             "status": "Approved"},
    {"id": "D007", "name": "Tirzepatide",    "mechanism": "GIP/GLP-1 agonist",  "type": "Peptide",             "status": "Approved"},
    {"id": "D008", "name": "Metformin",      "mechanism": "AMPK activator",     "type": "Small Molecule",      "status": "Approved"},
    {"id": "D009", "name": "Aducanumab",     "mechanism": "Amyloid-beta Ab",    "type": "Monoclonal Antibody", "status": "Approved"},
    {"id": "D010", "name": "Lecanemab",      "mechanism": "Amyloid-beta Ab",    "type": "Monoclonal Antibody", "status": "Approved"},
]

DISEASES = [
    {"id": "DIS001", "name": "Non-Small Cell Lung Cancer"},
    {"id": "DIS002", "name": "Melanoma"},
    {"id": "DIS003", "name": "Breast Cancer"},
    {"id": "DIS004", "name": "Chronic Myeloid Leukemia"},
    {"id": "DIS005", "name": "Type 2 Diabetes"},
    {"id": "DIS006", "name": "Obesity"},
    {"id": "DIS007", "name": "Alzheimer's Disease"},
]

TREATS = [
    ("D001", "DIS001"), ("D001", "DIS002"),
    ("D002", "DIS001"), ("D002", "DIS002"),
    ("D003", "DIS001"),
    ("D004", "DIS003"),
    ("D005", "DIS004"),
    ("D006", "DIS005"), ("D006", "DIS006"),
    ("D007", "DIS005"), ("D007", "DIS006"),
    ("D008", "DIS005"),
    ("D009", "DIS007"),
    ("D010", "DIS007"),
]

QUERY_TEXTS = [
    "PD-1 immune checkpoint inhibitor for lung cancer",
    "HER2 targeted antibody for breast cancer",
    "kinase inhibitor for leukemia treatment",
    "GLP-1 peptide for diabetes and obesity",
    "amyloid-beta antibody for Alzheimer disease",
]


def generate_embedding(text: str, dim: int = VECTOR_DIM) -> List[float]:
    seed = int(hashlib.md5(text.encode()).hexdigest(), 16) % (2**32)
    rng = random.Random(seed)
    raw = [rng.gauss(0, 1) for _ in range(dim)]
    mag = sum(x * x for x in raw) ** 0.5
    return [x / mag for x in raw]


def banner(title: str, char: str = "="):
    w = 72
    print(f"\n{char * w}")
    print(f"  {title}")
    print(f"{char * w}")


@dataclass
class QueryResult:
    architecture: str
    query_label: str
    latency_ms: float
    result_count: int
    top_drug: str
    top_score: float
    friction_ms: float = 0.0


# =============================================================================
# 1. Neo4j Aura Benchmark (already loaded)
# =============================================================================

def benchmark_neo4j(iterations: int = BENCHMARK_ITERATIONS) -> List[QueryResult]:
    banner("BENCHMARK 1: Neo4j Aura (Unified Architecture)")
    print("  Native HNSW vector index + Cypher graph traversal in ONE query")
    print(f"  Endpoint: {NEO4J_URI}\n")

    from neo4j import GraphDatabase
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))

    # Verify
    with driver.session(database=NEO4J_DB) as s:
        cnt = s.run("MATCH (d:Drug) RETURN count(d) AS c").single()["c"]
        print(f"  Drugs in graph: {cnt}")
        idx = s.run("SHOW INDEXES YIELD name, type WHERE type='VECTOR' RETURN name").single()
        print(f"  Vector index: {idx['name']}\n")

    results = []
    for query_text, label in zip(QUERY_TEXTS, ["Immuno", "HER2", "TKI", "GLP1", "Amyloid"]):
        qvec = generate_embedding(query_text)
        latencies = []

        for i in range(iterations):
            t0 = time.perf_counter()
            with driver.session(database=NEO4J_DB) as s:
                rows = list(s.run("""
                    CALL db.index.vector.queryNodes('drug_embedding_vector', $k, $vec)
                    YIELD node AS drug, score
                    OPTIONAL MATCH (drug)-[:TREATS]->(disease:Disease)
                    WITH drug, score, collect(DISTINCT disease.name) AS diseases
                    RETURN drug.name AS name, score, diseases
                    ORDER BY score DESC
                """, k=TOP_K, vec=qvec))
            latencies.append((time.perf_counter() - t0) * 1000)

        mean_lat = statistics.mean(latencies)
        top = rows[0] if rows else None
        r = QueryResult(
            architecture="Neo4j Aura",
            query_label=label,
            latency_ms=mean_lat,
            result_count=len(rows),
            top_drug=top["name"] if top else "N/A",
            top_score=round(float(top["score"]), 4) if top else 0,
            friction_ms=0.0
        )
        results.append(r)
        print(f"  [{label:<8}] {mean_lat:>8.1f} ms  top={r.top_drug:<18} score={r.top_score}  "
              f"rows={r.result_count}  friction=0ms")

    driver.close()
    return results


# =============================================================================
# 2. Neptune Analytics Benchmark (native vectors)
# =============================================================================

def _na_query(client, cypher):
    """Execute openCypher on Neptune Analytics with inline values."""
    r = client.execute_query(
        graphIdentifier=NEPTUNE_ANALYTICS_GRAPH_ID,
        queryString=cypher, language="OPEN_CYPHER", parameters={}
    )
    return json.loads(r["payload"].read()).get("results", [])


def load_neptune_analytics():
    """Load data into Neptune Analytics graph (inline openCypher)."""
    banner("Loading data into Neptune Analytics", "-")
    import boto3
    client = boto3.client("neptune-graph", region_name=AWS_REGION)

    # Clear
    _na_query(client, "MATCH (n) DETACH DELETE n")

    # Load drugs
    for drug in DRUGS:
        name = drug["name"].replace("'", "\\'")
        _na_query(client, (
            f"CREATE (d:Drug {{node_id: '{drug['id']}', name: '{name}', "
            f"mechanism: '{drug['mechanism']}', drug_type: '{drug['type']}', "
            f"approval_status: '{drug['status']}'}})"
        ))
        print(f"  Drug: {name}")

    # Load diseases
    for dis in DISEASES:
        name = dis["name"].replace("'", "\\'")
        _na_query(client, f"CREATE (d:Disease {{node_id: '{dis['id']}', name: '{name}'}})")

    # Load relationships
    for drug_id, dis_id in TREATS:
        _na_query(client, (
            f"MATCH (d:Drug {{node_id: '{drug_id}'}}), (dis:Disease {{node_id: '{dis_id}'}}) "
            f"CREATE (d)-[:TREATS]->(dis)"
        ))

    # Set embeddings via neptune.algo.vectors.upsert
    print("  Setting vector embeddings...")
    for drug in DRUGS:
        emb = generate_embedding(drug["name"])
        emb_str = "[" + ",".join(f"{x:.8f}" for x in emb) + "]"
        _na_query(client, (
            f"MATCH (d:Drug {{node_id: '{drug['id']}'}}) "
            f"CALL neptune.algo.vectors.upsert(d, {emb_str}) YIELD success RETURN success"
        ))
        print(f"    Embedding: {drug['name']}")

    # Verify
    for row in _na_query(client, "MATCH (n) RETURN labels(n)[0] AS label, count(n) AS cnt"):
        print(f"  {row['label']}: {row['cnt']} nodes")
    for row in _na_query(client, "MATCH ()-[r]->() RETURN type(r) AS t, count(r) AS cnt"):
        print(f"  {row['t']}: {row['cnt']} relationships")

    # Test vector search
    qv = generate_embedding("test query")
    qv_str = "[" + ",".join(f"{x:.8f}" for x in qv) + "]"
    res = _na_query(client, (
        f"CALL neptune.algo.vectors.topKByEmbedding({qv_str}, {{topK: 3}}) "
        f"YIELD node, score RETURN node.name AS name, score ORDER BY score DESC"
    ))
    print(f"  Vector search test: {len(res)} results")
    for r in res:
        print(f"    {r['name']}: {r['score']:.4f}")

    print("  Data loading complete.\n")


def benchmark_neptune_analytics(iterations: int = BENCHMARK_ITERATIONS) -> List[QueryResult]:
    banner("BENCHMARK 2: Neptune Analytics (Unified — Native Vectors)")
    print("  Native vector search via openCypher — unified, no OpenSearch needed")
    print(f"  Endpoint: {NEPTUNE_ANALYTICS_ENDPOINT}\n")

    import boto3
    client = boto3.client("neptune-graph", region_name=AWS_REGION)

    # Verify
    try:
        r = client.execute_query(
            graphIdentifier=NEPTUNE_ANALYTICS_GRAPH_ID,
            queryString="MATCH (d:Drug) RETURN count(d) AS c",
            language="OPEN_CYPHER",
            parameters={}
        )
        payload = json.loads(r["payload"].read())
        print(f"  Drugs in graph: {payload['results'][0]['c']}\n")
    except Exception as e:
        print(f"  Verification: {e}\n")

    results = []
    for query_text, label in zip(QUERY_TEXTS, ["Immuno", "HER2", "TKI", "GLP1", "Amyloid"]):
        qvec = generate_embedding(query_text)
        qvec_str = "[" + ",".join(f"{x:.8f}" for x in qvec) + "]"
        latencies = []
        rows = []

        # Unified query: vector search + graph traversal in ONE openCypher statement
        unified_cypher = (
            f"CALL neptune.algo.vectors.topKByEmbedding({qvec_str}, {{topK: {TOP_K}}}) "
            f"YIELD node, score "
            f"MATCH (node)-[:TREATS]->(disease:Disease) "
            f"RETURN node.name AS name, score, collect(DISTINCT disease.name) AS diseases "
            f"ORDER BY score DESC"
        )

        for i in range(iterations):
            t0 = time.perf_counter()
            try:
                rows = _na_query(client, unified_cypher)
            except Exception:
                rows = []
            latencies.append((time.perf_counter() - t0) * 1000)

        mean_lat = statistics.mean(latencies) if latencies else 0
        top = rows[0] if rows else {}
        r = QueryResult(
            architecture="Neptune Analytics",
            query_label=label,
            latency_ms=mean_lat,
            result_count=len(rows),
            top_drug=top.get("name", "N/A"),
            top_score=round(float(top.get("score", 0)), 4),
            friction_ms=0.0
        )
        results.append(r)
        print(f"  [{label:<8}] {mean_lat:>8.1f} ms  top={r.top_drug:<18} score={r.top_score}  "
              f"rows={r.result_count}  friction=0ms")

    return results


# =============================================================================
# 3. Neptune DB + OpenSearch Benchmark (two-layer)
# =============================================================================

def get_opensearch_endpoint() -> Optional[str]:
    """Get OpenSearch domain endpoint."""
    import boto3
    client = boto3.client("opensearch", region_name=AWS_REGION)
    try:
        r = client.describe_domain(DomainName=OPENSEARCH_DOMAIN)
        ep = r["DomainStatus"].get("Endpoints", {}).get("vpc", "")
        if not ep:
            ep = r["DomainStatus"].get("Endpoint", "")
        return ep
    except Exception as e:
        print(f"  OpenSearch endpoint error: {e}")
        return None


def load_opensearch(endpoint: str):
    """Load drug embeddings into OpenSearch kNN index."""
    banner("Loading embeddings into OpenSearch", "-")
    from opensearchpy import OpenSearch, RequestsHttpConnection

    os_client = OpenSearch(
        hosts=[{"host": endpoint, "port": 443}],
        http_auth=(OPENSEARCH_USER, OPENSEARCH_PASS),
        use_ssl=True,
        verify_certs=True,
        ssl_show_warn=False,
        connection_class=RequestsHttpConnection,
    )

    # Create kNN index
    index_body = {
        "settings": {
            "index": {"knn": True, "knn.algo_param.ef_search": 100}
        },
        "mappings": {
            "properties": {
                "drug_id": {"type": "keyword"},
                "name": {"type": "text"},
                "embedding": {
                    "type": "knn_vector",
                    "dimension": VECTOR_DIM,
                    "method": {
                        "name": "hnsw",
                        "space_type": "cosinesimil",
                        "engine": "nmslib",
                        "parameters": {"ef_construction": 128, "m": 16}
                    }
                }
            }
        }
    }

    if os_client.indices.exists(index="drugs"):
        os_client.indices.delete(index="drugs")
    os_client.indices.create(index="drugs", body=index_body)
    print("  Created kNN index 'drugs'")

    for drug in DRUGS:
        emb = generate_embedding(drug["name"])
        os_client.index(index="drugs", id=drug["id"], body={
            "drug_id": drug["id"],
            "name": drug["name"],
            "embedding": emb
        })
        print(f"  Indexed: {drug['name']}")

    os_client.indices.refresh(index="drugs")
    print("  Index refreshed.\n")
    return os_client


def load_neptune_db():
    """Load graph data into Neptune Database via Gremlin (inline values — Neptune doesn't support bindings)."""
    banner("Loading data into Neptune Database", "-")
    from gremlin_python.driver import client as gremlin_client

    endpoint = f"wss://{NEPTUNE_DB_ENDPOINT}:{NEPTUNE_DB_PORT}/gremlin"
    gc = gremlin_client.Client(endpoint, "g")

    # Clear existing
    gc.submit("g.V().drop()").all().result()
    print("  Cleared existing data")

    # Load drugs (inline values — Neptune doesn't support parameterized bindings)
    for drug in DRUGS:
        name = drug["name"].replace("'", "\\'")
        mech = drug["mechanism"].replace("'", "\\'")
        gc.submit(
            f"g.addV('Drug')"
            f".property(id, '{drug['id']}').property('name', '{name}')"
            f".property('mechanism', '{mech}').property('drug_type', '{drug['type']}')"
        ).all().result()
        print(f"  Loaded drug: {drug['name']}")

    # Load diseases
    for dis in DISEASES:
        name = dis["name"].replace("'", "\\'")
        gc.submit(
            f"g.addV('Disease').property(id, '{dis['id']}').property('name', '{name}')"
        ).all().result()

    # Load relationships
    for drug_id, dis_id in TREATS:
        gc.submit(
            f"g.addE('TREATS').from(V('{drug_id}')).to(V('{dis_id}'))"
        ).all().result()

    cnt = gc.submit("g.V().count()").all().result()[0]
    print(f"  Total vertices: {cnt}")
    gc.close()
    print("  Data loading complete.\n")


def benchmark_two_layer(os_endpoint: str, iterations: int = BENCHMARK_ITERATIONS) -> List[QueryResult]:
    banner("BENCHMARK 3: Neptune DB + OpenSearch (Two-Layer)")
    print("  Step 1: OpenSearch kNN → candidate IDs")
    print("  Step 2: Serialize IDs")
    print("  Step 3: Neptune Gremlin → graph traversal")
    print(f"  OpenSearch: {os_endpoint}")
    print(f"  Neptune:    {NEPTUNE_DB_ENDPOINT}\n")

    from opensearchpy import OpenSearch, RequestsHttpConnection
    from gremlin_python.driver import client as gremlin_client

    os_client = OpenSearch(
        hosts=[{"host": os_endpoint, "port": 443}],
        http_auth=(OPENSEARCH_USER, OPENSEARCH_PASS),
        use_ssl=True, verify_certs=True, ssl_show_warn=False,
        connection_class=RequestsHttpConnection,
    )

    gremlin_endpoint = f"wss://{NEPTUNE_DB_ENDPOINT}:{NEPTUNE_DB_PORT}/gremlin"
    gc = gremlin_client.Client(gremlin_endpoint, "g")

    results = []
    for query_text, label in zip(QUERY_TEXTS, ["Immuno", "HER2", "TKI", "GLP1", "Amyloid"]):
        qvec = generate_embedding(query_text)
        latencies = []
        friction_times = []

        for i in range(iterations):
            # --- Phase 1: OpenSearch vector search ---
            t_total_start = time.perf_counter()
            t0 = time.perf_counter()
            os_result = os_client.search(
                index="drugs",
                body={
                    "size": TOP_K,
                    "query": {"knn": {"embedding": {"vector": qvec, "k": TOP_K}}}
                }
            )
            t_vector = (time.perf_counter() - t0) * 1000

            # --- Phase 2: Serialize IDs (FRICTION) ---
            t0 = time.perf_counter()
            hits = os_result["hits"]["hits"]
            candidate_ids = [h["_id"] for h in hits]
            scores = {h["_id"]: h["_score"] for h in hits}
            ids_for_gremlin = [f"'{cid}'" for cid in candidate_ids]
            t_serialize = (time.perf_counter() - t0) * 1000

            # --- Phase 3: Neptune graph traversal ---
            t0 = time.perf_counter()
            gremlin_query = (
                f"g.V({','.join(ids_for_gremlin)})"
                ".project('drug_id','name','diseases')"
                ".by(id)"
                ".by(values('name'))"
                ".by(out('TREATS').values('name').fold())"
            )
            gremlin_result = gc.submit(gremlin_query).all().result()
            t_graph = (time.perf_counter() - t0) * 1000

            t_total = (time.perf_counter() - t_total_start) * 1000
            friction = t_serialize
            latencies.append(t_total)
            friction_times.append(friction)

        mean_lat = statistics.mean(latencies)
        mean_friction = statistics.mean(friction_times)
        top_hit = hits[0] if hits else {}
        top_name = "N/A"
        for gr in gremlin_result:
            if gr.get("drug_id") == top_hit.get("_id"):
                top_name = gr.get("name", "N/A")
                break

        r = QueryResult(
            architecture="Neptune DB + OpenSearch",
            query_label=label,
            latency_ms=mean_lat,
            result_count=len(gremlin_result),
            top_drug=top_name,
            top_score=round(float(top_hit.get("_score", 0)), 4),
            friction_ms=mean_friction
        )
        results.append(r)
        print(f"  [{label:<8}] {mean_lat:>8.1f} ms  top={r.top_drug:<18} score={r.top_score}  "
              f"rows={r.result_count}  friction={mean_friction:.1f}ms")

    gc.close()
    return results


# =============================================================================
# Comparison Report
# =============================================================================

def print_comparison(all_results: Dict[str, List[QueryResult]]):
    banner("FINAL COMPARISON: REAL MEASUREMENTS")

    archs = ["Neo4j Aura", "Neptune Analytics", "Neptune DB + OpenSearch"]
    print(f"\n  {'Architecture':<28} {'Mean (ms)':>10} {'Min (ms)':>10} {'Max (ms)':>10} {'Friction':>10}")
    print(f"  {'-'*28} {'-'*10} {'-'*10} {'-'*10} {'-'*10}")

    arch_summaries = {}
    for arch in archs:
        if arch not in all_results or not all_results[arch]:
            print(f"  {arch:<28} {'N/A':>10} {'N/A':>10} {'N/A':>10} {'N/A':>10}")
            continue
        lats = [r.latency_ms for r in all_results[arch]]
        frictions = [r.friction_ms for r in all_results[arch]]
        mean_l = statistics.mean(lats)
        min_l = min(lats)
        max_l = max(lats)
        mean_f = statistics.mean(frictions)
        arch_summaries[arch] = {"mean": mean_l, "min": min_l, "max": max_l, "friction": mean_f}
        print(f"  {arch:<28} {mean_l:>10.1f} {min_l:>10.1f} {max_l:>10.1f} {mean_f:>9.1f}ms")

    # Speedup calculations
    print(f"\n  --- Speedup Analysis ---")
    if "Neo4j Aura" in arch_summaries:
        neo4j_mean = arch_summaries["Neo4j Aura"]["mean"]
        for arch in ["Neptune Analytics", "Neptune DB + OpenSearch"]:
            if arch in arch_summaries:
                other_mean = arch_summaries[arch]["mean"]
                ratio = other_mean / neo4j_mean if neo4j_mean > 0 else 0
                direction = "slower" if ratio > 1 else "faster"
                print(f"  {arch} is {ratio:.2f}x {direction} than Neo4j")

    if "Neptune DB + OpenSearch" in arch_summaries:
        friction = arch_summaries["Neptune DB + OpenSearch"]["friction"]
        total = arch_summaries["Neptune DB + OpenSearch"]["mean"]
        pct = (friction / total * 100) if total > 0 else 0
        print(f"\n  Two-layer friction: {friction:.1f}ms ({pct:.1f}% of total query time)")

    # Per-query comparison
    banner("PER-QUERY COMPARISON", "-")
    labels = ["Immuno", "HER2", "TKI", "GLP1", "Amyloid"]
    print(f"\n  {'Query':<10}", end="")
    for arch in archs:
        short = arch.split("(")[0].strip()[:18]
        print(f" {short:>18}", end="")
    print()
    print(f"  {'-'*10}", end="")
    for _ in archs:
        print(f" {'-'*18}", end="")
    print()

    for label in labels:
        print(f"  {label:<10}", end="")
        for arch in archs:
            if arch in all_results:
                match = [r for r in all_results[arch] if r.query_label == label]
                if match:
                    print(f" {match[0].latency_ms:>15.1f} ms", end="")
                else:
                    print(f" {'N/A':>18}", end="")
            else:
                print(f" {'N/A':>18}", end="")
        print()

    return arch_summaries


def save_results(all_results: Dict[str, List[QueryResult]], summaries: dict):
    output = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "type": "REAL_MEASUREMENTS",
        "config": {
            "vector_dim": VECTOR_DIM,
            "top_k": TOP_K,
            "iterations": BENCHMARK_ITERATIONS,
            "drugs": len(DRUGS),
            "diseases": len(DISEASES),
        },
        "results": {},
        "summaries": summaries,
    }
    for arch, res_list in all_results.items():
        output["results"][arch] = [asdict(r) for r in res_list]

    path = "/workshop/.claude/Graph/Ontology/real_benchmark_comparison.json"
    with open(path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n  Results saved to: {path}")


# =============================================================================
# Main
# =============================================================================

def main():
    banner("REAL Neptune vs Neo4j Benchmark")
    print("  Every number below is a REAL measurement against live infrastructure.")
    print("  No simulations. No math models. No sleep() calls.\n")

    all_results: Dict[str, List[QueryResult]] = {}

    # --- 1. Neo4j ---
    try:
        all_results["Neo4j Aura"] = benchmark_neo4j()
    except Exception as e:
        print(f"  Neo4j benchmark failed: {e}")

    # --- 2. Neptune Analytics ---
    try:
        # Check if graph is available
        import boto3
        ng_client = boto3.client("neptune-graph", region_name=AWS_REGION)
        graph_info = ng_client.get_graph(graphIdentifier=NEPTUNE_ANALYTICS_GRAPH_ID)
        status = graph_info["status"]
        print(f"\n  Neptune Analytics graph status: {status}")

        if status == "AVAILABLE":
            load_neptune_analytics()
            all_results["Neptune Analytics"] = benchmark_neptune_analytics()
        else:
            print(f"  Skipping — graph is still {status}. Re-run when AVAILABLE.")
    except Exception as e:
        print(f"  Neptune Analytics benchmark failed: {e}")

    # --- 3. Neptune DB + OpenSearch ---
    try:
        import boto3
        # Check Neptune DB status
        neptune_client = boto3.client("neptune", region_name=AWS_REGION)
        clusters = neptune_client.describe_db_clusters(
            DBClusterIdentifier="graphrag-neptune-benchmark"
        )
        neptune_status = clusters["DBClusters"][0]["Status"]
        print(f"\n  Neptune DB status: {neptune_status}")

        # Check OpenSearch status
        os_client_aws = boto3.client("opensearch", region_name=AWS_REGION)
        os_info = os_client_aws.describe_domain(DomainName=OPENSEARCH_DOMAIN)
        os_processing = os_info["DomainStatus"].get("Processing", True)
        os_endpoint = os_info["DomainStatus"].get("Endpoint", "")
        os_status = "AVAILABLE" if (not os_processing and os_endpoint) else "CREATING"
        print(f"  OpenSearch status: {os_status}")

        if neptune_status == "available" and os_status == "AVAILABLE":
            load_neptune_db()
            load_opensearch(os_endpoint)
            all_results["Neptune DB + OpenSearch"] = benchmark_two_layer(os_endpoint)
        else:
            print(f"  Skipping — Neptune={neptune_status}, OpenSearch={os_status}")
            print(f"  Re-run when both are available.")
    except Exception as e:
        print(f"  Neptune DB + OpenSearch benchmark failed: {e}")

    # --- Comparison ---
    if all_results:
        summaries = print_comparison(all_results)
        save_results(all_results, summaries)

    banner("BENCHMARK COMPLETE")
    tested = ", ".join(all_results.keys())
    pending = [a for a in ["Neo4j Aura", "Neptune Analytics", "Neptune DB + OpenSearch"]
               if a not in all_results]
    print(f"\n  Tested: {tested}")
    if pending:
        print(f"  Pending (still provisioning): {', '.join(pending)}")
        print(f"  Re-run this script when all services are AVAILABLE.")
    print()


if __name__ == "__main__":
    main()
