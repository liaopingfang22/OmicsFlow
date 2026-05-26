import { useState, useEffect } from 'react';
import { BarChart3, Download, Share2, FileText, ExternalLink } from 'lucide-react';

interface ResultsPageProps {
  taskId?: string;
  outputDir?: string;
}

interface FileItem {
  name: string;
  size: number;
  size_human: string;
  modified: string;
}

export default function ResultsPage() {
  const [taskId, setTaskId] = useState('');
  const [outputDir, setOutputDir] = useState('');
  const [files, setFiles] = useState<FileItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<'files' | 'volcano' | 'heatmap' | 'cnv' | 'report'>('files');
  const [vizHtml, setVizHtml] = useState('');
  const [reportContent, setReportContent] = useState('');
  const [shareLink, setShareLink] = useState('');
  const [csvPath, setCsvPath] = useState('');
  const [countsPath, setCountsPath] = useState('');

  const fetchFiles = async () => {
    if (!taskId || !outputDir) return;
    setLoading(true);
    try {
      const resp = await fetch(`/api/v1/results/files/${taskId}?output_dir=${encodeURIComponent(outputDir)}`, {
        headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
      });
      const data = await resp.json();
      setFiles(data.files || []);
    } catch { setFiles([]); }
    setLoading(false);
  };

  const generateViz = async (type: string) => {
    setLoading(true);
    try {
      const endpoint = type === 'volcano' ? '/api/v1/results/visualize/volcano'
        : type === 'heatmap' ? '/api/v1/results/visualize/heatmap' : '';

      if (!endpoint) { setLoading(false); return; }

      const body = type === 'volcano'
        ? { results_csv: csvPath, output_path: `${outputDir}/${taskId}_volcano.html`, log2fc_threshold: 1.0, pval_threshold: 0.05, title: `火山图 - ${taskId}` }
        : { counts_tsv: countsPath, output_path: `${outputDir}/${taskId}_heatmap.html`, top_n: 50, title: `基因表达热图 - ${taskId}` };

      const resp = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem('access_token')}` },
        body: JSON.stringify(body),
      });
      const data = await resp.json();
      if (data.path) {
        const fileResp = await fetch(`/api/v1/datasets/download?path=${encodeURIComponent(data.path)}`, {
          headers: { Authorization: `Bearer ${localStorage.getItem('access_token')}` },
        });
        setVizHtml(await fileResp.text());
      }
    } catch { }
    setLoading(false);
  };

  const packageDownload = async (format: string = 'tar.gz') => {
    setLoading(true);
    try {
      const resp = await fetch('/api/v1/results/download/package', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem('access_token')}` },
        body: JSON.stringify({ task_id: taskId, output_dir: outputDir, format, expires_hours: 72 }),
      });
      const data = await resp.json();
      if (data.share_link?.url) setShareLink(data.share_link.url);
    } catch { }
    setLoading(false);
  };

  const cnvVizHtml = (files: FileItem[]) => {
    const cnrFile = files.find(f => f.name.endsWith('.cnr'));
    const cnsFile = files.find(f => f.name.endsWith('.cns'));
    if (!cnrFile && !cnsFile) return '<p>未找到 CNV 结果文件 (.cnr/.cns)</p>';

    return `<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>CNV Profile</title>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
<style>body{font-family:Arial;margin:20px;}#cnv{width:100%;height:600px;}</style>
</head><body>
<h2>CNV 图谱</h2>
<p>请加载 .cnr 和 .cns 文件数据生成交互式 CNV 图谱</p>
<p>支持的文件格式: CNVkit .cnr (逐探针) 和 .cns (分段)</p>
<div id="cnv"></div>
<script>
const layout = {
  title: 'Copy Number Profile',
  xaxis: { title: 'Genomic Position' },
  yaxis: { title: 'log2 Copy Ratio', range: [-3, 2] },
  shapes: [
    { type: 'line', x0: 0, x1: 1, y0: 0, y1: 0, yref: 'y', line: { dash: 'dash', color: '#999' } },
    { type: 'line', x0: 0, x1: 1, y0: -1, y1: -1, yref: 'y', line: { dash: 'dot', color: '#e74c3c' } },
    { type: 'line', x0: 0, x1: 1, y0: 1, y1: 1, yref: 'y', line: { dash: 'dot', color: '#3498db' } }
  ]
};
Plotly.newPlot('cnv', [], layout);
</script></body></html>`;
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6 flex items-center gap-2"><BarChart3 size={28} /> 分析结果</h1>

      <div className="card mb-4">
        <div className="flex gap-3">
          <input className="flex-1 px-3 py-2 border rounded-lg" placeholder="任务 ID" value={taskId} onChange={e => setTaskId(e.target.value)} />
          <input className="flex-1 px-3 py-2 border rounded-lg" placeholder="输出目录路径" value={outputDir} onChange={e => setOutputDir(e.target.value)} />
          <button onClick={fetchFiles} className="btn btn-primary" disabled={loading}>加载结果</button>
        </div>
      </div>

      {files.length > 0 && (
        <>
          <div className="flex gap-2 mb-4 border-b pb-2">
            {[
              { id: 'files', label: '文件列表', icon: FileText },
              { id: 'volcano', label: '火山图', icon: BarChart3 },
              { id: 'heatmap', label: '热图', icon: BarChart3 },
              { id: 'cnv', label: 'CNV 图谱', icon: BarChart3 },
              { id: 'report', label: '分析报告', icon: FileText },
            ].map(t => (
              <button key={t.id} onClick={() => setActiveTab(t.id as any)}
                className={`flex items-center gap-1 px-3 py-2 text-sm ${activeTab === t.id ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'}`}>
                <t.icon size={14} /> {t.label}
              </button>
            ))}
          </div>

          {activeTab === 'files' && (
            <div className="card">
              <div className="flex justify-between items-center mb-4">
                <h3 className="font-semibold">输出文件 ({files.length})</h3>
                <div className="flex gap-2">
                  <button onClick={() => packageDownload('tar.gz')} className="btn btn-secondary text-sm flex items-center gap-1">
                    <Download size={14} /> 下载 tar.gz
                  </button>
                  <button onClick={() => packageDownload('zip')} className="btn btn-secondary text-sm flex items-center gap-1">
                    <Download size={14} /> 下载 zip
                  </button>
                  {shareLink && (
                    <a href={shareLink} className="btn btn-secondary text-sm flex items-center gap-1 text-green-600">
                      <Share2 size={14} /> 分享链接
                    </a>
                  )}
                </div>
              </div>
              <table className="w-full text-sm">
                <thead><tr className="border-b text-left text-gray-500">
                  <th className="py-2">文件名</th><th>大小</th><th>修改时间</th>
                </tr></thead>
                <tbody>{files.map((f, i) => (
                  <tr key={i} className="border-b hover:bg-gray-50">
                    <td className="py-2 font-mono text-xs">{f.name}</td>
                    <td className="text-gray-500">{f.size_human}</td>
                    <td className="text-gray-400">{new Date(f.modified).toLocaleString()}</td>
                  </tr>
                ))}</tbody>
              </table>
            </div>
          )}

          {activeTab === 'volcano' && (
            <div className="card">
              <div className="flex gap-3 mb-4">
                <input className="flex-1 px-3 py-2 border rounded-lg" placeholder="DE 结果 CSV 路径" value={csvPath} onChange={e => setCsvPath(e.target.value)} />
                <button onClick={() => generateViz('volcano')} className="btn btn-primary" disabled={loading}>生成火山图</button>
              </div>
              {vizHtml ? (
                <iframe srcDoc={vizHtml} className="w-full h-[600px] border rounded-lg" title="火山图" />
              ) : (
                <p className="text-gray-400 text-center py-12">输入 DE 结果 CSV 路径并点击生成</p>
              )}
            </div>
          )}

          {activeTab === 'heatmap' && (
            <div className="card">
              <div className="flex gap-3 mb-4">
                <input className="flex-1 px-3 py-2 border rounded-lg" placeholder="计数矩阵 TSV 路径" value={countsPath} onChange={e => setCountsPath(e.target.value)} />
                <button onClick={() => generateViz('heatmap')} className="btn btn-primary" disabled={loading}>生成热图</button>
              </div>
              {vizHtml ? (
                <iframe srcDoc={vizHtml} className="w-full h-[800px] border rounded-lg" title="热图" />
              ) : (
                <p className="text-gray-400 text-center py-12">输入计数矩阵 TSV 路径并点击生成</p>
              )}
            </div>
          )}

          {activeTab === 'cnv' && (
            <div className="card">
              <h3 className="font-semibold mb-4">CNV 图谱</h3>
              <iframe srcDoc={cnvVizHtml(files)} className="w-full h-[600px] border rounded-lg" title="CNV 图谱" />
              <div className="mt-4 text-sm text-gray-500">
                <p>CNV 结果文件：</p>
                {files.filter(f => f.name.match(/\.(cnr|cns|bed)$/)).map((f, i) => (
                  <span key={i} className="inline-block bg-gray-100 px-2 py-1 rounded mr-2 mt-1">{f.name} ({f.size_human})</span>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'report' && (
            <div className="card">
              {files.filter(f => f.name.match(/(report|\.md|\.html)$/i)).map((f, i) => (
                <div key={i} className="mb-2 flex items-center gap-2">
                  <FileText size={16} className="text-blue-500" />
                  <span className="font-mono text-sm">{f.name}</span>
                  <span className="text-xs text-gray-400">{f.size_human}</span>
                </div>
              ))}
              {files.filter(f => f.name.match(/(report|\.md|\.html)$/i)).length === 0 && (
                <p className="text-gray-400 text-center py-12">未找到报告文件</p>
              )}
            </div>
          )}
        </>
      )}

      {files.length === 0 && !loading && (
        <div className="card text-center py-12">
          <BarChart3 size={48} className="mx-auto text-gray-300 mb-4" />
          <p className="text-gray-500">输入任务 ID 和输出目录查看分析结果</p>
        </div>
      )}
    </div>
  );
}
