nextflow.enable.dsl = 2

params.sample_sheet = null
params.kraken2_db = null
params.output_dir = "./results"
params.threads = 8
params.skip_bracken = false
params.singularity_cache = "/data/singularity"

singularity {
    enabled = true
    autoMounts = true
    cacheDir = params.singularity_cache
}

log.info """
==========================================
 Metagenomics Classification Pipeline
==========================================
 Sample Sheet:   ${params.sample_sheet}
 Kraken2 DB:     ${params.kraken2_db}
 Output Dir:     ${params.output_dir}
 Threads:        ${params.threads}
 Skip Bracken:   ${params.skip_bracken}
==========================================
"""

include { FASTQC; MULTIQC } from "${projectDir}/modules/quality_control/qc.nf"
include { KRAKEN2_CLASSIFY_PAIRED; KRAKEN2_MERGE_REPORTS; BRACKEN_ESTIMATE } from "${projectDir}/modules/metagenomics/kraken2_classify.nf"

workflow {
    // Parse sample sheet
    Channel
        .fromPath(params.sample_sheet)
        .splitCsv(header: true, sep: '\t')
        .map { row -> tuple(row.sample_id, file(row.read1), file(row.read2)) }
        .set { samples_ch }

    // QC
    samples_ch
        .map { sid, r1, r2 -> tuple(sid, [r1, r2]) }
        .set { fastq_ch }
    FASTQC(fastq_ch)
    MULTIQC(FASTQC.out.zip.collect())

    // Kraken2 classification
    kraken2_db = file(params.kraken2_db)
    KRAKEN2_CLASSIFY_PAIRED(samples_ch, kraken2_db)

    // Merge reports
    KRAKEN2_MERGE_REPORTS(KRAKEN2_CLASSIFY_PAIRED.out.report.map { sid, r -> r }.collect())

    // Bracken abundance estimation
    if (!params.skip_bracken) {
        BRACKEN_ESTIMATE(KRAKEN2_CLASSIFY_PAIRED.out.report, kraken2_db)
    }
}

workflow.onComplete {
    log.info """
    ==========================================
     Metagenomics Pipeline Complete
     Status: ${workflow.status}
     Duration: ${workflow.duration}
     Results: ${params.output_dir}
    ==========================================
    """
}