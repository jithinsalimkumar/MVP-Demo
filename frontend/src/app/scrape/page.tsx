'use client';

import React, { useState } from 'react';
import Sidebar from '@/components/Sidebar';
import Navbar from '@/components/Navbar';
import Toast from '@/components/Toast';
import { triggerScrapeApi } from '@/lib/api';
import { Download, Globe, Search, Hash, Sparkles, CheckCircle2, ArrowRight, Code2 } from 'lucide-react';
import Link from 'next/link';

export default function ScrapePage() {
  const [country, setCountry] = useState('United States');
  const [jobKeyword, setJobKeyword] = useState('Software Engineer');
  const [limit, setLimit] = useState<number>(10);

  const [loading, setLoading] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const [lastResult, setLastResult] = useState<{ count: number; country: string; keyword: string } | null>(null);

  const countries = [
    'United States',
    'United Kingdom',
    'Canada',
    'Germany',
    'India',
    'Australia',
    'Singapore',
    'France',
  ];

  const handleScrape = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setToast(null);

    try {
      const res = await triggerScrapeApi({
        country,
        job_keyword: jobKeyword,
        limit: Number(limit),
      });

      if (res.success) {
        setToast({
          message: `Successfully scraped ${res.count} jobs into MongoDB!`,
          type: 'success',
        });
        setLastResult({
          count: res.count,
          country,
          keyword: jobKeyword,
        });
      } else {
        setToast({
          message: res.message || 'Scraping returned an issue',
          type: 'error',
        });
      }
    } catch (err: any) {
      setToast({
        message: err.message || 'Scraping failed. Check backend connection.',
        type: 'error',
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100">
      <Sidebar />

      <main className="flex-1 flex flex-col min-w-0">
        <Navbar title="Lead Discovery Crawler" subtitle="Launch automated discovery jobs across target platforms" />

        <div className="p-8 max-w-4xl space-y-8">
          {/* Section Header */}
          <div className="space-y-1">
            <h1 className="text-xl font-bold text-slate-100">Lead Intelligence Crawler</h1>
            <p className="text-xs text-slate-400">
              Select search parameters to execute real-time discovery jobs. Collected leads automatically update your pipeline.
            </p>
          </div>

          {/* Form Card */}
          <div className="glass-card rounded-2xl p-6 border border-slate-800/80 space-y-6">
            <form onSubmit={handleScrape} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
                {/* Country Dropdown */}
                <div className="space-y-2">
                  <label className="text-xs font-semibold uppercase text-slate-400 tracking-wider flex items-center gap-1.5">
                    <Globe className="w-3.5 h-3.5 text-sky-400" />
                    Target Country
                  </label>
                  <select
                    value={country}
                    onChange={(e) => setCountry(e.target.value)}
                    className="w-full bg-slate-950/80 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 transition-all cursor-pointer"
                  >
                    {countries.map((c) => (
                      <option key={c} value={c} className="bg-slate-900 text-slate-100">
                        {c}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Job Keyword Input */}
                <div className="space-y-2">
                  <label className="text-xs font-semibold uppercase text-slate-400 tracking-wider flex items-center gap-1.5">
                    <Search className="w-3.5 h-3.5 text-sky-400" />
                    Job Keyword / Title
                  </label>
                  <input
                    type="text"
                    required
                    value={jobKeyword}
                    onChange={(e) => setJobKeyword(e.target.value)}
                    placeholder="e.g. Email Marketing Specialist"
                    className="w-full bg-slate-950/80 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-slate-100 placeholder-slate-600 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 transition-all"
                  />
                </div>

                {/* Limit Input */}
                <div className="space-y-2">
                  <label className="text-xs font-semibold uppercase text-slate-400 tracking-wider flex items-center gap-1.5">
                    <Hash className="w-3.5 h-3.5 text-sky-400" />
                    Record Limit
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={100}
                    required
                    value={limit}
                    onChange={(e) => setLimit(Number(e.target.value))}
                    className="w-full bg-slate-950/80 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-slate-100 focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 transition-all"
                  />
                </div>
              </div>

              {/* Action Button */}
              <div className="pt-2 flex items-center justify-between border-t border-slate-800/80">
                <div className="flex items-center gap-2 text-xs text-slate-400">
                  <Sparkles className="w-4 h-4 text-sky-400 animate-pulse" />
                  <span>Executes automated lead discovery &amp; updates pipeline</span>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-sky-500 to-blue-600 hover:from-sky-400 hover:to-blue-500 text-white font-semibold text-sm shadow-lg shadow-sky-500/25 flex items-center gap-2 transition-all disabled:opacity-50"
                >
                  {loading ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      <span>Scraping Live Data...</span>
                    </>
                  ) : (
                    <>
                      <Download className="w-4 h-4" />
                      <span>Start Scraping Now</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>

          {/* Last Scraping Results Card */}
          {lastResult && (
            <div className="p-5 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 flex items-center justify-between animate-in fade-in">
              <div className="flex items-center gap-3">
                <div className="p-2.5 rounded-xl bg-emerald-500/20 text-emerald-400">
                  <CheckCircle2 className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="font-bold text-sm text-slate-100">Scrape Completed!</h4>
                  <p className="text-xs text-slate-300">
                    Inserted <span className="font-bold text-emerald-400">{lastResult.count} new records</span> for "{lastResult.keyword}" in {lastResult.country}.
                  </p>
                </div>
              </div>

              <Link
                href="/jobs"
                className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center gap-1.5 transition-colors shadow-md shadow-emerald-600/20"
              >
                <span>View Jobs Table</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </Link>
            </div>
          )}

          {/* Lead Discovery Configuration */}
          <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-3">
            <h3 className="text-xs font-semibold uppercase text-slate-400 tracking-wider flex items-center gap-2">
              <Code2 className="w-4 h-4 text-purple-400" />
              Lead Discovery Configuration
            </h3>
            <p className="text-xs text-slate-300 leading-relaxed">
              Target job titles and geographic regions can be configured in your system settings. All captured job postings automatically synchronize with your leads directory.
            </p>
          </div>
        </div>
      </main>

      {/* Toast Notification */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
}
