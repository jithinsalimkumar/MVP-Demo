'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, Download, Database, LogOut, Building2 } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';

export default function Sidebar() {
  const pathname = usePathname();
  const { logout, username } = useAuth();

  const navItems = [
    { name: 'Dashboard', href: '/dashboard', icon: LayoutDashboard },
    { name: 'Scrape Jobs', href: '/scrape', icon: Download },
    { name: 'Scraped Jobs', href: '/jobs', icon: Database },
  ];

  return (
    <aside className="w-64 bg-slate-900 border-r border-slate-800/80 flex flex-col justify-between h-screen sticky top-0">
      <div>
        {/* Brand Logo Header */}
        <div className="p-6 flex items-center gap-3 border-b border-slate-800/60">
          <div className="w-10 h-10 rounded-xl overflow-hidden shadow-lg shadow-sky-500/20 border border-slate-700/60 bg-slate-900 flex items-center justify-center flex-shrink-0">
            <img src="/logo.png" alt="LeadPulse Logo" className="w-full h-full object-cover" />
          </div>
          <div>
            <h1 className="font-bold text-lg text-slate-100 tracking-tight">
              LeadPulse
            </h1>
            <p className="text-xs text-slate-400">Outreach Intelligence</p>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="p-4 space-y-1.5">
          <div className="px-3 py-2 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
            Menu
          </div>
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 px-3.5 py-2.5 rounded-xl font-medium text-sm transition-all duration-200 ${
                  isActive
                    ? 'bg-sky-600/15 text-sky-400 border border-sky-500/30 shadow-sm'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                }`}
              >
                <Icon className={`w-4 h-4 ${isActive ? 'text-sky-400' : 'text-slate-400'}`} />
                {item.name}
              </Link>
            );
          })}
        </nav>
      </div>

      {/* User Profile & Logout Footer */}
      <div className="p-4 border-t border-slate-800/60">
        <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/50 flex items-center justify-between">
          <div className="flex items-center gap-3 overflow-hidden">
            <div className="w-8 h-8 rounded-full bg-sky-500/20 text-sky-400 font-semibold text-xs flex items-center justify-center border border-sky-500/30 flex-shrink-0">
              {username ? username[0].toUpperCase() : 'A'}
            </div>
            <div className="truncate">
              <p className="text-xs font-semibold text-slate-200 truncate">{username || 'Admin User'}</p>
              <p className="text-[10px] text-slate-400">Administrator</p>
            </div>
          </div>
          <button
            onClick={logout}
            title="Log Out"
            className="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </div>
    </aside>
  );
}
