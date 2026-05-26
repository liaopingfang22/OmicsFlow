#!/bin/bash

set -e

BASE_DIR="/public/xalab/liaopingfang/pipeline_test/OmicsFlow"
DATA_DIR="/data"
SINGULARITY_CACHE="${SINGULARITY_CACHE:-/data/singularity}"

echo "========================================="
echo "  OmicsFlow Deployment Script"
echo "========================================="

mkdir -p "${DATA_DIR}/output"
mkdir -p "${DATA_DIR}/storage"
mkdir -p "${DATA_DIR}/singularity"
mkdir -p "${BASE_DIR}/workflows"
mkdir -p "${BASE_DIR}/modules"

cd "${BASE_DIR}"

echo ""
echo "[1/4] Building Singularity containers..."
cd containers

if [ ! -f "omicsflow.sif" ]; then
    echo "Building omicsflow.sif..."
    singularity build omicsflow.sif omicsflow.def
fi

if [ ! -f "cnvkit.sif" ]; then
    echo "Building cnvkit.sif..."
    singularity build cnvkit.sif cnvkit.def
fi

if [ ! -f "bioconductor.sif" ]; then
    echo "Building bioconductor.sif..."
    singularity build bioconductor.sif bioconductor.def
fi

if [ ! -f "qc_tools.sif" ]; then
    echo "Building qc_tools.sif..."
    singularity build qc_tools.sif qc_tools.def
fi

echo ""
echo "[2/4] Initializing database..."
cd "${BASE_DIR}"
if command -v psql &> /dev/null; then
    PGPASSWORD=postgres psql -h localhost -U postgres -c "CREATE DATABASE omicsflow;" 2>/dev/null || true
    psql -h localhost -U postgres -d omicsflow -f database/schema.sql
fi

echo ""
echo "[3/4] Starting backend services..."
cd backend
if [ ! -d "venv" ]; then
    python3 -m venv venv
    source venv/bin/activate
    pip install -e .
else
    source venv/bin/activate
fi

nohup uvicorn api.main:app --host 0.0.0.0 --port 8000 > /tmp/omicsflow_backend.log 2>&1 &
BACKEND_PID=$!

echo ""
echo "[4/4] Starting frontend..."
cd "${BASE_DIR}/frontend"
if [ ! -d "node_modules" ]; then
    npm install
fi
npm run dev &
FRONTEND_PID=$!

echo ""
echo "========================================="
echo "  OmicsFlow Started!"
echo "========================================="
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "Singularity Cache: ${SINGULARITY_CACHE}"
echo "========================================="
