#!/bin/bash
# Import example documents for testing
# Author: Marcus A. Sanchez
# Date: 2025-11-12

set -e

echo "Importing example documents..."

# Create data directories
mkdir -p data/sources
mkdir -p data/cases
mkdir -p data/statutes

# Create sample documents
cat > data/sources/example1.txt << 'EOF'
SAMPLE STATUTE - Example 1

This is an example legal document for testing purposes.
It contains multiple sentences. Some sentences are longer than others.
This document may reference 42 U.S.C. 1983 as an example citation.

Effective date: January 1, 2020
Source: Example Legal Database
EOF

cat > data/sources/example2.txt << 'EOF'
SAMPLE CONTRACT - Example 2

This sample contract demonstrates the ingestion capabilities.
All parties agree to the terms outlined herein.
See 18 U.S.C. 1001 for relevant federal statutes.

Signed: December 15, 2019
Source: Example Repository
EOF

echo "Created 2 example documents in data/sources/"
echo ""
echo "To ingest these documents, run:"
echo "  python -m oraculus_di_auditor.cli ingest --source data/sources"
