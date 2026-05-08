"use client";

import { useEffect } from "react";
import { useParams, useRouter } from "next/navigation";
import { useReport } from "@/hooks/useReport";
import { ExecutiveSummary } from "@/components/report/executive-summary";
import { ApplicabilityMatrix } from "@/components/report/applicability-matrix";
import { ScoreBreakdown } from "@/components/report/score-breakdown";
import { GapAnalysis } from "@/components/report/gap-analysis";
import { ActionPlan } from "@/components/report/action-plan";
import { Button } from "@/components/ui/button";
import { Loader2, ArrowLeft } from "lucide-react";

export default function ReportPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = params.id as string;
  const { report, loading, error, fetch } = useReport(jobId);

  useEffect(() => { fetch(); }, [fetch]);

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-brand-600" />
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4">
        <p className="text-sm text-red-600">{error ?? "Report not found"}</p>
        <Button variant="outline" onClick={() => router.push("/analyze")}>
          New analysis
        </Button>
      </div>
    );
  }

  const score = report.overall_score_percent;
  const scoreColor = score >= 75 ? "text-emerald-600" : score >= 50 ? "text-amber-500" : "text-red-500";

  return (
    <div>
      {/* Report header */}
      <div className="border-b border-slate-200/70 bg-white">
        <div className="mx-auto max-w-5xl px-6 py-6">
          <div className="flex items-start justify-between gap-4 flex-wrap">
            <div className="flex items-start gap-4">
              <div className="flex h-14 w-14 flex-shrink-0 items-center justify-center rounded-2xl bg-brand-50">
                <span className={`text-xl font-bold ${scoreColor}`}>{score}%</span>
              </div>
              <div>
                <h1 className="text-xl font-bold text-slate-900 tracking-tight">{report.company_name}</h1>
                <p className="text-sm text-slate-500 mt-0.5">
                  Preliminary Screening ·{" "}
                  {new Date(report.generated_at).toLocaleDateString("en-GB", {
                    day: "numeric", month: "short", year: "numeric",
                  })}
                </p>
              </div>
            </div>
            <Button variant="outline" size="sm" onClick={() => router.push("/analyze")}>
              <ArrowLeft className="h-3.5 w-3.5" />
              New screening
            </Button>
          </div>
        </div>
      </div>

      <main className="mx-auto max-w-5xl px-6 py-8">
        <div className="flex flex-col gap-5">
          <ExecutiveSummary report={report} />
          <div className="grid lg:grid-cols-2 gap-5">
            <ApplicabilityMatrix report={report} />
            <ScoreBreakdown report={report} />
          </div>
          <GapAnalysis report={report} />
          <ActionPlan report={report} />
        </div>
      </main>
    </div>
  );
}
