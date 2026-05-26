nextflow.enable.dsl = 2

params.input_bam = null
params.sample_sheet = null
params.reference = null
params.output_dir = "./results"
params.threads = 4
params.target_bed = null
params.singularity_image = "cnvkit.sif"

singularity {
    enabled = true
    autoMounts = true
    cacheDir = "${params.singularity_cache ?: '/data/singularity'}"
}

log.info """
==========================================
 CNV Analysis Pipeline (Singularity)
==========================================
 Input BAM:     ${params.input_bam}
 Sample Sheet:  ${params.sample_sheet}
 Reference:     ${params.reference}
 Output Dir:    ${params.output_dir}
 Threads:       ${params.threads}
 Singularity:   ${params.singularity_image}
==========================================
"""

include { CNVKIT_TARGET } from "${projectDir}/modules/cnv_analysis/cnvkit.nf"
include { CNVKIT_REFERENCE } from "${projectDir}/modules/cnv_analysis/cnvkit.nf"
include { CNVKIT_ANALYSIS } from "${projectDir}/modules/cnv_analysis/cnvkit.nf"
include { CNVKIT_EXPORT } from "${projectDir}/modules/cnv_analysis/cnvkit.nf"

workflow {
    main:
        input_ch = channel.fromPath(params.input_bam)
        
        CNVKIT_TARGET(input_ch, params.target_bed)
        
        CNVKIT_REFERENCE(
            input_ch.collect(),
            CNVKIT_TARGET.out.targets
        )
        
        CNVKIT_ANALYSIS(
            input_ch.collect(),
            CNVKIT_REFERENCE.out.reference
        )
        
        CNVKIT_EXPORT(
            CNVKIT_ANALYSIS.out.cnr.collect(),
            CNVKIT_ANALYSIS.out.cns.collect()
        )
}
