process SCANPY_PREPROCESS {
    tag "SCANPY_PREPROCESS on ${sample}"
    container "quay.io/biocontainers/scanpy:1.9.8--pyhdfd78af_1"
    cpus params.threads ?: 4

    input:
    tuple val(sample), path(h5ad)

    output:
    tuple val(sample), path("${sample}.preprocessed.h5ad"), emit: h5ad
    tuple val(sample), path("${sample}.qc_metrics.csv"), emit: metrics

    script:
    """
    #!/usr/bin/env python3
    import scanpy as sc
    import pandas as pd

    adata = sc.read_h5ad("${h5ad}")

    adata.var_names_make_unique()

    sc.pp.calculate_qc_metrics(adata, percent_top=None, log1p=False, inplace=True)
    adata.var['mt'] = adata.var_names.str.startswith('MT-')
    sc.pp.calculate_qc_metrics(adata, qc_vars=['mt'], percent_top=None, log1p=False, inplace=True)

    metrics = pd.DataFrame({
        'metric': ['n_cells_raw', 'n_genes_raw', 'median_genes', 'median_counts', 'pct_mito_median'],
        'value': [
            adata.n_obs,
            adata.n_vars,
            adata.obs['n_genes_by_counts'].median(),
            adata.obs['total_counts'].median(),
            adata.obs['pct_counts_mt'].median()
        ]
    })
    metrics.to_csv("${sample}.qc_metrics.csv", index=False)

    sc.pp.filter_cells(adata, min_genes=200)
    sc.pp.filter_genes(adata, min_cells=3)
    adata = adata[adata.obs.pct_counts_mt < 20, :]

    sc.pp.normalize_total(adata, target_sum=1e4)
    sc.pp.log1p(adata)

    adata.write_h5ad("${sample}.preprocessed.h5ad")
    """
}

process SCANPY_CLUSTER {
    tag "SCANPY_CLUSTER on ${sample}"
    container "quay.io/biocontainers/scanpy:1.9.8--pyhdfd78af_1"
    cpus params.threads ?: 4

    input:
    tuple val(sample), path(h5ad)

    output:
    tuple val(sample), path("${sample}.clustered.h5ad"), emit: h5ad
    tuple val(sample), path("${sample}.cluster_markers.csv"), emit: markers
    path "${sample}.umap.png", emit: umap

    script:
    """
    #!/usr/bin/env python3
    import scanpy as sc
    import pandas as pd

    sc.settings.n_jobs = ${task.cpus}
    sc.settings.figdir = '.'

    adata = sc.read_h5ad("${h5ad}")

    sc.pp.highly_variable_genes(adata, min_mean=0.0125, max_mean=3, min_disp=0.5)
    adata = adata[:, adata.var.highly_variable]
    sc.pp.scale(adata, max_value=10)

    sc.tl.pca(adata, svd_solver='arpack')
    sc.pp.neighbors(adata, n_neighbors=10, n_pcs=40)
    sc.tl.umap(adata)
    sc.tl.leiden(adata, resolution=0.5)
    sc.tl.louvain(adata, resolution=0.5)

    sc.tl.rank_genes_groups(adata, 'leiden', method='wilcoxon')
    result = adata.uns['rank_genes_groups']
    groups = result['names'].dtype.names
    markers_list = []
    for g in groups:
        for i in range(min(10, len(result['names'][g]))):
            markers_list.append({
                'cluster': g,
                'gene': result['names'][g][i],
                'score': result['scores'][g][i],
                'pval': result['pvals'][g][i],
                'pval_adj': result['pvals_adj'][g][i],
                'logfoldchanges': result['logfoldchanges'][g][i]
            })
    markers_df = pd.DataFrame(markers_list)
    markers_df.to_csv("${sample}.cluster_markers.csv", index=False)

    sc.pl.umap(adata, color='leiden', save=False, show=False)
    import matplotlib.pyplot as plt
    plt.savefig("${sample}.umap.png", dpi=150, bbox_inches='tight')

    adata.write_h5ad("${sample}.clustered.h5ad")
    """
}

process SCANPY_MARKER_HEATMAP {
    tag "SCANPY_HEATMAP on ${sample}"
    container "quay.io/biocontainers/scanpy:1.9.8--pyhdfd78af_1"

    input:
    tuple val(sample), path(h5ad)

    output:
    path "${sample}.marker_heatmap.png", emit: heatmap

    script:
    """
    #!/usr/bin/env python3
    import scanpy as sc
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    sc.settings.figdir = '.'
    adata = sc.read_h5ad("${h5ad}")

    sc.tl.rank_genes_groups(adata, 'leiden', method='wilcoxon', n_genes=50)

    fig, ax = plt.subplots(figsize=(16, 10))
    sc.pl.rank_genes_groups_heatmap(adata, n_genes=5, show=False, show_gene_labels=True, ax=ax)
    plt.savefig("${sample}.marker_heatmap.png", dpi=150, bbox_inches='tight')
    """
}
process DOUBLET_DETECTION {
    tag "SCRUBLET on ${sample}"
    container "quay.io/biocontainers/scanpy:1.9.8--pyhdfd78af_1"
    cpus params.threads ?: 4

    input:
    tuple val(sample), path(h5ad)

    output:
    tuple val(sample), path("${sample}.scrublet.h5ad"), emit: h5ad
    tuple val(sample), path("${sample}.doublet_scores.csv"), emit: scores

    script:
    """
    #!/usr/bin/env python3
    import scanpy as sc
    import scrublet as scr
    import pandas as pd

    adata = sc.read_h5ad("${h5ad}")
    
    scrub = scr.Scrublet(adata.X)
    doublet_scores, predicted_doublets = scrub.scrub_doublets()
    
    adata.obs['doublet_score'] = doublet_scores
    adata.obs['is_doublet'] = predicted_doublets
    
    n_doublets = predicted_doublets.sum()
    total = len(predicted_doublets)
    
    scores_df = pd.DataFrame({
        'metric': ['total_cells', 'predicted_doublets', 'doublet_rate', 'mean_score'],
        'value': [total, n_doublets, f"{n_doublets/total*100:.1f}%", f"{doublet_scores.mean():.4f}"]
    })
    scores_df.to_csv("${sample}.doublet_scores.csv", index=False)
    
    adata = adata[~adata.obs['is_doublet']].copy()
    adata.write_h5ad("${sample}.scrublet.h5ad")
    """
}

process CELL_TYPE_ANNOTATION {
    tag "CELLTYPIST on ${sample}"
    container "quay.io/biocontainers/celltypist:1.6.3--pyhdfd78af_0"
    cpus params.threads ?: 4

    input:
    tuple val(sample), path(h5ad)
    path(model_path)

    output:
    tuple val(sample), path("${sample}.annotated.h5ad"), emit: h5ad
    tuple val(sample), path("${sample}.cell_types.csv"), emit: cell_types
    tuple val(sample), path("${sample}.annotation_plot.png"), emit: plot

    script:
    def model_arg = model_path.name != "NO_MODEL" ? "--model ${model_path}" : "--model Immune_All_Low.pkl"
    """
    #!/usr/bin/env python3
    import scanpy as sc
    import celltypist
    import pandas as pd
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    adata = sc.read_h5ad("${h5ad}")
    
    # CellTypist annotation
    predictions = celltypist.annotate(adata, model='${model_path}' if '${model_path}' != 'NO_MODEL' else 'Immune_All_Low.pkl')
    adata = predictions.to_adata()
    
    # Save cell type counts
    ct_counts = adata.obs['predicted_labels'].value_counts().reset_index()
    ct_counts.columns = ['cell_type', 'count']
    ct_counts.to_csv("${sample}.cell_types.csv", index=False)
    
    # Plot
    fig, axes = plt.subplots(1, 2, figsize=(16, 8))
    sc.pl.umap(adata, color='predicted_labels', ax=axes[0], show=False, title='Cell Types')
    sc.pl.umap(adata, color='conf_score', ax=axes[1], show=False, title='Confidence Score')
    plt.savefig("${sample}.annotation_plot.png", dpi=150, bbox_inches='tight')
    
    adata.write_h5ad("${sample}.annotated.h5ad")
    """
}

process TRAJECTORY_INFERENCE {
    tag "TRAJECTORY on ${sample}"
    container "quay.io/biocontainers/scanpy:1.9.8--pyhdfd78af_1"

    input:
    tuple val(sample), path(h5ad)

    output:
    tuple val(sample), path("${sample}.trajectory.h5ad"), emit: h5ad
    path "${sample}.trajectory_plot.png", emit: plot
    path "${sample}.pseudotime.csv", emit: pseudotime

    script:
    """
    #!/usr/bin/env python3
    import scanpy as sc
    import pandas as pd
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    adata = sc.read_h5ad("${h5ad}")

    # PAGA trajectory
    sc.tl.paga(adata, groups='leiden')
    sc.pl.paga(adata, plot=False)
    sc.tl.draw_graph(adata, init_pos='paga')
    
    # Diffusion pseudotime
    sc.tl.diffmap(adata)
    adata.uns['iroot'] = adata.obs['leiden'].astype(int).idxmax()
    sc.tl.dpt(adata)
    
    # Save pseudotime
    pt = adata.obs[['dpt_pseudotime', 'leiden']].copy()
    pt.index.name = 'cell_id'
    pt.to_csv("${sample}.pseudotime.csv")
    
    # Plot
    fig, axes = plt.subplots(1, 3, figsize=(20, 6))
    sc.pl.paga(adata, ax=axes[0], show=False, title='PAGA')
    sc.pl.draw_graph(adata, color='leiden', ax=axes[1], show=False, title='Clusters')
    sc.pl.draw_graph(adata, color='dpt_pseudotime', ax=axes[2], show=False, title='Pseudotime')
    plt.savefig("${sample}.trajectory_plot.png", dpi=150, bbox_inches='tight')
    
    adata.write_h5ad("${sample}.trajectory.h5ad")
    """
}

process MULTI_SAMPLE_INTEGRATION {
    tag "INTEGRATION"
    container "quay.io/biocontainers/scanpy:1.9.8--pyhdfd78af_1"
    cpus params.threads ?: 8

    input:
    path(h5ad_files)

    output:
    path "integrated.h5ad", emit: h5ad
    path "integration_plot.png", emit: plot

    script:
    """
    #!/usr/bin/env python3
    import scanpy as sc
    import anndata as ad
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import glob

    files = sorted(glob.glob("*.h5ad"))
    adatas = [sc.read_h5ad(f) for f in files]
    for i, a in enumerate(adatas):
        a.obs['sample'] = f'sample_{i}'
    
    adata = ad.concat(adatas, join='inner')
    
    sc.pp.highly_variable_genes(adata, batch_key='sample')
    adata = adata[:, adata.var.highly_variable]
    sc.pp.scale(adata, max_value=10)
    sc.tl.pca(adata)
    sc.external.pp.harmony_integrate(adata, 'sample')
    sc.pp.neighbors(adata, use_rep='X_pca_harmony')
    sc.tl.umap(adata)
    sc.tl.leiden(adata)
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    sc.pl.umap(adata, color='sample', ax=axes[0], show=False, title='By Sample')
    sc.pl.umap(adata, color='leiden', ax=axes[1], show=False, title='By Cluster')
    plt.savefig("integration_plot.png", dpi=150, bbox_inches='tight')
    
    adata.write_h5ad("integrated.h5ad")
    """
}
