"use client";

import { useState, FormEvent } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { Suspense } from "react";
import { createClient } from "@/lib/supabase/client";
import { Mail, Lock, AlertCircle, Loader2 } from "lucide-react";

function LoginInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const next = searchParams.get("next") ?? "/analyze";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const supabase = createClient();
    const { data, error: authError } = await supabase.auth.signInWithPassword({ email, password });

    if (authError) {
      setError(authError.message);
      setLoading(false);
      return;
    }

    // Sync profile to our DB
    if (data.session) {
      await fetch(`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/auth/sync-profile`, {
        method: "POST",
        headers: { Authorization: `Bearer ${data.session.access_token}` },
      }).catch(() => {});
    }

    router.push(next);
    router.refresh();
  };

  return (
    <main className="bg-dark-950 min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <Link href="/">
            <img src="/logo-dark-bg.png" alt="Complio" className="h-10 w-auto mx-auto mb-6" />
          </Link>
          <h1 className="text-2xl font-black text-white tracking-tight">Welcome back</h1>
          <p className="text-sm text-slate-500 mt-1">Sign in to your Complio account</p>
        </div>

        <form onSubmit={handleSubmit} className="rounded-2xl border border-white/[0.07] bg-dark-900/60 p-7 flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="flex items-center gap-2 text-xs font-semibold text-slate-400 uppercase tracking-widest">
              <Mail className="h-3.5 w-3.5" /> Email
            </label>
            <input
              type="email"
              required
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="anna@company.de"
              className="w-full rounded-xl border border-white/[0.08] bg-white/[0.03] px-4 py-3 text-sm text-white placeholder-slate-600 outline-none focus:border-brand-500/50 focus:ring-2 focus:ring-brand-500/15 transition-all"
            />
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="flex items-center gap-2 text-xs font-semibold text-slate-400 uppercase tracking-widest">
              <Lock className="h-3.5 w-3.5" /> Password
            </label>
            <input
              type="password"
              required
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full rounded-xl border border-white/[0.08] bg-white/[0.03] px-4 py-3 text-sm text-white placeholder-slate-600 outline-none focus:border-brand-500/50 focus:ring-2 focus:ring-brand-500/15 transition-all"
            />
          </div>

          {error && (
            <div className="flex items-start gap-2 rounded-xl bg-red-500/10 border border-red-500/25 px-4 py-3 text-sm text-red-400">
              <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="mt-1 rounded-xl bg-brand-600 px-6 py-3 text-sm font-semibold text-white hover:bg-brand-500 transition-colors shadow-glow-blue-sm hover:shadow-glow-blue disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading && <Loader2 className="h-4 w-4 animate-spin" />}
            {loading ? "Signing in…" : "Sign in"}
          </button>

          <p className="text-center text-xs text-slate-600">
            No account?{" "}
            <Link href="/register" className="text-brand-400 hover:text-brand-300 transition-colors">
              Request access
            </Link>
          </p>
        </form>
      </div>
    </main>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<main className="bg-dark-950 min-h-screen" />}>
      <LoginInner />
    </Suspense>
  );
}
