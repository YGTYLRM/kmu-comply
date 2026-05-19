"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Trash2, AlertTriangle, Shield, Database } from "lucide-react";
import { createClient } from "@/lib/supabase/client";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function apiDelete(path: string, token: string) {
  const res = await fetch(`${API}${path}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `HTTP ${res.status}`);
  }
  return res.json();
}

export default function AccountSettingsPage() {
  const router = useRouter();
  const [confirm, setConfirm]     = useState("");
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState<string | null>(null);
  const [success, setSuccess]     = useState<string | null>(null);

  const getToken = async () => {
    const supabase = createClient();
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) throw new Error("Not authenticated");
    return session.access_token;
  };

  const handleDeleteAccount = async () => {
    if (confirm !== "mein konto löschen") return;
    setLoading(true);
    setError(null);
    try {
      const token = await getToken();
      await apiDelete("/api/account", token);
      const supabase = createClient();
      await supabase.auth.signOut();
      router.push("/");
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Unbekannter Fehler");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen pt-32 pb-20">
      <div className="mx-auto max-w-2xl px-6">
        <h1 className="text-2xl font-bold text-white mb-2">Kontoeinstellungen</h1>
        <p className="text-sm text-slate-500 mb-10">Verwalten Sie Ihre Daten und Datenschutzeinstellungen.</p>

        {/* Data rights section */}
        <div className="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-500/10">
              <Shield className="h-4 w-4 text-blue-400" />
            </div>
            <div>
              <p className="text-sm font-semibold text-white">Ihre Datenschutzrechte (DSGVO)</p>
              <p className="text-xs text-slate-500">Art. 15–17 DSGVO</p>
            </div>
          </div>
          <div className="grid sm:grid-cols-2 gap-3 text-xs text-slate-400">
            {[
              { right: "Auskunft (Art. 15)", desc: "Welche Daten wir über Sie speichern" },
              { right: "Berichtigung (Art. 16)", desc: "Unrichtige Daten korrigieren lassen" },
              { right: "Löschung (Art. 17)", desc: "Ihre Daten vollständig löschen" },
              { right: "Datenübertragbarkeit (Art. 20)", desc: "Ihre Daten im maschinenlesbaren Format" },
            ].map(({ right, desc }) => (
              <div key={right} className="rounded-lg border border-white/[0.05] bg-white/[0.02] p-3">
                <p className="font-semibold text-slate-300 mb-0.5">{right}</p>
                <p className="text-slate-600">{desc}</p>
              </div>
            ))}
          </div>
          <p className="mt-4 text-xs text-slate-600">
            Für Auskunft oder Datenübertragbarkeit wenden Sie sich an:{" "}
            <a href="mailto:[CONTACT_EMAIL]" className="text-brand-400 hover:text-brand-300">[CONTACT_EMAIL]</a>
          </p>
        </div>

        {/* Data overview */}
        <div className="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-6 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-purple-500/10">
              <Database className="h-4 w-4 text-purple-400" />
            </div>
            <p className="text-sm font-semibold text-white">Gespeicherte Daten</p>
          </div>
          <div className="space-y-2 text-xs text-slate-400">
            {[
              { label: "Unternehmensprofile", retention: "Bis zur manuellen Löschung" },
              { label: "Compliance-Berichte", retention: "Bis zur manuellen Löschung" },
              { label: "Hochgeladene Dokumente", retention: "7 Tage, dann automatische Löschung" },
              { label: "Rechnungsdaten", retention: "10 Jahre (§ 147 AO)" },
              { label: "Server-Logs", retention: "30 Tage" },
            ].map(({ label, retention }) => (
              <div key={label} className="flex justify-between items-start gap-4 rounded-lg border border-white/[0.04] px-3 py-2">
                <span className="text-slate-300">{label}</span>
                <span className="text-slate-600 text-right flex-shrink-0">{retention}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Danger zone */}
        <div className="rounded-2xl border border-red-500/20 bg-red-500/5 p-6">
          <div className="flex items-center gap-3 mb-4">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-red-500/10">
              <Trash2 className="h-4 w-4 text-red-400" />
            </div>
            <div>
              <p className="text-sm font-semibold text-red-400">Konto löschen</p>
              <p className="text-xs text-slate-500">Nicht rückgängig zu machen</p>
            </div>
          </div>

          <div className="rounded-xl border border-amber-500/20 bg-amber-500/5 px-4 py-3 mb-5 flex items-start gap-2">
            <AlertTriangle className="h-4 w-4 text-amber-400 flex-shrink-0 mt-0.5" />
            <p className="text-xs text-amber-300/80">
              Hiermit werden Ihr Konto, alle Unternehmensprofile, alle Compliance-Berichte und alle Benachrichtigungen
              dauerhaft gelöscht. Rechnungsdaten werden gemäß gesetzlicher Aufbewahrungspflichten (§ 147 AO, 10 Jahre)
              aufbewahrt.
            </p>
          </div>

          {error && (
            <div className="rounded-xl border border-red-500/25 bg-red-500/10 px-4 py-2.5 mb-4 text-xs text-red-400">
              {error}
            </div>
          )}
          {success && (
            <div className="rounded-xl border border-emerald-500/25 bg-emerald-500/10 px-4 py-2.5 mb-4 text-xs text-emerald-400">
              {success}
            </div>
          )}

          <div className="space-y-3">
            <div>
              <label className="block text-xs text-slate-500 mb-1.5">
                Zum Bestätigen eingeben: <span className="font-mono text-slate-300">mein konto löschen</span>
              </label>
              <input
                type="text"
                value={confirm}
                onChange={(e) => setConfirm(e.target.value)}
                placeholder="mein konto löschen"
                className="w-full rounded-xl border border-white/10 bg-white/5 px-4 py-2.5 text-sm text-white placeholder-slate-600 focus:border-red-500/50 focus:outline-none focus:ring-1 focus:ring-red-500/30"
              />
            </div>
            <button
              type="button"
              disabled={confirm !== "mein konto löschen" || loading}
              onClick={handleDeleteAccount}
              className="w-full rounded-xl bg-red-600/80 py-2.5 text-sm font-semibold text-white hover:bg-red-600 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
            >
              {loading ? "Wird gelöscht…" : "Konto und alle Daten dauerhaft löschen"}
            </button>
          </div>
        </div>
      </div>
    </main>
  );
}
