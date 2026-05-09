"use client";

import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { useReport } from "@/hooks/useReport";
import { ExecutiveSummary } from "@/components/report/executive-summary";
import { ApplicabilityMatrix } from "@/components/report/applicability-matrix";
import { ScoreBreakdown } from "@/components/report/score-breakdown";
import { GapAnalysis } from "@/components/report/gap-analysis";
import { ActionPlan } from "@/components/report/action-plan";
import { Button } from "@/components/ui/button";
import { Loader2, ArrowLeft, Download } from "lucide-react";
import { useState } from "react";

export default function ReportPage() {
  const params  = useParams();
  const router  = useRouter();
  const jobId   = params.id as string;
  const { report, loading, error, fetch: loadReport } = useReport(jobId);
  const [downloading, setDownloading] = useState(false);

  const downloadPdf = async () => {
    setDownloading(true);
    try {
      const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
      const res  = await window.fetch(`${BASE}/api/report/${jobId}/pdf`, { method: "POST" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob     = await res.blob();
      const url      = URL.createObjectURL(blob);
      const a        = document.createElement("a");
      a.href         = url;
      a.download     = `complio-screening-${jobId.slice(0, 8)}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error("PDF download failed:", e);
    } finally {
      setDownloading(false);
    }
  };

  useEffect(() => { loadReport(); }, [loadReport]);

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
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
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4">
        <p className="text-sm text-red-400">{error ?? "Report not found"}</p>
        <Button variant="outline" onClick={() => router.push("/analyze")}>
          New analysis
        </Button>
      </div>
    );
  }

  const score      = report.overall_score_percent;
  const scoreColor = score >= 75 ? "text-emerald-400" : score >= 50 ? "text-amber-400" : "text-red-400";
  const scoreBg    = score >= 75 ? "bg-emerald-500/10 border-emerald-500/25" : score >= 50 ? "bg-amber-500/10 border-amber-500/25" : "bg-red-500/10 border-red-500/25";

  return (
    <div className="bg-dark-950 min-h-screen">
      {/* Report header */}
      <div className="border-b border-white/[0.06] bg-dark-900/60">
        <div className="mx-auto max-w-5xl px-6 py-6">
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
            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={downloadPdf}
                disabled={downloading}
              >
                {downloading
                  ? <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  : <Download className="h-3.5 w-3.5" />
                }
                {downloading ? "Generating..." : "Download PDF"}
              </Button>
              <Button variant="outline" size="sm" onClick={() => router.push("/analyze")}>
                <ArrowLeft className="h-3.5 w-3.5" />
                New screening
              </Button>
            </div>
          </motion.div>
        </div>
      </div>

      <main className="mx-auto max-w-5xl px-6 py-8">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="flex flex-col gap-5"
        >
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
