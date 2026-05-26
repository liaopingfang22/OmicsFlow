process EDGER_ANALYSIS {
    tag "EDGER_ANALYSIS"
    container "singularity://bioconductor.sif"
    
    input:
    path(count_matrix)
    val(sample_sheet)
    
    output:
    path "dge_results.csv", emit: results
    path "dge_results.rds", emit: rds
    
    script:
    """
    #!/usr/bin/env Rscript

    library(edgeR)
    library(readr)

    counts <- read_delim("${count_matrix}", delim='\t')
    rownames(counts) <- counts[[1]]
    counts <- counts[, -1]

    dge <- DGEList(counts=as.matrix(counts))
    dge <- calcNormFactors(dge)

    design <- model.matrix(~group, data=data.frame(
        group=factor(rep(c("control", "treatment"), each=ncol(counts)/2))
    ))

    dge <- estimateDisp(dge, design)
    fit <- glmQLFTest(dge, design)
    
    results <- topTags(fit, n=nrow(counts))\$table
    results <- cbind(Gene=rownames(results), results)
    write_csv(as.data.frame(results), "dge_results.csv")

    saveRDS(fit, "dge_results.rds")

    cat("EdgeR analysis complete\n")
    """
}

process DESEQ2_ANALYSIS {
    tag "DESEQ2_ANALYSIS"
    container "singularity://bioconductor.sif"
    
    input:
    path(count_matrix)
    val(sample_sheet)
    
    output:
    path "deseq2_results.csv", emit: results
    path "deseq2_results.rds", emit: rds
    
    script:
    """
    #!/usr/bin/env Rscript

    library(DESeq2)
    library(readr)

    counts <- read_delim("${count_matrix}", delim='\t')
    rownames(counts) <- counts[[1]]
    counts <- counts[, -1]

    coldata <- data.frame(
        condition=factor(rep(c("control", "treatment"), each=ncol(counts)/2))
    )
    rownames(coldata) <- colnames(counts)

    dds <- DESeqDataSetFromMatrix(countData=as.matrix(counts), colData=coldata, design=~condition)
    dds <- DESeq(dds)

    results <- results(dds, contrast=c("condition", "treatment", "control"))
    results <- cbind(Gene=rownames(results), as.data.frame(results))
    write_csv(results, "deseq2_results.csv")

    saveRDS(dds, "deseq2_results.rds")

    cat("DESeq2 analysis complete\n")
    """
}
