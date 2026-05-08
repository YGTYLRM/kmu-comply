"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn, REGULATION_LABEL, STATUS_COLOR } from "@/lib/utils";
import type { ComplianceReport, Regulation } from "@/lib/types";
import { ChevronDown, ChevronUp } from "lucide-react";

interface Props {
  report: ComplianceReport;
}

export function GapAnalysis({ report }: Props) {
  const [expanded, setExpanded] = useState<string | null>(null);

  const byRegulation = report.gap_analysis.reduce<Record<string, typeof report.gap_analysis>>(
    (acc, gap) => {
      const key = gap.regulation;
      if (!acc[key]) acc[key] = [];
      acc[key].push(gap);
      return acc;
    },
    {}
  );

  return (
    <Card>
      <CardHeader>
        <CardTitle>Gap Analysis</CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        {Object.entries(byRegulation).map(([reg, gaps]) => (
          <div key={reg} className="border-b border-slate-100 last:border-0">
            <button
              type="button"
              className="flex w-full items-center justify-between px-6 py-3 hover:bg-slate-50 transition-colors"
              onClick={() => setExpanded(expanded === reg ? null : reg)}
            >
              <span className="text-sm font-medium text-slate-800">
                {REGULATION_LABEL[reg] ?? reg}
              </span>
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-500">{gaps.length} items</span>
                {expanded === reg ? (
                  <ChevronUp className="h-4 w-4 text-slate-400" />
                ) : (
                  <ChevronDown className="h-4 w-4 text-slate-400" />
                )}
              </div>
            </button>
            {expanded === reg && (
              <div className="divide-y divide-slate-50 px-6 pb-4">
                {gaps.map((gap, i) => (
                  <div key={i} className="py-3">
                    <div className="flex items-start gap-2 flex-wrap">
                      <span className="text-xs font-mono text-slate-500 flex-shrink-0">
                        Art. {gap.article_number}
                      </span>
                      <span className="text-sm font-medium text-slate-800">{gap.article_title}</span>
                      <Badge className={cn("ml-auto", STATUS_COLOR[gap.status])}>
                        {gap.status.replace("_", " ")}
                      </Badge>
                    </div>
                    <p className="mt-1.5 text-xs text-slate-600">{gap.evidence}</p>
                    {gap.deficiency_description && (
                      <p className="mt-1 text-xs text-red-600">{gap.deficiency_description}</p>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
        {report.gap_analysis.length === 0 && (
          <div className="px-6 py-8 text-center text-sm text-slate-400">
            No gaps identified
          </div>
        )}
      </CardContent>
    </Card>
  );
}
