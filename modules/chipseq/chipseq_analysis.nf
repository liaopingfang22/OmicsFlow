process BOWTIE2_INDEX {
    tag "BOWTIE2_INDEX on ${reference.baseName}"
    container "quay.io/biocontainers/bowtie2:2.5.1--py39h6b7c446_2"
    input: path(reference)
    output: path "${reference}.*.bt2*", emit: index
    script: "bowtie2-build --threads ${task.cpus} ${reference} ${reference}"
}

process BOWTIE2_ALIGN {
    tag "BOWTIE2 on ${sample}"
    container "quay.io/biocontainers/bowtie2:2.5.1--py39h6b7c446_2"
    cpus params.threads ?: 8
    input: tuple val(sample), path(reads); path(index); path(reference)
    output: tuple val(sample), path("${sample}.sorted.bam"), emit: bam
    script:
    """
    INDEX=\$(find . -name "*.bt2" | head -1 | sed 's/.\(1\|2\).bt2//')
    bowtie2 --very-sensitive -x \${INDEX} -U ${reads} -p ${task.cpus} | samtools sort -@ ${task.cpus} -o ${sample}.sorted.bam -
    samtools index ${sample}.sorted.bam
    """
}

process MACS3_CALLPEAK {
    tag "MACS3 on ${sample}"
    container "quay.io/biocontainers/macs3:3.0.1--py310h6b7c446_0"
    input: tuple val(sample), path(bam); val(peak_type)
    output: tuple val(sample), path("${sample}_peaks.*Peak"), emit: peaks; path "${sample}_summits.bed", emit: summits; path "${sample}_peaks.xls", emit: xls
    script:
    def ft = peak_type == "narrow" ? "-f BAM" : "-f BAM --broad"
    """
    macs3 callpeak -t ${bam} ${ft} --nomodel --shift -75 --extsize 150 -g hs --call-summits -n ${sample}
    """
}

process ANNOTATE_PEAKS {
    tag "ANNOTATE on ${sample}"
    container "quay.io/biocontainers/bioconductor-chipseeker:1.38.0--r43hdfd78af_0"
    input: path(peaks); path(gtf)
    output: path "annotated_peaks.tsv", emit: annotated
    script:
    """
    #!/usr/bin/env Rscript
    library(ChIPseeker)
    library(GenomicFeatures)
    txdb <- makeTxDbFromGFF("${gtf}")
    peaks_list <- list.files(".", pattern="*_peaks.*Peak", full.names=TRUE)
    all_peaks <- lapply(peaks_list, readPeakFile)
    names(all_peaks) <- gsub("_peaks.*", "", basename(peaks_list))
    annotated <- lapply(all_peaks, annotatePeak, TxDb=txdb)
    df <- as.data.frame(annotated[[1]])
    write.table(df, "annotated_peaks.tsv", sep="\\t", row.names=FALSE, quote=FALSE)
    """
}

process FIND_MOTIFS {
    tag "MOTIFS on ${sample}"
    container "quay.io/biocontainers/homer:4.11--pl5321h2e3e62a_3"
    input: path(peaks); path(genome)
    output: path "homer_motifs/", emit: motifs
    script:
    """
    mkdir -p homer_motifs
    findMotifsGenome.pl ${peaks} ${genome} homer_motifs -size 200 -p ${task.cpus}
    """
}