nextflow.enable.dsl = 2

params.sample_sheet = null
params.reference = null
params.platform = "ont"
params.output_dir = "./results"
params.threads = 8
params.singularity_cache = "/data/singularity"

singularity { enabled = true; autoMounts = true; cacheDir = params.singularity_cache }

log.info """==========================================\n Long-Read Sequencing Pipeline\n==========================================\n Platform: ${params.platform}\n Output Dir: ${params.output_dir}\n==========================================\n"""

include { MINIMAP2_ALIGN; MINIMAP2_HIFI; SNIFFLES_CALL; CLAIR3_CALL; MEDAKA_POLISH } from "${projectDir}/modules/long_read/longread_analysis.nf"
include { SAMTOOLS_INDEX_TUPLE } from "${projectDir}/modules/utils/samtools.nf"

workflow {
    Channel.fromPath(params.sample_sheet).splitCsv(header: true, sep: '\t')
        .map { row -> tuple(row.sample_id, file(row.reads)) }
        .set { samples_ch }

    ref = file(params.reference)
    ref_idx = file("${params.reference}.fai")

    if (params.platform == "hifi") {
        MINIMAP2_HIFI(samples_ch, ref)
        aligned = MINIMAP2_HIFI.out.bam
    } else {
        MINIMAP2_ALIGN(samples_ch, ref)
        aligned = MINIMAP2_ALIGN.out.bam
    }

    SAMTOOLS_INDEX_TUPLE(aligned)
    SNIFFLES_CALL(SAMTOOLS_INDEX_TUPLE.out.bam_bai)
    CLAIR3_CALL(SAMTOOLS_INDEX_TUPLE.out.bam_bai, ref, ref_idx)
}

workflow.onComplete { log.info "Pipeline complete: ${workflow.status}" }
