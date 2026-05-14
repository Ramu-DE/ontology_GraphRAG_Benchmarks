#!/bin/bash

echo "============================================================"
echo "Biomedical Knowledge Graph - Neo4j + AWS Bedrock Demo"
echo "============================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

echo "[Step 1/3] Installing dependencies..."
pip3 install -q neo4j boto3 python-dotenv pandas

echo ""
echo "[Step 2/3] Loading data into Neo4j Aura..."
echo "  Connecting to: neo4j+s://cad612f1.databases.neo4j.io"
echo ""
python3 scripts/csv_to_neo4j.py

echo ""
echo "[Step 3/3] Running AWS Bedrock Agent demo..."
echo ""
python3 aws_agent_neo4j.py

echo ""
echo "============================================================"
echo "Demo complete!"
echo ""
echo "Next steps:"
echo "  1. View graph at: https://console.neo4j.io"
echo "  2. Run interactive mode: python3 aws_agent_neo4j.py --interactive"
echo "  3. Check NEO4J_AWS_README.md for more examples"
echo "============================================================"
