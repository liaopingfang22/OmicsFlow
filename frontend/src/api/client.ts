import axios from 'axios';

const api = axios.create({
  baseURL: '/api/v1',
  headers: { 'Content-Type': 'application/json' },
});

// Request interceptor - add access token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor - handle token refresh on 401
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (value: unknown) => void;
  reject: (reason?: unknown) => void;
}> = [];

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If 401 and not already retrying
    if (error.response?.status === 401 && !originalRequest._retry) {
      // If already refreshing, queue this request
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return api(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        // No refresh token, redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(error);
      }

      try {
        // Call refresh endpoint
        const response = await axios.post('/api/v1/auth/refresh', null, {
          params: { refresh_token: refreshToken },
        });

        const { access_token, refresh_token: newRefreshToken } = response.data;
        localStorage.setItem('access_token', access_token);
        localStorage.setItem('refresh_token', newRefreshToken);

        // Update original request with new token
        originalRequest.headers.Authorization = `Bearer ${access_token}`;

        processQueue(null, access_token);
        return api(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        // Refresh failed, clear tokens and redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

export const authApi = {
  login: (username: string, password: string) =>
    api.post('/auth/login', new URLSearchParams({ username, password }), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    }),
  register: (data: { username: string; email: string; password: string; full_name?: string; roles?: string[] }) =>
    api.post('/auth/register', data),
  getMe: () => api.get('/auth/me'),
  getUsers: () => api.get('/auth/users'),
  updateUser: (id: string, data: { email?: string; full_name?: string; password?: string; roles?: string[] }) =>
    api.put(`/auth/users/${id}`, data),
  deleteUser: (id: string) => api.delete(`/auth/users/${id}`),
};

export const tasksApi = {
  list: () => api.get('/tasks'),
  get: (id: string) => api.get(`/tasks/${id}`),
  create: (data: { name: string; pipeline_id: string; dataset_id?: string; input_params?: object }) =>
    api.post('/tasks', data),
  run: (id: string) => api.post(`/tasks/${id}/run`),
  delete: (id: string) => api.delete(`/tasks/${id}`),
};

export const pipelinesApi = {
  list: () => api.get('/pipelines'),
  get: (id: string) => api.get(`/pipelines/${id}`),
  create: (data: { name: string; description?: string; pipeline_type?: string; config?: object }) =>
    api.post('/pipelines', data),
  delete: (id: string) => api.delete(`/pipelines/${id}`),
  listAvailable: () => api.get('/pipelines/available'),
};

export const datasetsApi = {
  list: () => api.get('/datasets'),
  get: (id: string) => api.get(`/datasets/${id}`),
  upload: (file: File, name?: string, description?: string) => {
    const formData = new FormData();
    formData.append('file', file);
    if (name) formData.append('name', name);
    if (description) formData.append('description', description);
    return api.post('/datasets', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
  delete: (id: string) => api.delete(`/datasets/${id}`),
};

export const aiApi = {
  analyzeIntent: (message: string) => api.post('/ai/intent', { message }),
  chat: (message: string, session_id?: string) => api.post('/ai/chat', { message, session_id }),
  listSkills: (category?: string) => api.get('/ai/skills', { params: { category } }),
  getSkill: (name: string) => api.get(`/ai/skills/${name}`),
};

export const skillsApi = {
  list: (category?: string) => api.get('/skills', { params: { category } }),
  get: (id: string) => api.get(`/skills/${id}`),
  getByName: (name: string) => api.get(`/skills/by-name/${name}`),
};

export const sequencersApi = {
  list: () => api.get('/sequencers'),
  get: (id: string) => api.get(`/sequencers/${id}`),
  create: (data: { name: string; model: string; platform?: string; location?: string; data_dir?: string }) =>
    api.post('/sequencers', data),
  delete: (id: string) => api.delete(`/sequencers/${id}`),
  scan: (id: string) => api.post(`/sequencers/${id}/scan`),
  listRuns: (id: string) => api.get(`/sequencers/${id}/runs`),
};

export const projectsApi = {
  list: () => api.get('/projects'),
  get: (id: string) => api.get(`/projects/${id}`),
  create: (data: { name: string; description?: string }) => api.post('/projects', data),
  delete: (id: string) => api.delete(`/projects/${id}`),
  listSamples: (id: string) => api.get(`/projects/${id}/samples`),
};

export default api;
