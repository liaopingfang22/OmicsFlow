import { useState } from 'react';
import { Search, Download, BookOpen, Database, Dna, Beaker } from 'lucide-react';

const TABS = [
  { id: 'geo', label: 'GEO 数据集', icon: Database },
  { id: 'sra', label: 'SRA 测序数据', icon: Dna },
  { id: 'pubmed', label: 'PubMed 文献', icon: BookOpen },
  { id: 'plan', label: '分析方案', icon: Beaker },
];

const DATA_TYPES = [
  'rnaseq', 'wgs', '16s', 'scrnaseq', 'chipseq', 'atac',
  'metagenomics', 'methylation', 'proteomics', 'spatial',
];

export default function DataBrowserPage() {
  const [tab, setTab] = useState('geo');
  const [query, setQuery] = useState('');
  const [organism, setOrganism] = useState('Homo sapiens');
  const [dataType, setDataType] = useState('rnaseq');
  const [results, setResults] = useState<any[]>([]);
  const [plan, setPlan] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [srrId, setSrrId] = useState('');

  const handleSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const endpoint = tab === 'geo' ? '/api/v1/data/geo/search'
        : tab === 'sra' ? '/api/v1/data/sra/search'
        : '/api/v1/data/pubmed/search';

      const body = tab === 'geo'
        ? { query, organism, max_results: 20 }
        : { query, max_results: 20 };

      const resp = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem('access_token')}` },
        body: JSON.stringify(body),
      });
      const data = await resp.json();
      setResults(data.results || []);
    } catch { setResults([]); }
    setLoading(false);
  };

  const handlePlan = async () => {
    setLoading(true);
    try {
      const resp = await fetch('/api/v1/data/literature/plan', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem('access_token')}` },
        body: JSON.stringify({ organism, data_type: dataType }),
      });
      setPlan(await resp.json());
    } catch { setPlan(null); }
    setLoading(false);
  };

  const handleDownload = async () => {
    if (!srrId.trim()) return;
    setLoading(true);
    try {
      const resp = await fetch('/api/v1/data/sra/download', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem('access_token')}` },
        body: JSON.stringify({ srr_id: srrId }),
      });
      const data = await resp.json();
      alert(data.status === 'completed' ? `下载完成: ${data.output_dir}` : data.error || JSON.stringify(data));
    } catch { alert('下载失败'); }
    setLoading(false);
  };

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6 flex items-center gap-2"><Database size={28} /> 公共数据与文献</h1>

      <div className="flex gap-2 mb-6 border-b pb-2">
        {TABS.map(t => (
          <button key={t.id} onClick={() => { setTab(t.id); setResults([]); setPlan(null); }}
            className={`flex items-center gap-1 px-4 py-2 rounded-t-lg text-sm font-medium transition-colors ${tab === t.id ? 'bg-white border border-b-white text-blue-600' : 'text-gray-500 hover:text-gray-700'}`}>
            <t.icon size={16} /> {t.label}
          </button>
        ))}
      </div>

      {tab === 'geo' && (
        <div className="space-y-4">
          <div className="card">
            <div className="flex gap-3">
              <input className="flex-1 px-3 py-2 border rounded-lg" placeholder="搜索 GEO 数据集，如 RNA-seq lung cancer..."
                value={query} onChange={e => setQuery(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleSearch()} />
              <input className="w-48 px-3 py-2 border rounded-lg" value={organism} onChange={e => setOrganism(e.target.value)} placeholder="物种" />
              <button onClick={handleSearch} className="btn btn-primary" disabled={loading}><Search size={16} /></button>
            </div>
          </div>
          {results.map((r: any, i: number) => (
            <div key={i} className="card">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-semibold text-blue-700">{r.geo_id}</h3>
                  <p className="text-sm mt-1">{r.title}</p>
                  <p className="text-xs text-gray-500 mt-1">{r.organism} · {r.platform} · {r.n_samples} 样本 · {r.pub_date}</p>
                </div>
                <a href={r.gse_link} target="_blank" rel="noreferrer" className="btn btn-secondary text-xs">查看</a>
              </div>
              {r.summary && <p className="text-xs text-gray-600 mt-2 line-clamp-2">{r.summary}</p>}
            </div>
          ))}
        </div>
      )}

      {tab === 'sra' && (
        <div className="space-y-4">
          <div className="card">
            <div className="flex gap-3">
              <input className="flex-1 px-3 py-2 border rounded-lg" placeholder="搜索 SRA，如 16S microbiome gut..."
                value={query} onChange={e => setQuery(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleSearch()} />
              <button onClick={handleSearch} className="btn btn-primary" disabled={loading}><Search size={16} /></button>
            </div>
          </div>
          <div className="card">
            <h3 className="font-semibold mb-2">下载 SRA 数据</h3>
            <div className="flex gap-3">
              <input className="flex-1 px-3 py-2 border rounded-lg" placeholder="输入 SRR ID，如 SRR12345678" value={srrId} onChange={e => setSrrId(e.target.value)} />
              <button onClick={handleDownload} className="btn btn-primary flex items-center gap-1" disabled={loading}><Download size={16} /> 下载</button>
            </div>
            <p className="text-xs text-gray-500 mt-1">需要服务器安装 SRA Toolkit (prefetch + fasterq-dump)</p>
          </div>
          {results.map((r: any, i: number) => (
            <div key={i} className="card">
              <h3 className="font-semibold">{r.title}</h3>
              <p className="text-xs text-gray-500 mt-1">{r.organism} · {r.bioproject} · {r.created}</p>
              {r.run_ids?.length > 0 && <p className="text-xs text-blue-600 mt-1">Runs: {r.run_ids.join(', ')}</p>}
            </div>
          ))}
        </div>
      )}

      {tab === 'pubmed' && (
        <div className="space-y-4">
          <div className="card">
            <div className="flex gap-3">
              <input className="flex-1 px-3 py-2 border rounded-lg" placeholder="搜索 PubMed，如 CRISPR gene therapy..."
                value={query} onChange={e => setQuery(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleSearch()} />
              <button onClick={handleSearch} className="btn btn-primary" disabled={loading}><Search size={16} /></button>
            </div>
          </div>
          {results.map((r: any, i: number) => (
            <div key={i} className="card">
              <a href={r.pubmed_link} target="_blank" rel="noreferrer" className="font-semibold text-blue-700 hover:underline">{r.title}</a>
              <p className="text-xs text-gray-500 mt-1">{r.journal} · {r.pubdate} · PMID: {r.pmid}</p>
              <p className="text-xs text-gray-600 mt-1">{r.authors?.join(', ')}</p>
              {r.doi && <p className="text-xs text-gray-400">{r.doi}</p>}
            </div>
          ))}
        </div>
      )}

      {tab === 'plan' && (
        <div className="space-y-4">
          <div className="card">
            <h3 className="font-semibold mb-3">基于文献推荐分析方案</h3>
            <div className="flex gap-3">
              <input className="w-48 px-3 py-2 border rounded-lg" value={organism} onChange={e => setOrganism(e.target.value)} placeholder="物种" />
              <select className="flex-1 px-3 py-2 border rounded-lg" value={dataType} onChange={e => setDataType(e.target.value)}>
                {DATA_TYPES.map(dt => <option key={dt} value={dt}>{dt}</option>)}
              </select>
              <button onClick={handlePlan} className="btn btn-primary" disabled={loading}><Search size={16} /> 推荐方案</button>
            </div>
          </div>
          {plan && (
            <div className="card border-l-4 border-blue-500">
              <h3 className="font-semibold text-lg mb-2">推荐分析方案</h3>
              <div className="grid grid-cols-2 gap-4 mb-4">
                <div><span className="text-sm text-gray-500">推荐管线</span><p className="font-mono bg-gray-100 px-2 py-1 rounded mt-1">{plan.pipeline}</p></div>
                <div><span className="text-sm text-gray-500">推荐工具</span><p className="mt-1">{plan.tools}</p></div>
                <div><span className="text-sm text-gray-500">典型参数</span><p className="font-mono bg-gray-100 px-2 py-1 rounded mt-1 text-sm">{plan.typical_params || '使用默认参数'}</p></div>
                <div><span className="text-sm text-gray-500">物种</span><p className="mt-1">{plan.organism}</p></div>
              </div>
              {plan.references?.length > 0 && (
                <div>
                  <h4 className="font-semibold text-sm mb-2">参考文献</h4>
                  <div className="space-y-2">
                    {plan.references.map((ref: any, i: number) => (
                      <div key={i} className="text-sm border-l-2 border-gray-200 pl-3">
                        <a href={ref.pubmed_link} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline">{ref.title}</a>
                        <p className="text-xs text-gray-500">{ref.journal} · {ref.pubdate} · PMID: {ref.pmid}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {tab !== 'plan' && results.length === 0 && !loading && (
        <div className="card text-center py-12 mt-4">
          <Search size={48} className="mx-auto text-gray-300 mb-4" />
          <p className="text-gray-500">输入关键词搜索公共数据库</p>
        </div>
      )}
    </div>
  );
}