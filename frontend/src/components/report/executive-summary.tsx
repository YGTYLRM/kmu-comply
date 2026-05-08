import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import type { ComplianceReport } from "@/lib/types";

interface Props {
  report: ComplianceReport;
}

export function ExecutiveSummary({ report }: Props) {
  const score = report.overall_score_percent;
  const scoreColor =
    score >= 75 ? "text-green-700" : score >= 50 ? "text-yellow-700" : "text-red-700";

  return (
    <Card>
      <CardHeader>
        <CardTitle>Executive Summary</CardTitle>
      </CardHeader>
      <CardContent className="flex flex-col gap-5">
        <div className="flex items-center gap-4">
          <div className="flex-shrink-0 text-center">
            <div className={`text-4xl font-bold ${scoreColor}`}>{score}%</div>
            <div className="text-xs text-slate-500 mt-0.5">Overall Score</div>
          </div>
          <div className="flex-1">
            <Progress value={score} />
          </div>
        </div>
        <p className="text-sm text-slate-700 leading-relaxed whitespace-pre-wrap">
          {report.executive_summary}
        </p>
        {report.requires_manual_review.length > 0 && (
          <div className="rounded-lg bg-amber-50 border border-amber-200 px-4 py-3">
            <p className="text-xs font-medium text-amber-800 mb-1">Requires manual review</p>
            <ul className="text-xs text-amber-700 list-disc list-inside space-y-0.5">
              {report.requires_manual_review.map((item, i) => (
                <li key={i}>{item}</li>
              ))}
            </ul>
          </div>
        )}
        {report.validation_warnings.length > 0 && (
          <div className="rounded-lg bg-slate-50 border border-slate-200 px-4 py-3">
            <p className="text-xs font-medium text-slate-600 mb-1">Profile warnings</p>
            <ul className="text-xs text-slate-500 list-disc list-inside space-y-0.5">
              {report.validation_warnings.map((w, i) => (
                <li key={i}>{w}</li>
              ))}
            </ul>
          </div>
        )}
        <p className="text-xs text-slate-400 italic">{report.disclaimer}</p>
      </CardContent>
    </Card>
  );
}
