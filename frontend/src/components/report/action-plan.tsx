import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn, REGULATION_LABEL, PRIORITY_COLOR } from "@/lib/utils";
import type { ComplianceReport } from "@/lib/types";
import { Clock, AlertCircle } from "lucide-react";

interface Props {
  report: ComplianceReport;
}

const PRIORITY_ORDER = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 };

export function ActionPlan({ report }: Props) {
  const sorted = [...report.action_plan].sort(
    (a, b) => PRIORITY_ORDER[a.priority] - PRIORITY_ORDER[b.priority]
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle>Action Plan</CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <div className="divide-y divide-slate-100">
          {sorted.map((item, i) => (
            <div key={i} className="px-6 py-4">
              <div className="flex items-start gap-2 flex-wrap">
                <Badge className={cn("flex-shrink-0", PRIORITY_COLOR[item.priority])}>
                  {item.priority}
                </Badge>
                <span className="text-xs text-slate-400 flex-shrink-0">
                  {REGULATION_LABEL[item.regulation] ?? item.regulation} · Art. {item.article_number}
                </span>
              </div>
              <p className="mt-2 text-sm text-slate-800">{item.action}</p>
              <div className="mt-2 flex flex-wrap gap-4 text-xs text-slate-500">
                <span className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {item.estimated_effort}
                </span>
                {item.deadline && (
                  <span className="flex items-center gap-1">
                    <AlertCircle className="h-3 w-3" />
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
          ))}
          {sorted.length === 0 && (
            <div className="px-6 py-8 text-center text-sm text-slate-400">No actions required</div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
