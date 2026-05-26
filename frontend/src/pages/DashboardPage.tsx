import { useQuery } from '@tanstack/react-query';
import { pipelinesApi, tasksApi } from '@/api/client';
import { GitBranch, Activity, Play } from 'lucide-react';

export function DashboardPage() {
  const { data: tasks } = useQuery({
    queryKey: ['tasks'],
    queryFn: () => tasksApi.list().then(res => res.data),
  });

  const { data: pipelines } = useQuery({
    queryKey: ['pipelines', 'available'],
    queryFn: () => pipelinesApi.listAvailable().then(res => res.data),
  });

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Dashboard</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="card bg-blue-600 text-white">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-blue-100">Total Tasks</p>
              <p className="text-3xl font-bold">{tasks?.length || 0}</p>
            </div>
            <Activity size={40} className="opacity-50" />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <GitBranch size={20} />
            Available Pipelines
          </h2>
          {pipelines?.length > 0 ? (
            <div className="space-y-2">
              {pipelines.map((p: any) => (
                <div key={p.name} className="p-3 bg-gray-50 rounded-lg">
                  <p className="font-medium">{p.name}</p>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500">No pipelines available</p>
          )}
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Play size={20} />
            Recent Tasks
          </h2>
          {tasks?.length > 0 ? (
            <div className="space-y-2">
              {tasks.slice(0, 5).map((t: any) => (
                <div key={t.id} className="p-3 bg-gray-50 rounded-lg flex justify-between">
                  <p className="font-medium">{t.name}</p>
                  <span className="text-sm text-gray-500">{t.status}</span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-500">No tasks yet</p>
          )}
        </div>
      </div>
    </div>
  );
}
