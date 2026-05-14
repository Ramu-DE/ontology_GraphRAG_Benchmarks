#!/bin/bash
# Monitor Neptune + OpenSearch Infrastructure Status

echo "╔══════════════════════════════════════════════════════════════════════════════╗"
echo "║              NEPTUNE + OPENSEARCH INFRASTRUCTURE STATUS                      ║"
echo "╚══════════════════════════════════════════════════════════════════════════════╝"
echo ""

# Neptune Cluster
echo "🔵 Neptune Cluster:"
CLUSTER_STATUS=$(aws neptune describe-db-clusters \
    --db-cluster-identifier graphrag-neptune-cluster \
    --region us-west-2 \
    --query 'DBClusters[0].Status' \
    --output text 2>&1)

CLUSTER_ENDPOINT=$(aws neptune describe-db-clusters \
    --db-cluster-identifier graphrag-neptune-cluster \
    --region us-west-2 \
    --query 'DBClusters[0].Endpoint' \
    --output text 2>&1)

echo "   Status: $CLUSTER_STATUS"
echo "   Endpoint: $CLUSTER_ENDPOINT"
echo ""

# Neptune Instance
echo "🔵 Neptune Instance:"
INSTANCE_STATUS=$(aws neptune describe-db-instances \
    --db-instance-identifier graphrag-neptune-instance \
    --region us-west-2 \
    --query 'DBInstances[0].DBInstanceStatus' \
    --output text 2>&1)

echo "   Status: $INSTANCE_STATUS"
echo ""

# OpenSearch
echo "🟠 OpenSearch Domain:"
OPENSEARCH_STATUS=$(aws opensearch describe-domain \
    --domain-name graphrag-opensearch \
    --region us-west-2 \
    --query 'DomainStatus.Processing' \
    --output text 2>&1)

OPENSEARCH_ENDPOINT=$(aws opensearch describe-domain \
    --domain-name graphrag-opensearch \
    --region us-west-2 \
    --query 'DomainStatus.Endpoint' \
    --output text 2>&1)

if [ "$OPENSEARCH_STATUS" = "True" ]; then
    echo "   Status: Creating..."
else
    echo "   Status: Available"
fi
echo "   Endpoint: $OPENSEARCH_ENDPOINT"
echo ""

# Summary
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ "$CLUSTER_STATUS" = "available" ] && [ "$INSTANCE_STATUS" = "available" ] && [ "$OPENSEARCH_STATUS" = "False" ]; then
    echo "✅ ALL RESOURCES READY!"
    echo ""
    echo "Next steps:"
    echo "  1. Load data to Neptune"
    echo "  2. Load data to OpenSearch"
    echo "  3. Run benchmarks"
    echo "  4. Compare with Neo4j results (195ms)"
else
    echo "⏱️  PROVISIONING IN PROGRESS..."
    echo ""
    echo "Estimated time remaining:"
    if [ "$INSTANCE_STATUS" != "available" ]; then
        echo "  - Neptune: 15-25 minutes"
    fi
    if [ "$OPENSEARCH_STATUS" = "True" ]; then
        echo "  - OpenSearch: 10-15 minutes"
    fi
fi

echo ""
echo "Run this script again to check status:"
echo "  bash neptune_infrastructure_status.sh"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
