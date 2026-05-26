import { useState } from 'react';
import { useTasks, usePipelines, useCreateTask, useRunTask, useDeleteTask } from '@/hooks';
import { Plus, Play, Trash2, Clock, CheckCircle, XCircle, Loader } from 'lucide-react';

export default function TasksPage() {
  const { data: tasks, isLoading } = useTasks();
  const { data: pipelines } = usePipelines();
  const createTask = useCreateTask();
  const runTask = useRunTask();
  const deleteTask = useDeleteTask();
  
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    pipeline_id: '',
    dataset_id: '',
    input_params: {} as Record<string, any>,
  });

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createTask.mutateAsync(formData);
      setShowForm(false);
      setFormData({ name: '', pipeline_id: '', dataset_id: '', input_params: {} });
    } catch {
    }
  };

  const handleRun = async (taskId: string) => {
    await runTask.mutateAsync(taskId);
  };

  const handleDelete = async (id: string) => {
    if (confirm('Are you sure you want to delete this task?')) {
      await deleteTask.mutateAsync(id);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle size={20} className="text-green-600" />;
      case 'running':
        return <Loader size={20} className="text-yellow-600 animate-spin" />;
      case 'failed':
        return <XCircle size={20} className="text-red-600" />;
      default:
        return <Clock size={20} className="text-gray-400" />;
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Tasks</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="btn btn-primary flex items-center gap-2"
        >
          <Plus size={20} />
          New Task
        </button>
      </div>

      {showForm && (
        <div className="card mb-6">
          <h2 className="text-lg font-semibold mb-4">Create New Task</h2>
          <form onSubmit={handleCreate} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Task Name
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
                  Pipeline
                </label>
                <select
                  className="input"
                  value={formData.pipeline_id}
                  onChange={(e) => setFormData({ ...formData, pipeline_id: e.target.value })}
                  required
                >
                  <option value="">Select a pipeline</option>
                  {pipelines?.map((p: any) => (
                    <option key={p.id} value={p.id}>
                      {p.name}
                    </option>
                  ))}
                </select>
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
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-16 bg-gray-100 rounded-lg"></div>
          ))}
        </div>
      ) : tasks && tasks.length > 0 ? (
        <div className="space-y-3">
          {tasks.map((task: any) => (
            <div key={task.id} className="card flex items-center justify-between">
              <div className="flex items-center gap-4">
                {getStatusIcon(task.status)}
                <div>
                  <h3 className="font-semibold">{task.name}</h3>
                  <p className="text-sm text-gray-500">
                    {task.progress > 0 ? `${task.progress}%` : 'Pending'}
                    {task.started_at && ` • Started: ${new Date(task.started_at).toLocaleString()}`}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {task.status === 'pending' && (
                  <button
                    onClick={() => handleRun(task.id)}
                    className="btn btn-primary flex items-center gap-1 text-sm"
                    disabled={runTask.isPending}
                  >
                    <Play size={16} />
                    Run
                  </button>
                )}
                <button
                  onClick={() => handleDelete(task.id)}
                  className="p-2 hover:bg-red-50 rounded-lg text-red-600 transition-colors"
                >
                  <Trash2 size={18} />
                </button>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="card text-center py-12">
          <Clock size={48} className="mx-auto text-gray-300 mb-4" />
          <p className="text-gray-500">No tasks yet. Create your first task!</p>
        </div>
      )}
    </div>
  );
}
