"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { UserCheck, Loader2, CheckCircle2, AlertCircle, ChevronDown } from "lucide-react";
import { authFetch } from "@/lib/api";
import type { ComplianceReport } from "@/lib/types";

interface Props {
  report: ComplianceReport;
  jobId: string;
}

export function ExpertReview({ report, jobId }: Props) {
  const [open, setOpen] = useState(false);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const criticalHighGaps = report.gap_analysis.filter(
    g => g.status === "NON_COMPLIANT" || g.status === "PARTIALLY_COMPLIANT"
  );

  const submit = async () => {
    setLoading(true);
    setError(null);
    try {
      const focus = criticalHighGaps.slice(0, 10).map(g => ({
        regulation: g.regulation,
        article_number: g.article_number,
      }));
      const res = await authFetch("/api/expert-review", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ job_id: jobId, message, focus_items: focus }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      setDone(true);
    } catch {
      setError("Request failed. Please try again or contact us directly.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card className="border-brand-500/20 bg-brand-500/[0.03]">
      <CardHeader>
        <button onClick={() => setOpen(v => !v)} className="flex items-center justify-between w-full text-left">
          <div className="flex items-center gap-2.5">
            <UserCheck className="h-4 w-4 text-brand-400" />
            <CardTitle>Request Expert Review</CardTitle>
            <span className="rounded-full bg-brand-500/15 border border-brand-500/25 px-2.5 py-0.5 text-[10px] font-bold text-brand-400">
              Paid add-on
            </span>
          </div>
          <ChevronDown className={`h-4 w-4 text-slate-600 transition-transform duration-200 ${open ? "rotate-180" : ""}`} />
        </button>
        {open && (
          <p className="text-xs text-slate-500 mt-1 leading-relaxed">
            Have a qualified German compliance expert or attorney review your critical and high-priority findings.
            We will contact you within 2 business days with pricing and next steps.
          </p>
        )}
      </CardHeader>

      {open && (
        <CardContent className="pt-0">
          {done ? (
            <div className="flex items-start gap-3 rounded-xl border border-emerald-500/20 bg-emerald-500/[0.06] px-4 py-4">
              <CheckCircle2 className="h-5 w-5 text-emerald-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-semibold text-emerald-300 mb-0.5">Request submitted</p>
                <p className="text-xs text-slate-400 leading-relaxed">
                  We received your request for <span className="text-white font-medium">{report.company_name}</span>.
                  We will email you within 2 business days with expert availability and pricing.
                </p>
              </div>
            </div>
          ) : (
            <div className="flex flex-col gap-4">
              {/* What gets reviewed */}
              <div className="rounded-xl border border-white/[0.07] bg-white/[0.02] p-4">
                <p className="text-xs font-semibold text-slate-300 mb-2">
                  {criticalHighGaps.length} findings will be submitted for expert review
                </p>
                <div className="flex flex-col gap-1 max-h-32 overflow-y-auto">
                  {criticalHighGaps.slice(0, 10).map((g, i) => (
                    <div key={i} className="flex items-center gap-2 text-xs text-slate-500">
                      <span className={`h-1.5 w-1.5 rounded-full flex-shrink-0 ${g.status === "NON_COMPLIANT" ? "bg-red-400" : "bg-amber-400"}`} />
                      <span className="truncate">{g.article_title || `${g.article_number}`}</span>
                      <span className="text-slate-700 flex-shrink-0">· {g.regulation}</span>
                    </div>
                  ))}
                  {criticalHighGaps.length > 10 && (
                    <p className="text-xs text-slate-600">+{criticalHighGaps.length - 10} more</p>
                  )}
                </div>
              </div>

              {/* Message */}
              <div>
                <label className="text-xs font-semibold text-slate-400 mb-1.5 block">
                  What would you like the expert to focus on? (optional)
                </label>
                <textarea
                  value={message}
                  onChange={e => setMessage(e.target.value)}
                  rows={3}
                  placeholder="e.g. We are particularly concerned about GDPR compliance and our new AI hiring tool..."
                  className="w-full rounded-xl border border-white/[0.08] bg-white/[0.03] px-4 py-3 text-sm text-slate-300 placeholder-slate-600 resize-none focus:outline-none focus:border-brand-500/50"
                />
              </div>

              {error && (
                <div className="flex items-center gap-2 text-xs text-red-400">
                  <AlertCircle className="h-3.5 w-3.5 flex-shrink-0" />{error}
                </div>
              )}

              <button
                onClick={submit}
                disabled={loading || criticalHighGaps.length === 0}
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-brand-600 px-6 py-3 text-sm font-bold text-white hover:bg-brand-500 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <UserCheck className="h-4 w-4" />}
                {loading ? "Submitting..." : "Request expert review"}
              </button>
              <p className="text-[10px] text-slate-600 text-center">
                No payment taken now. We will confirm availability and pricing by email before any charge.
              </p>
            </div>
          )}
        </CardContent>
      )}
    </Card>
  );
}
