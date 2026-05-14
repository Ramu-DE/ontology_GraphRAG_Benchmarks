#!/bin/bash

echo "============================================================"
echo "Biomedical Knowledge Graph - Full Demonstration"
echo "W3C Semantic Stack (RDF + RDFS + OWL + SPARQL + SHACL)"
echo "============================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

echo "[Step 1/4] Installing dependencies..."
pip install -q rdflib pyshacl pandas python-dateutil

echo "[Step 2/4] Creating output directory..."
mkdir -p output

echo "[Step 3/4] Converting CSV data to RDF triples..."
python3 scripts/csv_to_rdf.py

echo ""
echo "[Step 4/4] Running main demonstration..."
echo ""
python3 main.py

echo ""
echo "============================================================"
echo "Demo complete! Check the following files:"
echo "  - output/biomedical_data.ttl   (RDF data in Turtle format)"
echo "  - output/kg_summary.json       (Statistics and summary)"
echo "============================================================"
