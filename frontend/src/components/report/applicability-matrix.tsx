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
        <div className="divide-y divide-white/[0.04]">
          {report.applicable_regulations.map((reg) => (
            <div key={reg.regulation} className="flex items-start gap-3 px-6 py-4">
              {reg.applies ? (
                <CheckCircle2 className="h-5 w-5 text-brand-400 mt-0.5 flex-shrink-0" />
              ) : (
                <XCircle className="h-5 w-5 text-slate-700 mt-0.5 flex-shrink-0" />
              )}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <span className="text-sm font-medium text-slate-300">
                    {REGULATION_LABEL[reg.regulation] ?? reg.regulation}
                  </span>
                  <Badge
                    className={cn(
                      reg.applies
                        ? "border-brand-500/30 bg-brand-500/10 text-brand-300"
                        : "border-white/10 bg-white/5 text-slate-600"
                    )}
                  >
                    {reg.applies ? "Applies" : "Not applicable"}
                  </Badge>
                  {reg.key_threshold && (
                    <span className="text-xs text-slate-600">{reg.key_threshold}</span>
                  )}
                </div>
                <p className="text-xs text-slate-600 mt-0.5">{reg.reason}</p>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
