import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn, REGULATION_LABEL } from "@/lib/utils";
import type { ComplianceReport } from "@/lib/types";
import { CheckCircle2, XCircle } from "lucide-react";

interface Props {
  report: ComplianceReport;
}

export function ApplicabilityMatrix({ report }: Props) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Regulation Applicability</CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <div className="divide-y divide-slate-100">
          {report.applicable_regulations.map((reg) => (
            <div key={reg.regulation} className="flex items-start gap-3 px-6 py-4">
              {reg.applies ? (
                <CheckCircle2 className="h-5 w-5 text-brand-600 mt-0.5 flex-shrink-0" />
              ) : (
                <XCircle className="h-5 w-5 text-slate-300 mt-0.5 flex-shrink-0" />
              )}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-sm font-medium text-slate-900">
                    {REGULATION_LABEL[reg.regulation] ?? reg.regulation}
                  </span>
                  <Badge
                    className={cn(
                      reg.applies
                        ? "border-brand-200 bg-brand-50 text-brand-700"
                        : "border-slate-200 bg-slate-50 text-slate-500"
                    )}
                  >
                    {reg.applies ? "Applies" : "Not applicable"}
                  </Badge>
                  {reg.key_threshold && (
                    <span className="text-xs text-slate-400">{reg.key_threshold}</span>
                  )}
                </div>
                <p className="text-xs text-slate-500 mt-0.5">{reg.reason}</p>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
