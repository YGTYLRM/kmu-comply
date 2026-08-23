import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { REGULATION_LABEL } from "@/lib/utils";
import type { ComplianceReport } from "@/lib/types";

interface Props {
  report: ComplianceReport;
}

export function ScoreBreakdown({ report }: Props) {
  const scores = report.regulation_scores;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Score Breakdown</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-4">
        {scores.map((s) =>
          s.total_requirements === 0 ? (
            <div key={s.regulation}>
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-sm font-medium text-slate-300">
                  {REGULATION_LABEL[s.regulation] ?? s.regulation}
                </span>
                <span className="text-sm font-semibold text-slate-600">No findings</span>
              </div>
              <p className="text-xs text-slate-600">
                Analysis did not return findings for this regulation — treat as incomplete, not compliant.
              </p>
            </div>
          ) : (
            <div key={s.regulation}>
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-sm font-medium text-slate-300">
                  {REGULATION_LABEL[s.regulation] ?? s.regulation}
                </span>
                <span className="text-sm font-semibold text-white">{s.score_percent}%</span>
              </div>
              <Progress value={s.score_percent} className="h-2" />
              <div className="flex gap-4 mt-1.5 text-xs text-slate-600">
                <span className="text-emerald-500">{s.compliant} compliant</span>
                <span className="text-amber-500">{s.partially_compliant} partial</span>
                <span className="text-red-500">{s.non_compliant} non-compliant</span>
                {s.cannot_assess > 0 && <span className="text-slate-600">{s.cannot_assess} unassessed</span>}
              </div>
            </div>
          )
        )}
        {scores.length === 0 && (
          <p className="text-sm text-slate-600 text-center py-4">No applicable regulations to score</p>
        )}
      </CardContent>
    </Card>
  );
}
