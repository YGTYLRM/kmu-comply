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
import { Loader2 } from "lucide-react";

export default function ReportPage() {
  const params = useParams();
  const router = useRouter();
  const jobId = params.id as string;
  const { report, loading, error, fetch } = useReport(jobId);

  useEffect(() => {
    fetch();
  }, [fetch]);

  if (loading) {
    return (
      <main className="flex min-h-[60vh] items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-brand-600" />
      </main>
    );
  }

  if (error || !report) {
    return (
      <main className="flex min-h-[60vh] flex-col items-center justify-center gap-4">
        <p className="text-sm text-red-600">{error ?? "Report not found"}</p>
        <Button variant="outline" onClick={() => router.push("/analyze")}>
          New analysis
        </Button>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-4xl px-6 py-10">
      <div className="mb-6 flex items-start justify-between gap-4 flex-wrap">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{report.company_name}</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            Generated {new Date(report.generated_at).toLocaleDateString("de-DE", {
              day: "2-digit", month: "long", year: "numeric",
            })}
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={() => router.push("/analyze")}>
          New analysis
        </Button>
      </div>

      <div className="flex flex-col gap-6">
        <ExecutiveSummary report={report} />
        <ApplicabilityMatrix report={report} />
        <ScoreBreakdown report={report} />
        <GapAnalysis report={report} />
        <ActionPlan report={report} />
      </div>
    </main>
  );
}
