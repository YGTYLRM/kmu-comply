"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { useReport } from "@/hooks/useReport";
import { ExecutiveSummary } from "@/components/report/executive-summary";
import { ApplicabilityMatrix } from "@/components/report/applicability-matrix";
import { ScoreBreakdown } from "@/components/report/score-breakdown";
import { GapAnalysis } from "@/components/report/gap-analysis";
import { ActionPlan } from "@/components/report/action-plan";
import { DocumentNudge } from "@/components/report/document-nudge";
import { Button } from "@/components/ui/button";
import { Loader2, ArrowLeft, Download, AlertTriangle, Link2, Check, RefreshCw, TrendingUp, TrendingDown, Minus, Database, ChevronDown } from "lucide-react";
import { api } from "@/lib/api";
import type { ComplianceReport } from "@/lib/types";

export default function ReportPage() {
  const params       = useParams();
  const router       = useRouter();
  const searchParams = useSearchParams();
  const jobId        = params.id as string;
  const prevJobId    = searchParams.get("prev");
  const { report, loading, error, fetch: loadReport } = useReport(jobId);
  const [prevReport, setPrevReport] = useState<ComplianceReport | null>(null);
  const [headerOpacity, setHeaderOpacity] = useState(1);
  const [copied, setCopied] = useState(false);

  const copyLink = () => {
    navigator.clipboard.writeText(window.location.href).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  useEffect(() => { loadReport(); }, [loadReport]);
  useEffect(() => {
    if (prevJobId) {
      api.getReport(prevJobId).then(setPrevReport).catch(() => {});
    }
  }, [prevJobId]);

  useEffect(() => {
    const onScroll = () => {
      setHeaderOpacity(Math.max(0, 1 - window.scrollY / 220));
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center pt-24">
        <div className="flex flex-col items-center gap-4">
          <div className="h-12 w-12 rounded-2xl bg-brand-500/10 border border-brand-500/25 flex items-center justify-center shadow-glow-blue-sm">
            <Loader2 className="h-6 w-6 animate-spin text-brand-400" />
          </div>
          <p className="text-sm text-slate-500">Loading your report…</p>
        </div>
      </div>
    );
  }

  if (error || !report) {
    const isNotFound = error?.includes("404") || error?.includes("not found");
    const isOffline  = error?.toLowerCase().includes("fetch") || error?.toLowerCase().includes("network");
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-6 pt-24 px-6">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-red-500/10 border border-red-500/20">
          <AlertTriangle className="h-8 w-8 text-red-400" />
        </div>
        <div className="text-center max-w-sm">
          <h2 className="text-lg font-bold text-white mb-2">
            {isNotFound ? "Report not found" : isOffline ? "Cannot reach server" : "Something went wrong"}
          </h2>
          <p className="text-sm text-slate-500 leading-relaxed">
            {isNotFound
              ? "This report could not be found. The link may be invalid or the report was never completed."
              : isOffline
              ? "The backend server is not responding. Make sure it is running on port 8000 and refresh."
              : (error ?? "An unexpected error occurred.")}
          </p>
        </div>
        <div className="flex flex-col sm:flex-row gap-3">
          <Button variant="outline" onClick={() => loadReport()}>
            Try again
          </Button>
          <Button onClick={() => router.push("/analyze")}>
            New screening
          </Button>
        </div>
      </div>
    );
  }

  const score      = report.overall_score_percent;
  const scoreColor = score >= 75 ? "text-emerald-400" : score >= 50 ? "text-amber-400" : "text-red-400";
  const scoreBg    = score >= 75 ? "bg-emerald-500/10 border-emerald-500/25" : score >= 50 ? "bg-amber-500/10 border-amber-500/25" : "bg-red-500/10 border-red-500/25";

  return (
    <div className="bg-dark-950 min-h-screen pt-24">
      {/* Report header — geometric diagonal bottom, fades on scroll */}
      <div style={{ opacity: headerOpacity, transition: "opacity 0.1s linear" }}>
        <div
          className="bg-dark-900/85 backdrop-blur-sm"
          style={{ clipPath: "polygon(0 0, 100% 0, 100% calc(100% - 22px), 0 100%)" }}
        >
          <div className="mx-auto max-w-5xl px-4 sm:px-6 pt-6 pb-12">
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y:  0 }}
              transition={{ duration: 0.4 }}
              className="flex items-start justify-between gap-4 flex-wrap"
            >
              <div className="flex items-start gap-4">
                <div className={`flex h-14 w-14 flex-shrink-0 items-center justify-center rounded-2xl border ${scoreBg}`}>
                  <span className={`text-xl font-bold ${scoreColor}`}>{score}%</span>
                </div>
                <div>
                  <h1 className="text-xl font-bold text-white tracking-tight">{report.company_name}</h1>
                  <p className="text-sm text-slate-500 mt-0.5">
                    Preliminary Screening ·{" "}
                    {new Date(report.generated_at).toLocaleDateString("en-GB", {
                      day: "numeric", month: "short", year: "numeric",
                    })}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2 flex-wrap">
                <button
                  onClick={copyLink}
                  className="inline-flex items-center gap-1.5 rounded-xl border border-white/[0.10] bg-white/[0.04] px-4 py-2 text-sm font-medium text-slate-300 hover:bg-white/[0.08] hover:text-white transition-all duration-200"
                >
                  {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Link2 className="h-3.5 w-3.5" />}
                  {copied ? "Copied!" : "Copy link"}
                </button>
                <a
                  href={`/report/${jobId}/print`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 rounded-xl border border-white/[0.10] bg-white/[0.04] px-4 py-2 text-sm font-medium text-slate-300 hover:bg-white/[0.08] hover:text-white transition-all duration-200"
                >
                  <Download className="h-3.5 w-3.5" />
                  Download PDF
                </a>
                <Button variant="outline" size="sm" onClick={() => router.push(`/analyze?from=${jobId}`)}>
                  <RefreshCw className="h-3.5 w-3.5" />
                  Re-run
                </Button>
                <Button variant="outline" size="sm" onClick={() => router.push("/analyze")}>
                  <ArrowLeft className="h-3.5 w-3.5" />
                  New screening
                </Button>
              </div>
            </motion.div>
          </div>
        </div>
      </div>

      <main className="mx-auto max-w-5xl px-4 sm:px-6 py-8">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="flex flex-col gap-5"
        >
          {prevReport && <DeltaBanner current={report} prev={prevReport} prevJobId={prevJobId!} />}

          {/* Profile completeness warning — shown when < 70% of relevant fields were answered */}
          {report.profile_completeness && report.profile_completeness.score_percent < 70 && (
            <div className="rounded-xl border border-orange-500/30 bg-orange-500/[0.06] px-5 py-4 flex gap-3 items-start">
              <AlertTriangle className="h-4 w-4 text-orange-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-semibold text-orange-300 mb-1">
                  Report completeness: {report.profile_completeness.score_percent}%
                </p>
                <p className="text-xs text-slate-400 leading-relaxed">
                  {report.profile_completeness.unanswered_count} compliance-relevant{" "}
                  {report.profile_completeness.unanswered_count === 1 ? "field was" : "fields were"} not
                  provided. Some findings may be based on assumptions rather than confirmed data.{" "}
                  <button
                    onClick={() => router.push(`/analyze?from=${jobId}`)}
                    className="text-orange-400 hover:text-orange-300 underline underline-offset-2 transition-colors"
                  >
                    Re-run with more data
                  </button>{" "}
                  to improve accuracy.
                </p>
              </div>
            </div>
          )}

          <DocumentNudge report={report} />
          <ExecutiveSummary report={report} />
          <div className="grid lg:grid-cols-2 gap-5">
            <ApplicabilityMatrix report={report} />
            <ScoreBreakdown report={report} />
          </div>
          <GapAnalysis report={report} />
          <ActionPlan report={report} />

          {/* Legal database versions */}
          {report.knowledge_base_versions && Object.keys(report.knowledge_base_versions).length > 0 && (
            <KnowledgeBaseVersions versions={report.knowledge_base_versions} />
          )}

          {/* Legal disclaimer */}
          <div className="rounded-xl border border-amber-500/20 bg-amber-500/[0.05] px-5 py-4">
            <p className="text-xs text-amber-400/80 font-semibold uppercase tracking-widest mb-1">Preliminary screening only — not legal advice</p>
            <p className="text-xs text-slate-500 leading-relaxed">{report.disclaimer}</p>
          </div>
        </motion.div>
      </main>
    </div>
  );
}

const REG_DISPLAY: Record<string, string> = {
  gdpr_dsgvo: "GDPR / DSGVO", bdsg: "BDSG", nis2: "NIS2", eu_ai_act: "EU AI Act",
  hinschg: "HinSchG", workplace_law: "Employment & Workplace Law", agg: "AGG",
  milog: "MiLoG", lksg: "LkSG", enefg: "EnEfG / EDL-G", csrd: "CSRD",
};

function KnowledgeBaseVersions({ versions }: { versions: Record<string, { fetched_at: string; source_file_hash: string; source_url: string }> }) {
  const [open, setOpen] = useState(false);
  const entries = Object.entries(versions);

  return (
    <div className="rounded-xl border border-white/[0.07] bg-white/[0.02]">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between px-5 py-3.5 text-left"
      >
        <div className="flex items-center gap-2.5">
          <Database className="h-3.5 w-3.5 text-slate-500" />
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-widest">Legal database versions</span>
          <span className="text-xs text-slate-600">— which law version was used for this report</span>
        </div>
        <ChevronDown className={`h-3.5 w-3.5 text-slate-600 transition-transform duration-200 ${open ? "rotate-180" : ""}`} />
      </button>
      {open && (
        <div className="border-t border-white/[0.05] px-5 pb-4 pt-3">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-slate-600 uppercase tracking-wider">
                <th className="text-left pb-2 font-medium">Regulation</th>
                <th className="text-left pb-2 font-medium">Fetched at</th>
                <th className="text-left pb-2 font-medium">File hash</th>
                <th className="text-left pb-2 font-medium">Source</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.03]">
              {entries.map(([reg, meta]) => (
                <tr key={reg}>
                  <td className="py-1.5 pr-4 text-slate-300 font-medium">{REG_DISPLAY[reg] ?? reg}</td>
                  <td className="py-1.5 pr-4 text-slate-500 font-mono">
                    {meta.fetched_at !== "unknown" ? meta.fetched_at.split("T")[0] : "unknown"}
                  </td>
                  <td className="py-1.5 pr-4 text-slate-600 font-mono">{meta.source_file_hash.slice(0, 8)}</td>
                  <td className="py-1.5 text-slate-600">
                    {meta.source_url
                      ? <a href={meta.source_url} target="_blank" rel="noopener noreferrer" className="hover:text-brand-400 transition-colors underline underline-offset-2">official text</a>
                      : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-3 text-xs text-slate-600 leading-relaxed">
            This report was generated using the legal texts listed above. If a regulation has been amended since the date shown,
            re-run the screening to get an updated assessment.
          </p>
        </div>
      )}
    </div>
  );
}

function DeltaBanner({ current, prev, prevJobId }: { current: ComplianceReport; prev: ComplianceReport; prevJobId: string }) {
  const delta = current.overall_score_percent - prev.overall_score_percent;
  const absD  = Math.abs(delta).toFixed(1);

  const prevStatuses = Object.fromEntries(
    prev.gap_analysis.map((g) => [`${g.regulation}:${g.article_number}`, g.status])
  );
  let improved = 0, regressed = 0;
  for (const g of current.gap_analysis) {
    const key = `${g.regulation}:${g.article_number}`;
    const was = prevStatuses[key];
    if (!was) continue;
    const rank = (s: string) => s === "COMPLIANT" ? 2 : s === "PARTIALLY_COMPLIANT" ? 1 : 0;
    if (rank(g.status) > rank(was)) improved++;
    if (rank(g.status) < rank(was)) regressed++;
  }

  const deltaColor = delta > 0 ? "text-emerald-400" : delta < 0 ? "text-red-400" : "text-slate-400";
  const borderColor = delta > 0 ? "border-emerald-500/25 bg-emerald-500/[0.04]"
    : delta < 0 ? "border-red-500/25 bg-red-500/[0.04]"
    : "border-white/[0.07] bg-white/[0.02]";

  return (
    <div className={`rounded-xl border px-5 py-4 flex items-center justify-between gap-4 flex-wrap ${borderColor}`}>
      <div className="flex items-center gap-3">
        {delta > 0 ? <TrendingUp className="h-5 w-5 text-emerald-400 flex-shrink-0" />
          : delta < 0 ? <TrendingDown className="h-5 w-5 text-red-400 flex-shrink-0" />
          : <Minus className="h-5 w-5 text-slate-500 flex-shrink-0" />}
        <div>
          <p className="text-sm font-semibold text-white">
            {delta > 0 ? `+${absD}%` : delta < 0 ? `-${absD}%` : "No change"}{" "}
            <span className={`${deltaColor}`}>
              {delta > 0 ? "improvement" : delta < 0 ? "decline" : "in score"}
            </span>
            {" "}since previous screening
          </p>
          <p className="text-xs text-slate-500 mt-0.5">
            {improved > 0 && `${improved} gap${improved !== 1 ? "s" : ""} resolved`}
            {improved > 0 && regressed > 0 && " · "}
            {regressed > 0 && `${regressed} gap${regressed !== 1 ? "s" : ""} regressed`}
            {improved === 0 && regressed === 0 && "No gap status changes"}
          </p>
        </div>
      </div>
      <a href={`/report/${prevJobId}`} className="text-xs text-slate-500 hover:text-slate-300 transition-colors underline underline-offset-2 flex-shrink-0">
        View previous report
      </a>
    </div>
  );
}
