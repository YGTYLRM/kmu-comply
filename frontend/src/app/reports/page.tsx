"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { api, type ReportSummary } from "@/lib/api";
import { Loader2, FileText, ArrowRight, AlertTriangle } from "lucide-react";

function ScoreBadge({ score }: { score: number }) {
  const color =
    score >= 75 ? "text-emerald-400 bg-emerald-500/10 border-emerald-500/25"
    : score >= 40 ? "text-amber-400 bg-amber-500/10 border-amber-500/25"
    : "text-red-400 bg-red-500/10 border-red-500/25";
  return (
    <span className={`inline-flex items-center rounded-lg border px-2.5 py-1 text-sm font-bold ${color}`}>
      {score}%
    </span>
  );
}

export default function ReportsPage() {
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState<string | null>(null);

  useEffect(() => {
    api.listReports()
      .then((r) => setReports(r.reports))
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load reports"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="min-h-screen bg-dark-950 pt-24">
      <div className="border-b border-white/[0.06] bg-dark-900/60 px-4 sm:px-6 py-6">
        <div className="mx-auto max-w-3xl">
          <h1 className="text-xl font-bold text-white tracking-tight">Recent Reports</h1>
          <p className="text-sm text-slate-500 mt-1">All screenings run on this server</p>
        </div>
      </div>

      <main className="mx-auto max-w-3xl px-4 sm:px-6 py-8">
        {loading && (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="h-6 w-6 animate-spin text-slate-600" />
          </div>
        )}

        {error && (
          <div className="flex items-center gap-3 rounded-xl border border-red-500/20 bg-red-500/[0.05] px-5 py-4 text-sm text-red-400">
            <AlertTriangle className="h-4 w-4 flex-shrink-0" />
            {error}
          </div>
        )}

        {!loading && !error && reports.length === 0 && (
          <div className="flex flex-col items-center gap-4 py-20 text-center">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-white/[0.07] bg-white/[0.03]">
              <FileText className="h-6 w-6 text-slate-600" />
            </div>
            <p className="text-slate-500 text-sm">No reports yet.</p>
            <Link
              href="/analyze"
              className="rounded-xl bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-500 transition-colors"
            >
              Run your first screening
            </Link>
          </div>
        )}

        {!loading && reports.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.3 }}
            className="flex flex-col gap-3"
          >
            {reports.map((r, i) => (
              <motion.div
                key={r.job_id}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.25, delay: i * 0.04 }}
              >
                <Link
                  href={`/report/${r.job_id}`}
                  className="group flex items-center justify-between gap-4 rounded-xl border border-white/[0.07] bg-white/[0.03] px-5 py-4 hover:bg-white/[0.06] hover:border-white/[0.12] transition-all duration-200"
                >
                  <div className="flex items-center gap-4 min-w-0">
                    <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg border border-white/[0.07] bg-white/[0.04]">
                      <FileText className="h-4 w-4 text-slate-500" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-sm font-semibold text-white truncate group-hover:text-brand-300 transition-colors">
                        {r.company_name}
                      </p>
                      <p className="text-xs text-slate-600 mt-0.5">
                        {new Date(r.generated_at).toLocaleDateString("en-GB", {
                          day: "numeric", month: "short", year: "numeric",
                        })}
                        {" · "}
                        {r.applicable_regulation_count} regulation{r.applicable_regulation_count !== 1 ? "s" : ""}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 flex-shrink-0">
                    <ScoreBadge score={r.overall_score_percent} />
                    <ArrowRight className="h-4 w-4 text-slate-700 group-hover:text-slate-400 transition-colors" />
                  </div>
                </Link>
              </motion.div>
            ))}
          </motion.div>
        )}
      </main>
    </div>
  );
}
