import React, { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Layout from '@/components/Layout';

// Helper to wrap named exports as default exports
const wrapNamedExport = (moduleName: string) => (module: any) => ({
  default: module[moduleName],
});

// Lazy-loaded page components for code splitting
const DashboardPage = lazy(() =>
  import('@/pages/DashboardPage').then(wrapNamedExport('DashboardPage'))
);
const LoginPage = lazy(() =>
  import('@/pages/LoginPage').then(wrapNamedExport('LoginPage'))
);
const SequencersPage = lazy(() => import('@/pages/SequencersPage'));
const PipelinesPage = lazy(() => import('@/pages/PipelinesPage'));
const TasksPage = lazy(() => import('@/pages/TasksPage'));
const DatasetsPage = lazy(() => import('@/pages/DatasetsPage'));
const UsersPage = lazy(() => import('@/pages/UsersPage'));
const AIChatPage = lazy(() => import('@/pages/AIChatPage'));
const DataBrowserPage = lazy(() => import('@/pages/DataBrowserPage'));
const ResultsPage = lazy(() => import('@/pages/ResultsPage'));

const queryClient = new QueryClient();

// Loading spinner component
function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center min-h-screen">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>
  );
}

// Error boundary component
class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Page error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex flex-col items-center justify-center min-h-screen">
          <h2 className="text-2xl font-bold mb-4">Something went wrong</h2>
          <p className="text-gray-600 mb-4">{this.state.error?.message}</p>
          <button
            onClick={() => {
              this.setState({ hasError: false, error: null });
              window.location.reload();
            }}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Try again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <Suspense fallback={<LoadingSpinner />}>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route element={<Layout />}>
                <Route path="/" element={<DashboardPage />} />
                <Route path="/pipelines" element={<PipelinesPage />} />
                <Route path="/tasks" element={<TasksPage />} />
                <Route path="/datasets" element={<DatasetsPage />} />
                <Route path="/sequencers" element={<SequencersPage />} />
                <Route path="/users" element={<UsersPage />} />
                <Route path="/ai-chat" element={<AIChatPage />} />
                <Route path="/data-browser" element={<DataBrowserPage />} />
                <Route path="/results" element={<ResultsPage />} />
              </Route>
            </Routes>
          </Suspense>
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;