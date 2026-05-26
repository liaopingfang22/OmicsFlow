---
name: bio-workflows-wgs-variant-calling
description: End-to-end WGS variant calling from FASTQ to filtered VCF using GATK Best Practices
---

# WGS Variant Calling Pipeline (GATK Best Practices)

## Pipeline Overview

Complete germline variant calling from whole genome sequencing (WES/WGS) data following GATK Best Practices.

## Pipeline Steps

### 1. Quality Control
- FastQC per-base quality, adapter content, GC bias
- MultiQC aggregated report

### 2. Adapter Trimming (Trim Galore)
```bash
trim_galore --paired --quality 20 R1.fq.gz R2.fq.gz
```

### 3. Alignment (BWA-MEM2)
```bash
bwa-mem2 mem -t 8 -R "@RG\tID:sample\tSM:sample\tPL:ILLUMINA" \
    ref.fa R1.fq.gz R2.fq.gz | samtools sort -o sample.bam
```

### 4. Mark Duplicates (GATK)
```bash
gatk MarkDuplicates -I sample.bam -O sample.dedup.bam -M metrics.txt --CREATE_INDEX true
```

### 5. Variant Calling (GATK HaplotypeCaller)
```bash
# Per-sample GVCF
gatk HaplotypeCaller -R ref.fa -I sample.dedup.bam -O sample.g.vcf.gz -ERC GVCF

# Joint genotyping
gatk GenotypeGVCFs -R ref.fa -V sample1.g.vcf.gz -V sample2.g.vcf.gz -O cohort.vcf.gz
```

### 6. Variant Filtering
```bash
gatk VariantFiltration -R ref.fa -V cohort.vcf.gz -O filtered.vcf.gz \
    --filter-expression "QD < 2.0" --filter-name "LowQD" \
    --filter-expression "FS > 60.0" --filter-name "HighFS" \
    --filter-expression "MQ < 40.0" --filter-name "LowMQ"
```

## Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `--reference` | Reference genome FASTA | Required |
| `--dbsnp` | dbSNP VCF for annotation | Optional |
| `--threads` | Number of threads | 8 |

## Output Files

- `*.dedup.bam` — Deduplicated aligned reads
- `*.g.vcf.gz` — Per-sample GVCF
- `cohort.vcf.gz` — Joint-called VCF
- `filtered.vcf.gz` — Quality-filtered VCF