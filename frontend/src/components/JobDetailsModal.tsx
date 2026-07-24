'use client';

import React from 'react';
import { X, ExternalLink, Building2, MapPin, Globe, Calendar, Code, CheckCircle2 } from 'lucide-react';
import { JobRecord } from '@/lib/api';

interface JobDetailsModalProps {
  job: JobRecord | null;
  onClose: () => void;
}

export default function JobDetailsModal({ job, onClose }: JobDetailsModalProps) {
  if (!job) return null;

  const formatDate = (isoStr: string) => {
    try {
      return new Date(isoStr).toLocaleString();
    } catch {
      return isoStr;
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-slate-950/70 backdrop-blur-sm transition-opacity animate-in fade-in duration-200">
      {/* Backdrop click to close */}
      <div className="flex-1" onClick={onClose}></div>

      {/* Drawer Card */}
      <div className="w-full max-w-xl bg-slate-900 border-l border-slate-800 h-full p-6 flex flex-col justify-between overflow-y-auto shadow-2xl animate-in slide-in-from-right duration-300">
        <div className="space-y-6">
          {/* Header */}
          <div className="flex items-start justify-between border-b border-slate-800 pb-4">
            <div className="space-y-1">
              <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/20 text-xs font-medium">
                <CheckCircle2 className="w-3 h-3" />
                {job.portal || 'Verified Lead'}
              </div>
              <h2 className="text-xl font-bold text-slate-100">{job.job_title}</h2>
              <p className="text-sm font-medium text-slate-400 flex items-center gap-1.5">
                <Building2 className="w-4 h-4 text-sky-400" />
                {job.company}
              </p>
            </div>
            <button
              onClick={onClose}
              className="p-2 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Quick Info Grid */}
          <div className="grid grid-cols-2 gap-3">
            <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1">
              <p className="text-[10px] uppercase font-semibold text-slate-500 flex items-center gap-1">
                <MapPin className="w-3 h-3" /> Country
              </p>
              <p className="text-sm font-semibold text-slate-200">{job.country}</p>
            </div>
            <div className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 space-y-1">
              <p className="text-[10px] uppercase font-semibold text-slate-500 flex items-center gap-1">
                <Calendar className="w-3 h-3" /> Captured At
              </p>
              <p className="text-xs font-semibold text-slate-200">{formatDate(job.scraped_date)}</p>
            </div>
          </div>

          {/* Company URL */}
          {job.company_url && (
            <div className="p-3.5 rounded-xl bg-slate-950/60 border border-slate-800/80 flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs font-medium text-slate-300">
                <Globe className="w-4 h-4 text-sky-400" />
                <span>Company Portal URL</span>
              </div>
              <a
                href={job.company_url}
                target="_blank"
                rel="noreferrer"
                className="text-xs font-semibold text-sky-400 hover:text-sky-300 flex items-center gap-1 hover:underline"
              >
                Visit Site <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          )}

          {/* Lead Technical Payload */}
          <div className="space-y-2">
            <h4 className="text-xs font-semibold uppercase text-slate-400 flex items-center gap-1.5">
              <Code className="w-4 h-4 text-purple-400" />
              Lead Technical Payload
            </h4>
            <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 font-mono text-xs text-sky-300 overflow-x-auto max-h-64 scrollbar-thin">
              <pre>{JSON.stringify(job.raw_data || job, null, 2)}</pre>
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="pt-4 border-t border-slate-800 flex items-center justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-sm font-medium transition-colors"
          >
            Close Details
          </button>
        </div>
      </div>
    </div>
  );
}
