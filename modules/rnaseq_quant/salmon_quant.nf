process SALMON_INDEX {
    tag "SALMON_INDEX"
    container "quay.io/biocontainers/salmon:1.10.3--h6dccd9a_2"
    cpus params.threads ?: 8

    input:
    path(transcriptome)

    output:
    path "salmon_index", emit: index

    script:
    """
    salmon index -t ${transcriptome} -i salmon_index -p ${task.cpus}
    """
}

process SALMON_QUANT {
    tag "SALMON_QUANT on ${sample}"
    container "quay.io/biocontainers/salmon:1.10.3--h6dccd9a_2"
    cpus params.threads ?: 8

    input:
    tuple val(sample), path(read1), path(read2)
    path(index)

    output:
    tuple val(sample), path("${sample}_quant"), emit: quant
    path "${sample}_quant/quant.sf", emit: sf

    script:
    """
    salmon quant -i ${index} \
        -l A \
        -1 ${read1} \
        -2 ${read2} \
        -p ${task.cpus} \
        --validateMappings \
        --gcBias \
        --seqBias \
        -o ${sample}_quant
    """
}

process SALMON_QUANT_SINGLE {
    tag "SALMON_QUANT on ${sample}"
    container "quay.io/biocontainers/salmon:1.10.3--h6dccd9a_2"
    cpus params.threads ?: 8

    input:
    tuple val(sample), path(reads)
    path(index)

    output:
    tuple val(sample), path("${sample}_quant"), emit: quant

    script:
    """
    salmon quant -i ${index} \
        -l A \
        -r ${reads} \
        -p ${task.cpus} \
        --validateMappings \
        -o ${sample}_quant
    """
}

process SALMON_MERGE {
    tag "SALMON_MERGE"
    container "quay.io/biocontainers/salmon:1.10.3--h6dccd9a_2"

    input:
    path(quant_dirs)

    output:
    path "salmon.merged.gene_counts.tsv", emit: counts
    path "salmon.merged.gene_tpm.tsv", emit: tpm

    script:
    """
    #!/usr/bin/env python3
    import os
    import pandas as pd

    samples = []
    counts_list = []
    tpm_list = []

    for d in sorted(os.listdir('.')):
        sf = os.path.join(d, 'quant.sf')
        if os.path.isfile(sf):
            df = pd.read_csv(sf, sep='\t')
            sample_name = d.replace('_quant', '')
            samples.append(sample_name)
            counts_list.append(df.set_index('Name')['NumReads'])
            tpm_list.append(df.set_index('Name')['TPM'])

    counts_df = pd.DataFrame(counts_list, index=samples).T
    counts_df.index.name = 'Name'
    counts_df.to_csv('salmon.merged.gene_counts.tsv', sep='\\t')

    tpm_df = pd.DataFrame(tpm_list, index=samples).T
    tpm_df.index.name = 'Name'
    tpm_df.to_csv('salmon.merged.gene_tpm.tsv', sep='\\t')
    """
}