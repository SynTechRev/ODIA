'use client';

import React, { useEffect } from 'react';
import { useAppNavigate } from '@/lib/navigation';

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  const nav = useAppNavigate();

  useEffect(() => {
    console.error('[ODIA] Page error:', error);
  }, [error]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 p-8">
      <div className="max-w-md w-full text-center space-y-4">
        <div className="w-12 h-12 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center mx-auto text-2xl ring-1 ring-amber-200">
          ⚠
        </div>
        <h1 className="text-xl font-bold text-slate-900">Page failed to load</h1>
        <p className="text-sm text-slate-500">
          {error?.message ?? 'An unexpected error occurred.'}
        </p>
        <div className="flex justify-center gap-3 pt-2">
          <button
            onClick={reset}
            className="px-4 py-2 rounded-lg bg-amber-500 text-slate-900 font-semibold text-sm hover:bg-amber-400 transition-colors"
          >
            Try again
          </button>
          <button
            onClick={() => nav('/')}
            className="px-4 py-2 rounded-lg border border-slate-200 bg-white text-slate-700 font-semibold text-sm hover:bg-slate-50 transition-colors"
          >
            Dashboard
          </button>
        </div>
      </div>
    </div>
  );
}
