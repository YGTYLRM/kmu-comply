"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { useReport } from "@/hooks/useReport";
import { ExecutiveSummary } from "@/components/report/executive-summary";
import { ApplicabilityMatrix } from "@/components/report/applicability-matrix";
import { ScoreBreakdown } from "@/components/report/score-breakdown";
import { GapAnalysis } from "@/components/report/gap-analysis";
import { ActionPlan } from "@/components/report/action-plan";
import { DocumentNudge } from "@/components/report/document-nudge";
import { Button } from "@/components/ui/button";
import { Loader2, ArrowLeft, Download, AlertTriangle } from "lucide-react";

export default function ReportPage() {
  const params  = useParams();
  const router  = useRouter();
  const jobId   = params.id as string;
  const { report, loading, error, fetch: loadReport } = useReport(jobId);
  const [headerOpacity, setHeaderOpacity] = useState(1);

  useEffect(() => { loadReport(); }, [loadReport]);

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
              ? "This report may have expired or the link is invalid. Reports are available for 1 hour after generation."
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
                <a
                  href={`/report/${jobId}/print`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 rounded-xl border border-white/[0.10] bg-white/[0.04] px-4 py-2 text-sm font-medium text-slate-300 hover:bg-white/[0.08] hover:text-white transition-all duration-200"
                >
                  <Download className="h-3.5 w-3.5" />
                  Download PDF
                </a>
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
          <DocumentNudge report={report} />
          <ExecutiveSummary report={report} />
          <div className="grid lg:grid-cols-2 gap-5">
            <ApplicabilityMatrix report={report} />
            <ScoreBreakdown report={report} />
          </div>
          <GapAnalysis report={report} />
          <ActionPlan report={report} />
        </motion.div>
      </main>
    </div>
  );
}
