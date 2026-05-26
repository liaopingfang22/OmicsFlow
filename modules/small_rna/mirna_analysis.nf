process MIRDEEP2_PREPROCESS {
    tag "MIRDEEP2_PREP on ${sample}"
    container "quay.io/biocontainers/mirdeep2:2.0.1.3--hdfd78af_0"
    input: tuple val(sample), path(reads)
    output: tuple val(sample), path("${sample}_collapsed.fa"), emit: fasta; path "${sample}_reads_collapsed.arf", emit: arf
    script:
    """
    gunzip -c ${reads} > reads.fq
    mapper.pl reads.fq -c -i -j -l 18 -m -p ${sample} -s ${sample}_collapsed.fa -t ${sample}_reads_collapsed.arf -v
    """
}

process MIRDEEP2_QUANTIFY {
    tag "MIRDEEP2_QUANT on ${sample}"
    container "quay.io/biocontainers/mirdeep2:2.0.1.3--hdfd78af_0"
    input: tuple val(sample), path(fasta), path(arf); path(mirna_ref); path(genome); path(mature)
    output: path "${sample}_miRNAs_expressed.csv", emit: results; path "${sample}_result_*.csv", emit: all_results
    script:
    """
    miRDeep2.pl ${fasta} ${genome} ${sample}_reads_collapsed.arf ${mature} none ${mirna_ref} -t hsa 2> report.log
    """
}

process MIRGE3_QUANTIFY {
    tag "MIRGE3 on ${sample}"
    container "quay.io/biocontainers/mirge3:3.0.0--pyhdfd78af_0"
    input: tuple val(sample), path(reads)
    output: tuple val(sample), path("${sample}_miRge3_quantification.csv"), emit: counts
    script:
    """
    mirge3 -i ${reads} -o ${sample}_miRge3_quantification.csv -species hsa -cpu ${task.cpus}
    """
}