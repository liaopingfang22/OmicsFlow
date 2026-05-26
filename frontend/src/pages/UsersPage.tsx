import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { authApi } from '@/api/client';
import { Users, Shield, Edit, Trash2, UserPlus } from 'lucide-react';

interface User {
  id: string;
  username: string;
  email: string;
  full_name?: string;
  is_active: boolean;
  roles: string[];
  created_at: string;
}

const ROLE_LABELS: Record<string, string> = {
  admin: '管理员',
  bioinformatician: '生信分析人员',
  librarian: '建库人员',
  viewer: '查看者',
};

const ROLE_COLORS: Record<string, string> = {
  admin: 'bg-red-100 text-red-700',
  bioinformatician: 'bg-blue-100 text-blue-700',
  librarian: 'bg-green-100 text-green-700',
  viewer: 'bg-gray-100 text-gray-700',
};

export default function UsersPage() {
  const queryClient = useQueryClient();
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [selectedRoles, setSelectedRoles] = useState<string[]>([]);

  const { data: users, isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: () => authApi.getUsers().then((r) => r.data),
  });

  const updateUser = useMutation({
    mutationFn: ({ id, data }: { id: string; data: any }) => authApi.updateUser(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
      setEditingUser(null);
    },
  });

  const deleteUser = useMutation({
    mutationFn: (id: string) => authApi.deleteUser(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['users'] }),
  });

  const handleEditRoles = (user: User) => {
    setEditingUser(user);
    setSelectedRoles(user.roles || []);
  };

  const handleSaveRoles = () => {
    if (editingUser) {
      updateUser.mutate({ id: editingUser.id, data: { roles: selectedRoles } });
    }
  };

  const allRoles = ['admin', 'bioinformatician', 'librarian', 'viewer'];

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold flex items-center gap-2">
          <Users size={28} /> 用户管理
        </h1>
      </div>

      {editingUser && (
        <div className="card mb-6 border-2 border-blue-200">
          <h2 className="text-lg font-semibold mb-4">
            编辑用户角色: {editingUser.username}
          </h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
            {allRoles.map((role) => (
              <label key={role} className="flex items-center gap-2 p-3 border rounded-lg cursor-pointer hover:bg-gray-50">
                <input
                  type="checkbox"
                  checked={selectedRoles.includes(role)}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedRoles([...selectedRoles, role]);
                    } else {
                      setSelectedRoles(selectedRoles.filter((r) => r !== role));
                    }
                  }}
                  className="rounded"
                />
                <div>
                  <p className="font-medium text-sm">{ROLE_LABELS[role]}</p>
                  <p className="text-xs text-gray-500">{role}</p>
                </div>
              </label>
            ))}
          </div>
          <div className="flex gap-2">
            <button onClick={handleSaveRoles} className="btn btn-primary" disabled={updateUser.isPending}>
              保存
            </button>
            <button onClick={() => setEditingUser(null)} className="btn btn-secondary">取消</button>
          </div>
        </div>
      )}

      {isLoading ? (
        <div className="animate-pulse space-y-4">{[1, 2, 3].map((i) => <div key={i} className="h-16 bg-gray-100 rounded-lg" />)}</div>
      ) : users && users.length > 0 ? (
        <div className="card overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">用户名</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">邮箱</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">角色</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">状态</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-700">注册时间</th>
                <th className="px-4 py-3 text-right text-sm font-medium text-gray-700">操作</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {users.map((user: User) => (
                <tr key={user.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <p className="font-medium">{user.username}</p>
                    {user.full_name && <p className="text-xs text-gray-500">{user.full_name}</p>}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">{user.email}</td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {(user.roles || ['viewer']).map((role) => (
                        <span key={role} className={`px-2 py-0.5 rounded-full text-xs font-medium ${ROLE_COLORS[role] || 'bg-gray-100'}`}>
                          {ROLE_LABELS[role] || role}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-0.5 rounded-full text-xs ${user.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                      {user.is_active ? '活跃' : '已禁用'}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500">
                    {new Date(user.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <button onClick={() => handleEditRoles(user)} className="p-1 hover:bg-blue-50 rounded text-blue-600 mr-1" title="编辑角色">
                      <Shield size={16} />
                    </button>
                    <button onClick={() => deleteUser.mutate(user.id)} className="p-1 hover:bg-red-50 rounded text-red-600" title="禁用用户">
                      <Trash2 size={16} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="card text-center py-12">
          <Users size={48} className="mx-auto text-gray-300 mb-4" />
          <p className="text-gray-500">暂无用户数据</p>
        </div>
      )}
    </div>
  );
}