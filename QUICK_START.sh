#!/bin/bash
# Quick Start Script for Real GraphRAG Benchmarks
# Run this to execute real performance tests on Neo4j Aura

set -e  # Exit on error

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║        Real GraphRAG Benchmark - Quick Start                  ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check Python
echo "🐍 Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+"
    exit 1
fi
echo "✅ Python $(python3 --version | cut -d' ' -f2) found"

# Check pip
echo ""
echo "📦 Checking pip..."
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip not found. Please install pip"
    exit 1
fi
echo "✅ pip found"

# Install dependencies
echo ""
echo "📥 Installing dependencies..."
pip3 install --quiet neo4j python-dotenv 2>/dev/null || {
    echo "⚠️  Some packages may already be installed"
}
echo "✅ Dependencies ready"

# Check .env file
echo ""
echo "🔐 Checking credentials..."
if [ ! -f ".env" ]; then
    echo "❌ .env file not found"
    echo "Please create .env with:"
    echo "  NEO4J_URI=neo4j+s://cad612f1.databases.neo4j.io"
    echo "  NEO4J_USER=neo4j"
    echo "  NEO4J_PASSWORD=your-password"
    exit 1
fi

if ! grep -q "NEO4J_URI" .env; then
    echo "❌ NEO4J_URI not found in .env"
    exit 1
fi

echo "✅ Credentials found"

# Test connection
echo ""
echo "🔌 Testing Neo4j connection..."
python3 -c "
from dotenv import load_dotenv
import os
from neo4j import GraphDatabase

load_dotenv()
uri = os.getenv('NEO4J_URI')
user = os.getenv('NEO4J_USER', 'neo4j')
password = os.getenv('NEO4J_PASSWORD')

try:
    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        result = session.run('RETURN 1 as n')
        assert result.single()['n'] == 1
    driver.close()
    print('✅ Connection successful')
except Exception as e:
    print(f'❌ Connection failed: {e}')
    exit(1)
" || exit 1

# Load data
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "📊 STEP 1: Load Sample Data"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "This will load 10 drugs, 7 diseases, 8 genes with embeddings"
echo "and create a vector index for similarity search."
echo ""
read -p "Continue? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
    echo "Cancelled"
    exit 0
fi

echo ""
python3 neo4j_data_loader.py

# Run benchmarks
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "🚀 STEP 2: Run Real Benchmarks"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "This will execute actual Cypher queries and measure real latency."
echo ""
read -p "Continue? (yes/no): " -r
if [[ ! $REPLY =~ ^[Yy]es$ ]]; then
    echo "Skipped benchmarks"
    exit 0
fi

echo ""
python3 real_benchmark_implementation.py

# Show results
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "📈 RESULTS"
echo "════════════════════════════════════════════════════════════════"
echo ""

if [ -f "real_benchmark_results.json" ]; then
    echo "✅ Results saved to: real_benchmark_results.json"
    echo ""
    echo "View results:"
    echo "  cat real_benchmark_results.json | python3 -m json.tool"
    echo ""
    
    # Extract key metrics if jq is available
    if command -v jq &> /dev/null; then
        echo "Key Metrics:"
        echo "────────────────────────────────────────────────────────────────"
        jq -r '.results[] | "\(.operation): \(.latency_ms)ms"' real_benchmark_results.json 2>/dev/null || true
    fi
else
    echo "⚠️  Results file not found"
fi

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ BENCHMARK COMPLETE"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Next steps:"
echo "  • Scale up: python3 neo4j_data_generator.py --scale 10000"
echo "  • Re-benchmark: python3 real_benchmark_implementation.py"
echo "  • Read guide: cat REAL_BENCHMARK_SETUP.md"
echo ""
