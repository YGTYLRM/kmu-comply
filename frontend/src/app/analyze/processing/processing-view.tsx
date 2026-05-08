"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { api } from "@/lib/api";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";
import type { StepProgress, AnalysisStep } from "@/lib/types";
import { CheckCircle2, Circle, Loader2, XCircle } from "lucide-react";

const STEP_LABELS: Record<AnalysisStep, string> = {
  profile_validation: "Validating profile",
  applicability_determination: "Determining applicable regulations",
  article_retrieval: "Retrieving regulation articles",
  gap_analysis: "Analysing compliance gaps",
  action_plan: "Building action plan",
  report_assembly: "Assembling report",
};

const STEP_ORDER: AnalysisStep[] = [
  "profile_validation",
  "applicability_determination",
  "article_retrieval",
  "gap_analysis",
  "action_plan",
  "report_assembly",
];

export function ProcessingView() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const jobId = searchParams.get("jobId") ?? sessionStorage.getItem("kmu_job_id") ?? null;

  const [steps, setSteps] = useState<StepProgress[]>([]);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!jobId) {
      router.replace("/analyze");
      return;
    }

    const poll = async () => {
      try {
        const status = await api.getStatus(jobId);
        setSteps(status.steps);

        if (status.status === "completed") {
          clearInterval(intervalRef.current!);
          router.push(`/report/${jobId}`);
        } else if (status.status === "failed") {
          clearInterval(intervalRef.current!);
          setError(status.error ?? "Analysis failed. Please try again.");
        }
      } catch (e) {
        setError(e instanceof Error ? e.message : "Connection error");
        clearInterval(intervalRef.current!);
      }
    };

    poll();
    intervalRef.current = setInterval(poll, 2000);
    return () => clearInterval(intervalRef.current!);
  }, [jobId, router]);

  const completedCount = steps.filter((s) => s.status === "completed").length;
  const progressPct = Math.round((completedCount / STEP_ORDER.length) * 100);

  return (
    <main className="mx-auto max-w-xl px-6 py-20 flex flex-col items-center gap-8">
      <div className="text-center">
        <h1 className="text-2xl font-bold text-slate-900">Analysing your compliance</h1>
        <p className="text-slate-500 text-sm mt-1">This usually takes 1–2 minutes</p>
      </div>

      <div className="w-full">
        <Progress value={progressPct} className="h-3" />
        <p className="text-xs text-slate-400 text-right mt-1">{progressPct}%</p>
      </div>

      <div className="w-full flex flex-col gap-3">
        {STEP_ORDER.map((stepKey) => {
          const stepData = steps.find((s) => s.step === stepKey);
          const status = stepData?.status ?? "pending";
          return (
            <div key={stepKey} className="flex items-center gap-3">
              <StepIcon status={status} />
              <div className="flex-1">
                <p
                  className={cn(
                    "text-sm font-medium",
                    status === "completed" ? "text-slate-700" : status === "running" ? "text-brand-700" : "text-slate-400"
                  )}
                >
                  {STEP_LABELS[stepKey]}
                </p>
                {stepData?.message && (
                  <p className="text-xs text-slate-400 mt-0.5">{stepData.message}</p>
                )}
              </div>
              {stepData?.duration_seconds != null && (
                <span className="text-xs text-slate-400">{stepData.duration_seconds.toFixed(1)}s</span>
              )}
            </div>
          );
        })}
      </div>

      {error && (
        <div className="w-full rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
          {error}
          <button
            className="block mt-2 text-red-600 underline text-xs"
            onClick={() => router.push("/analyze")}
          >
            Go back and try again
          </button>
        </div>
      )}
    </main>
  );
}

function StepIcon({ status }: { status: string }) {
  if (status === "completed")
    return <CheckCircle2 className="h-5 w-5 text-green-500 flex-shrink-0" />;
  if (status === "running")
    return <Loader2 className="h-5 w-5 text-brand-600 animate-spin flex-shrink-0" />;
  if (status === "failed")
    return <XCircle className="h-5 w-5 text-red-500 flex-shrink-0" />;
  return <Circle className="h-5 w-5 text-slate-200 flex-shrink-0" />;
}
