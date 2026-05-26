process KRAKEN2_BUILD {
    tag "KRAKEN2_BUILD"
    container "quay.io/biocontainers/kraken2:2.1.3--pl5321hdc45558_2"

    input:
    path(db_archive)

    output:
    path "kraken2_db", emit: db

    script:
    """
    mkdir -p kraken2_db
    tar -xzf ${db_archive} -C kraken2_db --strip-components=1
    """
}

process KRAKEN2_CLASSIFY {
    tag "KRAKEN2 on ${sample}"
    container "quay.io/biocontainers/kraken2:2.1.3--pl5321hdc45558_2"
    cpus params.threads ?: 8

    input:
    tuple val(sample), path(reads)
    path(db)

    output:
    tuple val(sample), path("${sample}.kraken2.report"), emit: report
    tuple val(sample), path("${sample}.kraken2.output"), emit: output

    script:
    """
    kraken2 --db ${db} \
        --threads ${task.cpus} \
        --report ${sample}.kraken2.report \
        --output ${sample}.kraken2.output \
        --gzip-compressed \
        ${reads}
    """
}

process KRAKEN2_CLASSIFY_PAIRED {
    tag "KRAKEN2 on ${sample}"
    container "quay.io/biocontainers/kraken2:2.1.3--pl5321hdc45558_2"
    cpus params.threads ?: 8

    input:
    tuple val(sample), path(read1), path(read2)
    path(db)

    output:
    tuple val(sample), path("${sample}.kraken2.report"), emit: report
    tuple val(sample), path("${sample}.kraken2.output"), emit: output

    script:
    """
    kraken2 --db ${db} \
        --threads ${task.cpus} \
        --report ${sample}.kraken2.report \
        --output ${sample}.kraken2.output \
        --paired \
        --gzip-compressed \
        ${read1} ${read2}
    """
}

process KRAKEN2_MERGE_REPORTS {
    tag "KRAKEN2_MERGE"
    container "quay.io/biocontainers/krakentools:1.2--pyh5e36f6f_2"

    input:
    path(reports)

    output:
    path "merged_kraken2_report.tsv", emit: merged

    script:
    """
    #!/usr/bin/env python3
    import os
    import pandas as pd

    all_reports = {}
    for f in sorted(os.listdir('.')):
        if f.endswith('.kraken2.report'):
            sample = f.replace('.kraken2.report', '')
            df = pd.read_csv(f, sep='\\t', header=None,
                names=['pct', 'reads_clade', 'reads_direct', 'rank', 'taxid', 'name'])
            df['name'] = df['name'].str.strip()
            all_reports[sample] = df.set_index('taxid')['reads_clade']

    merged = pd.DataFrame(all_reports).fillna(0).astype(int)
    merged.index.name = 'taxid'
    merged.to_csv('merged_kraken2_report.tsv', sep='\\t')
    """
}

process BRACKEN_ESTIMATE {
    tag "BRACKEN on ${sample}"
    container "quay.io/biocontainers/bracken:2.9--py39h28a0618_0"

    input:
    tuple val(sample), path(report)
    path(db)

    output:
    tuple val(sample), path("${sample}.bracken.species"), emit: bracken
    tuple val(sample), path("${sample}.bracken.report"), emit: report

    script:
    """
    bracken -d ${db} \
        -i ${report} \
        -o ${sample}.bracken.species \
        -w ${sample}.bracken.report \
        -r 150 \
        -l S \
        -t 10
    """
}