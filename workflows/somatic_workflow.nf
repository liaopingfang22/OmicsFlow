nextflow.enable.dsl = 2

params.sample_sheet = null
params.reference = null
params.dbsnp = null
params.pon = null
params.output_dir = "./results"
params.threads = 8
params.singularity_cache = "/data/singularity"

singularity { enabled = true; autoMounts = true; cacheDir = params.singularity_cache }

log.info """==========================================\n Somatic Variant Calling Pipeline\n==========================================\n Reference: ${params.reference}\n Output Dir: ${params.output_dir}\n==========================================\n"""

include { FASTQC; MULTIQC } from "${projectDir}/modules/quality_control/qc.nf"
include { MUTECT2_CALL; LEARN_READORIENTATION; FILTER_MUTECT_CALLS } from "${projectDir}/modules/somatic/somatic_variants.nf"
include { SAMTOOLS_INDEX_TUPLE } from "${projectDir}/modules/utils/samtools.nf"

workflow {
    Channel.fromPath(params.sample_sheet).splitCsv(header: true, sep: '\t')
        .map { row -> tuple(row.sample_id, file(row.tumor_bam), file(row.tumor_bai), file(row.normal_bam), file(row.normal_bai)) }
        .set { samples_ch }

    ref = file(params.reference)
    ref_idx = file("${params.reference}.fai")
    ref_dict = file(params.reference.replace('.fa', '.dict').replace('.fasta', '.dict'))
    dbsnp = params.dbsnp ? file(params.dbsnp) : file("NO_FILE")
    dbsnp_idx = params.dbsnp ? file("${params.dbsnp}.tbi") : file("NO_FILE")
    pon = params.pon ? file(params.pon) : file("NO_FILE")
    pon_idx = params.pon ? file("${params.pon}.tbi") : file("NO_FILE")
    germline = file("NO_FILE")
    germline_idx = file("NO_FILE")

    MUTECT2_CALL(samples_ch, ref, ref_idx, ref_dict, pon, pon_idx, germline, germline_idx)
    LEARN_READORIENTATION(MUTECT2_CALL.out.f1r2)
    FILTER_MUTECT_CALLS(MUTECT2_CALL.out.vcf.join(MUTECT2_CALL.out.tbi).join(LEARN_READORIENTATION.out.model), file("NO_FILE"), ref, ref_idx, ref_dict)
}

workflow.onComplete { log.info "Pipeline complete: ${workflow.status}" }
