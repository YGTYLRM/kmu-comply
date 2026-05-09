"use client";

import { useCallback, useState } from "react";
import { Upload, X, FileText, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

const HINTS = [
  { label: "GDPR / BDSG",  examples: "Privacy policy, records of processing, DPO appointment letter" },
  { label: "NIS2",         examples: "Information security policy, incident response plan, risk assessment" },
  { label: "EU AI Act",    examples: "AI system documentation, impact assessment, human oversight procedures" },
  { label: "HinSchG",      examples: "Whistleblower policy, reporting channel documentation" },
  { label: "ArbSchG",      examples: "Workplace risk assessment (Gefährdungsbeurteilung), safety instructions" },
  { label: "AGG / MiLoG",  examples: "Anti-discrimination policy, working time records, payroll procedures" },
];

interface Props {
  files: File[];
  onChange: (files: File[]) => void;
}

export function Step6Documents({ files, onChange }: Props) {
  const [dragging, setDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const addFiles = useCallback((incoming: FileList | null) => {
    if (!incoming) return;
    setError(null);

    const allowed = ["application/pdf", "text/plain", "text/markdown"];
    const valid: File[] = [];
    const bad: string[] = [];

    Array.from(incoming).forEach((f) => {
      if (!allowed.includes(f.type) && !f.name.endsWith(".txt") && !f.name.endsWith(".md")) {
        bad.push(f.name);
      } else if (f.size > 15 * 1024 * 1024) {
        bad.push(`${f.name} (exceeds 15 MB)`);
      } else {
        valid.push(f);
      }
    });

    if (bad.length) setError(`Skipped: ${bad.join(", ")} — only PDF and TXT files up to 15 MB.`);
    if (valid.length) onChange([...files, ...valid]);
  }, [files, onChange]);

  const remove = (i: number) => {
    const next = [...files];
    next.splice(i, 1);
    onChange(next);
  };

  return (
    <div className="flex flex-col gap-6">
      <div>
        <p className="text-sm text-slate-400 leading-relaxed">
          Upload your company documents to get evidence-backed assessments instead of questionnaire-only results. The AI will read your actual policies and cite specific clauses.
        </p>
        <p className="text-xs text-slate-600 mt-1.5">Optional — you can skip and run the screening without documents.</p>
      </div>

      {/* Drop zone */}
      <label
        className={cn(
          "flex flex-col items-center justify-center gap-3 rounded-2xl border-2 border-dashed p-8 cursor-pointer transition-all duration-200",
          dragging
            ? "border-brand-500 bg-brand-500/8"
            : "border-white/15 bg-white/[0.02] hover:border-white/25 hover:bg-white/[0.04]"
        )}
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => { e.preventDefault(); setDragging(false); addFiles(e.dataTransfer.files); }}
      >
        <input
          type="file"
          multiple
          accept=".pdf,.txt,.md"
          className="sr-only"
          onChange={(e) => addFiles(e.target.files)}
        />
        <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-brand-500/10">
          <Upload className="h-6 w-6 text-brand-400" />
        </div>
        <div className="text-center">
          <p className="text-sm font-semibold text-slate-300">Drop files here or click to browse</p>
          <p className="text-xs text-slate-600 mt-1">PDF, TXT — up to 15 MB per file</p>
        </div>
      </label>

      {error && (
        <div className="flex items-start gap-2 rounded-xl bg-red-500/10 border border-red-500/25 px-4 py-3 text-xs text-red-400">
          <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
          {error}
        </div>
      )}

      {/* Uploaded file list */}
      {files.length > 0 && (
        <div className="flex flex-col gap-2">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-widest">{files.length} file{files.length !== 1 ? "s" : ""} selected</p>
          {files.map((f, i) => (
            <div key={i} className="flex items-center gap-3 rounded-xl border border-white/8 bg-white/[0.03] px-4 py-2.5">
              <FileText className="h-4 w-4 text-brand-400 flex-shrink-0" />
              <span className="flex-1 text-sm text-slate-300 truncate">{f.name}</span>
              <span className="text-xs text-slate-600 flex-shrink-0">{(f.size / 1024).toFixed(0)} KB</span>
              <button
                type="button"
                onClick={() => remove(i)}
                className="flex h-5 w-5 items-center justify-center rounded-full hover:bg-white/10 transition-colors"
              >
                <X className="h-3.5 w-3.5 text-slate-500 hover:text-slate-300" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* What to upload hints */}
      <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4">
        <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3">What to upload per regulation</p>
        <div className="grid sm:grid-cols-2 gap-y-2 gap-x-6">
          {HINTS.map(({ label, examples }) => (
            <div key={label}>
              <span className="text-xs font-semibold text-slate-400">{label}: </span>
              <span className="text-xs text-slate-600">{examples}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
