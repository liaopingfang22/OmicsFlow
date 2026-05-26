import { Outlet, Link, useLocation } from 'react-router-dom';
import { useAuth } from '@/hooks';
import { Activity, Database, GitBranch, LogOut, Cpu, FolderOpen, Users, Sparkles, Globe, BarChart3 } from 'lucide-react';

const navItems = [
  { path: '/', label: 'Dashboard', icon: Activity },
  { path: '/ai-chat', label: 'AI 助手', icon: Sparkles },
  { path: '/data-browser', label: '公共数据', icon: Globe },
  { path: '/sequencers', label: '测序仪', icon: Cpu },
  { path: '/pipelines', label: 'Pipelines', icon: GitBranch },
  { path: '/tasks', label: 'Tasks', icon: Activity },
  { path: '/results', label: '结果查看', icon: BarChart3 },
  { path: '/datasets', label: 'Datasets', icon: Database },
  { path: '/users', label: '用户管理', icon: Users },
];

export default function Layout() {
  const location = useLocation();
  const { user, logout } = useAuth();

  return (
    <div className="min-h-screen flex">
      <aside className="w-64 bg-gray-900 text-white flex flex-col">
        <div className="p-6 border-b border-gray-800">
          <h1 className="text-xl font-bold">Pipeline Test</h1>
          <p className="text-sm text-gray-400 mt-1">BioSkills Platform</p>
        </div>
        
        <nav className="flex-1 p-4">
          {navItems.map(({ path, label, icon: Icon }) => (
            <Link
              key={path}
              to={path}
              className={`flex items-center gap-3 px-4 py-3 rounded-lg mb-2 transition-colors ${
                location.pathname === path
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-300 hover:bg-gray-800'
              }`}
            >
              <Icon size={20} />
              {label}
            </Link>
          ))}
        </nav>
        
        <div className="p-4 border-t border-gray-800">
          <div className="flex items-center justify-between">
            <div className="text-sm">
              <p className="font-medium">{user?.username}</p>
              <p className="text-gray-400 text-xs">{user?.email}</p>
            </div>
            <button
              onClick={logout}
              className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
              title="Logout"
            >
              <LogOut size={20} />
            </button>
          </div>
        </div>
      </aside>
      
      <main className="flex-1 bg-gray-50">
        <div className="p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
