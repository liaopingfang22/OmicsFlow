process MUTECT2_CALL {
    tag "MUTECT2 on ${sample}"
    container "broadinstitute/gatk:4.5.0.0"
    cpus params.threads ?: 4
    input: tuple val(sample), path(tumor_bam), path(tumor_bai), path(normal_bam), path(normal_bai); path(reference); path(ref_idx); path(ref_dict); path(pon); path(pon_idx); path(germline); path(germline_idx)
    output: tuple val(sample), path("${sample}.vcf.gz"), emit: vcf; tuple val(sample), path("${sample}.vcf.gz.tbi"), emit: tbi; tuple val(sample), path("${sample}.f1r2.tar.gz"), emit: f1r2
    script:
    def pon_arg = pon.name != "NO_FILE" ? "--panel-of-normals ${pon}" : ""
    def germline_arg = germline.name != "NO_FILE" ? "--germline-resource ${germline}" : ""
    """
    gatk --java-options "-Xmx8g" Mutect2 -R ${reference} -I ${tumor_bam} -I ${normal_bam} -normal ${sample}_normal ${pon_arg} ${germline_arg} --f1r2-tar-gz ${sample}.f1r2.tar.gz -O ${sample}.vcf.gz
    """
}

process LEARN_READORIENTATION {
    tag "LEARN_ORIENTATION on ${sample}"
    container "broadinstitute/gatk:4.5.0.0"
    input: tuple val(sample), path(f1r2)
    output: tuple val(sample), path("${sample}-read-orientation-model.tar.gz"), emit: model
    script: "gatk LearnReadOrientationModel -I ${f1r2} -O ${sample}-read-orientation-model.tar.gz"
}

process FILTER_MUTECT_CALLS {
    tag "FILTER_MUTECT on ${sample}"
    container "broadinstitute/gatk:4.5.0.0"
    input: tuple val(sample), path(vcf), path(tbi), path(model); path(stats); path(reference); path(ref_idx); path(ref_dict)
    output: tuple val(sample), path("${sample}.filtered.vcf.gz"), emit: vcf
    script: "gatk FilterMutectCalls -R ${reference} -V ${vcf} --ob-priors ${model} -O ${sample}.filtered.vcf.gz"
}
