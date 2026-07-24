'use client';

import React from 'react';
import { LucideIcon } from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  color?: 'blue' | 'emerald' | 'amber' | 'purple';
  loading?: boolean;
}

export default function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  color = 'blue',
  loading = false,
}: StatCardProps) {
  const colorMap = {
    blue: 'from-sky-500/20 to-blue-600/10 text-sky-400 border-sky-500/20',
    emerald: 'from-emerald-500/20 to-teal-600/10 text-emerald-400 border-emerald-500/20',
    amber: 'from-amber-500/20 to-orange-600/10 text-amber-400 border-amber-500/20',
    purple: 'from-purple-500/20 to-indigo-600/10 text-purple-400 border-purple-500/20',
  };

  const iconBgMap = {
    blue: 'bg-sky-500/10 text-sky-400 border-sky-500/20',
    emerald: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20',
    amber: 'bg-amber-500/10 text-amber-400 border-amber-500/20',
    purple: 'bg-purple-500/10 text-purple-400 border-purple-500/20',
  };

  return (
    <div className={`p-5 rounded-2xl bg-gradient-to-br ${colorMap[color]} glass-card glass-card-hover border flex items-start justify-between relative overflow-hidden`}>
      <div className="space-y-1">
        <p className="text-xs font-semibold text-slate-400 tracking-wide uppercase">{title}</p>
        {loading ? (
          <div className="h-8 w-24 bg-slate-800 animate-pulse rounded-lg mt-1"></div>
        ) : (
          <h3 className="text-2xl font-bold text-slate-100 tracking-tight">{value}</h3>
        )}
        {subtitle && <p className="text-[11px] text-slate-400">{subtitle}</p>}
      </div>

      <div className={`p-3 rounded-xl border ${iconBgMap[color]} shadow-inner`}>
        <Icon className="w-5 h-5" />
      </div>
    </div>
  );
}
