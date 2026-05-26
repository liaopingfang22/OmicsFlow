nextflow.enable.dsl = 2

params.sample_sheet = null
params.fasta = null
params.mq_params = null
params.method = "dda"
params.output_dir = "./results"
params.threads = 8
params.singularity_cache = "/data/singularity"

singularity { enabled = true; autoMounts = true; cacheDir = params.singularity_cache }

log.info """==========================================\n Proteomics Analysis Pipeline\n==========================================\n Method: ${params.method}\n Output Dir: ${params.output_dir}\n==========================================\n"""

include { MAXQUANT_SEARCH; DIANN_ANALYSIS } from "${projectDir}/modules/proteomics/proteomics_analysis.nf"

workflow {
    if (params.method == "dda") {
        Channel.fromPath("${params.sample_sheet}").splitCsv(header: true, sep: '\t')
            .map { row -> file(row.mzml) }
            .collect()
            .set { mzml_ch }
        MAXQUANT_SEARCH(mzml_ch, file(params.fasta), file(params.mq_params))
    } else {
        Channel.fromPath("${params.sample_sheet}").splitCsv(header: true, sep: '\t')
            .map { row -> file(row.mzml) }
            .collect()
            .set { mzml_ch }
        DIANN_ANALYSIS(mzml_ch, file(params.fasta))
    }
}

workflow.onComplete { log.info "Pipeline complete: ${workflow.status}" }
