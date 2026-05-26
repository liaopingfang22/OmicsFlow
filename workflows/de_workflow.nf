nextflow.enable.dsl = 2

params.count_matrix = null
params.sample_sheet = null
params.output_dir = "./results"
params.method = "edger"
params.threads = 4
params.singularity_image = "bioconductor.sif"

singularity {
    enabled = true
    autoMounts = true
    cacheDir = "${params.singularity_cache ?: '/data/singularity'}"
}

log.info """
==========================================
 Differential Expression Analysis Pipeline
==========================================
 Count Matrix:  ${params.count_matrix}
 Sample Sheet:   ${params.sample_sheet}
 Method:         ${params.method}
 Output Dir:     ${params.output_dir}
 Singularity:    ${params.singularity_image}
==========================================
"""

include { EDGER_ANALYSIS } from "${projectDir}/modules/differential_expression/edger_analysis.nf"
include { DESEQ2_ANALYSIS } from "${projectDir}/modules/differential_expression/deseq2_analysis.nf"

workflow {
    main:
        counts = channel.fromPath(params.count_matrix)
        samples = params.sample_sheet ? channel.fromPath(params.sample_sheet) : null
        
        if (params.method == "edger") {
            EDGER_ANALYSIS(counts, samples)
            results = EDGER_ANALYSIS.out.results
        } else if (params.method == "deseq2") {
            DESEQ2_ANALYSIS(counts, samples)
            results = DESEQ2_ANALYSIS.out.results
        } else {
            log.error "Unknown method: ${params.method}"
            exit 1
        }
    
    emit:
        results = results
}
