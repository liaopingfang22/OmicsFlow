nextflow.enable.dsl = 2

params.input = null
params.output_dir = "./results"
params.threads = 8
params.singularity_cache = "/data/singularity"

singularity { enabled = true; autoMounts = true; cacheDir = params.singularity_cache }

log.info """==========================================\n Spatial Transcriptomics Pipeline\n==========================================\n Input: ${params.input}\n Output Dir: ${params.output_dir}\n==========================================\n"""

include { SPATIAL_PREPROCESS; SPATIAL_BUILD_GRAPH; SPATIAL_DOMAINS; SPATIAL_VISUALIZATION } from "${projectDir}/modules/spatial/spatial_analysis.nf"

workflow {
    Channel.fromPath(params.input).set { h5ad_ch }

    SPATIAL_PREPROCESS(h5ad_ch.map { f -> tuple(f.baseName, f) })
    SPATIAL_BUILD_GRAPH(SPATIAL_PREPROCESS.out.h5ad)
    SPATIAL_DOMAINS(SPATIAL_BUILD_GRAPH.out.h5ad)
    SPATIAL_VISUALIZATION(SPATIAL_DOMAINS.out.h5ad)
}

workflow.onComplete { log.info "Pipeline complete: ${workflow.status}" }