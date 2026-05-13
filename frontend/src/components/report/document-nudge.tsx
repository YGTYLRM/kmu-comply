import Link from "next/link";
import { FileUp, ArrowRight, FileText, Shield, Scale } from "lucide-react";
import type { ComplianceReport } from "@/lib/types";

const DOC_EXAMPLES = [
  { icon: Shield,   label: "Privacy policy",        hint: "Turns most GDPR / BDSG items from unassessed to a real verdict" },
  { icon: FileText, label: "Security procedures",   hint: "Unlocks NIS2 and EU AI Act requirements" },
  { icon: Scale,    label: "Whistleblower policy",  hint: "Needed for HinSchG assessment" },
];

interface Props {
  report: ComplianceReport;
}

export function DocumentNudge({ report }: Props) {
  const cannotCount = report.gap_analysis.filter(g => g.status === "CANNOT_ASSESS").length;
  if (cannotCount === 0) return null;

  const totalCount  = report.gap_analysis.length;
  const pct         = Math.round((cannotCount / totalCount) * 100);

  return (
    <div className="rounded-2xl border border-amber-500/25 overflow-hidden"
         style={{ background: "rgba(20,15,5,0.7)" }}>

      {/* Top strip */}
      <div className="border-b border-amber-500/15 bg-amber-500/8 px-6 py-4 flex items-center gap-3">
        <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-xl bg-amber-500/15 border border-amber-500/20">
          <FileUp className="h-4 w-4 text-amber-400" />
        </div>
        <div className="flex-1">
          <p className="text-sm font-bold text-amber-200">
            {cannotCount} of {totalCount} requirements ({pct}%) could not be assessed
          </p>
          <p className="text-xs text-amber-400/70 mt-0.5">
            Without company documents the AI can only use what you declared in the form.
          </p>
        </div>
      </div>

      {/* Body */}
      <div className="px-6 py-5 flex flex-col gap-5 sm:flex-row sm:items-start sm:gap-8">
        {/* What to upload */}
        <div className="flex-1 flex flex-col gap-3">
          <p className="text-xs font-bold uppercase tracking-widest text-slate-500">
            Upload these to unlock real verdicts
          </p>
          {DOC_EXAMPLES.map(({ icon: Icon, label, hint }) => (
            <div key={label} className="flex items-start gap-3">
              <div className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-lg bg-white/[0.04] border border-white/[0.06]">
                <Icon className="h-3.5 w-3.5 text-slate-400" />
              </div>
              <div>
                <p className="text-xs font-semibold text-slate-300">{label}</p>
                <p className="text-xs text-slate-600 leading-snug">{hint}</p>
              </div>
            </div>
          ))}
        </div>

        {/* What changes */}
        <div className="flex-1 flex flex-col gap-3">
          <p className="text-xs font-bold uppercase tracking-widest text-slate-500">
            What changes
          </p>
          <ul className="flex flex-col gap-2">
            {[
              "CANNOT ASSESS → COMPLIANT, PARTIAL, or NON-COMPLIANT",
              "AI cites the exact clause in your policy",
              "Action plan becomes specific to your documents",
              "Overall score reflects your actual posture",
            ].map(t => (
              <li key={t} className="flex items-start gap-2 text-xs text-slate-400">
                <ArrowRight className="h-3 w-3 text-amber-500 flex-shrink-0 mt-0.5" />
                {t}
              </li>
            ))}
          </ul>

          <Link
            href="/analyze"
            className="mt-2 inline-flex items-center justify-center gap-2 rounded-xl bg-amber-500 px-5 py-2.5 text-sm font-semibold text-dark-950 hover:bg-amber-400 transition-colors duration-200"
          >
            Re-run with documents
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </div>
    </div>
  );
}
