// ============================================================================
// NEO4J CYPHER QUERY EXAMPLES
// Biomedical Knowledge Graph Queries
// ============================================================================
//
// These queries can be run in Neo4j Browser at: https://console.neo4j.io
// Or via the Python driver in the scripts
// ============================================================================

// ────────────────────────────────────────────────────────────────────────────
// 1. DATABASE INSPECTION
// ────────────────────────────────────────────────────────────────────────────

// Count all nodes
MATCH (n) RETURN count(n) as totalNodes;

// Count all relationships
MATCH ()-[r]->() RETURN count(r) as totalRelationships;

// Show all node labels
CALL db.labels() YIELD label
RETURN label ORDER BY label;

// Show all relationship types
CALL db.relationshipTypes() YIELD relationshipType
RETURN relationshipType ORDER BY relationshipType;

// Get count per label
MATCH (n)
RETURN labels(n)[0] as label, count(*) as count
ORDER BY count DESC;

// Show database info
CALL dbms.components() YIELD name, versions, edition
RETURN name, versions, edition;

// List all indexes
SHOW INDEXES;

// List all constraints
SHOW CONSTRAINTS;


// ────────────────────────────────────────────────────────────────────────────
// 2. BASIC NODE QUERIES
// ────────────────────────────────────────────────────────────────────────────

// Get all drugs
MATCH (d:Drug)
RETURN d.name, d.mechanism, d.description
LIMIT 10;

// Get all diseases
MATCH (dis:Disease)
RETURN dis.name, dis.code, dis.category
LIMIT 10;

// Get all genes
MATCH (g:Gene)
RETURN g.symbol, g.name, g.chromosome
LIMIT 10;

// Sample random nodes
MATCH (n)
WITH n, rand() as random
ORDER BY random
LIMIT 5
RETURN labels(n) as type, properties(n) as props;


// ────────────────────────────────────────────────────────────────────────────
// 3. RELATIONSHIP QUERIES
// ────────────────────────────────────────────────────────────────────────────

// Find all drug-disease relationships
MATCH (d:Drug)-[r:TREATS]->(dis:Disease)
RETURN d.name as drug,
       dis.name as disease,
       r.efficacyRate as efficacy
ORDER BY r.efficacyRate DESC
LIMIT 20;

// Find drugs by mechanism
MATCH (d:Drug)
WHERE d.mechanism CONTAINS 'inhibitor'
RETURN d.name, d.mechanism, d.description
ORDER BY d.name;

// Find diseases by category
MATCH (dis:Disease)
WHERE dis.category = 'cancer'
RETURN dis.name, dis.code
ORDER BY dis.name;


// ────────────────────────────────────────────────────────────────────────────
// 4. GRAPH TRAVERSAL (Multi-hop)
// ────────────────────────────────────────────────────────────────────────────

// Gene → Disease → Drug pathway
MATCH (g:Gene)-[:ASSOCIATED_WITH]->(dis:Disease)<-[t:TREATS]-(d:Drug)
RETURN g.symbol as gene,
       dis.name as disease,
       d.name as drug,
       d.mechanism as mechanism
ORDER BY g.symbol, dis.name
LIMIT 20;

// Find all paths from a specific drug
MATCH path = (d:Drug {name: 'Pembrolizumab'})-[*1..2]->()
RETURN path
LIMIT 10;

// Find drugs treating diseases associated with EGFR gene
MATCH (g:Gene {symbol: 'EGFR'})-[:ASSOCIATED_WITH]->(dis:Disease)<-[t:TREATS]-(d:Drug)
RETURN d.name as drug,
       d.mechanism as mechanism,
       dis.name as disease,
       t.efficacyRate as efficacy
ORDER BY t.efficacyRate DESC;

// Find common diseases treated by multiple drugs
MATCH (d1:Drug)-[:TREATS]->(dis:Disease)<-[:TREATS]-(d2:Drug)
WHERE d1.name < d2.name
RETURN dis.name as disease,
       d1.name as drug1,
       d2.name as drug2
ORDER BY dis.name
LIMIT 10;


// ────────────────────────────────────────────────────────────────────────────
// 5. CLINICAL TRIAL QUERIES
// ────────────────────────────────────────────────────────────────────────────

// Find all trials for a specific drug
MATCH (t:ClinicalTrial)-[:INVESTIGATES]->(d:Drug {name: 'Pembrolizumab'})
MATCH (t)-[:STUDIES]->(dis:Disease)
RETURN t.title as trial,
       t.phase as phase,
       t.status as status,
       t.enrollment as enrollment,
       dis.name as disease
ORDER BY t.enrollment DESC;

// Find large trials (enrollment > 1000)
MATCH (t:ClinicalTrial)-[:INVESTIGATES]->(d:Drug)
MATCH (t)-[:STUDIES]->(dis:Disease)
WHERE t.enrollment > 1000
RETURN t.title as trial,
       t.phase as phase,
       t.enrollment as enrollment,
       d.name as drug,
       dis.name as disease
ORDER BY t.enrollment DESC;

// Trials by phase
MATCH (t:ClinicalTrial)
RETURN t.phase as phase, count(*) as count
ORDER BY phase;


// ────────────────────────────────────────────────────────────────────────────
// 6. PROTEIN TARGET QUERIES
// ────────────────────────────────────────────────────────────────────────────

// Find all drug-protein relationships
MATCH (d:Drug)-[r:TARGETS]->(p:Protein)
RETURN d.name as drug,
       p.name as protein,
       p.proteinClass as proteinClass,
       r.bindingAffinity as affinity,
       r.mechanismType as mechanism
LIMIT 20;

// Find drugs targeting the same protein
MATCH (d1:Drug)-[:TARGETS]->(p:Protein)<-[:TARGETS]-(d2:Drug)
WHERE d1.name < d2.name
RETURN p.name as protein,
       p.proteinClass as proteinClass,
       collect(d1.name) + collect(d2.name) as drugs
LIMIT 10;

// Find proteins by cellular location
MATCH (p:Protein)
WHERE p.cellularLocation = 'membrane'
RETURN p.name, p.proteinClass, p.uniprotId
LIMIT 10;


// ────────────────────────────────────────────────────────────────────────────
// 7. ADVERSE EVENT QUERIES
// ────────────────────────────────────────────────────────────────────────────

// Find adverse events for a drug
MATCH (d:Drug)<-[:INVESTIGATES]-(t:ClinicalTrial)-[:REPORTS]->(e:AdverseEvent)
WHERE d.name = 'Pembrolizumab'
RETURN DISTINCT e.name as event,
       e.severity as severity,
       e.category as category,
       e.frequency as frequency
ORDER BY e.severity DESC, e.frequency DESC;

// Find severe adverse events across all drugs
MATCH (d:Drug)<-[:INVESTIGATES]-(t:ClinicalTrial)-[:REPORTS]->(e:AdverseEvent)
WHERE e.severity = 'severe'
RETURN e.name as event,
       e.category as category,
       collect(DISTINCT d.name) as drugs
ORDER BY size(drugs) DESC;


// ────────────────────────────────────────────────────────────────────────────
// 8. BIOMARKER QUERIES
// ────────────────────────────────────────────────────────────────────────────

// Find biomarkers that predict drug response
MATCH (b:Biomarker)-[:PREDICTS_RESPONSE]->(d:Drug)
RETURN b.name as biomarker,
       b.type as type,
       b.clinicalSignificance as significance,
       d.name as drug
ORDER BY b.name;

// Find biomarkers by type
MATCH (b:Biomarker)
WHERE b.type = 'genetic'
RETURN b.name, b.clinicalSignificance, b.measurementUnit;


// ────────────────────────────────────────────────────────────────────────────
// 9. RESEARCH NETWORK QUERIES
// ────────────────────────────────────────────────────────────────────────────

// Find high-impact researchers
MATCH (r:Researcher)-[:AFFILIATED_WITH]->(i:Institution)
WHERE r.hIndex >= 70
RETURN r.name as researcher,
       r.specialization as specialization,
       r.hIndex as hIndex,
       r.totalPublications as publications,
       i.name as institution
ORDER BY r.hIndex DESC;

// Find researchers by specialization
MATCH (r:Researcher)
WHERE r.specialization CONTAINS 'Oncology'
RETURN r.name, r.hIndex, r.totalPublications
ORDER BY r.hIndex DESC
LIMIT 10;

// Find research papers by drug
MATCH (p:ResearchPaper)-[:MENTIONS_DRUG]->(d:Drug {name: 'Pembrolizumab'})
MATCH (p)-[:AUTHORED_BY]->(r:Researcher)
RETURN p.title as paper,
       p.journal as journal,
       p.year as year,
       collect(r.name) as authors
ORDER BY p.year DESC
LIMIT 10;

// Find institutional collaborations
MATCH (r1:Researcher)-[:AFFILIATED_WITH]->(i:Institution)<-[:AFFILIATED_WITH]-(r2:Researcher)
WHERE r1 <> r2
WITH i, collect(DISTINCT r1.name) as researchers
WHERE size(researchers) > 1
RETURN i.name as institution,
       size(researchers) as researcherCount,
       researchers[0..5] as sampleResearchers
ORDER BY researcherCount DESC
LIMIT 10;


// ────────────────────────────────────────────────────────────────────────────
// 10. ANALYTICAL QUERIES
// ────────────────────────────────────────────────────────────────────────────

// Drug distribution by mechanism
MATCH (d:Drug)
RETURN d.mechanism as mechanism,
       count(*) as drugCount,
       collect(d.name)[0..5] as sampleDrugs
ORDER BY drugCount DESC;

// Most researched diseases (by trial count)
MATCH (t:ClinicalTrial)-[:STUDIES]->(dis:Disease)
RETURN dis.name as disease,
       count(t) as trialCount
ORDER BY trialCount DESC
LIMIT 10;

// Drug efficacy statistics
MATCH (d:Drug)-[t:TREATS]->(dis:Disease)
RETURN d.name as drug,
       count(dis) as diseasesTargeted,
       avg(t.efficacyRate) as avgEfficacy,
       max(t.efficacyRate) as maxEfficacy
ORDER BY avgEfficacy DESC
LIMIT 10;

// Gene-disease associations count
MATCH (g:Gene)-[:ASSOCIATED_WITH]->(dis:Disease)
RETURN g.symbol as gene,
       count(dis) as diseaseCount,
       collect(dis.name)[0..3] as sampleDiseases
ORDER BY diseaseCount DESC
LIMIT 10;


// ────────────────────────────────────────────────────────────────────────────
// 11. VECTOR SEARCH (Requires vector index)
// ────────────────────────────────────────────────────────────────────────────

// Create vector index (run once)
CREATE VECTOR INDEX drug_embedding_vector IF NOT EXISTS
FOR (d:Drug)
ON d.embedding
OPTIONS {
    indexConfig: {
        `vector.dimensions`: 384,
        `vector.similarity_function`: 'cosine'
    }
};

// Vector similarity search (requires query vector from Python)
// Use in Python with generated embedding:
// CALL db.index.vector.queryNodes('drug_embedding_vector', 10, $queryVector)
// YIELD node, score
// RETURN node.name, node.description, score
// ORDER BY score DESC
// LIMIT 10


// ────────────────────────────────────────────────────────────────────────────
// 12. FULL-TEXT SEARCH
// ────────────────────────────────────────────────────────────────────────────

// Create full-text index
CREATE FULLTEXT INDEX drugSearch IF NOT EXISTS
FOR (d:Drug)
ON EACH [d.name, d.description, d.mechanism];

// Search drugs by keyword
CALL db.index.fulltext.queryNodes('drugSearch', 'PD-1 inhibitor')
YIELD node, score
RETURN node.name, node.mechanism, score
ORDER BY score DESC
LIMIT 10;


// ────────────────────────────────────────────────────────────────────────────
// 13. GRAPH ALGORITHMS (Requires GDS library)
// ────────────────────────────────────────────────────────────────────────────

// PageRank to find important drugs
CALL gds.pageRank.stream('drug-network')
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).name AS drug, score
ORDER BY score DESC
LIMIT 10;

// Community detection
CALL gds.louvain.stream('drug-network')
YIELD nodeId, communityId
RETURN gds.util.asNode(nodeId).name AS drug, communityId
ORDER BY communityId, drug;


// ────────────────────────────────────────────────────────────────────────────
// 14. DATA MANAGEMENT
// ────────────────────────────────────────────────────────────────────────────

// Count nodes by label
MATCH (n)
RETURN labels(n)[0] as label, count(*) as count
ORDER BY count DESC;

// Count relationships by type
MATCH ()-[r]->()
RETURN type(r) as relationshipType, count(*) as count
ORDER BY count DESC;

// Find orphan nodes (no relationships)
MATCH (n)
WHERE NOT (n)-[]-()
RETURN labels(n) as label, count(n) as orphanCount;

// Check for duplicate nodes
MATCH (d:Drug)
WITH d.name as name, collect(d) as nodes
WHERE size(nodes) > 1
RETURN name, size(nodes) as duplicateCount;


// ────────────────────────────────────────────────────────────────────────────
// 15. PERFORMANCE QUERIES
// ────────────────────────────────────────────────────────────────────────────

// Explain query execution plan
EXPLAIN
MATCH (d:Drug)-[:TREATS]->(dis:Disease)
WHERE d.mechanism CONTAINS 'inhibitor'
RETURN d.name, dis.name;

// Profile query with statistics
PROFILE
MATCH (d:Drug)-[:TREATS]->(dis:Disease)
WHERE d.mechanism CONTAINS 'inhibitor'
RETURN d.name, dis.name
LIMIT 10;

// Check active queries
CALL dbms.listQueries()
YIELD query, elapsedTimeMillis, cpuTimeMillis
WHERE elapsedTimeMillis > 1000
RETURN query, elapsedTimeMillis, cpuTimeMillis
ORDER BY elapsedTimeMillis DESC;


// ────────────────────────────────────────────────────────────────────────────
// 16. USEFUL ADMIN QUERIES
// ────────────────────────────────────────────────────────────────────────────

// Show database statistics
CALL dbms.queryJmx('org.neo4j:instance=kernel#0,name=Store file sizes')
YIELD attributes
RETURN attributes;

// Clear all data (DANGEROUS - use with caution!)
// MATCH (n) DETACH DELETE n;

// Delete specific label
// MATCH (n:OldLabel) DETACH DELETE n;

// Backup sample data before deletion
MATCH (n:Drug)
RETURN properties(n) as drugProperties
LIMIT 100;


// ============================================================================
// END OF QUERY EXAMPLES
// ============================================================================
//
// To run these queries:
// 1. Visit https://console.neo4j.io
// 2. Login with your credentials
// 3. Copy and paste queries into the query editor
// 4. Or use Python driver with: session.run(query, parameters)
// ============================================================================
