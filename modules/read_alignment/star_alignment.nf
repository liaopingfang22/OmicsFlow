process STAR_INDEX {
    tag "STAR_INDEX on ${reference.baseName}"
    container "quay.io/biocontainers/star:2.7.11b--h0033a4d_7"
    cpus params.threads ?: 8

    input:
    path(reference)
    path(gtf)

    output:
    path "star_index", emit: index

    script:
    """
    mkdir -p star_index
    STAR --runMode genomeGenerate \
         --runThreadN ${task.cpus} \
         --genomeDir star_index \
         --genomeFastaFiles ${reference} \
         --sjdbGTFfile ${gtf} \
         --sjdbOverhang 149
    """
}

process STAR_ALIGN {
    tag "STAR_ALIGN on ${sample}"
    container "quay.io/biocontainers/star:2.7.11b--h0033a4d_7"
    cpus params.threads ?: 8

    input:
    tuple val(sample), path(read1), path(read2)
    path(index)

    output:
    tuple val(sample), path("${sample}.Aligned.sortedByCoord.out.bam"), emit: bam
    tuple val(sample), path("${sample}.ReadsPerGene.out.tab"), emit: counts
    path "${sample}.Log.final.out", emit: log
    path "${sample}.SJ.out.tab", emit: sj

    script:
    """
    STAR --runThreadN ${task.cpus} \
         --genomeDir ${index} \
         --readFilesIn ${read1} ${read2} \
         --readFilesCommand zcat \
         --outSAMtype BAM SortedByCoordinate \
         --outFileNamePrefix ${sample}. \
         --quantMode GeneCounts \
         --outSAMstrandField intronMotif \
         --outFilterIntronMotifs RemoveNoncanonical \
         --outSAMattributes NH HI AS NM MD
    """
}

process STAR_QUANT {
    tag "STAR_QUANT on ${sample}"
    container "quay.io/biocontainers/star:2.7.11b--h0033a4d_7"
    cpus params.threads ?: 8

    input:
    tuple val(sample), path(read1), path(read2)
    path(index)

    output:
    tuple val(sample), path("${sample}.Aligned.toTranscriptome.out.bam"), emit: bam
    tuple val(sample), path("${sample}.ReadsPerGene.out.tab"), emit: counts

    script:
    """
    STAR --runThreadN ${task.cpus} \
         --genomeDir ${index} \
         --readFilesIn ${read1} ${read2} \
         --readFilesCommand zcat \
         --outSAMtype BAM SortedByCoordinate \
         --outFileNamePrefix ${sample}. \
         --quantMode GeneCounts TranscriptomeSAM \
         --outSAMstrandField intronMotif
    """
}