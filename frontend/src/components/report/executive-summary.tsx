import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { AlertTriangle, Info } from "lucide-react";
import type { ComplianceReport } from "@/lib/types";

interface Props { report: ComplianceReport }

export function ExecutiveSummary({ report }: Props) {
  const score = report.overall_score_percent;
  const scoreColor = score >= 75 ? "text-emerald-600" : score >= 50 ? "text-amber-500" : "text-red-500";
  const barColor = score >= 75 ? "bg-emerald-500" : score >= 50 ? "bg-amber-500" : "bg-red-500";

  return (
    <Card>
      <CardHeader>
        <CardTitle>Executive Summary</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-5">
        <div className="flex items-center gap-5 rounded-xl bg-slate-50 border border-slate-100 px-5 py-4">
          <div className="flex-shrink-0 text-center">
            <div className={`text-4xl font-bold tabular-nums ${scoreColor}`}>{score}%</div>
            <div className="text-xs text-slate-500 mt-0.5 font-medium">Overall Score</div>
          </div>
          <div className="flex-1">
            <Progress value={score} indicatorClassName={barColor} />
            <p className="text-xs text-slate-500 mt-2 leading-relaxed">
              {score >= 75
                ? "Good overall compliance posture. Address remaining gaps."
                : score >= 50
                ? "Partial compliance. Several gaps need attention."
                : "Significant compliance gaps identified. Immediate action required."}
            </p>
          </div>
        </div>

        <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
          {report.executive_summary}
        </p>

        {report.requires_manual_review.length > 0 && (
          <div className="rounded-xl bg-amber-50 border border-amber-200 px-4 py-3.5 flex gap-3">
            <AlertTriangle className="h-4 w-4 text-amber-600 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-xs font-semibold text-amber-800 mb-1.5">Requires manual legal review</p>
              <ul className="text-xs text-amber-700 space-y-1">
                {report.requires_manual_review.map((item, i) => (
                  <li key={i} className="flex gap-1.5"><span>·</span>{item}</li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {report.validation_warnings.length > 0 && (
          <div className="rounded-xl bg-slate-50 border border-slate-200 px-4 py-3.5 flex gap-3">
            <Info className="h-4 w-4 text-slate-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-xs font-semibold text-slate-600 mb-1.5">Profile notes</p>
              <ul className="text-xs text-slate-500 space-y-1">
                {report.validation_warnings.map((w, i) => (
                  <li key={i} className="flex gap-1.5"><span>·</span>{w}</li>
                ))}
              </ul>
            </div>
          </div>
        )}

        <div className="border-t border-slate-100 pt-4 space-y-1">
          <p className="text-xs font-semibold text-slate-500">Preliminary screening — not a legal audit</p>
          <p className="text-xs text-slate-400 italic">{report.disclaimer}</p>
        </div>
      </CardContent>
    </Card>
  );
}
