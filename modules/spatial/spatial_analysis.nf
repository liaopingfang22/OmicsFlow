process SPATIAL_LOAD_VISIUM {
    tag "SPATIAL_LOAD on ${sample}"
    container "quay.io/biocontainers/squidpy:1.4.1--pyhdfd78af_0"

    input:
    path(space_ranger_output)

    output:
    path "${sample}_spatial.h5ad", emit: h5ad

    script:
    """
    #!/usr/bin/env python3
    import squidpy as sq
    import scanpy as sc
    from pathlib import Path

    adata = sq.datasets.visium_hne_adata() if not Path("${space_ranger_output}").exists() \
        else sc.read_visium("${space_ranger_output}")
    adata.var_names_make_unique()
    adata.write_h5ad("${sample}_spatial.h5ad")
    """
}

process SPATIAL_PREPROCESS {
    tag "SPATIAL_PREPROCESS on ${sample}"
    container "quay.io/biocontainers/squidpy:1.4.1--pyhdfd78af_0"

    input:
    tuple val(sample), path(h5ad)

    output:
    tuple val(sample), path("${sample}_preprocessed.h5ad"), emit: h5ad

    script:
    """
    #!/usr/bin/env python3
    import squidpy as sq
    import scanpy as sc

    adata = sc.read_h5ad("${h5ad}")
    adata.var_names_make_unique()
    sc.pp.filter_cells(adata, min_counts=100)
    sc.pp.filter_genes(adata, min_cells=3)
    adata.var['mt'] = adata.var_names.str.startswith('MT-')
    sc.pp.calculate_qc_metrics(adata, qc_vars=['mt'], inplace=True)
    adata = adata[adata.obs.pct_counts_mt < 20]
    sc.pp.normalize_total(adata, target_sum=1e4)
    sc.pp.log1p(adata)
    adata.write_h5ad("${sample}_preprocessed.h5ad")
    """
}

process SPATIAL_BUILD_GRAPH {
    tag "SPATIAL_GRAPH on ${sample}"
    container "quay.io/biocontainers/squidpy:1.4.1--pyhdfd78af_0"

    input:
    tuple val(sample), path(h5ad)

    output:
    tuple val(sample), path("${sample}_graph.h5ad"), emit: h5ad

    script:
    """
    #!/usr/bin/env python3
    import squidpy as sq
    import scanpy as sc

    adata = sc.read_h5ad("${h5ad}")
    sq.gr.spatial_neighbors(adata, coord_type="generic", n_neighs=6)
    adata.write_h5ad("${sample}_graph.h5ad")
    """
}

process SPATIAL_DOMAINS {
    tag "SPATIAL_DOMAINS on ${sample}"
    container "quay.io/biocontainers/squidpy:1.4.1--pyhdfd78af_0"

    input:
    tuple val(sample), path(h5ad)

    output:
    tuple val(sample), path("${sample}_domains.h5ad"), emit: h5ad
    path "${sample}_spatial_stats.tsv", emit: stats

    script:
    """
    #!/usr/bin/env python3
    import squidpy as sq
    import scanpy as sc
    import pandas as pd

    adata = sc.read_h5ad("${h5ad}")

    # Highly variable genes
    sc.pp.highly_variable_genes(adata, flavor="seurat_v3", n_top_genes=2000)
    sc.pp.pca(adata)
    sc.pp.neighbors(adata)
    sc.tl.umap(adata)
    sc.tl.leiden(adata, resolution=0.5, flavor="igraph", n_iterations=2)

    # Spatial autocorrelation - Moran's I
    sq.gr.spatial_autocorr(adata, mode="moran")
    if "moranI" in adata.uns:
        moran_df = adata.uns["moranI"]
        moran_df.to_csv("${sample}_spatial_stats.tsv", sep="\\t")

    adata.write_h5ad("${sample}_domains.h5ad")
    """
}

process SPATIAL_VISUALIZATION {
    tag "SPATIAL_VIZ on ${sample}"
    container "quay.io/biocontainers/squidpy:1.4.1--pyhdfd78af_0"

    input:
    tuple val(sample), path(h5ad)

    output:
    path "${sample}_spatial_plot.png", emit: plot
    path "${sample}_spatial_features.png", emit: features

    script:
    """
    #!/usr/bin/env python3
    import squidpy as sq
    import scanpy as sc
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    adata = sc.read_h5ad("${h5ad}")

    # Spatial clusters
    fig, ax = plt.subplots(figsize=(8, 8))
    sc.pl.spatial(adata, color="leiden", spot_size=20, show=False, ax=ax)
    plt.savefig("${sample}_spatial_plot.png", dpi=150, bbox_inches="tight")

    # Spatial gene expression (top 6 HVGs)
    top_genes = adata.var_names[adata.var.highly_variable][:6].tolist()
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    for i, gene in enumerate(top_genes):
        ax = axes[i // 3, i % 3]
        sc.pl.spatial(adata, color=gene, spot_size=20, show=False, ax=ax, title=gene)
    plt.savefig("${sample}_spatial_features.png", dpi=150, bbox_inches="tight")
    """
}