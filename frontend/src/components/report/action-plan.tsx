"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn, REGULATION_LABEL } from "@/lib/utils";
import type { ComplianceReport, Priority } from "@/lib/types";
import { Clock, CalendarDays, CheckCircle2, Circle } from "lucide-react";

interface Props { report: ComplianceReport }

const PRIORITY_ORDER: Record<Priority, number> = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 };

const PRIORITY_STYLE: Record<Priority, { bar: string; badge: string; label: string }> = {
  CRITICAL: { bar: "bg-red-500",    badge: "bg-red-500/15 text-red-400 border-red-500/30",       label: "Critical" },
  HIGH:     { bar: "bg-orange-500", badge: "bg-orange-500/15 text-orange-400 border-orange-500/30", label: "High" },
  MEDIUM:   { bar: "bg-amber-400",  badge: "bg-amber-500/15 text-amber-400 border-amber-500/30",   label: "Medium" },
  LOW:      { bar: "bg-emerald-500",badge: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30", label: "Low" },
};

function taskKey(jobId: string, regulation: string, article: string) {
  return `complio_done_${jobId}_${regulation}_${article}`;
}

export function ActionPlan({ report }: Props) {
  const params = useParams();
  const jobId  = (params?.id as string) ?? "";

  const sorted = [...report.action_plan].sort(
    (a, b) => PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority]
  );

  const [done, setDone] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (!jobId) return;
    const initialDone = new Set<string>();
    sorted.forEach((item) => {
      const k = taskKey(jobId, item.regulation, item.article_number);
      if (localStorage.getItem(k) === "done") initialDone.add(k);
    });
    setDone(initialDone);
  }, [jobId]); // eslint-disable-line react-hooks/exhaustive-deps

  const toggle = (key: string) => {
    setDone((prev) => {
      const next = new Set(prev);
      if (next.has(key)) {
        next.delete(key);
        localStorage.removeItem(key);
      } else {
        next.add(key);
        localStorage.setItem(key, "done");
      }
      return next;
    });
  };

  const doneCount = sorted.filter((item) =>
    done.has(taskKey(jobId, item.regulation, item.article_number))
  ).length;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Action Plan</CardTitle>
          <div className="flex items-center gap-2">
            {doneCount > 0 && (
              <span className="text-xs text-emerald-400 font-medium">
                {doneCount}/{sorted.length} done
              </span>
            )}
            <span className="text-xs text-slate-600">{sorted.length} items</span>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="divide-y divide-white/[0.04]">
          {sorted.map((item, i) => {
            const style = PRIORITY_STYLE[item.priority];
            const key   = taskKey(jobId, item.regulation, item.article_number);
            const isDone = done.has(key);
            return (
              <div key={i} className={cn("flex gap-0 transition-opacity duration-200", isDone && "opacity-40")}>
                <div className={cn("w-1 flex-shrink-0", style.bar)} />
                <div className="flex-1 px-5 py-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-2 flex-wrap mb-2">
                      <span className={cn("rounded-full border px-2.5 py-0.5 text-[10px] font-bold", style.badge)}>
                        {style.label}
                      </span>
                      <span className="text-xs text-slate-600">
                        {REGULATION_LABEL[item.regulation] ?? item.regulation} · {item.article_number}
                      </span>
                    </div>
                    <button
                      onClick={() => toggle(key)}
                      title={isDone ? "Mark as not done" : "Mark as done"}
                      className="flex-shrink-0 mt-0.5 text-slate-600 hover:text-emerald-400 transition-colors"
                    >
                      {isDone
                        ? <CheckCircle2 className="h-4 w-4 text-emerald-400" />
                        : <Circle className="h-4 w-4" />}
                    </button>
                  </div>
                  <p className={cn("text-sm leading-relaxed", isDone ? "line-through text-slate-500" : "text-slate-300")}>
                    {item.action}
                  </p>
                  <div className="mt-2.5 flex flex-wrap gap-4">
                    <span className="flex items-center gap-1.5 text-xs text-slate-600">
                      <Clock className="h-3 w-3 text-slate-600" />
                      {item.estimated_effort}
                    </span>
                    {item.deadline && (
                      <span className="flex items-center gap-1.5 text-xs text-slate-600">
                        <CalendarDays className="h-3 w-3 text-slate-600" />
                        By {item.deadline}
                      </span>
                    )}
                  </div>
                  {item.dependencies.length > 0 && (
                    <p className="mt-1.5 text-xs text-slate-600">
                      Depends on: {item.dependencies.join(", ")}
                    </p>
                  )}
                </div>
              </div>
            );
          })}
          {sorted.length === 0 && (
            <div className="px-6 py-8 text-center text-sm text-slate-600">No actions required</div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
