process GATK_MARK_DUPLICATES {
    tag "MARK_DUP on ${sample}"
    container "broadinstitute/gatk:4.5.0.0"
    cpus params.threads ?: 4

    input:
    tuple val(sample), path(bam)

    output:
    tuple val(sample), path("${sample}.dedup.bam"), emit: bam
    tuple val(sample), path("${sample}.dedup.bam.bai"), emit: bai
    path "${sample}.MarkDuplicates.metrics.txt", emit: metrics

    script:
    """
    gatk MarkDuplicates \
        -I ${bam} \
        -O ${sample}.dedup.bam \
        -M ${sample}.MarkDuplicates.metrics.txt \
        --CREATE_INDEX true
    """
}

process GATK_HAPLOTYPE_CALLER {
    tag "HAPLOTYPE_CALLER on ${sample}"
    container "broadinstitute/gatk:4.5.0.0"
    cpus params.threads ?: 4

    input:
    tuple val(sample), path(bam), path(bai)
    path(reference)
    path(ref_index)
    path(ref_dict)
    path(dbsnp)
    path(dbsnp_index)

    output:
    tuple val(sample), path("${sample}.g.vcf.gz"), emit: gvcf
    tuple val(sample), path("${sample}.g.vcf.gz.tbi"), emit: tbi

    script:
    def dbsnp_arg = dbsnp.name != 'NO_FILE' ? "--dbsnp ${dbsnp}" : ""
    """
    gatk --java-options "-Xmx8g" HaplotypeCaller \
        -R ${reference} \
        -I ${bam} \
        -O ${sample}.g.vcf.gz \
        -ERC GVCF \
        ${dbsnp_arg} \
        --native-pair-hmm-threads ${task.cpus}
    """
}

process GATK_GENOTYPE_GVCFS {
    tag "GENOTYPE_GVCFS"
    container "broadinstitute/gatk:4.5.0.0"
    cpus params.threads ?: 4

    input:
    path(gvcfs)
    path(tbis)
    path(reference)
    path(ref_index)
    path(ref_dict)

    output:
    path "cohort.vcf.gz", emit: vcf
    path "cohort.vcf.gz.tbi", emit: tbi

    script:
    def gvcf_args = gvcfs.collect { "-V ${it}" }.join(' ')
    """
    gatk --java-options "-Xmx16g" GenotypeGVCFs \
        -R ${reference} \
        ${gvcf_args} \
        -O cohort.vcf.gz
    """
}

process GATK_VARIANT_FILTRATION {
    tag "VARIANT_FILTRATION"
    container "broadinstitute/gatk:4.5.0.0"

    input:
    path(vcf)
    path(tbi)
    path(reference)
    path(ref_index)
    path(ref_dict)

    output:
    path "filtered.vcf.gz", emit: vcf
    path "filtered.vcf.gz.tbi", emit: tbi

    script:
    """
    gatk VariantFiltration \
        -R ${reference} \
        -V ${vcf} \
        -O filtered.vcf.gz \
        --filter-expression "QD < 2.0" --filter-name "LowQD" \
        --filter-expression "FS > 60.0" --filter-name "HighFS" \
        --filter-expression "MQ < 40.0" --filter-name "LowMQ" \
        --filter-expression "MQRankSum < -12.5" --filter-name "LowMQRankSum" \
        --filter-expression "ReadPosRankSum < -8.0" --filter-name "LowReadPosRankSum"
    """
}