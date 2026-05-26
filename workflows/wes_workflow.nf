nextflow.enable.dsl = 2

params.sample_sheet = null
params.reference = null
params.bt2_index = null
params.target_bed = null
params.dbsnp = null
params.output_dir = "./results"
params.threads = 8
params.singularity_cache = "/data/singularity"

singularity { enabled = true; autoMounts = true; cacheDir = params.singularity_cache }

log.info """==========================================\n WES Targeted Sequencing Pipeline\n==========================================\n Target BED: ${params.target_bed}\n Output Dir: ${params.output_dir}\n==========================================\n"""

include { FASTQC; MULTIQC } from "${projectDir}/modules/quality_control/qc.nf"
include { BWA_INDEX; BWA_MEM_PAIRED } from "${projectDir}/modules/read_alignment/bwa_alignment.nf"
include { GATK_MARK_DUPLICATES; GATK_HAPLOTYPE_CALLER; GATK_GENOTYPE_GVCFS; GATK_VARIANT_FILTRATION } from "${projectDir}/modules/variant_calling/gatk_haplotypecaller.nf"
include { SAMTOOLS_INDEX_TUPLE; SAMTOOLS_STATS; SAMTOOLS_FLAGSTAT } from "${projectDir}/modules/utils/samtools.nf"
include { WES_COVERAGE } from "${projectDir}/modules/wes/wes_analysis.nf"

workflow {
    Channel.fromPath(params.sample_sheet).splitCsv(header: true, sep: '\t')
        .map { row -> tuple(row.sample_id, file(row.read1), file(row.read2)) }
        .set { samples_ch }

    samples_ch.map { s, r1, r2 -> tuple(s, [r1, r2]) }.set { fastq_ch }
    FASTQC(fastq_ch)
    MULTIQC(FASTQC.out.zip.collect())

    ref = file(params.reference)
    BWA_INDEX(ref)
    BWA_MEM_PAIRED(samples_ch, BWA_INDEX.out.index, ref)
    GATK_MARK_DUPLICATES(BWA_MEM_PAIRED.out.bam)
    SAMTOOLS_INDEX_TUPLE(GATK_MARK_DUPLICATES.out.bam)
    SAMTOOLS_STATS(GATK_MARK_DUPLICATES.out.bam)
    SAMTOOLS_FLAGSTAT(GATK_MARK_DUPLICATES.out.bam)
    WES_COVERAGE(SAMTOOLS_INDEX_TUPLE.out.bam_bai, file(params.target_bed))

    ref_idx = file("${params.reference}.fai")
    ref_dict = file(params.reference.replace('.fa', '.dict').replace('.fasta', '.dict'))
    dbsnp_file = params.dbsnp ? file(params.dbsnp) : file("NO_FILE")
    dbsnp_idx = params.dbsnp ? file("${params.dbsnp}.tbi") : file("NO_FILE")

    GATK_HAPLOTYPE_CALLER(SAMTOOLS_INDEX_TUPLE.out.bam_bai, ref, ref_idx, ref_dict, dbsnp_file, dbsnp_idx)
}

workflow.onComplete { log.info "Pipeline complete: ${workflow.status}" }
