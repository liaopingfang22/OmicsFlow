process MINIMAP2_ALIGN {
    tag "MINIMAP2 on ${sample}"
    container "quay.io/biocontainers/minimap2:2.28--h7132678_0"
    cpus params.threads ?: 8
    input: tuple val(sample), path(reads); path(reference)
    output: tuple val(sample), path("${sample}.sorted.bam"), emit: bam
    script:
    """
    minimap2 -ax map-ont -t ${task.cpus} ${reference} ${reads} | samtools sort -@ ${task.cpus} -o ${sample}.sorted.bam -
    samtools index ${sample}.sorted.bam
    """
}

process MINIMAP2_HIFI {
    tag "MINIMAP2_HIFI on ${sample}"
    container "quay.io/biocontainers/minimap2:2.28--h7132678_0"
    cpus params.threads ?: 8
    input: tuple val(sample), path(reads); path(reference)
    output: tuple val(sample), path("${sample}.sorted.bam"), emit: bam
    script:
    """
    minimap2 -ax map-hifi -t ${task.cpus} ${reference} ${reads} | samtools sort -@ ${task.cpus} -o ${sample}.sorted.bam -
    samtools index ${sample}.sorted.bam
    """
}

process SNIFFLES_CALL {
    tag "SNIFFLES on ${sample}"
    container "quay.io/biocontainers/sniffles:2.3.3--hdfd78af_0"
    input: tuple val(sample), path(bam), path(bai)
    output: tuple val(sample), path("${sample}.sv.vcf"), emit: vcf
    script: "sniffles --input ${bam} --vcf ${sample}.sv.vcf --reference ${params.reference}"
}

process CLAIR3_CALL {
    tag "CLAIR3 on ${sample}"
    container "quay.io/biocontainers/clair3:1.0.10--hdfd78af_0"
    cpus params.threads ?: 8
    input: tuple val(sample), path(bam), path(bai); path(reference); path(ref_idx)
    output: tuple val(sample), path("merge_output.vcf.gz"), emit: vcf
    script:
    """
    run_clair3.sh --bam_fn=${bam} --ref_fn=${reference} --output=output_dir \
        --platform="ont" --sample_name=${sample} --threads=${task.cpus} --disable_c_gpu
    mv output_dir/merge_output.vcf.gz .
    """
}

process MEDAKA_POLISH {
    tag "MEDAKA on ${sample}"
    container "quay.io/biocontainers/medaka:2.0.1--py310h8b49995_0"
    cpus params.threads ?: 4
    input: tuple val(sample), path(reads); path(assembly)
    output: tuple val(sample), path("${sample}_polished.fasta"), emit: polished
    script:
    """
    medaka_consensus -i ${reads} -d ${assembly} -o polished_dir -t ${task.cpus} -m r941_min_sup_g507
    mv polished_dir/consensus.fasta ${sample}_polished.fasta
    """
}
