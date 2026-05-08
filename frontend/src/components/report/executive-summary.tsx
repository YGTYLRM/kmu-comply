import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { AlertTriangle, Info } from "lucide-react";
import type { ComplianceReport } from "@/lib/types";

interface Props { report: ComplianceReport }

export function ExecutiveSummary({ report }: Props) {
  const score = report.overall_score_percent;
  const scoreColor = score >= 75 ? "text-emerald-400" : score >= 50 ? "text-amber-400" : "text-red-400";
  const scoreBg    = score >= 75 ? "bg-emerald-500/10 border-emerald-500/25" : score >= 50 ? "bg-amber-500/10 border-amber-500/25" : "bg-red-500/10 border-red-500/25";

  return (
    <Card>
      <CardHeader>
        <CardTitle>Executive Summary</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-5">
        <div className={`flex items-center gap-5 rounded-xl border px-5 py-4 ${scoreBg}`}>
          <div className="flex-shrink-0 text-center">
            <div className={`text-4xl font-bold tabular-nums ${scoreColor}`}>{score}%</div>
            <div className="text-xs text-slate-500 mt-0.5 font-medium">Overall Score</div>
          </div>
          <div className="flex-1">
            <Progress value={score} />
            <p className="text-xs text-slate-500 mt-2 leading-relaxed">
              {score >= 75
                ? "Good overall compliance posture. Address remaining gaps."
                : score >= 50
                ? "Partial compliance. Several gaps need attention."
                : "Significant compliance gaps identified. Immediate action required."}
            </p>
          </div>
        </div>

        <p className="text-sm text-slate-400 leading-relaxed whitespace-pre-wrap">
          {report.executive_summary}
        </p>

        {report.requires_manual_review.length > 0 && (
          <div className="rounded-xl bg-amber-500/10 border border-amber-500/25 px-4 py-3.5 flex gap-3">
            <AlertTriangle className="h-4 w-4 text-amber-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-xs font-semibold text-amber-300 mb-1.5">Requires manual legal review</p>
              <ul className="text-xs text-amber-400/80 space-y-1">
                {report.requires_manual_review.map((item, i) => (
                  <li key={i} className="flex gap-1.5"><span>·</span>{item}</li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {report.validation_warnings.length > 0 && (
          <div className="rounded-xl bg-white/[0.04] border border-white/8 px-4 py-3.5 flex gap-3">
            <Info className="h-4 w-4 text-slate-500 flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-xs font-semibold text-slate-400 mb-1.5">Profile notes</p>
              <ul className="text-xs text-slate-500 space-y-1">
                {report.validation_warnings.map((w, i) => (
                  <li key={i} className="flex gap-1.5"><span>·</span>{w}</li>
                ))}
              </ul>
            </div>
          </div>
        )}

        <div className="border-t border-white/[0.06] pt-4 space-y-1">
          <p className="text-xs font-semibold text-slate-600">Preliminary screening, not a legal audit</p>
          <p className="text-xs text-slate-600 italic">{report.disclaimer}</p>
        </div>
      </CardContent>
    </Card>
  );
}
