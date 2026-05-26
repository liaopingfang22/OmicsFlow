process BISMARK_ALIGN {
    tag "BISMARK on ${sample}"
    container "quay.io/biocontainers/bismark:0.24.2--hdfd78af_0"
    cpus params.threads ?: 8
    input: tuple val(sample), path(read1), path(read2); path(genome_dir)
    output: tuple val(sample), path("${sample}_pe.bam"), emit: bam; path "${sample}_PE_report.txt", emit: report
    script: "bismark --genome ${genome_dir} -1 ${read1} -2 ${read2} --bam -p ${task.cpus}"
}

process BISMARK_DEDUPLICATE {
    tag "DEDUP on ${sample}"
    container "quay.io/biocontainers/bismark:0.24.2--hdfd78af_0"
    input: tuple val(sample), path(bam)
    output: tuple val(sample), path("${sample}.deduplicated.bam"), emit: bam
    script: "deduplicate_bismark --bam ${bam}"
}

process BISMARK_METHYLATION {
    tag "BISMARK_METH on ${sample}"
    container "quay.io/biocontainers/bismark:0.24.2--hdfd78af_0"
    input: tuple val(sample), path(bam)
    output: tuple val(sample), path("CpG_context_${sample}.txt.gz"), emit: cpg; tuple val(sample), path("${sample}_PE_report.txt"), emit: report
    script: "bismark_methylation_extractor --paired-end --gzip ${bam}"
}

process METHYLKIT_DMR {
    tag "METHYLKIT"
    container "quay.io/biocontainers/bioconductor-methylkit:1.28.0--r43hdfd78af_0"
    input: path(cpg_files); path(sample_info)
    output: path "dmr_results.csv", emit: dmr; path "methylation_plots.pdf", emit: plots
    script:
    """
    #!/usr/bin/env Rscript
    library(methylKit)
    files <- list.files(".", pattern="CpG_context.*.txt.gz", full.names=TRUE)
    sample_ids <- gsub("CpG_context_", "", gsub(".txt.gz", "", basename(files)))
    myobj <- methRead(as.list(files), sample.id=as.list(sample_ids), assembly="hg38", context="CpG", treatment=c(0,0,1,1))
    meth <- unite(myobj, destrand=TRUE)
    myDiff <- calculateDiffMeth(meth)
    myDiff25 <- getMethylDiff(myDiff, difference=25, qvalue=0.01)
    write.csv(as.data.frame(myDiff25), "dmr_results.csv", row.names=FALSE)
    pdf("methylation_plots.pdf", width=12, height=8)
    plotMethylationProfile(meth[1:1000,])
    dev.off()
    """
}
