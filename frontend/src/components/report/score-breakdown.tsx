import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { REGULATION_LABEL } from "@/lib/utils";
import type { ComplianceReport } from "@/lib/types";

interface Props {
  report: ComplianceReport;
}

export function ScoreBreakdown({ report }: Props) {
  const applicable = report.regulation_scores.filter((s) => s.total_requirements > 0);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Score Breakdown</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {applicable.map((s) => (
          <div key={s.regulation}>
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-sm font-medium text-slate-700">
                {REGULATION_LABEL[s.regulation] ?? s.regulation}
              </span>
              <span className="text-sm font-semibold text-slate-900">{s.score_percent}%</span>
            </div>
            <Progress value={s.score_percent} className="h-2" />
            <div className="flex gap-4 mt-1.5 text-xs text-slate-500">
              <span className="text-green-600">{s.compliant} compliant</span>
              <span className="text-yellow-600">{s.partially_compliant} partial</span>
              <span className="text-red-600">{s.non_compliant} non-compliant</span>
              {s.cannot_assess > 0 && <span className="text-slate-400">{s.cannot_assess} unassessed</span>}
            </div>
          </div>
        ))}
        {applicable.length === 0 && (
          <p className="text-sm text-slate-400 text-center py-4">No applicable regulations to score</p>
        )}
      </CardContent>
    </Card>
  );
}
