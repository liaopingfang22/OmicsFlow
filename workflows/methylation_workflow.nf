nextflow.enable.dsl = 2

params.sample_sheet = null
params.genome_dir = null
params.output_dir = "./results"
params.threads = 8
params.singularity_cache = "/data/singularity"

singularity { enabled = true; autoMounts = true; cacheDir = params.singularity_cache }

log.info """==========================================\n Methylation Analysis Pipeline\n==========================================\n Genome Dir: ${params.genome_dir}\n Output Dir: ${params.output_dir}\n==========================================\n"""

include { BISMARK_ALIGN; BISMARK_DEDUPLICATE; BISMARK_METHYLATION; METHYLKIT_DMR } from "${projectDir}/modules/methylation/methylation_analysis.nf"

workflow {
    Channel.fromPath(params.sample_sheet).splitCsv(header: true, sep: '\t')
        .map { row -> tuple(row.sample_id, file(row.read1), file(row.read2)) }
        .set { samples_ch }

    BISMARK_ALIGN(samples_ch, file(params.genome_dir))
    BISMARK_DEDUPLICATE(BISMARK_ALIGN.out.bam)
    BISMARK_METHYLATION(BISMARK_DEDUPLICATE.out.bam)
    METHYLKIT_DMR(BISMARK_METHYLATION.out.cpg.map { s, c -> c }.collect(), file("NO_FILE"))
}

workflow.onComplete { log.info "Pipeline complete: ${workflow.status}" }
