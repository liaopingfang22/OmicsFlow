#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OMICSFLOW_DIR="$(dirname "${SCRIPT_DIR}")"
WORKFLOW_DIR="${OMICSFLOW_DIR}/workflows"
SINGULARITY_CACHE="${SINGULARITY_CACHE:-/data/singularity}"

PIPELINE="${1:-cnv}"
INPUT_FILE="${2:-}"
OUTPUT_DIR="${3:-./results}"

echo "========================================="
echo "  Running OmicsFlow Pipeline"
echo "========================================="
echo "Pipeline: ${PIPELINE}"
echo "Input: ${INPUT_FILE}"
echo "Output: ${OUTPUT_DIR}"
echo "Singularity Cache: ${SINGULARITY_CACHE}"
echo "========================================="

mkdir -p "${OUTPUT_DIR}"

cd "${WORKFLOW_DIR}"

nextflow run main.nf \
    --pipeline "${PIPELINE}" \
    --input "${INPUT_FILE}" \
    --output_dir "${OUTPUT_DIR}" \
    -work-dir "${OUTPUT_DIR}/work" \
    -with-singularity \
    -singularity-cache "${SINGULARITY_CACHE}" \
    -ansi-log false

echo ""
echo "Pipeline complete! Results in: ${OUTPUT_DIR}"
