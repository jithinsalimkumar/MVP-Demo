'use client';

import React from 'react';
import { ShieldCheck, Database, Bell } from 'lucide-react';

interface NavbarProps {
  title: string;
  subtitle?: string;
}

export default function Navbar({ title, subtitle }: NavbarProps) {
  return (
    <header className="h-16 bg-slate-900/80 backdrop-blur-md border-b border-slate-800/60 px-8 flex items-center justify-between sticky top-0 z-30">
      <div>
        <h2 className="text-lg font-bold text-slate-100">{title}</h2>
        {subtitle && <p className="text-xs text-slate-400">{subtitle}</p>}
      </div>

      <div className="flex items-center gap-4">
        {/* Status indicator */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-950/80 border border-slate-800 text-xs">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
          <span className="text-slate-300 font-medium">System Connected</span>
        </div>

        {/* Verified Session Badge */}
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-sky-500/10 border border-sky-500/20 text-sky-400 text-xs font-medium">
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Active Session</span>
        </div>
      </div>
    </header>
  );
}
