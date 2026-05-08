import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn, REGULATION_LABEL } from "@/lib/utils";
import type { ComplianceReport, Priority } from "@/lib/types";
import { Clock, CalendarDays } from "lucide-react";

interface Props { report: ComplianceReport }

const PRIORITY_ORDER: Record<Priority, number> = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 };

const PRIORITY_STYLE: Record<Priority, { bar: string; badge: string; label: string }> = {
  CRITICAL: { bar: "bg-red-500",    badge: "bg-red-50 text-red-700 border-red-200",    label: "Critical" },
  HIGH:     { bar: "bg-orange-500", badge: "bg-orange-50 text-orange-700 border-orange-200", label: "High" },
  MEDIUM:   { bar: "bg-amber-400",  badge: "bg-amber-50 text-amber-700 border-amber-200",  label: "Medium" },
  LOW:      { bar: "bg-emerald-500",badge: "bg-emerald-50 text-emerald-700 border-emerald-200", label: "Low" },
};

export function ActionPlan({ report }: Props) {
  const sorted = [...report.action_plan].sort(
    (a, b) => PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority]
  );

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Action Plan</CardTitle>
          <span className="text-xs text-slate-400">{sorted.length} items</span>
        </div>
      </CardHeader>
      <CardContent className="p-0">
        <div className="divide-y divide-slate-100">
          {sorted.map((item, i) => {
            const style = PRIORITY_STYLE[item.priority];
            return (
              <div key={i} className="flex gap-0">
                <div className={cn("w-1 flex-shrink-0 rounded-l-none", style.bar)} />
                <div className="flex-1 px-5 py-4">
                  <div className="flex items-center gap-2 flex-wrap mb-2">
                    <span className={cn("rounded-full border px-2.5 py-0.5 text-[10px] font-bold", style.badge)}>
                      {style.label}
                    </span>
                    <span className="text-xs text-slate-400">
                      {REGULATION_LABEL[item.regulation] ?? item.regulation} · Art. {item.article_number}
                    </span>
                  </div>
                  <p className="text-sm text-slate-800 leading-relaxed">{item.action}</p>
                  <div className="mt-2.5 flex flex-wrap gap-4">
                    <span className="flex items-center gap-1.5 text-xs text-slate-500">
                      <Clock className="h-3 w-3 text-slate-400" />
                      {item.estimated_effort}
                    </span>
                    {item.deadline && (
                      <span className="flex items-center gap-1.5 text-xs text-slate-500">
                        <CalendarDays className="h-3 w-3 text-slate-400" />
                        By {item.deadline}
                      </span>
                    )}
                  </div>
                  {item.dependencies.length > 0 && (
                    <p className="mt-1.5 text-xs text-slate-400">
                      Depends on: {item.dependencies.join(", ")}
                    </p>
                  )}
                </div>
              </div>
            );
          })}
          {sorted.length === 0 && (
            <div className="px-6 py-8 text-center text-sm text-slate-400">No actions required</div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
