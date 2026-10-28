import React from 'react';
import { Home, Mic, Search, ShoppingBag, Settings, LogOut } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export const Sidebar = ({ activeTab, setActiveTab }) => {
  const { logout } = useAuth();

  const navItems = [
    { id: 'home', label: 'Dashboard', icon: Home },
    { id: 'assistant', label: 'Voice Assistant', icon: Mic },
    { id: 'search', label: 'Search Products', icon: Search },
    { id: 'cart', label: 'My Cart', icon: ShoppingBag },
    { id: 'preferences', label: 'Preferences', icon: Settings },
  ];

  return (
    <aside className="w-64 bg-slate-950 border-r border-slate-800 flex flex-col justify-between p-6">
      <div>
        <div className="flex items-center gap-3 mb-10">
          <div className="w-10 h-10 bg-purple-600/20 border border-purple-500/40 rounded-xl flex items-center justify-center text-purple-400 font-bold">
            SC
          </div>
          <span className="text-base font-bold text-white tracking-wide">SmartCart AI</span>
        </div>

        <nav className="space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-medium transition-all ${
                  isActive
                    ? 'bg-purple-600 text-white shadow-lg shadow-purple-600/25'
                    : 'text-gray-400 hover:text-white hover:bg-slate-900'
                }`}
              >
                <Icon className="w-5 h-5" />
                <span>{item.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      <button
        onClick={logout}
        className="flex items-center gap-3 px-4 py-3 text-red-400 hover:bg-red-950/20 rounded-xl text-sm font-medium transition-all w-full"
      >
        <LogOut className="w-5 h-5" />
        <span>End Session</span>
      </button>
    </aside>
  );
};