"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { api, type CompanySummary } from "@/lib/api";
import { Building2, ChevronRight, Plus, Clock, BarChart3, AlertCircle, Loader2 } from "lucide-react";

function ScoreRing({ score }: { score: number | null }) {
  if (score === null) return (
    <div className="flex h-16 w-16 items-center justify-center rounded-full border-2 border-white/10 text-xs text-slate-600">
      N/A
    </div>
  );
  const color = score >= 75 ? "#10b981" : score >= 50 ? "#f59e0b" : "#ef4444";
  const r = 28, circ = 2 * Math.PI * r;
  const dash = (score / 100) * circ;
  return (
    <div className="relative flex h-16 w-16 items-center justify-center">
      <svg width="64" height="64" className="-rotate-90">
        <circle cx="32" cy="32" r={r} fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth="5" />
        <circle cx="32" cy="32" r={r} fill="none" stroke={color} strokeWidth="5"
          strokeDasharray={`${dash} ${circ}`} strokeLinecap="round" />
      </svg>
      <span className="absolute text-sm font-bold" style={{ color }}>{score.toFixed(0)}%</span>
    </div>
  );
}

function triggerLabel(triggered_by: string) {
  if (triggered_by === "reg_change") return "Regulation update";
  if (triggered_by === "scheduled")  return "Monthly check";
  return "Manual";
}

export default function DashboardPage() {
  const router = useRouter();
  const [companies, setCompanies] = useState<CompanySummary[]>([]);
  const [loading, setLoading]     = useState(true);
  const [error, setError]         = useState<string | null>(null);

  useEffect(() => {
    api.listCompanies()
      .then(d => setCompanies(d.companies))
      .catch(() => setError("Failed to load companies."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <main className="bg-dark-950 min-h-screen pt-28 pb-16 px-4 sm:px-6">
      <div className="mx-auto max-w-5xl">

        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <p className="text-xs font-bold uppercase tracking-widest text-brand-400 mb-1">Compliance Monitor</p>
            <h1 className="text-2xl font-black text-white tracking-tight">Your companies</h1>
          </div>
          <Link
            href="/analyze"
            className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-500 transition-all shadow-glow-blue-sm hover:shadow-glow-blue"
          >
            <Plus className="h-4 w-4" /> New screening
          </Link>
        </div>

        {/* States */}
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

        {!loading && !error && companies.length === 0 && (
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            className="flex flex-col items-center justify-center py-24 text-center gap-4"
          >
            <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-brand-500/10 border border-brand-500/20">
              <BarChart3 className="h-7 w-7 text-brand-400" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-white mb-1">No companies yet</h2>
              <p className="text-sm text-slate-500 max-w-xs">
                Run your first screening to enrol a company in continuous compliance monitoring.
              </p>
            </div>
            <Link
              href="/analyze"
              className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-6 py-3 text-sm font-semibold text-white hover:bg-brand-500 transition-all"
            >
              <Plus className="h-4 w-4" /> Start a screening
            </Link>
          </motion.div>
        )}

        {/* Company grid */}
        {!loading && companies.length > 0 && (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {companies.map((c, i) => (
              <motion.div
                key={c.id}
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
              >
                <Link
                  href={`/dashboard/${c.id}`}
                  className="group flex flex-col gap-4 rounded-2xl border border-white/[0.07] bg-dark-900/60 p-5 hover:border-brand-500/30 hover:bg-dark-900/80 transition-all duration-200"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl bg-brand-500/10 border border-brand-500/20">
                      <Building2 className="h-5 w-5 text-brand-400" />
                    </div>
                    <ScoreRing score={c.latest_score ?? null} />
                  </div>

                  <div>
                    <h3 className="font-bold text-white text-sm truncate group-hover:text-brand-300 transition-colors">
                      {c.name}
                    </h3>
                    <p className="text-xs text-slate-500 mt-0.5">
                      {[c.industry, c.employee_count ? `${c.employee_count} employees` : null]
                        .filter(Boolean).join(" · ")}
                    </p>
                  </div>

                  <div className="flex items-center justify-between text-xs text-slate-600">
                    <span className="flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      {c.last_report_at
                        ? new Date(c.last_report_at).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })
                        : "Never assessed"}
                    </span>
                    <span className="flex items-center gap-0.5 text-brand-500 group-hover:text-brand-400">
                      {c.report_count} report{c.report_count !== 1 ? "s" : ""}
                      <ChevronRight className="h-3 w-3" />
                    </span>
                  </div>
                </Link>
              </motion.div>
            ))}
          </div>
        )}
      </div>
    </main>
  );
}
