import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { sequencersApi } from '@/api/client';
import { Plus, Trash2, Cpu, RefreshCw, HardDrive, Wifi } from 'lucide-react';

export default function SequencersPage() {
  const queryClient = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({ name: '', model: 'G99', platform: 'BGI', location: '', data_dir: '' });

  const { data: sequencers, isLoading } = useQuery({
    queryKey: ['sequencers'],
    queryFn: () => sequencersApi.list().then((r) => r.data),
  });

  const createSeq = useMutation({
    mutationFn: (data: typeof formData) => sequencersApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sequencers'] });
      setShowForm(false);
      setFormData({ name: '', model: 'G99', platform: 'BGI', location: '', data_dir: '' });
    },
  });

  const deleteSeq = useMutation({
    mutationFn: (id: string) => sequencersApi.delete(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['sequencers'] }),
  });

  const scanSeq = useMutation({
    mutationFn: (id: string) => sequencersApi.scan(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['sequencers'] }),
  });

  const modelOptions = [
    { value: 'G99', label: '华大智造 G99' },
    { value: 'T1Plus', label: '华大智造 T1+' },
    { value: 'T7', label: '华大智造 T7' },
    { value: 'DNBSEQ-Tx', label: 'DNBSEQ-Tx' },
  ];

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">测序仪管理</h1>
        <button onClick={() => setShowForm(!showForm)} className="btn btn-primary flex items-center gap-2">
          <Plus size={20} /> 注册测序仪
        </button>
      </div>

      {showForm && (
        <div className="card mb-6">
          <h2 className="text-lg font-semibold mb-4">注册新测序仪</h2>
          <form onSubmit={(e) => { e.preventDefault(); createSeq.mutate(formData); }} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">名称</label>
                <input type="text" className="input" value={formData.name} onChange={(e) => setFormData({ ...formData, name: e.target.value })} placeholder="如: G99-01" required />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">型号</label>
                <select className="input" value={formData.model} onChange={(e) => setFormData({ ...formData, model: e.target.value })}>
                  {modelOptions.map((m) => <option key={m.value} value={m.value}>{m.label}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">位置</label>
                <input type="text" className="input" value={formData.location} onChange={(e) => setFormData({ ...formData, location: e.target.value })} placeholder="如: 3楼测序室" />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">数据目录</label>
              <input type="text" className="input" value={formData.data_dir} onChange={(e) => setFormData({ ...formData, data_dir: e.target.value })} placeholder="/path/to/sequencer/output" required />
            </div>
            <div className="flex gap-2">
              <button type="submit" className="btn btn-primary">注册</button>
              <button type="button" onClick={() => setShowForm(false)} className="btn btn-secondary">取消</button>
            </div>
          </form>
        </div>
      )}

      {isLoading ? (
        <div className="animate-pulse space-y-4">{[1, 2, 3].map((i) => <div key={i} className="h-24 bg-gray-100 rounded-lg" />)}</div>
      ) : sequencers && sequencers.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {sequencers.map((seq: any) => (
            <div key={seq.id} className="card">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="p-2 bg-green-100 rounded-lg">
                    <Cpu size={20} className="text-green-600" />
                  </div>
                  <div>
                    <h3 className="font-semibold">{seq.name}</h3>
                    <p className="text-sm text-gray-500">{seq.model} · {seq.platform}</p>
                  </div>
                </div>
                <button onClick={() => deleteSeq.mutate(seq.id)} className="p-2 hover:bg-red-50 rounded-lg text-red-600 transition-colors">
                  <Trash2 size={18} />
                </button>
              </div>
              {seq.location && <p className="text-sm text-gray-600 flex items-center gap-1 mb-2"><HardDrive size={14} /> {seq.location}</p>}
              {seq.data_dir && <p className="text-xs text-gray-400 mb-3 truncate">📁 {seq.data_dir}</p>}
              {seq.last_seen && <p className="text-xs text-gray-400 mb-3"><Wifi size={12} className="inline" /> 最后活跃: {new Date(seq.last_seen).toLocaleString()}</p>}
              <button onClick={() => scanSeq.mutate(seq.id)} className="btn btn-secondary text-sm flex items-center gap-1 w-full justify-center" disabled={scanSeq.isPending}>
                <RefreshCw size={14} className={scanSeq.isPending ? 'animate-spin' : ''} /> 扫描新数据
              </button>
            </div>
          ))}
        </div>
      ) : (
        <div className="card text-center py-12">
          <Cpu size={48} className="mx-auto text-gray-300 mb-4" />
          <p className="text-gray-500">暂无注册的测序仪。点击"注册测序仪"添加第一台设备。</p>
        </div>
      )}
    </div>
  );
}