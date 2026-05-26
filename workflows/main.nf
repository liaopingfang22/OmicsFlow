nextflow.enable.dsl = 2

params.input = null
params.pipeline = "cnv"
params.output_dir = "./results"
params.threads = 4
params.singularity_cache = "/data/singularity"

singularity {
    enabled = true
    autoMounts = true
    cacheDir = params.singularity_cache
}

log.info """
==========================================
 OmicsFlow Main Pipeline
==========================================
 Pipeline: ${params.pipeline}
 Output Dir: ${params.output_dir}
 Singularity Cache: ${params.singularity_cache}
==========================================
"""

workflow {
    main:
        pipeline_file = get_pipeline_file(params.pipeline)
        log.info "Running pipeline: ${params.pipeline}"
        log.info "Pipeline file: ${pipeline_file}"
}

def get_pipeline_file(pipeline_type) {
    switch (pipeline_type) {
        case "cnv":
            return "${projectDir}/cnv_workflow.nf"
        case "de":
        case "differential_expression":
            return "${projectDir}/de_workflow.nf"
        case "qc":
            return "${projectDir}/qc_workflow.nf"
        case "rnaseq":
        case "rna_seq":
        case "rna-seq":
            return "${projectDir}/rnaseq_workflow.nf"
        case "wgs":
        case "variant_calling":
        case "variant-calling":
            return "${projectDir}/wgs_variant_workflow.nf"
        case "metagenomics":
        case "metagenome":
        case "kraken":
            return "${projectDir}/metagenomics_workflow.nf"
        case "amplicon":
        case "16s":
        case "its":
        case "dada2":
            return "${projectDir}/amplicon_workflow.nf"
        case "tcr":
        case "bcr":
        case "immune":
        case "repertoire":
            return "${projectDir}/tcr_workflow.nf"
        case "atac":
        case "atacseq":
        case "atac-seq":
        case "chromatin":
            return "${projectDir}/atac_workflow.nf"
        case "scrnaseq":
        case "scrna":
            return "${projectDir}/scrnaseq_workflow.nf"
        case "spatial":
        case "visium":
        case "stereo-seq":
            return "${projectDir}/spatial_workflow.nf"
        case "chipseq":
        case "chip-seq":
        case "chip":
            return "${projectDir}/chipseq_workflow.nf"
        case "smrna":
        case "small-rna":
        case "mirna":
        case "mirna-seq":
            return "${projectDir}/smrna_workflow.nf"
        case "somatic":
        case "mutect":
        case "tumor":
            return "${projectDir}/somatic_workflow.nf"
        case "methylation":
        case "bisulfite":
        case "bs-seq":
        case "wgbs":
            return "${projectDir}/methylation_workflow.nf"
        case "longread":
        case "long-read":
        case "nanopore":
        case "pacbio":
        case "ont":
            return "${projectDir}/longread_workflow.nf"
        case "wes":
        case "exome":
        case "targeted":
            return "${projectDir}/wes_workflow.nf"
        case "proteomics":
        case "mass-spec":
        case "dda":
        case "dia":
            return "${projectDir}/proteomics_workflow.nf"
        default:
            return "${projectDir}/cnv_workflow.nf"
    }
}

workflow.onComplete {
    log.info """
    ==========================================
     Pipeline Complete
     Status: ${workflow.status}
     Duration: ${workflow.duration}
    ==========================================
    """
}

workflow.onError {
    log.error """
    ==========================================
     Pipeline Failed
     Error: ${workflow.errorMessage}
     ==========================================
    """
}

// Note: scrnaseq already registered via case "spatial" above, 
// but adding explicit scrnaseq route:
// case "scrnaseq" maps to scrnaseq_workflow.nf
