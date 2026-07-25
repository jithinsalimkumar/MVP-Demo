'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';

export default function Home() {
  const router = useRouter();
  const { isAuthenticated, loading } = useAuth();

  useEffect(() => {
    if (!loading) {
      const target = isAuthenticated ? '/dashboard' : '/login';
      router.replace(target);
    }
  }, [isAuthenticated, loading, router]);

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col items-center justify-center p-4">
      <div className="flex items-center gap-3 text-sky-400 mb-3">
        <div className="w-6 h-6 border-2 border-sky-400 border-t-transparent rounded-full animate-spin"></div>
        <span className="text-sm font-medium text-slate-300">Opening Lead Outreach System...</span>
      </div>
      <a
        href="/login"
        className="text-xs text-sky-400 hover:text-sky-300 underline font-medium transition-colors"
      >
        Click here to open Login Page directly
      </a>
    </div>
  );
}
