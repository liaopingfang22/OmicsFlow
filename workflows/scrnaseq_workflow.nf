nextflow.enable.dsl = 2

params.sample_sheet = null
params.reference_genome = null
params.model_path = "NO_MODEL"
params.skip_doublet = false
params.skip_annotation = false
params.skip_trajectory = false
params.output_dir = "./results"
params.threads = 8
params.singularity_cache = "/data/singularity"

singularity { enabled = true; autoMounts = true; cacheDir = params.singularity_cache }

log.info """==========================================
 Single-Cell RNA-seq Analysis Pipeline
==========================================
 Sample Sheet: ${params.sample_sheet}
 Reference:    ${params.reference_genome}
 Doublet:      ${!params.skip_doublet}
 Annotation:   ${!params.skip_annotation}
 Trajectory:   ${!params.skip_trajectory}
==========================================
"""

include { SCANPY_PREPROCESS; SCANPY_CLUSTER; SCANPY_MARKER_HEATMAP; DOUBLET_DETECTION; CELL_TYPE_ANNOTATION; TRAJECTORY_INFERENCE; MULTI_SAMPLE_INTEGRATION } from "${projectDir}/modules/single_cell/scanpy_analysis.nf"

workflow {
    Channel.fromPath(params.sample_sheet).splitCsv(header: true, sep: '\t')
        .map { row -> tuple(row.sample_id, file(row.h5ad)) }
        .set { samples_ch }

    // Step 1: Preprocessing (QC + filtering + normalization)
    SCANPY_PREPROCESS(samples_ch)

    // Step 2: Optional doublet detection
    if (!params.skip_doublet) {
        DOUBLET_DETECTION(SCANPY_PREPROCESS.out.h5ad)
        preprocessed = DOUBLET_DETECTION.out.h5ad
    } else {
        preprocessed = SCANPY_PREPROCESS.out.h5ad
    }

    // Step 3: Clustering + marker genes
    SCANPY_CLUSTER(preprocessed)
    SCANPY_MARKER_HEATMAP(SCANPY_CLUSTER.out.h5ad)

    // Step 4: Optional cell type annotation
    if (!params.skip_annotation) {
        CELL_TYPE_ANNOTATION(SCANPY_CLUSTER.out.h5ad, file(params.model_path))
    }

    // Step 5: Optional trajectory inference
    if (!params.skip_trajectory) {
        TRAJECTORY_INFERENCE(SCANPY_CLUSTER.out.h5ad)
    }
}

workflow.onComplete { log.info "Pipeline complete: ${workflow.status}" }