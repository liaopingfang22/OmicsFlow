process SAMTOOLS_INDEX {
    tag "SAMTOOLS_INDEX on ${bam.baseName}"
    container "quay.io/biocontainers/samtools:1.20--h50ea8bc_0"
    cpus 2

    input:
    path(bam)

    output:
    path "${bam}.bai", emit: bai

    script:
    """
    samtools index -@ ${task.cpus} ${bam}
    """
}

process SAMTOOLS_INDEX_TUPLE {
    tag "SAMTOOLS_INDEX on ${sample}"
    container "quay.io/biocontainers/samtools:1.20--h50ea8bc_0"
    cpus 2

    input:
    tuple val(sample), path(bam)

    output:
    tuple val(sample), path(bam), path("${bam}.bai"), emit: bam_bai

    script:
    """
    samtools index -@ ${task.cpus} ${bam}
    """
}

process SAMTOOLS_STATS {
    tag "SAMTOOLS_STATS on ${sample}"
    container "quay.io/biocontainers/samtools:1.20--h50ea8bc_0"

    input:
    tuple val(sample), path(bam)

    output:
    tuple val(sample), path("${sample}.samtools.stats"), emit: stats

    script:
    """
    samtools stats ${bam} > ${sample}.samtools.stats
    """
}

process SAMTOOLS_FLAGSTAT {
    tag "SAMTOOLS_FLAGSTAT on ${sample}"
    container "quay.io/biocontainers/samtools:1.20--h50ea8bc_0"

    input:
    tuple val(sample), path(bam)

    output:
    tuple val(sample), path("${sample}.flagstat"), emit: flagstat

    script:
    """
    samtools flagstat ${bam} > ${sample}.flagstat
    """
}

process SAMTOOLS_DEPTH {
    tag "SAMTOOLS_DEPTH on ${sample}"
    container "quay.io/biocontainers/samtools:1.20--h50ea8bc_0"

    input:
    tuple val(sample), path(bam)

    output:
    tuple val(sample), path("${sample}.depth.txt"), emit: depth

    script:
    """
    samtools depth -a ${bam} > ${sample}.depth.txt
    """
}

process SAMTOOLS_MERGE {
    tag "SAMTOOLS_MERGE"
    container "quay.io/biocontainers/samtools:1.20--h50ea8bc_0"
    cpus params.threads ?: 4

    input:
    val(sample_name)
    path(bams)

    output:
    tuple val(sample_name), path("${sample_name}.merged.bam"), emit: bam

    script:
    """
    samtools merge -@ ${task.cpus} -o ${sample_name}.merged.bam ${bams.join(' ')}
    """
}

process SAMTOOLS_FILTER {
    tag "SAMTOOLS_FILTER on ${sample}"
    container "quay.io/biocontainers/samtools:1.20--h50ea8bc_0"
    cpus 2

    input:
    tuple val(sample), path(bam)

    output:
    tuple val(sample), path("${sample}.filtered.bam"), emit: bam

    script:
    """
    samtools view -@ ${task.cpus} -b -f 2 -q 30 ${bam} > ${sample}.filtered.bam
    """
}