nextflow.enable.dsl = 2

params.sample_sheet = null
params.genome = null
params.mature = null
params.mirna_ref = null
params.output_dir = "./results"
params.threads = 8
params.method = "mirge3"
params.singularity_cache = "/data/singularity"

singularity { enabled = true; autoMounts = true; cacheDir = params.singularity_cache }

log.info """==========================================\n small RNA-seq Pipeline\n==========================================\n Method: ${params.method}\n Output Dir: ${params.output_dir}\n==========================================\n"""

include { MIRDEEP2_PREPROCESS; MIRDEEP2_QUANTIFY; MIRGE3_QUANTIFY } from "${projectDir}/modules/small_rna/mirna_analysis.nf"

workflow {
    Channel.fromPath(params.sample_sheet).splitCsv(header: true, sep: '\t')
        .map { row -> tuple(row.sample_id, file(row.reads)) }
        .set { samples_ch }

    if (params.method == "mirdeep2") {
        MIRDEEP2_PREPROCESS(samples_ch)
        MIRDEEP2_QUANTIFY(MIRDEEP2_PREPROCESS.out.fasta.join(MIRDEEP2_PREPROCESS.out.arf), file(params.mirna_ref), file(params.genome), file(params.mature))
    } else {
        MIRGE3_QUANTIFY(samples_ch)
    }
}

workflow.onComplete { log.info "Pipeline complete: ${workflow.status}" }
