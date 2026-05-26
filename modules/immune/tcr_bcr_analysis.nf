process MIXCR_ALIGN {
    tag "MIXCR_ALIGN on ${sample}"
    container "quay.io/biocontainers/mixcr:4.6.0--hdfd78af_0"
    cpus params.threads ?: 4

    input:
    tuple val(sample), path(read1), path(read2)

    output:
    tuple val(sample), path("${sample}.vdjca"), emit: vdjca

    script:
    """
    mixcr align -p generic-amplicon \
        --species hs \
        ${read1} ${read2} \
        ${sample}.vdjca
    """
}

process MIXCR_ASSEMBLE {
    tag "MIXCR_ASSEMBLE on ${sample}"
    container "quay.io/biocontainers/mixcr:4.6.0--hdfd78af_0"
    cpus params.threads ?: 4

    input:
    tuple val(sample), path(vdjca)

    output:
    tuple val(sample), path("${sample}.clns"), emit: clns

    script:
    """
    mixcr assemble ${sample}.vdjca ${sample}.clns
    """
}

process MIXCR_EXPORT {
    tag "MIXCR_EXPORT on ${sample}"
    container "quay.io/biocontainers/mixcr:4.6.0--hdfd78af_0"

    input:
    tuple val(sample), path(clns)

    output:
    tuple val(sample), path("${sample}_clonotypes.tsv"), emit: clonotypes
    tuple val(sample), path("${sample}_clonotypes.all.tsv"), emit: all_clonotypes

    script:
    """
    mixcr exportClones ${clns} ${sample}_clonotypes.tsv
    mixcr exportClones --all ${clns} ${sample}_clonotypes.all.tsv
    """
}

process MIXCR_REPORT {
    tag "MIXCR_REPORT on ${sample}"
    container "quay.io/biocontainers/mixcr:4.6.0--hdfd78af_0"

    input:
    tuple val(sample), path(vdjca)

    output:
    tuple val(sample), path("${sample}_align.report.txt"), emit: report

    script:
    """
    mixcr alignReport ${vdjca} ${sample}_align.report.txt
    """
}

process REPERTOIRE_DIVERSITY {
    tag "REPERTOIRE_DIVERSITY on ${sample}"
    container "quay.io/biocontainers/scipy:1.11.0--py310h3bd602e_0"

    input:
    tuple val(sample), path(clonotypes)

    output:
    tuple val(sample), path("${sample}_diversity.tsv"), emit: diversity

    script:
    """
    #!/usr/bin/env python3
    import pandas as pd
    import numpy as np
    
    df = pd.read_csv("${clonotypes}", sep="\\t")
    
    clone_counts = df["cloneCount"].values if "cloneCount" in df.columns else df.iloc[:, 0].values
    total = clone_counts.sum()
    freq = clone_counts / total
    freq = freq[freq > 0]
    
    shannon = -np.sum(freq * np.log2(freq))
    simpson = 1 - np.sum(freq ** 2)
    gini_simpson = 1 - np.sum(freq ** 2)
    inv_simpson = 1 / np.sum(freq ** 2)
    richness = len(clone_counts)
    
    hill0 = richness
    hill1 = np.exp(shannon)
    hill2 = 1 / simpson if simpson > 0 else 0
    
    # Clonality (1 - normalized Shannon entropy)
    max_shannon = np.log2(richness) if richness > 0 else 1
    clonality = 1 - (shannon / max_shannon) if max_shannon > 0 else 0
    
    results = pd.DataFrame({
        "sample": ["${sample}"],
        "total_clones": [richness],
        "total_reads": [int(total)],
        "shannon_entropy": [round(shannon, 4)],
        "simpson_index": [round(simpson, 4)],
        "inverse_simpson": [round(inv_simpson, 4)],
        "gini_simpson": [round(gini_simpson, 4)],
        "clonality": [round(clonality, 4)],
        "hill_number_0": [round(hill0, 2)],
        "hill_number_1": [round(hill1, 2)],
        "hill_number_2": [round(hill2, 2)],
    })
    results.to_csv("${sample}_diversity.tsv", sep="\\t", index=False)
    """
}