"use client";

import { useEffect, useState, FormEvent } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";
import { Lock, AlertCircle, Loader2, CheckCircle2 } from "lucide-react";

export default function ResetPasswordPage() {
  const router = useRouter();
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const supabase = createClient();
    const { data: { subscription } } = supabase.auth.onAuthStateChange((event) => {
      if (event === "PASSWORD_RECOVERY") {
        setReady(true);
      }
    });
    return () => subscription.unsubscribe();
  }, []);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (password.length < 8) {
      setError("Das Passwort muss mindestens 8 Zeichen haben.");
      return;
    }
    if (password !== confirm) {
      setError("Die Passwörter stimmen nicht überein.");
      return;
    }
    setLoading(true);
    setError(null);

    const supabase = createClient();
    const { error: updateError } = await supabase.auth.updateUser({ password });

    if (updateError) {
      setError("Passwort konnte nicht geändert werden. Bitte erneut versuchen.");
      setLoading(false);
      return;
    }

    setDone(true);
    setLoading(false);
    setTimeout(() => router.push("/login"), 2500);
  };

  if (done) {
    return (
      <main className="bg-dark-950 min-h-screen flex items-center justify-center px-4">
        <div className="w-full max-w-sm text-center">
          <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-500/15">
            <CheckCircle2 className="h-7 w-7 text-emerald-400" />
          </div>
          <h2 className="text-xl font-bold text-white mb-2">Passwort geändert</h2>
          <p className="text-sm text-slate-500">
            Ihr Passwort wurde erfolgreich geändert. Sie werden zur Anmeldung weitergeleitet…
          </p>
        </div>
      </main>
    );
  }

  if (!ready) {
    return (
      <main className="bg-dark-950 min-h-screen flex items-center justify-center px-4">
        <div className="w-full max-w-sm text-center">
          <div className="flex h-12 w-12 mx-auto mb-4 items-center justify-center rounded-2xl border border-white/[0.08] bg-white/[0.03]">
            <Lock className="h-5 w-5 text-slate-500" />
          </div>
          <h2 className="text-lg font-bold text-white mb-2">Link wird geprüft…</h2>
          <p className="text-sm text-slate-500">
            Bitte warten Sie. Falls diese Seite nicht reagiert,{" "}
            <Link href="/forgot-password" className="text-brand-400 hover:text-brand-300">
              beantragen Sie einen neuen Link
            </Link>
            .
          </p>
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
          <h1 className="text-2xl font-black text-white tracking-tight">Neues Passwort</h1>
          <p className="text-sm text-slate-500 mt-1">Bitte wählen Sie ein neues Passwort.</p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="rounded-2xl border border-white/[0.07] bg-dark-900/60 p-7 flex flex-col gap-4"
        >
          <div className="flex flex-col gap-1.5">
            <label className="flex items-center gap-2 text-xs font-semibold text-slate-400 uppercase tracking-widest">
              <Lock className="h-3.5 w-3.5" /> Neues Passwort
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
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="flex items-center gap-2 text-xs font-semibold text-slate-400 uppercase tracking-widest">
              <Lock className="h-3.5 w-3.5" /> Passwort bestätigen
            </label>
            <input
              type="password"
              required
              autoComplete="new-password"
              value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              placeholder="Passwort wiederholen"
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
            {loading ? "Wird gespeichert…" : "Passwort speichern"}
          </button>
        </form>
      </div>
    </main>
  );
}
