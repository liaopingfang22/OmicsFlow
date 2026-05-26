nextflow.enable.dsl = 2

params.sample_sheet = null
params.reference = null
params.dbsnp = null
params.known_indels = null
params.output_dir = "./results"
params.threads = 8
params.caller = "gatk"  // gatk, bcftools
params.singularity_cache = "/data/singularity"

singularity {
    enabled = true
    autoMounts = true
    cacheDir = params.singularity_cache
}

log.info """
==========================================
 WGS Variant Calling Pipeline
==========================================
 Sample Sheet:   ${params.sample_sheet}
 Reference:      ${params.reference}
 dbSNP:          ${params.dbsnp}
 Caller:         ${params.caller}
 Output Dir:     ${params.output_dir}
 Threads:        ${params.threads}
==========================================
"""

include { FASTQC; MULTIQC } from "${projectDir}/modules/quality_control/qc.nf"
include { TRIM_ADAPTERS } from "${projectDir}/modules/quality_control/qc.nf"
include { BWA_INDEX; BWA_MEM_PAIRED } from "${projectDir}/modules/read_alignment/bwa_alignment.nf"
include { SAMTOOLS_INDEX_TUPLE; SAMTOOLS_STATS; SAMTOOLS_FLAGSTAT } from "${projectDir}/modules/utils/samtools.nf"
include { GATK_MARK_DUPLICATES; GATK_HAPLOTYPE_CALLER; GATK_GENOTYPE_GVCFS; GATK_VARIANT_FILTRATION } from "${projectDir}/modules/variant_calling/gatk_haplotypecaller.nf"

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

    // Trim adapters
    TRIM_ADAPTERS(fastq_ch)
    trimmed_ch = TRIM_ADAPTERS.out.trimmed
        .map { sid, files ->
            def r1 = files instanceof List ? files[0] : files
            def r2 = files instanceof List ? files[1] : null
            tuple(sid, r1, r2)
        }

    // BWA-MEM2 alignment
    ref_file = file(params.reference)
    BWA_INDEX(ref_file)
    BWA_MEM_PAIRED(trimmed_ch, BWA_INDEX.out.index, ref_file)

    // Mark duplicates
    GATK_MARK_DUPLICATES(BWA_MEM_PAIRED.out.bam)

    // Index BAM
    SAMTOOLS_INDEX_TUPLE(GATK_MARK_DUPLICATES.out.bam)

    // BAM QC
    SAMTOOLS_STATS(GATK_MARK_DUPLICATES.out.bam)
    SAMTOOLS_FLAGSTAT(GATK_MARK_DUPLICATES.out.bam)

    // Variant calling
    ref_idx = file("${params.reference}.fai")
    ref_dict = file(params.reference.replace('.fa', '.dict').replace('.fasta', '.dict').replace('.fna', '.dict'))
    dbsnp_file = params.dbsnp ? file(params.dbsnp) : file("NO_FILE")
    dbsnp_idx = params.dbsnp ? file("${params.dbsnp}.tbi") : file("NO_FILE")

    GATK_HAPLOTYPE_CALLER(
        SAMTOOLS_INDEX_TUPLE.out.bam_bai,
        ref_file, ref_idx, ref_dict,
        dbsnp_file, dbsnp_idx
    )

    // Joint genotyping (if multiple samples)
    gvcf_ch = GATK_HAPLOTYPE_CALLER.out.gvcf.map { sid, g -> g }.collect()
    tbi_ch = GATK_HAPLOTYPE_CALLER.out.tbi.map { sid, t -> t }.collect()
    GATK_GENOTYPE_GVCFS(gvcf_ch, tbi_ch, ref_file, ref_idx, ref_dict)

    // Variant filtering
    GATK_VARIANT_FILTRATION(
        GATK_GENOTYPE_GVCFS.out.vcf,
        GATK_GENOTYPE_GVCFS.out.tbi,
        ref_file, ref_idx, ref_dict
    )
}

workflow.onComplete {
    log.info """
    ==========================================
     WGS Variant Calling Pipeline Complete
     Status: ${workflow.status}
     Duration: ${workflow.duration}
     Results: ${params.output_dir}
    ==========================================
    """
}