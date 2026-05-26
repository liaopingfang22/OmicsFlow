nextflow.enable.dsl = 2

params.sample_sheet = null
params.fastq_dir = null
params.reference = null
params.gtf = null
params.transcriptome = null
params.output_dir = "./results"
params.threads = 8
params.method = "star_salmon"  // star_salmon, star_only, salmon_only
params.singularity_cache = "/data/singularity"

singularity {
    enabled = true
    autoMounts = true
    cacheDir = params.singularity_cache
}

log.info """
==========================================
 RNA-seq Analysis Pipeline
==========================================
 Sample Sheet:   ${params.sample_sheet}
 FASTQ Dir:      ${params.fastq_dir}
 Reference:      ${params.reference}
 GTF:            ${params.gtf}
 Method:         ${params.method}
 Output Dir:     ${params.output_dir}
 Threads:        ${params.threads}
==========================================
"""

include { FASTQC; MULTIQC } from "${projectDir}/modules/quality_control/qc.nf"
include { TRIM_ADAPTERS } from "${projectDir}/modules/quality_control/qc.nf"
include { STAR_INDEX; STAR_ALIGN } from "${projectDir}/modules/read_alignment/star_alignment.nf"
include { SALMON_INDEX; SALMON_QUANT; SALMON_MERGE } from "${projectDir}/modules/rnaseq_quant/salmon_quant.nf"
include { SAMTOOLS_INDEX_TUPLE; SAMTOOLS_STATS; SAMTOOLS_FLAGSTAT } from "${projectDir}/modules/utils/samtools.nf"
include { EDGER_ANALYSIS } from "${projectDir}/modules/differential_expression/edger_analysis.nf"

workflow {
    // Parse sample sheet: sample_name, read1, read2
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

    // Trim adapters
    TRIM_ADAPTERS(fastq_ch)
    trimmed_ch = TRIM_ADAPTERS.out.trimmed
        .map { sid, files -> 
            def r1 = files instanceof List ? files[0] : files
            def r2 = files instanceof List ? files[1] : null
            tuple(sid, r1, r2)
        }

    if (params.method == "star_salmon" || params.method == "star_only") {
        // STAR alignment
        STAR_INDEX(file(params.reference), file(params.gtf))
        STAR_ALIGN(trimmed_ch, STAR_INDEX.out.index)

        // BAM QC
        SAMTOOLS_STATS(STAR_ALIGN.out.bam)
        SAMTOOLS_FLAGSTAT(STAR_ALIGN.out.bam)

        if (params.method == "star_salmon") {
            // Also run Salmon for TPM quantification
            SALMON_INDEX(file(params.transcriptome))
            SALMON_QUANT(trimmed_ch, SALMON_INDEX.out.index)
            SALMON_MERGE(SALMON_QUANT.out.quant.collect())
        }
    } else if (params.method == "salmon_only") {
        // Alignment-free quantification
        SALMON_INDEX(file(params.transcriptome))
        SALMON_QUANT(trimmed_ch, SALMON_INDEX.out.index)
        SALMON_MERGE(SALMON_QUANT.out.quant.collect())
    }

    // Collect QC reports
    MULTIQC(FASTQC.out.zip.collect())
}

workflow.onComplete {
    log.info """
    ==========================================
     RNA-seq Pipeline Complete
     Status: ${workflow.status}
     Duration: ${workflow.duration}
     Results: ${params.output_dir}
    ==========================================
    """
}