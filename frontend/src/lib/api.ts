const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || '/api';


export interface LoginParams {
  username: string;
  password: string;
  remember_me?: boolean;
}

export interface ScrapeParams {
  country: string;
  job_keyword: string;
  limit: number;
}

export interface JobRecord {
  id?: string;
  company: string;
  job_title: string;
  country: string;
  portal: string;
  company_url?: string;
  job_url?: string;
  tier_signal?: string;
  scraped_date: string;
  raw_data?: Record<string, any>;
}

export interface JobsResponse {
  items: JobRecord[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface DashboardResponse {
  total_jobs: number;
  total_companies: number;
  last_scrape_time: string | null;
  total_records: number;
  recent_activity: JobRecord[];
}

export async function loginApi(params: LoginParams) {
  const res = await fetch(`${API_BASE_URL}/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Login failed' }));
    throw new Error(err.detail || 'Login failed');
  }

  return res.json();
}

export async function fetchDashboardStats(): Promise<DashboardResponse> {
  const res = await fetch(`${API_BASE_URL}/dashboard`, { cache: 'no-store' });
  if (!res.ok) {
    throw new Error('Failed to fetch dashboard metrics');
  }
  return res.json();
}

export interface FilterOptionsResponse {
  countries: string[];
  portals: string[];
  tier_signals: string[];
}

export async function fetchFilters(): Promise<FilterOptionsResponse> {
  const res = await fetch(`${API_BASE_URL}/filters`, { cache: 'no-store' });
  if (!res.ok) {
    throw new Error('Failed to fetch filter options');
  }
  return res.json();
}

export async function fetchJobs(params: {
  search?: string;
  country?: string;
  portal?: string;
  tier_signal?: string;
  page?: number;
  limit?: number;
}): Promise<JobsResponse> {
  const query = new URLSearchParams();
  if (params.search) query.set('search', params.search);
  if (params.country) query.set('country', params.country);
  if (params.portal) query.set('portal', params.portal);
  if (params.tier_signal) query.set('tier_signal', params.tier_signal);
  if (params.page) query.set('page', params.page.toString());
  if (params.limit) query.set('limit', params.limit.toString());

  const res = await fetch(`${API_BASE_URL}/jobs?${query.toString()}`, { cache: 'no-store' });
  if (!res.ok) {
    throw new Error('Failed to fetch jobs list');
  }
  return res.json();
}

export async function fetchJobById(id: string): Promise<JobRecord> {
  const res = await fetch(`${API_BASE_URL}/jobs/${id}`, { cache: 'no-store' });
  if (!res.ok) {
    throw new Error('Job not found');
  }
  return res.json();
}

export async function triggerScrapeApi(params: ScrapeParams) {
  const res = await fetch(`${API_BASE_URL}/scrape`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Scraping failed' }));
    throw new Error(err.detail || 'Scraping failed');
  }

  return res.json();
}
