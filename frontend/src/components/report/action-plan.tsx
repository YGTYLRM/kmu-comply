"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn, REGULATION_LABEL } from "@/lib/utils";
import type { ComplianceReport, Priority } from "@/lib/types";
import { Clock, CalendarDays, CheckCircle2, Circle, Loader2, ChevronDown, FileText, StickyNote, RotateCcw, PlayCircle } from "lucide-react";
import { authFetch } from "@/lib/api";

interface Props { report: ComplianceReport }

const PRIORITY_ORDER: Record<Priority, number> = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 };

const PRIORITY_STYLE: Record<Priority, { bar: string; badge: string; label: string }> = {
  CRITICAL: { bar: "bg-red-500",    badge: "bg-red-500/15 text-red-400 border-red-500/30",         label: "Critical" },
  HIGH:     { bar: "bg-orange-500", badge: "bg-orange-500/15 text-orange-400 border-orange-500/30", label: "High" },
  MEDIUM:   { bar: "bg-amber-400",  badge: "bg-amber-500/15 text-amber-400 border-amber-500/30",    label: "Medium" },
  LOW:      { bar: "bg-emerald-500",badge: "bg-emerald-500/15 text-emerald-400 border-emerald-500/30", label: "Low" },
};

type ItemStatus = "open" | "in_progress" | "done";

interface WorkflowState {
  status: ItemStatus;
  notes: string;
  evidence_note: string;
}

function itemKey(regulation: string, article: string) {
  return `${regulation}::${article}`;
}

export function ActionPlan({ report }: Props) {
  const params = useParams();
  const jobId  = (params?.id as string) ?? "";

  const sorted = [...report.action_plan].sort(
    (a, b) => PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority]
  );

  const [workflow, setWorkflow] = useState<Record<string, WorkflowState>>({});
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState<Set<string>>(new Set());

  // Load state from DB
  useEffect(() => {
    if (!jobId) return;
    authFetch(`/api/report/${jobId}/completions`)
      .then(r => r.json())
      .then(data => {
        const map: Record<string, WorkflowState> = {};
        for (const c of data.completions ?? []) {
          map[itemKey(c.regulation, c.article_number)] = {
            status: c.status ?? "open",
            notes: c.notes ?? "",
            evidence_note: c.evidence_note ?? "",
          };
        }
        setWorkflow(map);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [jobId]);

  const getState = (reg: string, art: string): WorkflowState =>
    workflow[itemKey(reg, art)] ?? { status: "open", notes: "", evidence_note: "" };

  const save = useCallback(async (regulation: string, article: string, patch: Partial<WorkflowState>) => {
    const key = itemKey(regulation, article);
    const current = workflow[key] ?? { status: "open", notes: "", evidence_note: "" };
    const next = { ...current, ...patch };
    setWorkflow(prev => ({ ...prev, [key]: next }));
    setSaving(prev => new Set(prev).add(key));
    try {
      await authFetch(`/api/report/${jobId}/completions`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ regulation, article_number: article, ...next }),
      });
    } catch {
      setWorkflow(prev => ({ ...prev, [key]: current }));
    } finally {
      setSaving(prev => { const s = new Set(prev); s.delete(key); return s; });
    }
  }, [workflow, jobId]);

  const cycleStatus = (reg: string, art: string) => {
    const current = getState(reg, art).status;
    const next: ItemStatus = current === "open" ? "in_progress" : current === "in_progress" ? "done" : "open";
    save(reg, art, { status: next });
  };

  const toggleExpanded = (key: string) =>
    setExpanded(prev => { const s = new Set(prev); s.has(key) ? s.delete(key) : s.add(key); return s; });

  const doneCount    = sorted.filter(i => getState(i.regulation, i.article_number).status === "done").length;
  const progressCount = sorted.filter(i => getState(i.regulation, i.article_number).status === "in_progress").length;

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Action Plan</CardTitle>
          <div className="flex items-center gap-3">
            {(doneCount > 0 || progressCount > 0) && (
              <div className="flex items-center gap-2 text-xs">
                {progressCount > 0 && <span className="text-amber-400 font-medium">{progressCount} in progress</span>}
                {doneCount > 0 && <span className="text-emerald-400 font-medium">{doneCount}/{sorted.length} done</span>}
              </div>
            )}
            <span className="text-xs text-slate-600">{sorted.length} items</span>
          </div>
        </div>
        {/* Progress bar */}
        {sorted.length > 0 && (
          <div className="h-1.5 w-full rounded-full bg-white/[0.05] overflow-hidden mt-2">
            <div
              className="h-full rounded-full bg-gradient-to-r from-amber-500 to-emerald-500 transition-all duration-500"
              style={{ width: `${((doneCount + progressCount * 0.5) / sorted.length) * 100}%` }}
            />
          </div>
        )}
      </CardHeader>
      <CardContent className="p-0">
        {loading ? (
          <div className="flex items-center justify-center py-10">
            <Loader2 className="h-5 w-5 animate-spin text-slate-600" />
          </div>
        ) : (
          <div className="divide-y divide-white/[0.04]">
            {sorted.map((item, i) => {
              const style  = PRIORITY_STYLE[item.priority];
              const key    = itemKey(item.regulation, item.article_number);
              const state  = getState(item.regulation, item.article_number);
              const isDone = state.status === "done";
              const isIP   = state.status === "in_progress";
              const isExp  = expanded.has(key);
              const isSaving = saving.has(key);

              const StatusIcon = isDone ? CheckCircle2 : isIP ? PlayCircle : Circle;
              const statusColor = isDone ? "text-emerald-400" : isIP ? "text-amber-400" : "text-slate-600";

              return (
                <div key={i} className={cn("flex gap-0 transition-opacity duration-200", isDone && "opacity-50")}>
                  <div className={cn("w-1 flex-shrink-0", style.bar)} />
                  <div className="flex-1 px-4 py-3">
                    {/* Header row */}
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-center gap-2 flex-wrap mb-1">
                        <span className={cn("rounded-full border px-2.5 py-0.5 text-[10px] font-bold", style.badge)}>
                          {style.label}
                        </span>
                        <span className="text-xs text-slate-600">
                          {REGULATION_LABEL[item.regulation] ?? item.regulation} · {item.article_number}
                        </span>
                      </div>
                      <div className="flex items-center gap-1 flex-shrink-0">
                        {isSaving ? (
                          <Loader2 className="h-4 w-4 animate-spin text-slate-600" />
                        ) : (
                          <button
                            onClick={() => cycleStatus(item.regulation, item.article_number)}
                            title={isDone ? "Mark open" : isIP ? "Mark done" : "Mark in progress"}
                            className={cn("transition-colors", statusColor, "hover:scale-110")}
                          >
                            <StatusIcon className="h-4 w-4" />
                          </button>
                        )}
                        <button
                          onClick={() => toggleExpanded(key)}
                          className="text-slate-700 hover:text-slate-400 transition-colors"
                          title="Notes & evidence"
                        >
                          <ChevronDown className={cn("h-3.5 w-3.5 transition-transform", isExp && "rotate-180")} />
                        </button>
                      </div>
                    </div>

                    {/* Action text */}
                    <p className={cn("text-sm leading-relaxed", isDone ? "line-through text-slate-500" : "text-slate-300")}>
                      {item.action}
                    </p>

                    {/* Meta */}
                    <div className="mt-2 flex flex-wrap gap-3">
                      <span className="flex items-center gap-1.5 text-xs text-slate-600">
                        <Clock className="h-3 w-3" />{item.estimated_effort}
                      </span>
                      {item.deadline && (
                        <span className="flex items-center gap-1.5 text-xs text-slate-600">
                          <CalendarDays className="h-3 w-3" />By {item.deadline}
                        </span>
                      )}
                      {state.status === "in_progress" && (
                        <span className="text-xs font-medium text-amber-400">In progress</span>
                      )}
                      {state.status === "done" && (
                        <span className="text-xs font-medium text-emerald-400">Done</span>
                      )}
                    </div>

                    {/* Expanded: notes + evidence */}
                    {isExp && (
                      <div className="mt-3 flex flex-col gap-2">
                        <div>
                          <label className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-widest text-slate-600 mb-1">
                            <StickyNote className="h-3 w-3" /> Notes
                          </label>
                          <textarea
                            value={state.notes}
                            onChange={e => setWorkflow(prev => ({ ...prev, [key]: { ...getState(item.regulation, item.article_number), notes: e.target.value } }))}
                            onBlur={e => save(item.regulation, item.article_number, { notes: e.target.value })}
                            rows={2}
                            placeholder="Add internal notes about this action..."
                            className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-xs text-slate-300 placeholder-slate-600 resize-none focus:outline-none focus:border-brand-500/50"
                          />
                        </div>
                        <div>
                          <label className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-widest text-slate-600 mb-1">
                            <FileText className="h-3 w-3" /> Evidence / proof of completion
                          </label>
                          <textarea
                            value={state.evidence_note}
                            onChange={e => setWorkflow(prev => ({ ...prev, [key]: { ...getState(item.regulation, item.article_number), evidence_note: e.target.value } }))}
                            onBlur={e => save(item.regulation, item.article_number, { evidence_note: e.target.value })}
                            rows={2}
                            placeholder="Describe what was implemented, link to document, policy version, etc."
                            className="w-full rounded-lg border border-white/[0.08] bg-white/[0.03] px-3 py-2 text-xs text-slate-300 placeholder-slate-600 resize-none focus:outline-none focus:border-brand-500/50"
                          />
                        </div>
                        <div className="flex justify-end">
                          <button
                            onClick={() => save(item.regulation, item.article_number, { status: "open", notes: "", evidence_note: "" })}
                            className="flex items-center gap-1 text-[10px] text-slate-600 hover:text-slate-400 transition-colors"
                          >
                            <RotateCcw className="h-3 w-3" /> Reset
                          </button>
                        </div>
                      </div>
                    )}

                    {item.dependencies.length > 0 && (
                      <p className="mt-1.5 text-xs text-slate-600">Depends on: {item.dependencies.join(", ")}</p>
                    )}
                  </div>
                </div>
              );
            })}
            {sorted.length === 0 && (
              <div className="px-6 py-8 text-center text-sm text-slate-600">No actions required</div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
