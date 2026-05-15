"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn, REGULATION_LABEL, STATUS_COLOR } from "@/lib/utils";
import type { ComplianceReport } from "@/lib/types";
import { ChevronDown, ChevronUp, HelpCircle, ExternalLink } from "lucide-react";

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
        {Object.entries(byRegulation).map(([reg, gaps]) => {
          const cannotCount   = gaps.filter(g => g.status === "CANNOT_ASSESS").length;
          const assessedCount = gaps.length - cannotCount;

          return (
            <div key={reg} className="border-b border-white/[0.05] last:border-0">
              <button
                type="button"
                className="flex w-full items-center justify-between px-6 py-3 hover:bg-white/[0.03] transition-colors"
                onClick={() => setExpanded(expanded === reg ? null : reg)}
              >
                <span className="text-sm font-medium text-slate-300">
                  {REGULATION_LABEL[reg] ?? reg}
                </span>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-slate-600">{assessedCount} assessed</span>
                  {cannotCount > 0 && (
                    <span className="flex items-center gap-1 rounded-full bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 text-[10px] font-semibold text-amber-500">
                      <HelpCircle className="h-2.5 w-2.5" />
                      {cannotCount} need docs
                    </span>
                  )}
                  {expanded === reg
                    ? <ChevronUp className="h-4 w-4 text-slate-600" />
                    : <ChevronDown className="h-4 w-4 text-slate-600" />
                  }
                </div>
              </button>

              {expanded === reg && (
                <div className="divide-y divide-white/[0.04] px-6 pb-4">
                  {/* Assessed items first */}
                  {gaps.filter(g => g.status !== "CANNOT_ASSESS").map((gap, i) => (
                    <div key={i} className="py-3">
                      <div className="flex items-start gap-2 flex-wrap">
                        <span className="text-xs font-mono text-slate-600 flex-shrink-0">
                          Art. {gap.article_number}
                        </span>
                        <span className="text-sm font-medium text-slate-300">{gap.article_title}</span>
                        {gap.source_url && (
                          <a
                            href={gap.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            title="View official source"
                            className="flex-shrink-0 text-slate-600 hover:text-brand-400 transition-colors"
                          >
                            <ExternalLink className="h-3 w-3" />
                          </a>
                        )}
                        <div className="ml-auto flex items-center gap-1.5 flex-shrink-0">
                          {gap.confidence && gap.confidence !== "HIGH" && (
                            <span
                              title={gap.confidence_reason}
                              className={cn(
                                "text-[10px] font-semibold px-1.5 py-0.5 rounded-full border",
                                gap.confidence === "MEDIUM"
                                  ? "bg-amber-500/10 border-amber-500/20 text-amber-400"
                                  : "bg-orange-500/10 border-orange-500/20 text-orange-400"
                              )}
                            >
                              {gap.confidence} confidence
                            </span>
                          )}
                          <Badge className={STATUS_COLOR[gap.status]}>
                            {gap.status.replace("_", " ")}
                          </Badge>
                        </div>
                      </div>
                      {gap.confidence_reason && gap.confidence !== "HIGH" && (
                        <p className="mt-1 text-[10px] text-slate-600 italic">{gap.confidence_reason}</p>
                      )}
                      <p className="mt-1.5 text-xs text-slate-500">{gap.evidence}</p>
                      {gap.deficiency_description && (
                        <p className="mt-1 text-xs text-red-400">{gap.deficiency_description}</p>
                      )}
                    </div>
                  ))}

                  {/* CANNOT_ASSESS items at the bottom, visually dimmed */}
                  {gaps.filter(g => g.status === "CANNOT_ASSESS").map((gap, i) => (
                    <div key={`ca-${i}`} className="py-3 opacity-50">
                      <div className="flex items-start gap-2 flex-wrap">
                        <span className="text-xs font-mono text-slate-600 flex-shrink-0">
                          Art. {gap.article_number}
                        </span>
                        <span className="text-sm font-medium text-slate-400">{gap.article_title}</span>
                        <span className="ml-auto flex items-center gap-1 text-[10px] font-semibold text-amber-500/80">
                          <HelpCircle className="h-3 w-3" />
                          Needs documents
                        </span>
                      </div>
                      <p className="mt-1.5 text-xs text-slate-600">{gap.evidence}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          );
        })}

        {report.gap_analysis.length === 0 && (
          <div className="px-6 py-8 text-center text-sm text-slate-600">
            No gaps identified
          </div>
        )}
      </CardContent>
    </Card>
  );
}
