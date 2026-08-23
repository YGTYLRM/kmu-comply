"use client";

import { useState, FormEvent } from "react";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";
import { Mail, AlertCircle, Loader2, CheckCircle2, ArrowLeft } from "lucide-react";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const supabase = createClient();
    const redirectTo =
      typeof window !== "undefined"
        ? `${window.location.origin}/reset-password`
        : "/reset-password";

    const { error: resetError } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo,
    });

    if (resetError) {
      setError("Anfrage fehlgeschlagen. Bitte erneut versuchen.");
      setLoading(false);
      return;
    }

    setDone(true);
    setLoading(false);
  };

  if (done) {
    return (
      <main className="bg-dark-950 min-h-screen flex items-center justify-center px-4">
        <div className="w-full max-w-sm text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-500/15">
            <CheckCircle2 className="h-7 w-7 text-emerald-400" />
          </div>
          <h2 className="text-xl font-bold text-white mb-2">E-Mail gesendet</h2>
          <p className="text-sm text-slate-500 leading-relaxed">
            Falls ein Konto für <span className="text-white">{email}</span> existiert,
            haben wir einen Link zum Zurücksetzen des Passworts gesendet.
            Bitte prüfen Sie Ihren Posteingang.
          </p>
          <Link
            href="/login"
            className="mt-6 inline-flex items-center gap-2 text-sm text-brand-400 hover:text-brand-300 transition-colors"
          >
            <ArrowLeft className="h-4 w-4" /> Zurück zur Anmeldung
          </Link>
        </div>
      </main>
    );
  }

  return (
    <main className="bg-dark-950 min-h-screen flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <Link href="/">
            <img src="/logo-dark-bg.png" alt="Complio" className="h-10 w-auto mx-auto mb-6" />
          </Link>
          <h1 className="text-2xl font-black text-white tracking-tight">Passwort vergessen</h1>
          <p className="text-sm text-slate-500 mt-1">
            Geben Sie Ihre E-Mail-Adresse ein. Wir senden Ihnen einen Reset-Link.
          </p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="rounded-2xl border border-white/[0.07] bg-dark-900/60 p-7 flex flex-col gap-4"
        >
          <div className="flex flex-col gap-1.5">
            <label className="flex items-center gap-2 text-xs font-semibold text-slate-400 uppercase tracking-widest">
              <Mail className="h-3.5 w-3.5" /> E-Mail
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
            {loading ? "Wird gesendet…" : "Reset-Link senden"}
          </button>

          <p className="text-center text-xs text-slate-600">
            <Link href="/login" className="text-brand-400 hover:text-brand-300 transition-colors">
              Zurück zur Anmeldung
            </Link>
          </p>
        </form>
      </div>
    </main>
  );
}
