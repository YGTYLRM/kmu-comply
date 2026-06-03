"use client";

import { useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";
import { Mail, Lock, User, AlertCircle, Loader2, CheckCircle2 } from "lucide-react";

export default function RegisterPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (password.length < 8) {
      setError("Das Passwort muss mindestens 8 Zeichen haben.");
      return;
    }
    setLoading(true);
    setError(null);

    const supabase = createClient();
    const { data, error: authError } = await supabase.auth.signUp({
      email,
      password,
      options: { data: { name } },
    });

    if (authError) {
      // Map common errors to user-friendly messages without leaking internals
      const msg = authError.message.toLowerCase();
      if (msg.includes("already")) setError("Ein Konto mit dieser E-Mail existiert bereits. Bitte anmelden.");
      else if (msg.includes("password")) setError("Das Passwort muss mindestens 8 Zeichen haben.");
      else setError("Registrierung fehlgeschlagen. Bitte erneut versuchen.");
      setLoading(false);
      return;
    }

    // If email confirmation is disabled, session is available immediately
    if (data.session) {
      await fetch(`/api/auth/sync-profile`, {
        method: "POST",
        headers: { Authorization: `Bearer ${data.session.access_token}` },
      }).catch(() => {});
      router.push("/");
      router.refresh();
    } else {
      setDone(true);
    }
  };

  if (done) {
    return (
      <main className="bg-dark-950 min-h-screen flex items-center justify-center px-4">
        <div className="w-full max-w-sm text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-500/15">
            <CheckCircle2 className="h-7 w-7 text-emerald-400" />
          </div>
          <h2 className="text-xl font-bold text-white mb-2">E-Mail bestätigen</h2>
          <p className="text-sm text-slate-500">Wir haben einen Bestätigungslink an <span className="text-white">{email}</span> gesendet. Bitte klicken Sie den Link, um Ihr Konto zu aktivieren.</p>
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
          <h1 className="text-2xl font-black text-white tracking-tight">Konto erstellen</h1>
          <p className="text-sm text-slate-500 mt-1">Jetzt starten</p>
        </div>

        <form onSubmit={handleSubmit} className="rounded-2xl border border-white/[0.07] bg-dark-900/60 p-7 flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="flex items-center gap-2 text-xs font-semibold text-slate-400 uppercase tracking-widest">
              <User className="h-3.5 w-3.5" /> Name
            </label>
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Anna Müller"
              className="w-full rounded-xl border border-white/[0.08] bg-white/[0.03] px-4 py-3 text-sm text-white placeholder-slate-600 outline-none focus:border-brand-500/50 focus:ring-2 focus:ring-brand-500/15 transition-all"
            />
          </div>

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

          <div className="flex flex-col gap-1.5">
            <label className="flex items-center gap-2 text-xs font-semibold text-slate-400 uppercase tracking-widest">
              <Lock className="h-3.5 w-3.5" /> Passwort
            </label>
            <input
              type="password"
              required
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Mind. 8 Zeichen"
              className="w-full rounded-xl border border-white/[0.08] bg-white/[0.03] px-4 py-3 text-sm text-white placeholder-slate-600 outline-none focus:border-brand-500/50 focus:ring-2 focus:ring-brand-500/15 transition-all"
            />
            <ul className="mt-1 flex flex-col gap-0.5 pl-1">
              <li className={`flex items-center gap-1.5 text-xs transition-colors ${password.length >= 8 ? "text-emerald-400" : "text-slate-600"}`}>
                <span className={`h-1 w-1 rounded-full flex-shrink-0 ${password.length >= 8 ? "bg-emerald-400" : "bg-slate-700"}`} />
                Mindestens 8 Zeichen
              </li>
              <li className={`flex items-center gap-1.5 text-xs transition-colors ${/[A-Z]/.test(password) ? "text-emerald-400" : "text-slate-600"}`}>
                <span className={`h-1 w-1 rounded-full flex-shrink-0 ${/[A-Z]/.test(password) ? "bg-emerald-400" : "bg-slate-700"}`} />
                Ein Großbuchstabe
              </li>
              <li className={`flex items-center gap-1.5 text-xs transition-colors ${/[0-9]/.test(password) ? "text-emerald-400" : "text-slate-600"}`}>
                <span className={`h-1 w-1 rounded-full flex-shrink-0 ${/[0-9]/.test(password) ? "bg-emerald-400" : "bg-slate-700"}`} />
                Eine Zahl
              </li>
            </ul>
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
            {loading ? "Konto wird erstellt…" : "Registrieren"}
          </button>

          <p className="text-center text-xs text-slate-600">
            Bereits ein Konto?{" "}
            <Link href="/login" className="text-brand-400 hover:text-brand-300 transition-colors">
              Anmelden
            </Link>
          </p>
        </form>
      </div>
    </main>
  );
}
