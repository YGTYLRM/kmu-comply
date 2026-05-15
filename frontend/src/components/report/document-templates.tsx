"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { FileText, Loader2, Download, ChevronDown, AlertCircle } from "lucide-react";
import { authFetch } from "@/lib/api";

const TEMPLATES = [
  { id: "privacy_notice",          label: "Privacy Notice",              regulation: "GDPR Art. 13/14" },
  { id: "processing_records",      label: "Processing Records",          regulation: "GDPR Art. 30" },
  { id: "tom_checklist",           label: "TOM Checklist",               regulation: "GDPR Art. 32" },
  { id: "incident_response_plan",  label: "Incident Response Plan",      regulation: "NIS2 / GDPR" },
  { id: "ai_usage_policy",         label: "AI Usage Policy",             regulation: "EU AI Act" },
  { id: "ai_inventory",            label: "AI System Inventory",         regulation: "EU AI Act Art. 11" },
  { id: "whistleblower_policy",    label: "Whistleblower Policy",        regulation: "HinSchG §13" },
  { id: "safety_instruction",      label: "Safety Instruction Template", regulation: "ArbSchG §12" },
  { id: "supplier_code_of_conduct",label: "Supplier Code of Conduct",    regulation: "LkSG §6" },
  { id: "nis2_risk_register",      label: "Cybersecurity Risk Register", regulation: "NIS2 Art. 21" },
];

interface Props { jobId: string }

function downloadMarkdown(content: string, filename: string) {
  const blob = new Blob([content], { type: "text/markdown" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export function DocumentTemplates({ jobId }: Props) {
  const [open, setOpen] = useState(false);
  const [generating, setGenerating] = useState<string | null>(null);
  const [preview, setPreview] = useState<{ id: string; content: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const generate = async (templateId: string, label: string) => {
    setGenerating(templateId);
    setError(null);
    setPreview(null);
    try {
      const res = await authFetch(`/api/report/${jobId}/templates/${templateId}`, { method: "POST" });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      setPreview({ id: templateId, content: data.content });
    } catch (e) {
      setError(`Failed to generate ${label}. Try again.`);
    } finally {
      setGenerating(null);
    }
  };

  return (
    <Card>
      <CardHeader>
        <button onClick={() => setOpen(v => !v)} className="flex items-center justify-between w-full text-left">
          <div className="flex items-center gap-2.5">
            <FileText className="h-4 w-4 text-brand-400" />
            <CardTitle>Document Templates</CardTitle>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-500">{TEMPLATES.length} templates available</span>
            <ChevronDown className={`h-4 w-4 text-slate-600 transition-transform duration-200 ${open ? "rotate-180" : ""}`} />
          </div>
        </button>
        {open && (
          <p className="text-xs text-slate-500 mt-1 leading-relaxed">
            AI-generated compliance document drafts personalised to your company profile.
            Always have these reviewed by a qualified legal or compliance professional before use.
          </p>
        )}
      </CardHeader>

      {open && (
        <CardContent className="pt-0">
          {error && (
            <div className="mb-4 flex items-center gap-2 rounded-lg border border-red-500/20 bg-red-500/[0.06] px-4 py-3 text-xs text-red-400">
              <AlertCircle className="h-3.5 w-3.5 flex-shrink-0" />{error}
            </div>
          )}

          <div className="grid sm:grid-cols-2 gap-2 mb-4">
            {TEMPLATES.map(t => (
              <button
                key={t.id}
                onClick={() => generate(t.id, t.label)}
                disabled={!!generating}
                className="flex items-center justify-between gap-3 rounded-xl border border-white/[0.07] bg-white/[0.02] px-4 py-3 text-left hover:bg-white/[0.05] hover:border-brand-500/20 transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed group"
              >
                <div className="min-w-0">
                  <p className="text-xs font-semibold text-slate-200 group-hover:text-white truncate">{t.label}</p>
                  <p className="text-[10px] text-slate-600 mt-0.5">{t.regulation}</p>
                </div>
                {generating === t.id
                  ? <Loader2 className="h-3.5 w-3.5 animate-spin text-brand-400 flex-shrink-0" />
                  : <FileText className="h-3.5 w-3.5 text-slate-700 group-hover:text-brand-400 flex-shrink-0 transition-colors" />
                }
              </button>
            ))}
          </div>

          {/* Preview pane */}
          {preview && (
            <div className="rounded-xl border border-white/[0.07] bg-dark-900/60 overflow-hidden">
              <div className="flex items-center justify-between px-4 py-3 border-b border-white/[0.05]">
                <p className="text-xs font-semibold text-slate-300">
                  {TEMPLATES.find(t => t.id === preview.id)?.label}
                </p>
                <button
                  onClick={() => downloadMarkdown(preview.content, `complio-${preview.id}.md`)}
                  className="flex items-center gap-1.5 rounded-lg border border-white/[0.08] bg-white/[0.04] px-3 py-1.5 text-xs font-medium text-slate-300 hover:text-white hover:bg-white/[0.08] transition-all"
                >
                  <Download className="h-3 w-3" /> Download .md
                </button>
              </div>
              <div className="px-4 py-4 max-h-96 overflow-y-auto">
                <pre className="text-xs text-slate-400 leading-relaxed whitespace-pre-wrap font-mono">
                  {preview.content}
                </pre>
              </div>
            </div>
          )}
        </CardContent>
      )}
    </Card>
  );
}
