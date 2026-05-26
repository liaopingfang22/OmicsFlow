import { useState } from 'react';
import { usePipelines, useCreatePipeline, useDeletePipeline } from '@/hooks';
import { Plus, Trash2, GitBranch } from 'lucide-react';

export default function PipelinesPage() {
  const { data: pipelines, isLoading } = usePipelines();
  const createPipeline = useCreatePipeline();
  const deletePipeline = useDeletePipeline();
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    pipeline_type: 'cnv',
  });

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createPipeline.mutateAsync(formData);
      setShowForm(false);
      setFormData({ name: '', description: '', pipeline_type: 'cnv' });
    } catch {
    }
  };

  const handleDelete = async (id: string) => {
    if (confirm('Are you sure you want to delete this pipeline?')) {
      await deletePipeline.mutateAsync(id);
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Pipelines</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="btn btn-primary flex items-center gap-2"
        >
          <Plus size={20} />
          New Pipeline
        </button>
      </div>

      {showForm && (
        <div className="card mb-6">
          <h2 className="text-lg font-semibold mb-4">Create New Pipeline</h2>
          <form onSubmit={handleCreate} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Name
                </label>
                <input
                  type="text"
                  className="input"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Type
                </label>
                <select
                  className="input"
                  value={formData.pipeline_type}
                  onChange={(e) => setFormData({ ...formData, pipeline_type: e.target.value })}
                >
                  <option value="cnv">CNV 分析 (CNVkit)</option>
                  <option value="de">差异表达 (edgeR/DESeq2)</option>
                  <option value="rnaseq">RNA-seq (STAR + Salmon)</option>
                  <option value="wgs">WGS 变异检测 (GATK)</option>
                  <option value="metagenomics">宏基因组 (Kraken2)</option>
                  <option value="amplicon">16S/ITS 扩增子 (DADA2)</option>
                  <option value="tcr">TCR/BCR 免疫组库 (MiXCR)</option>
                  <option value="atac">ATAC-seq (MACS3)</option>
                  <option value="spatial">空间转录组 (Squidpy)</option>
                  <option value="chipseq">ChIP-seq (MACS3)</option>
                  <option value="smrna">small RNA (miRDeep2)</option>
                  <option value="somatic">体细胞变异 (Mutect2)</option>
                  <option value="methylation">甲基化 (Bismark)</option>
                  <option value="longread">长读长测序 (Minimap2)</option>
                  <option value="wes">WES 靶向测序</option>
                  <option value="scrnaseq">单细胞 RNA-seq (Scanpy)</option>
                  <option value="proteomics">蛋白质组学 (MaxQuant)</option>
                  <option value="qc">质量控制 (FastQC)</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <input
                  type="text"
                  className="input"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                />
              </div>
            </div>
            <div className="flex gap-2">
              <button type="submit" className="btn btn-primary">
                Create
              </button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="btn btn-secondary"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {isLoading ? (
        <div className="animate-pulse space-y-4">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 bg-gray-100 rounded-lg"></div>
          ))}
        </div>
      ) : pipelines && pipelines.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {pipelines.map((pipeline: any) => (
            <div key={pipeline.id} className="card">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-primary-100 rounded-lg">
                    <GitBranch size={20} className="text-primary-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold">{pipeline.name}</h3>
                    <p className="text-sm text-gray-500">{pipeline.pipeline_type}</p>
                  </div>
                </div>
                <button
                  onClick={() => handleDelete(pipeline.id)}
                  className="p-2 hover:bg-red-50 rounded-lg text-red-600 transition-colors"
                >
                  <Trash2 size={18} />
                </button>
              </div>
              {pipeline.description && (
                <p className="text-sm text-gray-600">{pipeline.description}</p>
              )}
              <p className="text-xs text-gray-400 mt-3">
                Created: {new Date(pipeline.created_at).toLocaleDateString()}
              </p>
            </div>
          ))}
        </div>
      ) : (
        <div className="card text-center py-12">
          <GitBranch size={48} className="mx-auto text-gray-300 mb-4" />
          <p className="text-gray-500">No pipelines yet. Create your first pipeline!</p>
        </div>
      )}
    </div>
  );
}
