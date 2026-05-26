process ATAC_BOWTIE2 {
    tag "BOWTIE2 on ${sample}"
    container "quay.io/biocontainers/bowtie2:2.5.1--py39h6b7c446_2"
    cpus params.threads ?: 8

    input:
    tuple val(sample), path(read1), path(read2)
    path(bt2_index)

    output:
    tuple val(sample), path("${sample}.bam"), emit: bam

    script:
    """
    INDEX=\$(find . -name "*.bt2" | head -1 | sed 's/.1.bt2//')
    bowtie2 --very-sensitive -X 2000 --no-mixed --no-discordant \\
        -x \${INDEX} -1 ${read1} -2 ${read2} -p ${task.cpus} | \\
        samtools view -bS -q 30 -f 2 | \\
        samtools sort -@ ${task.cpus} -o ${sample}.bam -
    """
}

process ATAC_REMOVE_DUP {
    tag "REMOVE_DUP on ${sample}"
    container "quay.io/biocontainers/picard:3.1.1--hdfd78af_0"

    input:
    tuple val(sample), path(bam)

    output:
    tuple val(sample), path("${sample}.dedup.bam"), emit: bam
    path "${sample}.dup_metrics.txt", emit: metrics

    script:
    """
    picard MarkDuplicates I=${bam} O=${sample}.dedup.bam \\
        M=${sample}.dup_metrics.txt REMOVE_DUPLICATES=true
    """
}

process ATAC_FILTER_MITOCHONDRIAL {
    tag "FILTER_MT on ${sample}"
    container "quay.io/biocontainers/samtools:1.20--h50ea8bc_0"

    input:
    tuple val(sample), path(bam)

    output:
    tuple val(sample), path("${sample}.noMT.bam"), emit: bam

    script:
    """
    samtools view -h ${bam} | grep -v "chrM" | samtools view -b -o ${sample}.noMT.bam -
    samtools index ${sample}.noMT.bam
    """
}

process ATAC_CALL_PEAKS {
    tag "MACS3 on ${sample}"
    container "quay.io/biocontainers/macs3:3.0.1--py310h6b7c446_0"

    input:
    tuple val(sample), path(bam)

    output:
    tuple val(sample), path("${sample}_peaks.narrowPeak"), emit: peaks
    tuple val(sample), path("${sample}_summits.bed"), emit: summits
    path "${sample}_peaks.xls", emit: xls

    script:
    """
    macs3 callpeak -t ${bam} -f BAMPE --nomodel \\
        --shift -100 --extsize 200 --keep-dup all \\
        -g hs --call-summits -n ${sample}
    """
}

process ATAC_FRIP {
    tag "FRiP on ${sample}"
    container "quay.io/biocontainers/bedtools:2.31.1--h4ac6f70_0"

    input:
    tuple val(sample), path(bam), path(peaks)

    output:
    tuple val(sample), path("${sample}_frip.tsv"), emit: frip

    script:
    """
    TOTAL=\$(samtools view -c ${bam})
    IN_PEAKS=\$(bedtools intersect -a ${bam} -b ${peaks} -u | samtools view -c)
    FRIP=\$(echo "scale=4; \$IN_PEAKS / \$TOTAL" | bc)
    echo -e "sample\\ttotal_reads\\treads_in_peaks\\tFRiP" > ${sample}_frip.tsv
    echo -e "${sample}\\t\$TOTAL\\t\$IN_PEAKS\\t\$FRIP" >> ${sample}_frip.tsv
    """
}

process ATAC_INSERT_SIZE {
    tag "INSERT_SIZE on ${sample}"
    container "quay.io/biocontainers/picard:3.1.1--hdfd78af_0"

    input:
    tuple val(sample), path(bam)

    output:
    tuple val(sample), path("${sample}_insert_metrics.txt"), emit: metrics

    script:
    """
    picard CollectInsertSizeMetrics I=${bam} O=${sample}_insert_metrics.txt \\
        H=${sample}_insert_hist.pdf M=0.5
    """
}

process CHROMVAR_ANALYSIS {
    tag "CHROMVAR on ${sample}"
    container "quay.io/biocontainers/bioconductor-chromvar:1.24.0--r43hdfd78af_0"

    input:
    path(peaks_files)
    path(motif_db)

    output:
    path "chromvar_deviations.tsv", emit: deviations
    path "chromvar_results.pdf", emit: plots

    script:
    """
    #!/usr/bin/env Rscript
    library(chromVAR)
    library(motifmatchr)
    library(BSgenome.Hsapiens.UCSC.hg38)
    library(SummarizedExperiment)
    library(ggplot2)

    peak_files <- list.files(".", pattern="*_peaks.narrowPeak")
    all_peaks <- GRangesList()
    for (f in peak_files) {
        sample_name <- gsub("_peaks.narrowPeak", "", f)
        peaks <- import(f, format="BED")
        all_peaks[[sample_name]] <- peaks
    }

    merged_peaks <- reduce(unlist(all_peaks))
    fragment_counts <- getCounts(merged_peaks, ... , paired=TRUE, by_rg=TRUE)
    fragment_counts <- addGCBias(fragment_counts, genome=BSgenome.Hsapiens.UCSC.hg38)

    motif_ix <- matchMotifs(motif_db, fragment_counts, genome=BSgenome.Hsapiens.UCSC.hg38)
    dev <- computeDeviations(object=fragment_counts, annotations=motif_ix)

    deviations_df <- data.frame(
        motif = rownames(deviationScores(dev)),
        as.data.frame(deviationScores(dev))
    )
    write.table(deviations_df, "chromvar_deviations.tsv", sep="\\t", row.names=FALSE)

    pdf("chromvar_results.pdf", width=12, height=8)
    variability <- computeVariability(dev)
    plotVariability(variability, use_plotly=FALSE)
    dev.off()
    """
}