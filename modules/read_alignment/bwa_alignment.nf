process BWA_INDEX {
    tag "BWA_INDEX on ${reference.baseName}"
    container "quay.io/biocontainers/bwa-mem2:2.2.1--h7132678_2"

    input:
    path(reference)

    output:
    path "${reference}*", emit: index

    script:
    """
    bwa-mem2 index ${reference}
    """
}

process BWA_MEM {
    tag "BWA_MEM on ${sample}"
    container "quay.io/biocontainers/bwa-mem2:2.2.1--h7132678_2"
    cpus params.threads ?: 8

    input:
    tuple val(sample), path(reads)
    path(index)
    path(reference)

    output:
    tuple val(sample), path("${sample}.bam"), emit: bam

    script:
    """
    INDEX=\$(ls ${reference}.bwt.2bit.64 2>/dev/null | head -1 | sed 's/.bwt.2bit.64//')
    if [ -z "\$INDEX" ]; then
        INDEX=\$(ls ${reference}.*.ht2 2>/dev/null | head -1 | sed 's/..ht2//')
    fi

    bwa-mem2 mem -t ${task.cpus} \
        -R "@RG\\tID:${sample}\\tSM:${sample}\\tPL:ILLUMINA" \
        \$(find . -name "*.bwt.2bit.64" | head -1 | sed 's/.bwt.2bit.64//') \
        ${reads} | \
        samtools sort -@ ${task.cpus} -o ${sample}.bam -
    """
}

process BWA_MEM_PAIRED {
    tag "BWA_MEM on ${sample}"
    container "quay.io/biocontainers/bwa-mem2:2.2.1--h7132678_2"
    cpus params.threads ?: 8

    input:
    tuple val(sample), path(read1), path(read2)
    path(index)
    path(reference)

    output:
    tuple val(sample), path("${sample}.bam"), emit: bam

    script:
    """
    bwa-mem2 mem -t ${task.cpus} \
        -R "@RG\\tID:${sample}\\tSM:${sample}\\tPL:ILLUMINA" \
        \$(find . -name "*.bwt.2bit.64" | head -1 | sed 's/.bwt.2bit.64//') \
        ${read1} ${read2} | \
        samtools sort -@ ${task.cpus} -o ${sample}.bam -
    """
}