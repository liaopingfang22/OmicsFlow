process WES_BWA_ALIGN {
    tag "BWA on ${sample}"
    container "quay.io/biocontainers/bwa-mem2:2.2.1--h7132678_2"
    cpus params.threads ?: 8
    input: tuple val(sample), path(read1), path(read2); path(index); path(reference)
    output: tuple val(sample), path("${sample}.sorted.bam"), emit: bam
    script:
    """
    bwa-mem2 mem -t ${task.cpus} -R "@RG\\tID:${sample}\\tSM:${sample}\\tPL:ILLUMINA" \
        \$(find . -name "*.bwt.2bit.64" | head -1 | sed 's/.bwt.2bit.64//') \
        ${read1} ${read2} | samtools sort -@ ${task.cpus} -o ${sample}.sorted.bam -
    """
}

process WES_COVERAGE {
    tag "COVERAGE on ${sample}"
    container "quay.io/biocontainers/bedtools:2.31.1--h4ac6f70_0"
    input: tuple val(sample), path(bam), path(bai); path(bed)
    output: tuple val(sample), path("${sample}.coverage.tsv"), emit: coverage; tuple val(sample), path("${sample}.on_target.tsv"), emit: on_target
    script:
    """
    bedtools coverage -a ${bed} -b ${bam} -hist > ${sample}.coverage.tsv
    TOTAL=\$(samtools view -c ${bam})
    ON_TARGET=\$(bedtools intersect -a ${bam} -b ${bed} -u | samtools view -c)
    echo -e "sample\\ttotal\\ton_target\\tfrac" > ${sample}.on_target.tsv
    echo -e "${sample}\\t\$TOTAL\\t\$ON_TARGET\\t\$(echo "scale=4; \$ON_TARGET/\$TOTAL" | bc)" >> ${sample}.on_target.tsv
    """
}

process WES_GATK_HAPLOTYPE {
    tag "HAPLOTYPE on ${sample}"
    container "broadinstitute/gatk:4.5.0.0"
    cpus params.threads ?: 4
    input: tuple val(sample), path(bam), path(bai); path(reference); path(ref_idx); path(ref_dict); path(dbsnp); path(dbsnp_idx); path(intervals)
    output: tuple val(sample), path("${sample}.g.vcf.gz"), emit: gvcf
    script:
    """
    gatk --java-options "-Xmx8g" HaplotypeCaller -R ${reference} -I ${bam} -O ${sample}.g.vcf.gz -ERC GVCF \
        --dbsnp ${dbsnp} -L ${intervals} --native-pair-hmm-threads ${task.cpus}
    """
}
