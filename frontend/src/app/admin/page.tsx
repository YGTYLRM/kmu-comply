"use client";

import { useState } from "react";
import { api, type AdminExpertReview, type AdminRegulationUpdate } from "@/lib/api";
import { ShieldCheck, RefreshCw, Loader2, AlertCircle, CheckCircle2, Clock, Eye, UserPlus, X } from "lucide-react";

const STATUS_COLORS: Record<string, string> = {
  pending: "text-amber-400 bg-amber-500/10 border-amber-500/20",
  in_review: "text-blue-400 bg-blue-500/10 border-blue-500/20",
  completed: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
};

export default function AdminPage() {
  const [adminKey, setAdminKey] = useState(() =>
    typeof window !== "undefined" ? (localStorage.getItem("admin_key") ?? "") : ""
  );
  const [keyInput, setKeyInput] = useState("");
  const [tab, setTab] = useState<"expert" | "regulations">("expert");

  const [expertReviews, setExpertReviews] = useState<AdminExpertReview[] | null>(null);
  const [regUpdates, setRegUpdates] = useState<AdminRegulationUpdate[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [assigningId, setAssigningId] = useState<string | null>(null);
  const [assignInput, setAssignInput] = useState("");

  const authenticate = () => {
    localStorage.setItem("admin_key", keyInput);
    setAdminKey(keyInput);
    loadTab(keyInput, tab);
  };

  const loadTab = async (key: string, t: typeof tab) => {
    setLoading(true);
    setError(null);
    try {
      if (t === "expert") {
        const data = await api.adminListExpertReviews(key);
        setExpertReviews(data.reviews);
      } else {
        const data = await api.adminListRegulationUpdates(key);
        setRegUpdates(data.updates);
      }
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setLoading(false);
    }
  };

  const switchTab = (t: typeof tab) => {
    setTab(t);
    if (adminKey) loadTab(adminKey, t);
  };

  const updateStatus = async (id: string, status: string) => {
    if (!adminKey) return;
    try {
      await api.adminUpdateExpertReviewStatus(adminKey, id, status);
      setExpertReviews(prev =>
        prev?.map(r => r.id === id ? { ...r, status, reviewed_at: new Date().toISOString() } : r) ?? null
      );
    } catch (e) {
      alert((e as Error).message);
    }
  };

  const confirmAssign = async (id: string) => {
    if (!adminKey || !assignInput.trim()) return;
    try {
      await api.adminAssignExpertReview(adminKey, id, assignInput.trim());
      setExpertReviews(prev =>
        prev?.map(r => r.id === id ? { ...r, assigned_to: assignInput.trim(), status: r.status === "pending" ? "in_review" : r.status } : r) ?? null
      );
      setAssigningId(null);
      setAssignInput("");
    } catch (e) {
      alert((e as Error).message);
    }
  };

  if (!adminKey) {
    return (
      <div className="min-h-screen bg-dark-950 flex items-center justify-center px-4 pt-24">
        <div className="w-full max-w-sm rounded-2xl border border-white/[0.07] bg-dark-900/80 p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-500/10 border border-brand-500/20">
              <ShieldCheck className="h-5 w-5 text-brand-400" />
            </div>
            <h1 className="text-lg font-bold text-white">Admin-Zugang</h1>
          </div>
          <input
            type="password"
            placeholder="Admin API Key"
            value={keyInput}
            onChange={e => setKeyInput(e.target.value)}
            onKeyDown={e => e.key === "Enter" && authenticate()}
            className="w-full rounded-xl border border-white/[0.10] bg-white/[0.04] px-4 py-3 text-sm text-white placeholder-slate-600 outline-none focus:border-brand-500/50 mb-3"
          />
          <button
            onClick={authenticate}
            className="w-full rounded-xl bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-brand-500 transition-colors"
          >
            Anmelden
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-dark-950 pt-24 pb-16 px-4 sm:px-6">
      <div className="mx-auto max-w-5xl">
        <div className="flex items-center justify-between mb-6">
          <div>
            <p className="text-xs font-bold uppercase tracking-widest text-brand-400 mb-1">Admin</p>
            <h1 className="text-2xl font-black text-white tracking-tight">Dashboard</h1>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => loadTab(adminKey, tab)}
              className="inline-flex items-center gap-1.5 rounded-xl border border-white/10 bg-white/5 px-3.5 py-2 text-sm text-slate-400 hover:text-white transition-all"
            >
              <RefreshCw className="h-3.5 w-3.5" /> Aktualisieren
            </button>
            <button
              onClick={() => { localStorage.removeItem("admin_key"); setAdminKey(""); }}
              className="rounded-xl border border-white/10 bg-white/5 px-3.5 py-2 text-sm text-slate-400 hover:text-white transition-all"
            >
              Abmelden
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mb-5 rounded-xl border border-white/[0.07] bg-dark-900/60 p-1 w-fit">
          {(["expert", "regulations"] as const).map(t => (
            <button
              key={t}
              onClick={() => switchTab(t)}
              className={`rounded-lg px-4 py-2 text-sm font-medium transition-colors ${
                tab === t ? "bg-brand-600 text-white" : "text-slate-400 hover:text-white"
              }`}
            >
              {t === "expert" ? "Expertenbewertungen" : "Regelwerk-Updates"}
            </button>
          ))}
        </div>

        {loading && (
          <div className="flex items-center justify-center py-24">
            <Loader2 className="h-8 w-8 animate-spin text-brand-500" />
          </div>
        )}

        {error && (
          <div className="flex items-center gap-3 rounded-xl border border-red-500/25 bg-red-500/10 px-5 py-4 text-sm text-red-400">
            <AlertCircle className="h-4 w-4 flex-shrink-0" /> {error}
          </div>
        )}

        {/* Expert reviews */}
        {!loading && tab === "expert" && expertReviews && (
          <div className="flex flex-col gap-3">
            {expertReviews.length === 0 && (
              <p className="text-sm text-slate-500 text-center py-12">Keine Expertenbewertungsanfragen.</p>
            )}
            {expertReviews.map(r => (
              <div key={r.id} className="rounded-2xl border border-white/[0.07] bg-dark-900/60 p-5">
                <div className="flex items-start justify-between gap-3 flex-wrap mb-3">
                  <div>
                    <h3 className="font-bold text-white text-sm">{r.company_name}</h3>
                    <p className="text-xs text-slate-500 mt-0.5">{r.user_email ?? r.user_id}</p>
                  </div>
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${STATUS_COLORS[r.status] ?? "text-slate-400 bg-white/5 border-white/10"}`}>
                      {r.status}
                    </span>
                    <span className="text-xs text-slate-600">
                      {r.created_at ? new Date(r.created_at).toLocaleDateString("de-DE", { day: "numeric", month: "short", year: "numeric" }) : "—"}
                    </span>
                  </div>
                </div>

                {r.message && (
                  <p className="text-xs text-slate-400 bg-white/[0.03] rounded-lg px-3 py-2 mb-3 leading-relaxed">{r.message}</p>
                )}

                {r.focus_items && r.focus_items.length > 0 && (
                  <div className="flex flex-wrap gap-1.5 mb-3">
                    {r.focus_items.map((f, i) => (
                      <span key={i} className="text-xs rounded-full border border-white/10 bg-white/5 px-2.5 py-0.5 text-slate-400 font-mono">
                        {f.regulation} {f.article_number}
                      </span>
                    ))}
                  </div>
                )}

                {/* Assigned reviewer badge */}
                {r.assigned_to && (
                  <p className="text-xs text-slate-500 mb-3">
                    Zugewiesen an: <span className="text-slate-300 font-medium">{r.assigned_to}</span>
                  </p>
                )}

                {/* Inline assignment form */}
                {assigningId === r.id && (
                  <div className="flex gap-2 mb-3">
                    <input
                      type="text"
                      value={assignInput}
                      onChange={e => setAssignInput(e.target.value)}
                      placeholder="E-Mail oder Name des Prüfers"
                      onKeyDown={e => e.key === "Enter" && confirmAssign(r.id)}
                      className="flex-1 rounded-lg border border-white/10 bg-white/[0.04] px-3 py-1.5 text-xs text-white placeholder-slate-600 outline-none focus:border-brand-500/50"
                    />
                    <button
                      onClick={() => confirmAssign(r.id)}
                      className="rounded-lg bg-brand-600 px-3 py-1.5 text-xs text-white hover:bg-brand-500 transition-colors"
                    >Zuweisen</button>
                    <button
                      onClick={() => { setAssigningId(null); setAssignInput(""); }}
                      className="rounded-lg border border-white/10 bg-white/5 px-2 py-1.5 text-xs text-slate-400 hover:text-white transition-colors"
                    ><X className="h-3 w-3" /></button>
                  </div>
                )}

                <div className="flex items-center gap-2 flex-wrap">
                  <a
                    href={`/report/${r.job_id}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 bg-white/5 px-3 py-1.5 text-xs text-slate-400 hover:text-white transition-colors"
                  >
                    <Eye className="h-3 w-3" /> Bericht ansehen
                  </a>
                  {r.status !== "completed" && (
                    <button
                      onClick={() => { setAssigningId(r.id); setAssignInput(r.assigned_to ?? ""); }}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-brand-500/20 bg-brand-500/10 px-3 py-1.5 text-xs text-brand-400 hover:bg-brand-500/20 transition-colors"
                    >
                      <UserPlus className="h-3 w-3" /> {r.assigned_to ? "Neu zuweisen" : "Zuweisen"}
                    </button>
                  )}
                  {r.status === "pending" && (
                    <button
                      onClick={() => updateStatus(r.id, "in_review")}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-blue-500/20 bg-blue-500/10 px-3 py-1.5 text-xs text-blue-400 hover:bg-blue-500/20 transition-colors"
                    >
                      <Clock className="h-3 w-3" /> In Bearbeitung
                    </button>
                  )}
                  {r.status !== "completed" && (
                    <button
                      onClick={() => updateStatus(r.id, "completed")}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-emerald-500/20 bg-emerald-500/10 px-3 py-1.5 text-xs text-emerald-400 hover:bg-emerald-500/20 transition-colors"
                    >
                      <CheckCircle2 className="h-3 w-3" /> Abgeschlossen
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Regulation updates */}
        {!loading && tab === "regulations" && regUpdates && (
          <div className="flex flex-col gap-3">
            {regUpdates.length === 0 && (
              <p className="text-sm text-slate-500 text-center py-12">Keine ausstehenden Regelwerk-Updates.</p>
            )}
            {regUpdates.map(u => (
              <div key={u.id} className="rounded-2xl border border-white/[0.07] bg-dark-900/60 p-5">
                <div className="flex items-start justify-between gap-3 flex-wrap">
                  <div>
                    <h3 className="font-bold text-white text-sm uppercase tracking-wide">{u.regulation}</h3>
                    <p className="text-xs text-slate-500 mt-0.5 font-mono">{u.new_hash} {u.previous_hash ? `← ${u.previous_hash}` : "(neu)"}</p>
                  </div>
                  <span className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${STATUS_COLORS[u.status] ?? "text-slate-400 bg-white/5 border-white/10"}`}>
                    {u.status}
                  </span>
                </div>
                {u.change_summary && (
                  <p className="text-xs text-slate-400 bg-white/[0.03] rounded-lg px-3 py-2 mt-3 leading-relaxed">{u.change_summary}</p>
                )}
                {u.source_url && (
                  <a href={u.source_url} target="_blank" rel="noopener noreferrer" className="mt-2 inline-block text-xs text-brand-400 hover:text-brand-300 transition-colors underline underline-offset-2">
                    Quelle ansehen
                  </a>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
