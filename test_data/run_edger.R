#!/usr/bin/env Rscript

library(edgeR)
library(dplyr)

cat("==========================================\n")
cat("  EdgeR Differential Expression Analysis\n")
cat("==========================================\n")

args <- commandArgs(trailingOnly = TRUE)
count_file <- args[1]
sample_file <- args[2]
output_dir <- args[3]
comparison <- args[4]

cat("Count file:", count_file, "\n")
cat("Sample file:", sample_file, "\n")
cat("Output dir:", output_dir, "\n")
cat("Comparison:", comparison, "\n")

if (!dir.exists(output_dir)) {
    dir.create(output_dir, recursive = TRUE)
}

counts <- read.delim(count_file, sep = "\t", header = TRUE, stringsAsFactors = FALSE)
cat("\nLoaded count matrix:", nrow(counts), "genes x", ncol(counts)-2, "samples\n")

gene_info <- counts[, 1:2]
gene_info$gene_id_clean <- gsub("\\..*$", "", gene_info$gene_id)

counts <- counts[, -c(1, 2)]
rownames(counts) <- gene_info$gene_id_clean

samples <- read.delim(sample_file, sep = "\t", header = TRUE, stringsAsFactors = FALSE)
cat("Loaded sample sheet:", nrow(samples), "samples\n")

common_samples <- intersect(colnames(counts), samples$sample_id)
counts <- counts[, common_samples, drop = FALSE]
samples <- samples[samples$sample_id %in% common_samples, ]
samples <- samples[match(colnames(counts), samples$sample_id), ]

if (comparison == "A549_24_vs_NC") {
    group1 <- "A549_24"
    group2 <- "A549_NC"
    cat("\n--- Comparing A549_24 vs A549_NC ---\n")
} else if (comparison == "A549_48_vs_NC") {
    group1 <- "A549_48"
    group2 <- "A549_NC"
    cat("\n--- Comparing A549_48 vs A549_NC ---\n")
} else {
    stop("Unknown comparison: ", comparison)
}

keep_groups <- c(group2, group1)
samples_filtered <- samples[samples$group %in% keep_groups, ]
counts_filtered <- counts[, samples_filtered$sample_id, drop = FALSE]

samples_filtered$group <- factor(samples_filtered$group, levels = keep_groups)

cat("Samples in comparison:\n")
print(samples_filtered)

cat("\nUsing", ncol(counts_filtered), "samples for analysis\n")
counts_filtered <- counts_filtered[rowSums(counts_filtered > 0) >= 2, ]
cat("After filtering low expressed genes:", nrow(counts_filtered), "genes remaining\n")

dge <- DGEList(counts = counts_filtered)
dge <- calcNormFactors(dge)

cat("\nNormalization factors:\n")
print(dge$samples)

design <- model.matrix(~ group, data = samples_filtered)
cat("\nDesign matrix:\n")
print(design)

dge <- estimateDisp(dge, design)
cat("\nCommon dispersion:", dge$common.dispersion, "\n")

fit <- glmQLFit(dge, design)
lrt <- glmQLFTest(fit, coef = 2)

results <- topTags(lrt, n = nrow(counts_filtered))
results_df <- as.data.frame(results$table)
results_df$gene_id <- rownames(results_df)

gene_map <- gene_info$gene_name
names(gene_map) <- gene_info$gene_id_clean
results_df$gene_name <- gene_map[results_df$gene_id]

results_df <- results_df %>%
    select(gene_id, gene_name, everything()) %>%
    arrange(PValue)

results_file <- file.path(output_dir, paste0(comparison, "_results.csv"))
write.csv(results_df, results_file, row.names = FALSE)
cat("\nResults saved to:", results_file, "\n")

sig_genes <- results_df %>% filter(FDR < 0.05)
sig_up <- sig_genes %>% filter(logFC > 1)
sig_down <- sig_genes %>% filter(logFC < -1)

cat("\n==========================================\n")
cat("  Summary: ", comparison, "\n")
cat("==========================================\n")
cat("Total genes tested:", nrow(results_df), "\n")
cat("Significant (FDR < 0.05):", nrow(sig_genes), "\n")
cat("  Upregulated (logFC > 1):", nrow(sig_up), "\n")
cat("  Downregulated (logFC < -1):", nrow(sig_down), "\n")
cat("==========================================\n")

cat("\nTop 10 significant genes:\n")
if (nrow(sig_genes) > 0) {
    print(head(sig_genes[, c("gene_id", "gene_name", "logFC", "FDR")], 10))
} else {
    cat("No significant genes found\n")
}

saveRDS(lrt, file.path(output_dir, paste0(comparison, "_fit.rds")))
saveRDS(dge, file.path(output_dir, paste0(comparison, "_dge.rds")))

cat("\nAnalysis complete!\n")
