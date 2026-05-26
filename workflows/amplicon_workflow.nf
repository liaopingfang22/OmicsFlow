nextflow.enable.dsl = 2

params.sample_sheet = null
params.silva_ref = null
params.metadata = null
params.output_dir = "./results"
params.threads = 8
params.skip_diversity = false
params.singularity_cache = "/data/singularity"

singularity {
    enabled = true
    autoMounts = true
    cacheDir = params.singularity_cache
}

log.info """
==========================================
 16S/ITS Amplicon Analysis Pipeline
==========================================
 Sample Sheet:   ${params.sample_sheet}
 Silva Ref:      ${params.silva_ref}
 Metadata:       ${params.metadata}
 Output Dir:     ${params.output_dir}
==========================================
"""

include { DADA2_FILTER_AND_TRIM; DADA2_LEARN_ERRORS; DADA2_DADA; DADA2_MAKE_TABLE; DADA2_ASSIGN_TAXONOMY; PHYLOSEQ_ANALYSIS } from "${projectDir}/modules/amplicon/dada2_analysis.nf"

workflow {
    Channel
        .fromPath(params.sample_sheet)
        .splitCsv(header: true, sep: '\t')
        .map { row -> tuple(row.sample_id, [file(row.read1), file(row.read2)]) }
        .set { samples_ch }

    DADA2_FILTER_AND_TRIM(samples_ch)
    DADA2_LEARN_ERRORS(DADA2_FILTER_AND_TRIM.out.filtered.map { s, r1, r2 -> [r1, r2] }.flatten().collect())
    DADA2_DADA(DADA2_FILTER_AND_TRIM.out.filtered, DADA2_LEARN_ERRORS.out.err_R1.first(), DADA2_LEARN_ERRORS.out.err_R2.first())
    DADA2_MAKE_TABLE(DADA2_DADA.out.merged.collect())
    DADA2_ASSIGN_TAXONOMY(DADA2_MAKE_TABLE.out.seqtab_nochim, file(params.silva_ref))

    if (!params.skip_diversity && params.metadata) {
        PHYLOSEQ_ANALYSIS(DADA2_MAKE_TABLE.out.asv_table, DADA2_ASSIGN_TAXONOMY.out.taxa, file(params.metadata))
    }
}

workflow.onComplete {
    log.info "Pipeline complete: ${workflow.status}"
}