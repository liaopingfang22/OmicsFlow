process DADA2_FILTER_AND_TRIM {
    tag "DADA2_FILTER on ${sample}"
    container "quay.io/biocontainers/bioconductor-dada2:1.30.0--r43hdfd78af_0"
    cpus params.threads ?: 4

    input:
    tuple val(sample), path(reads)

    output:
    tuple val(sample), path("${sample}_filt_R1.fq.gz"), path("${sample}_filt_R2.fq.gz"), emit: filtered
    path "${sample}_filter_stats.tsv", emit: stats

    script:
    """
    #!/usr/bin/env Rscript
    library(dada2)
    
    out <- filterAndTrim(
        fwd = "${reads[0]}", filt = "${sample}_filt_R1.fq.gz",
        rev = "${reads[1]}", filt.rev = "${sample}_filt_R2.fq.gz",
        truncLen = c(240, 200),
        maxN = 0, maxEE = c(2, 2), truncQ = 2,
        rm.phix = TRUE, compress = TRUE, multithread = ${task.cpus}
    )
    write.csv(out, "${sample}_filter_stats.tsv")
    """
}

process DADA2_LEARN_ERRORS {
    tag "DADA2_LEARN_ERRORS"
    container "quay.io/biocontainers/bioconductor-dada2:1.30.0--r43hdfd78af_0"
    cpus params.threads ?: 4

    input:
    path(filt_reads)

    output:
    path "err_R1.rds", emit: err_R1
    path "err_R2.rds", emit: err_R2

    script:
    """
    #!/usr/bin/env Rscript
    library(dada2)
    
    fnFs <- sort(list.files(".", pattern="_filt_R1.fq.gz", full.names=TRUE))
    fnRs <- sort(list.files(".", pattern="_filt_R2.fq.gz", full.names=TRUE))
    
    errF <- learnErrors(fnFs, multithread=${task.cpus}, nbases=1e8)
    errR <- learnErrors(fnRs, multithread=${task.cpus}, nbases=1e8)
    
    saveRDS(errF, "err_R1.rds")
    saveRDS(errR, "err_R2.rds")
    """
}

process DADA2_DADA {
    tag "DADA2_DADA on ${sample}"
    container "quay.io/biocontainers/bioconductor-dada2:1.30.0--r43hdfd78af_0"

    input:
    tuple val(sample), path(filtF), path(filtR)
    path(errF), path(errR)

    output:
    tuple val(sample), path("${sample}_merged.rds"), emit: merged
    path "${sample}_track.tsv", emit: track

    script:
    """
    #!/usr/bin/env Rscript
    library(dada2)
    
    errF <- readRDS("${errF}")
    errR <- readRDS("${errR}")
    
    dadaF <- dada("${filtF}", err=errF, multithread=FALSE)
    dadaR <- dada("${filtR}", err=errR, multithread=FALSE)
    
    merged <- mergePairs(dadaF, "${filtF}", dadaR, "${filtR}", verbose=TRUE)
    saveRDS(merged, "${sample}_merged.rds")
    
    track <- data.frame(
        sample = "${sample}",
        input = sum(getUniques(dadaF)) + sum(getUniques(dadaR)),
        merged = sum(getUniques(merged))
    )
    write.table(track, "${sample}_track.tsv", sep="\\t", row.names=FALSE)
    """
}

process DADA2_MAKE_TABLE {
    tag "DADA2_MAKE_TABLE"
    container "quay.io/biocontainers/bioconductor-dada2:1.30.0--r43hdfd78af_0"

    input:
    path(merged_rds)

    output:
    path "seqtab.rds", emit: seqtab
    path "seqtab_nochim.rds", emit: seqtab_nochim
    path "asv_table.tsv", emit: asv_table
    path "asv_summary.tsv", emit: summary

    script:
    """
    #!/usr/bin/env Rscript
    library(dada2)
    
    mergers <- list()
    for (f in list.files(".", pattern="*_merged.rds")) {
        sample_name <- gsub("_merged.rds", "", f)
        mergers[[sample_name]] <- readRDS(f)
    }
    
    seqtab <- makeSequenceTable(mergers)
    saveRDS(seqtab, "seqtab.rds")
    
    seqtab_nochim <- removeBimeraDenovo(seqtab, method="consensus", multithread=TRUE)
    saveRDS(seqtab_nochim, "seqtab_nochim.rds")
    
    asv_df <- as.data.frame(seqtab_nochim)
    asv_df\$ASV <- paste0("ASV", 1:nrow(asv_df))
    asv_df <- asv_df[, c(ncol(asv_df), 1:(ncol(asv_df)-1))]
    write.table(asv_df, "asv_table.tsv", sep="\\t", row.names=FALSE, quote=FALSE)
    
    summary <- data.frame(
        Total_ASVs = nrow(seqtab_nochim),
        Total_Reads = sum(seqtab_nochim),
        Median_Reads_Per_Sample = median(colSums(seqtab_nochim))
    )
    write.table(summary, "asv_summary.tsv", sep="\\t", row.names=FALSE)
    """
}

process DADA2_ASSIGN_TAXONOMY {
    tag "DADA2_ASSIGN_TAXONOMY"
    container "quay.io/biocontainers/bioconductor-dada2:1.30.0--r43hdfd78af_0"

    input:
    path(seqtab_nochim)
    path(silva_ref)

    output:
    path "taxa.tsv", emit: taxa
    path "taxa.rds", emit: taxa_rds

    script:
    """
    #!/usr/bin/env Rscript
    library(dada2)
    
    seqtab <- readRDS("${seqtab_nochim}")
    taxa <- assignTaxonomy(seqtab, "${silva_ref}", multithread=TRUE, tryRC=TRUE)
    taxa <- addSpecies(taxa, "${silva_ref}")
    
    write.csv(as.data.frame(taxa), "taxa.csv")
    saveRDS(taxa, "taxa.rds")
    
    taxa_df <- as.data.frame(taxa)
    taxa_df\$ASV <- paste0("ASV", 1:nrow(taxa_df))
    write.table(taxa_df, "taxa.tsv", sep="\\t", row.names=FALSE, quote=FALSE)
    """
}

process PHYLOSEQ_ANALYSIS {
    tag "PHYLOSEQ_ANALYSIS"
    container "quay.io/biocontainers/bioconductor-phyloseq:1.46.0--r43hdfd78af_0"

    input:
    path(asv_table)
    path(taxa_table)
    path(metadata)

    output:
    path "alpha_diversity.tsv", emit: alpha
    path "beta_diversity.tsv", emit: beta
    path "phyloseq_plots.pdf", emit: plots

    script:
    """
    #!/usr/bin/env Rscript
    library(phyloseq)
    library(ggplot2)
    
    asv <- read.delim("${asv_table}", row.names=1)
    taxa <- read.delim("${taxa_table}", row.names=1)
    meta <- read.delim("${metadata}", row.names=1)
    
    OTU <- otu_table(as.matrix(asv), taxa_are_rows=TRUE)
    TAX <- tax_table(as.matrix(taxa))
    META <- sample_data(meta)
    
    ps <- phyloseq(OTU, TAX, META)
    
    # Alpha diversity
    alpha <- estimate_richness(ps, measures=c("Shannon", "Simpson", "Chao1"))
    alpha\$Sample <- rownames(alpha)
    write.table(alpha, "alpha_diversity.tsv", sep="\\t", row.names=FALSE)
    
    # Beta diversity (Bray-Curtis)
    bc <- as.matrix(vegdist(otu_table(ps), method="bray"))
    write.table(bc, "beta_diversity.tsv", sep="\\t")
    
    # Plots
    pdf("phyloseq_plots.pdf", width=12, height=8)
    plot_richness(ps, x="condition", measures=c("Shannon", "Simpson"))
    ord <- ordinate(ps, "NMDS", "bray")
    plot_ordination(ps, ord, type="samples", color="condition")
    dev.off()
    """
}