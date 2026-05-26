process MAXQUANT_SEARCH {
    tag "MAXQUANT"
    container "quay.io/biocontainers/maxquant:2.6.5.0--hdfd78af_0"
    input: path(mzml_files); path(fasta); path(params_file)
    output: path "combined/txt/proteinGroups.txt", emit: protein_groups; path "combined/txt/peptides.txt", emit: peptides
    script:
    """
    mkdir -p mq_run && cp ${params_file} mq_run/par.xml
    cp ${mzml_files} mq_run/ && cp ${fasta} mq_run/
    maxquant mq_run/par.xml
    """
}

process DIANN_ANALYSIS {
    tag "DIANN"
    container "quay.io/biocontainers/diann:1.8.1--hdfd78af_0"
    cpus params.threads ?: 4
    input: path(mzml_files); path(library)
    output: path "diann_output.tsv", emit: results
    script:
    """
    diann --f ${mzml_files.join(' --f ')} --lib ${library} --out diann_output.tsv --threads ${task.cpus}
    """
}
