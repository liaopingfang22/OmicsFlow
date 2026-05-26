import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { pipelinesApi } from '@/api/client';

export function usePipelines() {
  return useQuery({
    queryKey: ['pipelines'],
    queryFn: () => pipelinesApi.list().then(res => res.data),
  });
}

export function useAvailablePipelines() {
  return useQuery({
    queryKey: ['pipelines', 'available'],
    queryFn: () => pipelinesApi.listAvailable().then(res => res.data),
  });
}

export function usePipeline(id: string) {
  return useQuery({
    queryKey: ['pipelines', id],
    queryFn: () => pipelinesApi.get(id).then(res => res.data),
    enabled: !!id,
  });
}

export function useCreatePipeline() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: { name: string; description?: string; pipeline_type?: string; config?: object }) =>
      pipelinesApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pipelines'] });
    },
  });
}

export function useDeletePipeline() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (pipelineId: string) => pipelinesApi.delete(pipelineId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pipelines'] });
    },
  });
}
