process QC_FASTQC {
    tag "FASTQC on ${sample}"
    container "singularity://qc_tools.sif"
    
    input:
    tuple val(sample), path(fastq)
    
    output:
    path "*.html", emit: html
    path "*.zip", emit: zip
    
    script:
    """
    fastqc -o . -f fastq ${fastq}
    """
}

process QC_MULTIQC {
    tag "MULTIQC"
    container "singularity://qc_tools.sif"
    
    input:
    path(input_dir)
    
    output:
    path "multiqc_report.html", emit: report
    
    script:
    """
    multiqc ${input_dir} -o . -n multiqc_report.html
    """
}

process TRIM_ADAPTERS {
    tag "TRIM on ${sample}"
    container "singularity://qc_tools.sif"
    
    input:
    tuple val(sample), path(fastq)
    
    output:
    tuple val(sample), path("*.fq.gz"), emit: trimmed
    
    script:
    """
    trim_galore -q 20 ${fastq}
    """
}
