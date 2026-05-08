"use client";

import { cn } from "@/lib/utils";

interface BoolFieldProps {
  label: string;
  hint?: string;
  value: boolean | undefined;
  onChange: (v: boolean) => void;
  error?: string;
}

export function BoolField({ label, hint, value, onChange, error }: BoolFieldProps) {
  return (
    <div className="flex flex-col gap-2">
      <label className="text-sm font-semibold text-slate-300">{label}</label>
      {hint && <p className="text-xs text-slate-600 leading-relaxed">{hint}</p>}
      <div className="flex gap-2">
        {([true, false] as const).map((opt) => (
          <button
            key={String(opt)}
            type="button"
            onClick={() => onChange(opt)}
            className={cn(
              "flex items-center gap-2 rounded-xl border px-5 py-2.5 text-sm font-semibold transition-all duration-200",
              value === opt
                ? "border-brand-500/50 bg-brand-600 text-white shadow-glow-blue-sm"
                : "border-white/10 bg-white/5 text-slate-400 hover:border-white/20 hover:bg-white/8 hover:text-slate-200"
            )}
          >
            <span
              className={cn(
                "h-4 w-4 rounded-full border-2 flex items-center justify-center flex-shrink-0",
                value === opt ? "border-white/60" : "border-slate-600"
              )}
            >
              {value === opt && <span className="h-2 w-2 rounded-full bg-white" />}
            </span>
            {opt ? "Yes" : "No"}
          </button>
        ))}
      </div>
      {error && <p className="text-xs text-red-400">{error}</p>}
    </div>
  );
}
