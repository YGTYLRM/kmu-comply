"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn, REGULATION_LABEL } from "@/lib/utils";
import type { ComplianceReport, Priority } from "@/lib/types";
import { Clock, CalendarDays, CheckCircle2, Circle } from "lucide-react";
import { authFetch } from "@/lib/api";

interface Props { report: ComplianceReport }

const PRIORITY_ORDER: Record<Priority, number> = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 };

const PRIORITY_STYLE: Record<Priority, { bar: string; badge: string; label: string }> = {
  CRITICAL: { bar: "bg-red-500",    badge: "bg-red-500/15 text-red-400 border-red-500/30",         label: "Critical" },
  HIGH:     { bar: "bg-orange-500", badge: "bg-orange-500/15 text-orange-400 border-orange-500/30", label: "High" },
  MEDIUM:   { bar: "bg-amber-400",  badge: "bg-amber-500/15 text-amber-400 border-amber-500/30",    label: "Medium" },
  LOW:      { bar: "bg-emerald-500",badge: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30", label: "Low" },
};

function itemKey(regulation: string, article: string) {
  return `${regulation}::${article}`;
}

export function ActionPlan({ report }: Props) {
  const params = useParams();
  const jobId  = (params?.id as string) ?? "";

  const sorted = [...report.action_plan].sort(
    (a, b) => PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority]
  );

  const [done, setDone] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);

  // Load completion state from DB on mount
  useEffect(() => {
    if (!jobId) return;
    authFetch(`/api/report/${jobId}/completions`)
      .then((res) => res.json())
      .then((data) => {
        const keys = new Set<string>(
          (data.completions ?? []).map((c: { regulation: string; article_number: string }) =>
            itemKey(c.regulation, c.article_number)
          )
        );
        setDone(keys);
      })
      .catch(() => {
        // Fallback to localStorage if API fails (e.g. unauthenticated)
        const fallback = new Set<string>();
        sorted.forEach((item) => {
          const legacyKey = `complio_done_${jobId}_${item.regulation}_${item.article_number}`;
          if (localStorage.getItem(legacyKey) === "done") {
            fallback.add(itemKey(item.regulation, item.article_number));
          }
        });
        setDone(fallback);
      })
      .finally(() => setLoading(false));
  }, [jobId]); // eslint-disable-line react-hooks/exhaustive-deps

  const toggle = useCallback(async (regulation: string, article: string) => {
    const key = itemKey(regulation, article);
    const isDone = done.has(key);

    // Optimistic update
    setDone((prev) => {
      const next = new Set(prev);
      isDone ? next.delete(key) : next.add(key);
      return next;
    });

    try {
      if (isDone) {
        await authFetch(`/api/report/${jobId}/completions`, {
          method: "DELETE",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ regulation, article_number: article }),
        });
      } else {
        await authFetch(`/api/report/${jobId}/completions`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ regulation, article_number: article }),
        });
      }
    } catch {
      // Revert on failure
      setDone((prev) => {
        const next = new Set(prev);
        isDone ? next.add(key) : next.delete(key);
        return next;
      });
    }
  }, [done, jobId]);

  const doneCount = sorted.filter((item) =>
    done.has(itemKey(item.regulation, item.article_number))
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
            const style  = PRIORITY_STYLE[item.priority];
            const key    = itemKey(item.regulation, item.article_number);
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
                      onClick={() => toggle(item.regulation, item.article_number)}
                      disabled={loading}
                      title={isDone ? "Mark as not done" : "Mark as done"}
                      className="flex-shrink-0 mt-0.5 text-slate-600 hover:text-emerald-400 transition-colors disabled:opacity-40"
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
