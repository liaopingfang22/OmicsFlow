process CNVKIT_TARGET {
    tag "CNVKIT_TARGET on ${bam.baseName}"
    container "singularity://cnvkit.sif"
    
    input:
    path(bam)
    val(target_bed)
    
    output:
    path "*.target.bed", emit: targets
    
    script:
    """
    cnvkit target ${target_bed ?: ''} -o targets.bed
    """
}

process CNVKIT_REFERENCE {
    tag "CNVKIT_REFERENCE"
    container "singularity://cnvkit.sif"
    
    input:
    path(bams)
    path(targets)
    
    output:
    path "reference.cnn", emit: reference
    
    script:
    """
    cnvkit reference ${bams.join(' ')} -f ${targets} -o reference.cnn
    """
}

process CNVKIT_ANALYSIS {
    tag "CNVKIT_ANALYSIS on ${bam.baseName}"
    container "singularity://cnvkit.sif"
    
    input:
    path(bam)
    path(reference)
    
    output:
    path "*.cnr", emit: cnr
    path "*.cns", emit: cns
    
    script:
    """
    SAMPLE=\$(basename ${bam} .bam)
    cnvkit coverage ${bam} ${reference} -o \${SAMPLE}.cnr
    cnvkit segment \${SAMPLE}.cnr -o \${SAMPLE}.cns
    """
}

process CNVKIT_EXPORT {
    tag "CNVKIT_EXPORT"
    container "singularity://cnvkit.sif"
    
    input:
    path(cnr_files)
    path(cns_files)
    
    output:
    path "cnv_results.tsv", emit: results
    
    script:
    """
    cnvkit export seg \${CNS[0]} -o cnv_results.tsv
    """
}
