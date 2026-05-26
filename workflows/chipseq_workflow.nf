nextflow.enable.dsl = 2

params.sample_sheet = null
params.reference = null
params.bt2_index = null
params.gtf = null
params.peak_type = "narrow"
params.output_dir = "./results"
params.threads = 8
params.singularity_cache = "/data/singularity"

singularity { enabled = true; autoMounts = true; cacheDir = params.singularity_cache }

log.info """==========================================\n ChIP-seq Analysis Pipeline\n==========================================\n Peak Type: ${params.peak_type}\n Output Dir: ${params.output_dir}\n==========================================\n"""

include { FASTQC; MULTIQC } from "${projectDir}/modules/quality_control/qc.nf"
include { BOWTIE2_INDEX; BOWTIE2_ALIGN; MACS3_CALLPEAK; ANNOTATE_PEAKS; FIND_MOTIFS } from "${projectDir}/modules/chipseq/chipseq_analysis.nf"
include { SAMTOOLS_INDEX_TUPLE } from "${projectDir}/modules/utils/samtools.nf"

workflow {
    Channel.fromPath(params.sample_sheet).splitCsv(header: true, sep: '\t')
        .map { row -> tuple(row.sample_id, file(row.reads)) }
        .set { samples_ch }

    FASTQC(samples_ch.map { s, r -> tuple(s, [r]) })
    MULTIQC(FASTQC.out.zip.collect())

    BOWTIE2_ALIGN(samples_ch, file(params.bt2_index), file(params.reference))
    SAMTOOLS_INDEX_TUPLE(BOWTIE2_ALIGN.out.bam)
    MACS3_CALLPEAK(BOWTIE2_ALIGN.out.bam, params.peak_type)
    ANNOTATE_PEAKS(MACS3_CALLPEAK.out.peaks.map { s, p -> p }.collect(), file(params.gtf))
    FIND_MOTIFS(MACS3_CALLPEAK.out.summits.map { s, p -> p }.collect(), file(params.reference))
}

workflow.onComplete { log.info "Pipeline complete: ${workflow.status}" }
