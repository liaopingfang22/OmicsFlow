#!/bin/bash

set -e

SINGULARITY_CACHE="${SINGULARITY_CACHE:-/data/singularity}"

echo "========================================="
echo "  Building Singularity Containers"
echo "========================================="

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTAINER_DIR="$(dirname "${SCRIPT_DIR}")/containers"
OUTPUT_DIR="$(dirname "${SCRIPT_DIR}")"

mkdir -p "${SINGULARITY_CACHE}"

cd "${CONTAINER_DIR}"

build_container() {
    local name=$1
    local def=$2
    
    if [ ! -f "${OUTPUT_DIR}/${name}.sif" ]; then
        echo "Building ${name}.sif..."
        SINGULARITY_CACHEDIR="${SINGULARITY_CACHE}" \
        singularity build "${OUTPUT_DIR}/${name}.sif" "${def}"
        echo "${name}.sif built successfully"
    else
        echo "${name}.sif already exists, skipping..."
    fi
}

build_container "omicsflow" "omicsflow.def"
build_container "cnvkit" "cnvkit.def"
build_container "bioconductor" "bioconductor.def"
build_container "qc_tools" "qc_tools.def"

echo ""
echo "========================================="
echo "  All containers built!"
echo "  Cache location: ${SINGULARITY_CACHE}"
echo "========================================="
