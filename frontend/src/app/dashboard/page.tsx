'use client';

import React, { useEffect, useState } from 'react';
import Sidebar from '@/components/Sidebar';
import Navbar from '@/components/Navbar';
import StatCard from '@/components/StatCard';
import { fetchDashboardStats, DashboardResponse } from '@/lib/api';
import { Briefcase, Building2, Clock, Database, RefreshCw, ArrowUpRight, CheckCircle2 } from 'lucide-react';
import Link from 'next/link';

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchDashboardStats();
      setStats(data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch MongoDB stats');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const formatScrapeTime = (isoStr: string | null) => {
    if (!isoStr) return 'Never';
    try {
      const date = new Date(isoStr);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' }) + ' (' + date.toLocaleDateString() + ')';
    } catch {
      return isoStr;
    }
  };

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100">
      <Sidebar />

      <main className="flex-1 flex flex-col min-w-0">
        <Navbar title="Dashboard Overview" subtitle="Real-time Lead & Job Intelligence Metrics" />

        <div className="p-8 space-y-8">
          {/* Header Action Row */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold text-slate-100">Lead Outreach Overview</h1>
              <p className="text-xs text-slate-400">Real-time synchronized lead intelligence</p>
            </div>

            <div className="flex items-center gap-3">
              <button
                onClick={loadData}
                disabled={loading}
                className="px-3.5 py-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 hover:text-white text-xs font-medium flex items-center gap-2 transition-all hover:bg-slate-800"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />
                <span>Refresh Data</span>
              </button>

              <Link
                href="/scrape"
                className="px-4 py-2 rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white text-xs font-semibold shadow-lg shadow-sky-500/20 flex items-center gap-2 transition-all"
              >
                <span>Start New Scrape</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="p-4 rounded-2xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-300">
              {error}
            </div>
          )}

          {/* 4 Metric Stat Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
            <StatCard
              title="Total Jobs"
              value={stats ? stats.total_jobs.toLocaleString() : '0'}
              subtitle="Tracked job opportunities"
              icon={Briefcase}
              color="blue"
              loading={loading}
            />
            <StatCard
              title="Total Companies"
              value={stats ? stats.total_companies.toLocaleString() : '0'}
              subtitle="Unique target accounts"
              icon={Building2}
              color="emerald"
              loading={loading}
            />
            <StatCard
              title="Last Scrape Time"
              value={stats ? formatScrapeTime(stats.last_scrape_time) : 'Never'}
              subtitle="Latest sync execution"
              icon={Clock}
              color="amber"
              loading={loading}
            />
            <StatCard
              title="Total Records"
              value={stats ? stats.total_records.toLocaleString() : '0'}
              subtitle="Verified records in system"
              icon={Database}
              color="purple"
              loading={loading}
            />
          </div>

          {/* Recent Activity & Recent Scrapes Section */}
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-base font-bold text-slate-200">Recent Activity</h2>
              <Link href="/jobs" className="text-xs text-sky-400 hover:underline font-medium flex items-center gap-1">
                View All Scraped Records <ArrowUpRight className="w-3 h-3" />
              </Link>
            </div>

            <div className="glass-card rounded-2xl border border-slate-800/80 overflow-hidden">
              {loading ? (
                <div className="p-8 text-center text-slate-500 space-y-2">
                  <div className="w-6 h-6 border-2 border-sky-400 border-t-transparent rounded-full animate-spin mx-auto"></div>
                  <p className="text-xs">Loading activity feed...</p>
                </div>
              ) : stats && stats.recent_activity.length > 0 ? (
                <div className="divide-y divide-slate-800/60">
                  {stats.recent_activity.map((job, idx) => (
                    <div key={idx} className="p-4 flex items-center justify-between hover:bg-slate-800/40 transition-colors">
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-xl bg-sky-500/10 text-sky-400 border border-sky-500/20">
                          <CheckCircle2 className="w-4 h-4" />
                        </div>
                        <div>
                          <p className="text-sm font-bold text-slate-200">{job.job_title}</p>
                          <p className="text-xs text-slate-400">{job.company} &bull; <span className="text-sky-400">{job.portal || 'LinkedIn'}</span></p>
                        </div>
                      </div>
                      <div className="text-right">
                        <span className="inline-block px-2.5 py-0.5 rounded-full bg-slate-800 border border-slate-700 text-[11px] font-medium text-slate-300">
                          {job.country}
                        </span>
                        <p className="text-[10px] text-slate-500 mt-1">
                          {job.scraped_date ? new Date(job.scraped_date).toLocaleTimeString() : ''}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-12 text-center space-y-3">
                  <Database className="w-8 h-8 text-slate-600 mx-auto" />
                  <p className="text-sm font-semibold text-slate-400">No job records found</p>
                  <p className="text-xs text-slate-500 max-w-sm mx-auto">
                    Click "Start New Scrape" to launch a discovery job and populate your pipeline.
                  </p>
                  <Link
                    href="/scrape"
                    className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-sky-600 text-white text-xs font-semibold shadow-md shadow-sky-500/20 hover:bg-sky-500 transition-colors mt-2"
                  >
                    Go to Scrape Page
                  </Link>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
