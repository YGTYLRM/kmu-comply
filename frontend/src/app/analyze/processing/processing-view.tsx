"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { api } from "@/lib/api";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";
import type { StepProgress, AnalysisStep } from "@/lib/types";
import { CheckCircle2, Circle, Loader2, XCircle } from "lucide-react";

const STEP_LABELS: Record<AnalysisStep, string> = {
  profile_validation:          "Validating profile",
  applicability_determination: "Determining applicable regulations",
  article_retrieval:           "Retrieving regulation articles",
  gap_analysis:                "Analysing compliance gaps",
  action_plan:                 "Building action plan",
  report_assembly:             "Assembling report",
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
  const router       = useRouter();
  const searchParams = useSearchParams();
  const jobId = searchParams.get("jobId") ?? sessionStorage.getItem("kmu_job_id") ?? null;

  const [steps, setSteps] = useState<StepProgress[]>([]);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (!jobId) { router.replace("/analyze"); return; }

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
  const progressPct    = Math.round((completedCount / STEP_ORDER.length) * 100);
  const runningStep    = STEP_ORDER.find((k) => steps.find((s) => s.step === k)?.status === "running");

  return (
    <div className="min-h-screen bg-dark-950 pt-24 flex items-center justify-center px-6 py-16">
      {/* Background orb */}
      <div className="pointer-events-none fixed inset-0 flex items-center justify-center overflow-hidden">
        <div className="h-[500px] w-[500px] rounded-full bg-brand-600/10 blur-[120px]" />
      </div>

      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0  }}
        transition={{ duration: 0.5, ease: [0.21, 0.47, 0.32, 0.98] }}
        className="relative w-full max-w-md flex flex-col items-center gap-8"
      >
        {/* Header */}
        <div className="text-center">
          <div className={cn(
            "inline-flex h-14 w-14 items-center justify-center rounded-2xl mb-4",
            error
              ? "bg-red-500/10 border border-red-500/25"
              : "bg-brand-500/10 border border-brand-500/25 shadow-glow-blue-sm"
          )}>
            {error
              ? <XCircle className="h-7 w-7 text-red-400" />
              : <Loader2 className="h-7 w-7 text-brand-400 animate-spin" />
            }
          </div>
          <h1 className="text-xl font-bold text-white">
            {error ? "Something went wrong" : "Running your compliance screening"}
          </h1>
          <AnimatePresence mode="wait">
            <motion.p
              key={runningStep ?? "idle"}
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{    opacity: 0, y: -4 }}
              transition={{ duration: 0.25 }}
              className="text-sm text-slate-500 mt-1"
            >
              {runningStep ? STEP_LABELS[runningStep] : "This usually takes 1 to 2 minutes"}
            </motion.p>
          </AnimatePresence>
        </div>

        {/* Progress bar */}
        <div className="w-full">
          <div className="flex justify-between text-xs text-slate-600 mb-2">
            <span>Progress</span>
            <span>{progressPct}%</span>
          </div>
          <Progress value={progressPct} className="h-2" />
        </div>

        {/* Step list */}
        <div
          className="w-full rounded-2xl overflow-hidden border border-white/[0.07] shadow-card-dark"
          style={{ background: "rgba(10,22,40,0.8)" }}
        >
          {STEP_ORDER.map((stepKey, i) => {
            const stepData = steps.find((s) => s.step === stepKey);
            const status   = stepData?.status ?? "pending";
            return (
              <motion.div
                key={stepKey}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ delay: i * 0.06 }}
                className={cn(
                  "flex items-center gap-3 px-5 py-3.5",
                  i < STEP_ORDER.length - 1 && "border-b border-white/[0.05]",
                  status === "running" && "bg-brand-500/5"
                )}
              >
                <StepIcon status={status} />
                <div className="flex-1 min-w-0">
                  <p
                    className={cn(
                      "text-sm font-medium truncate transition-colors duration-300",
                      status === "completed" ? "text-slate-500" :
                      status === "running"   ? "text-brand-300" : "text-slate-600"
                    )}
                  >
                    {STEP_LABELS[stepKey]}
                  </p>
                </div>
                {stepData?.duration_seconds != null && (
                  <span className="text-xs text-slate-600 flex-shrink-0">
                    {stepData.duration_seconds.toFixed(1)}s
                  </span>
                )}
              </motion.div>
            );
          })}
        </div>

        {/* Error state */}
        {error && (
          <motion.div
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1   }}
            className="w-full rounded-2xl bg-red-500/8 border border-red-500/20 p-6 flex flex-col items-center gap-4 text-center"
          >
            <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-red-500/10 border border-red-500/20">
              <XCircle className="h-6 w-6 text-red-400" />
            </div>
            <div>
              <p className="text-sm font-semibold text-red-300 mb-1">Analysis failed</p>
              <p className="text-xs text-red-400/70 leading-relaxed">{error}</p>
              {error.toLowerCase().includes("connection") || error.toLowerCase().includes("fetch") ? (
                <p className="text-xs text-slate-600 mt-2">Make sure the backend server is running on port 8000.</p>
              ) : null}
            </div>
            <button
              onClick={() => router.push("/analyze")}
              className="rounded-xl bg-red-500/15 border border-red-500/25 px-5 py-2.5 text-sm font-semibold text-red-300 hover:bg-red-500/25 transition-colors"
            >
              Start a new screening
            </button>
          </motion.div>
        )}
      </motion.div>
    </div>
  );
}

function StepIcon({ status }: { status: string }) {
  if (status === "completed")
    return <CheckCircle2 className="h-5 w-5 text-emerald-500 flex-shrink-0" />;
  if (status === "running")
    return <Loader2 className="h-5 w-5 text-brand-400 animate-spin flex-shrink-0" />;
  if (status === "failed")
    return <XCircle className="h-5 w-5 text-red-500 flex-shrink-0" />;
  return <Circle className="h-5 w-5 text-white/15 flex-shrink-0" />;
}
