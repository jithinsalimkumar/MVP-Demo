'use client';

import React, { useEffect, useState } from 'react';
import Sidebar from '@/components/Sidebar';
import Navbar from '@/components/Navbar';
import JobDetailsModal from '@/components/JobDetailsModal';
import { fetchJobs, fetchFilters, JobRecord, JobsResponse } from '@/lib/api';
import {
  Search,
  Filter,
  ChevronLeft,
  ChevronRight,
  Building2,
  Calendar,
  Globe,
  ExternalLink,
  RefreshCw,
  Database,
  Tag,
  ArrowUpDown
} from 'lucide-react';

export default function JobsPage() {
  const [data, setData] = useState<JobsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Filters & Pagination State
  const [search, setSearch] = useState('');
  const [countryFilter, setCountryFilter] = useState('All');
  const [portalFilter, setPortalFilter] = useState('All');
  const [tierSignalFilter, setTierSignalFilter] = useState('All');
  const [page, setPage] = useState(1);
  const [limit] = useState(10);

  // Dynamic Filter Options
  const [countries, setCountries] = useState<string[]>(['All', 'United States', 'United Kingdom', 'Canada']);
  const [portals, setPortals] = useState<string[]>(['All', 'LinkedIn', 'Indeed']);
  const [tierSignals, setTierSignals] = useState<string[]>(['All']);

  // Modal State
  const [selectedJob, setSelectedJob] = useState<JobRecord | null>(null);

  useEffect(() => {
    async function initFilterOptions() {
      try {
        const opts = await fetchFilters();
        if (opts.countries && opts.countries.length > 0) {
          setCountries(['All', ...opts.countries]);
        }
        if (opts.portals && opts.portals.length > 0) {
          setPortals(['All', ...opts.portals]);
        }
        if (opts.tier_signals && opts.tier_signals.length > 0) {
          setTierSignals(['All', ...opts.tier_signals]);
        }
      } catch (e) {
        console.warn('Failed to load dynamic filter options', e);
      }
    }
    initFilterOptions();
  }, []);

  const loadJobs = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchJobs({
        search: search.trim() || undefined,
        country: countryFilter !== 'All' ? countryFilter : undefined,
        portal: portalFilter !== 'All' ? portalFilter : undefined,
        tier_signal: tierSignalFilter !== 'All' ? tierSignalFilter : undefined,
        page,
        limit,
      });
      setData(res);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch jobs');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadJobs();
  }, [page, countryFilter, portalFilter, tierSignalFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    loadJobs();
  };

  const formatDate = (isoStr: string) => {
    if (!isoStr) return '-';
    try {
      return new Date(isoStr).toLocaleDateString([], {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      });
    } catch {
      return isoStr;
    }
  };

  return (
    <div className="flex min-h-screen bg-slate-950 text-slate-100">
      <Sidebar />

      <main className="flex-1 flex flex-col min-w-0">
        <Navbar title="Jobs Directory" subtitle="Explore and filter tracked job leads across target platforms" />

        <div className="p-8 space-y-6">
          {/* Top Controls Bar */}
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            {/* Search Input */}
            <form onSubmit={handleSearchSubmit} className="flex items-center gap-2 flex-1 max-w-md">
              <div className="relative flex-1">
                <Search className="w-4 h-4 text-slate-500 absolute left-3.5 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search company, job title, or portal..."
                  className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-10 pr-4 py-2 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 transition-all"
                />
              </div>
              <button
                type="submit"
                className="px-4 py-2 bg-sky-600 hover:bg-sky-500 text-white rounded-xl text-sm font-medium transition-colors"
              >
                Search
              </button>
            </form>

            {/* Filters & Refresh */}
            <div className="flex items-center gap-3 flex-wrap">
              {/* Country Select */}
              <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-300">
                <Globe className="w-3.5 h-3.5 text-slate-500" />
                <select
                  value={countryFilter}
                  onChange={(e) => {
                    setCountryFilter(e.target.value);
                    setPage(1);
                  }}
                  className="bg-transparent text-slate-200 focus:outline-none cursor-pointer"
                >
                  {countries.map((c) => (
                    <option key={c} value={c} className="bg-slate-900 text-slate-200">
                      Country: {c}
                    </option>
                  ))}
                </select>
              </div>

              {/* Portal Select */}
              <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-300">
                <Filter className="w-3.5 h-3.5 text-slate-500" />
                <select
                  value={portalFilter}
                  onChange={(e) => {
                    setPortalFilter(e.target.value);
                    setPage(1);
                  }}
                  className="bg-transparent text-slate-200 focus:outline-none cursor-pointer"
                >
                  {portals.map((p) => (
                    <option key={p} value={p} className="bg-slate-900 text-slate-200">
                      Portal: {p}
                    </option>
                  ))}
                </select>
              </div>

              {/* Tier Signal Select */}
              <div className="flex items-center gap-1.5 bg-slate-900 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-300">
                <Tag className="w-3.5 h-3.5 text-slate-500" />
                <select
                  value={tierSignalFilter}
                  onChange={(e) => {
                    setTierSignalFilter(e.target.value);
                    setPage(1);
                  }}
                  className="bg-transparent text-slate-200 focus:outline-none cursor-pointer max-w-[170px] truncate"
                >
                  {tierSignals.map((t) => (
                    <option key={t} value={t} className="bg-slate-900 text-slate-200">
                      Tier Signal: {t}
                    </option>
                  ))}
                </select>
              </div>

              {/* Refresh Button */}
              <button
                onClick={loadJobs}
                className="p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
                title="Refresh Table"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>

          {/* Error Banner */}
          {error && (
            <div className="p-4 rounded-xl bg-rose-500/10 border border-rose-500/20 text-xs text-rose-300">
              {error}
            </div>
          )}

          {/* Jobs Data Table */}
          <div className="glass-card rounded-2xl border border-slate-800/80 overflow-hidden shadow-xl">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-300">
                <thead className="bg-slate-900/90 text-xs font-semibold uppercase text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="px-5 py-3.5">Company</th>
                    <th className="px-5 py-3.5">Job Title</th>
                    <th className="px-5 py-3.5">Tier Signal</th>
                    <th className="px-5 py-3.5">Country</th>
                    <th className="px-5 py-3.5">Portal</th>
                    <th className="px-5 py-3.5">Job URL</th>
                    <th className="px-5 py-3.5">Date</th>
                    <th className="px-5 py-3.5 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {loading ? (
                    Array.from({ length: 5 }).map((_, i) => (
                      <tr key={i} className="animate-pulse">
                        <td className="px-5 py-4">
                          <div className="h-4 w-32 bg-slate-800 rounded"></div>
                        </td>
                        <td className="px-5 py-4">
                          <div className="h-4 w-40 bg-slate-800 rounded"></div>
                        </td>
                        <td className="px-5 py-4">
                          <div className="h-4 w-24 bg-slate-800 rounded"></div>
                        </td>
                        <td className="px-5 py-4">
                          <div className="h-4 w-20 bg-slate-800 rounded"></div>
                        </td>
                        <td className="px-5 py-4">
                          <div className="h-4 w-16 bg-slate-800 rounded"></div>
                        </td>
                        <td className="px-5 py-4">
                          <div className="h-4 w-20 bg-slate-800 rounded"></div>
                        </td>
                        <td className="px-5 py-4">
                          <div className="h-4 w-20 bg-slate-800 rounded"></div>
                        </td>
                        <td className="px-5 py-4 text-right">
                          <div className="h-4 w-12 bg-slate-800 rounded ml-auto"></div>
                        </td>
                      </tr>
                    ))
                  ) : data && data.items.length > 0 ? (
                    data.items.map((job) => (
                      <tr
                        key={job.id}
                        onClick={() => setSelectedJob(job)}
                        className="hover:bg-sky-500/5 transition-colors cursor-pointer group"
                      >
                        <td className="px-5 py-4 font-semibold text-slate-100 flex items-center gap-2">
                          <div className="w-8 h-8 rounded-lg bg-slate-800 border border-slate-700 flex items-center justify-center text-sky-400 group-hover:border-sky-500/40 flex-shrink-0">
                            <Building2 className="w-4 h-4" />
                          </div>
                          <span className="truncate max-w-[180px]">{job.company}</span>
                        </td>
                        <td className="px-5 py-4 font-medium text-slate-200">{job.job_title}</td>
                        <td className="px-5 py-4">
                          <span className="inline-block px-2.5 py-0.5 rounded-full bg-purple-500/10 border border-purple-500/20 text-xs font-semibold text-purple-300">
                            {job.tier_signal || 'Unknown'}
                          </span>
                        </td>
                        <td className="px-5 py-4 whitespace-nowrap">
                          <span className="inline-block px-2.5 py-0.5 rounded-full bg-slate-900 border border-slate-800 text-xs text-slate-300 font-medium">
                            {job.country}
                          </span>
                        </td>
                        <td className="px-5 py-4 whitespace-nowrap">
                          <span className="inline-block px-2.5 py-0.5 rounded-full bg-sky-500/10 border border-sky-500/20 text-xs font-semibold text-sky-400">
                            {job.portal || 'LinkedIn'}
                          </span>
                        </td>
                        <td className="px-5 py-4 whitespace-nowrap">
                          {(job.job_url || job.company_url) ? (
                            <a
                              href={job.job_url || job.company_url}
                              target="_blank"
                              rel="noreferrer"
                              onClick={(e) => e.stopPropagation()}
                              className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-sky-500/10 border border-sky-500/20 text-xs font-medium text-sky-400 hover:bg-sky-500/20 hover:text-sky-300 transition-all"
                            >
                              <span>Open Job</span>
                              <ExternalLink className="w-3 h-3" />
                            </a>
                          ) : (
                            <span className="text-xs text-slate-500">N/A</span>
                          )}
                        </td>
                        <td className="px-5 py-4 text-xs text-slate-400 whitespace-nowrap">{formatDate(job.scraped_date)}</td>
                        <td className="px-5 py-4 text-right whitespace-nowrap">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setSelectedJob(job);
                            }}
                            className="text-xs font-semibold text-sky-400 hover:text-sky-300 bg-sky-500/10 hover:bg-sky-500/20 border border-sky-500/20 px-3 py-1 rounded-lg transition-all"
                          >
                            View Details
                          </button>
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={8} className="px-6 py-12 text-center">
                        <Database className="w-8 h-8 text-slate-600 mx-auto mb-2" />
                        <p className="text-sm font-semibold text-slate-400">No jobs match your query</p>
                        <p className="text-xs text-slate-500">Try adjusting search keywords or trigger a new scrape.</p>
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* Pagination Controls */}
            {data && data.total > 0 && (
              <div className="p-4 bg-slate-900/60 border-t border-slate-800 flex items-center justify-between text-xs text-slate-400">
                <p>
                  Showing <span className="font-semibold text-slate-200">{((page - 1) * limit) + 1}</span> to{' '}
                  <span className="font-semibold text-slate-200">{Math.min(page * limit, data.total)}</span> of{' '}
                  <span className="font-semibold text-slate-200">{data.total}</span> jobs
                </p>

                <div className="flex items-center gap-2">
                  <button
                    disabled={page <= 1}
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                    className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 disabled:opacity-40 transition-colors"
                  >
                    <ChevronLeft className="w-4 h-4" />
                  </button>
                  <span className="font-semibold text-slate-300">
                    Page {page} of {data.total_pages}
                  </span>
                  <button
                    disabled={page >= data.total_pages}
                    onClick={() => setPage((p) => p + 1)}
                    className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 disabled:opacity-40 transition-colors"
                  >
                    <ChevronRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </main>

      {/* Details Slide-Over Drawer Modal */}
      <JobDetailsModal
        job={selectedJob}
        onClose={() => setSelectedJob(null)}
      />
    </div>
  );
}
