"use client";

import { useState, useEffect, FormEvent, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";
import { ShieldCheck, AlertCircle, Loader2 } from "lucide-react";

function MfaChallengeInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const rawNext = searchParams.get("next") ?? "/dashboard";
  const next = rawNext.startsWith("/") ? rawNext : "/dashboard";

  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [checking, setChecking] = useState(true);
  const [factorId, setFactorId] = useState<string | null>(null);

  useEffect(() => {
    const check = async () => {
      const supabase = createClient();
      const { data: aal } = await supabase.auth.mfa.getAuthenticatorAssuranceLevel();
      if (!aal || aal.currentLevel === aal.nextLevel) {
        router.replace(next);
        return;
      }
      const { data: list } = await supabase.auth.mfa.listFactors();
      const factor = list?.totp.find((f) => f.status === "verified");
      if (!factor) {
        router.replace(next);
        return;
      }
      setFactorId(factor.id);
      setChecking(false);
    };
    check();
  }, [next, router]);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (code.length !== 6 || !factorId) return;
    setLoading(true);
    setError(null);
    try {
      const supabase = createClient();
      const { data: challenge, error: challengeError } = await supabase.auth.mfa.challenge({ factorId });
      if (challengeError) throw challengeError;
      const { error: verifyError } = await supabase.auth.mfa.verify({
        factorId,
        challengeId: challenge.id,
        code,
      });
      if (verifyError) throw verifyError;
      router.push(next);
      router.refresh();
    } catch {
      setError("Code ungültig. Bitte erneut versuchen.");
      setLoading(false);
    }
  };

  if (checking) {
    return <main className="bg-dark-950 min-h-screen" />;
  }

  return (
    <main className="bg-dark-950 min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <Link href="/">
            <img src="/logo-dark-bg.png" alt="Complio" className="h-10 w-auto mx-auto mb-6" />
          </Link>
          <h1 className="text-2xl font-black text-white tracking-tight">Bestätigungscode</h1>
          <p className="text-sm text-slate-500 mt-1">Code aus Ihrer Authenticator-App eingeben</p>
        </div>

        <form onSubmit={handleSubmit} className="rounded-2xl border border-white/[0.07] bg-dark-900/60 p-7 flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="flex items-center gap-2 text-xs font-semibold text-slate-400 uppercase tracking-widest">
              <ShieldCheck className="h-3.5 w-3.5" /> Code
            </label>
            <input
              type="text"
              inputMode="numeric"
              autoComplete="one-time-code"
              maxLength={6}
              required
              autoFocus
              value={code}
              onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
              placeholder="000000"
              className="w-full rounded-xl border border-white/[0.08] bg-white/[0.03] px-4 py-3 text-sm text-white tracking-widest placeholder-slate-600 outline-none focus:border-brand-500/50 focus:ring-2 focus:ring-brand-500/15 transition-all"
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
            disabled={loading || code.length !== 6}
            className="mt-1 rounded-xl bg-brand-600 px-6 py-3 text-sm font-semibold text-white hover:bg-brand-500 transition-colors shadow-glow-blue-sm hover:shadow-glow-blue disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
          >
            {loading && <Loader2 className="h-4 w-4 animate-spin" />}
            {loading ? "Wird geprüft…" : "Bestätigen"}
          </button>
        </form>
      </div>
    </main>
  );
}

export default function MfaChallengePage() {
  return (
    <Suspense fallback={<main className="bg-dark-950 min-h-screen" />}>
      <MfaChallengeInner />
    </Suspense>
  );
}
