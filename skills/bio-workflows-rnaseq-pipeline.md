---
name: bio-workflows-rnaseq-pipeline
description: End-to-end RNA-seq workflow from FASTQ to gene expression quantification
category: workflows
tags: [rnaseq, star, salmon, quantification, expression]
---

# RNA-seq Analysis Pipeline

## Workflow Overview

Complete RNA-seq analysis from raw FASTQ reads to gene-level count matrices and TPM values. Supports both STAR+featureCounts and STAR+Salmon quantification modes.

## Pipeline Steps

### 1. Quality Control (FastQC + MultiQC)
```bash
fastqc -t 8 -o qc_results sample_R1.fq.gz sample_R2.fq.gz
multiqc qc_results -o multiqc_report
```

### 2. Adapter Trimming (Trim Galore / fastp)
```bash
# Option A: Trim Galore
trim_galore --paired --quality 20 --length 36 --cores 4 \
    sample_R1.fq.gz sample_R2.fq.gz

# Option B: fastp (faster)
fastp -i sample_R1.fq.gz -I sample_R2.fq.gz \
    -o sample_R1_trimmed.fq.gz -O sample_R2_trimmed.fq.gz \
    --thread 8 --html fastp_report.html
```

### 3. Reference Genome Preparation
```bash
# STAR index (requires ~32GB RAM for human genome)
STAR --runMode genomeGenerate \
     --genomeDir star_index \
     --genomeFastaFiles GRCh38.primary_assembly.genome.fa \
     --sjdbGTFfile gencode.v44.annotation.gtf \
     --sjdbOverhang 149 \
     --runThreadN 16

# Salmon index (for quasi-mapping)
salmon index -t GRCh38.cdna.all.fa -i salmon_index --threads 8
```

### 4. Alignment (STAR)
```bash
# Two-pass mode for novel junction discovery
STAR --runMode alignReads \
     --genomeDir star_index \
     --readFilesIn sample_R1_trimmed.fq.gz sample_R2_trimmed.fq.gz \
     --readFilesCommand zcat \
     --outSAMtype BAM SortedByCoordinate \
     --outBAMsortingThreadN 8 \
     --quantMode GeneCounts TranscriptomeSAM \
     --twopassMode Basic \
     --outFileNamePrefix sample_ \
     --runThreadN 16 \
     --outSAMattrRGline ID:sample SM:sample PL:ILLUMINA
```

### 5. Quantification

#### Option A: featureCounts (gene-level)
```bash
featureCounts -T 8 -p --countReadPairs -a gencode.v44.annotation.gtf \
    -o gene_counts.txt sample_Aligned.sortedByCoord.out.bam
```

#### Option B: Salmon (transcript-level, alignment-free)
```bash
salmon quant -i salmon_index -l A \
    -1 sample_R1_trimmed.fq.gz -2 sample_R2_trimmed.fq.gz \
    -p 8 --validateMappings -o salmon_sample
```

### 6. Quality Metrics (SAMtools + RSeQC)
```bash
samtools flagstat sample_Aligned.sortedByCoord.out.bam
samtools stats sample_Aligned.sortedByCoord.out.bam
# RSeQC
geneBody_coverage.py -i sample.bam -r housekeeping.bed -o sample
read_distribution.py -i sample.bam -r annotation.bed
```

### 7. MultiQC Report
```bash
multiqc fastqc/ star/ salmon/ samtools/ -o final_report
```

## Key QC Metrics

| Metric | Good | Warning | Fail |
|--------|------|---------|------|
| Unique mapping rate | >80% | 60-80% | <60% |
| Multi-mapping rate | <10% | 10-20% | >20% |
| rRNA contamination | <5% | 5-10% | >10% |
| Gene body coverage | Uniform | 3'/5' bias | Extreme bias |
| Duplication rate | <30% | 30-50% | >50% |

## Output Files

| File | Description |
|------|-------------|
| `counts_matrix.tsv` | Raw gene counts (samples × genes) |
| `tpm_matrix.tsv` | TPM normalized expression |
| `star_log/` | STAR alignment logs per sample |
| `multiqc_report/` | Comprehensive QC report |
| `salmon_quant/` | Salmon quantification results per sample |

## Common Issues

1. **Low mapping rate**: Check if correct genome version is used
2. **High duplication**: May indicate over-amplification or low input
3. **3' bias**: Common with polyA selection, worse with degraded RNA
4. **Strand-specific library**: Use `--sA`, `--sS`, or `--sR` in featureCounts depending on protocol

## Nextflow Implementation

See `workflows/rnaseq_workflow.nf` for automated pipeline execution.
