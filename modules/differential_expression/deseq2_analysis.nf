process DESEQ2_ANALYSIS {
    tag "DESEQ2_ANALYSIS"
    container 'quay.io/biocontainers/bioconductor-deseq2:4.2.0--r351he1c0d29_0'
    
    input:
    path(count_matrix)
    val(sample_sheet)
    
    output:
    path "deseq2_results.csv", emit: results
    path "deseq2_results.rds", emit: rds
    path "norm_counts.csv", emit: norm_counts
    
    script:
    """
    #!/usr/bin/env Rscript

    library(DESeq2)
    library(readr)
    library(dplyr)

    counts <- read_delim("${count_matrix}", delim='\\t', escape_double=FALSE, trim_ws=TRUE)

    rownames(counts) <- counts[[1]]
    counts <- counts[, -1]

    coldata <- data.frame(
        condition = factor(rep(c("control", "treatment"), each=ncol(counts)/2))
    )
    rownames(coldata) <- colnames(counts)

    dds <- DESeqDataSetFromMatrix(countData=as.matrix(counts), colData=coldata, design=~condition)

    dds <- DESeq(dds)

    results <- results(dds, contrast=c("condition", "treatment", "control"))

    results_df <- as.data.frame(results) %>%
        mutate(Symbol = rownames(results)) %>%
        select(Symbol, everything()) %>%
        arrange(padj)

    write_csv(results_df, "deseq2_results.csv")

    saveRDS(dds, "deseq2_results.rds")

    norm_counts <- counts(dds, normalized=TRUE)
    write_csv(as.data.frame(norm_counts), "norm_counts.csv")

    cat("DESeq2 analysis complete. Found", sum(results_df\$padj < 0.05, na.rm=TRUE), "significant genes\\n")
    """
}

process DESEQ2_PLOTS {
    tag "DESEQ2_PLOTS"
    container 'quay.io/biocontainers/bioconductor-deseq2:4.2.0--r351he1c0d29_0'
    
    input:
    path(rds_file)
    
    output:
    path "*.pdf", emit: plots
    
    script:
    """
    #!/usr/bin/env Rscript

    library(DESeq2)
    library(ggplot2)
    library(vsn)

    dds <- readRDS("${rds_file}")

    pdf("deseq2_plots.pdf", width=10, height=8)

    rld <- rlogTransformation(dds)
    plotPCA(rld, intgroup="condition")

    meanSdPlot(assay(rld), ylim=c(0, 2))

    plotDispEsts(dds)

    dev.off()

    cat("DESeq2 plots complete\\n")
    """
}
