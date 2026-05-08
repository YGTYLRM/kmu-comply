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
    <div className="flex flex-col gap-1.5">
      <label className="text-sm font-medium text-slate-700">{label}</label>
      {hint && <p className="text-xs text-slate-500">{hint}</p>}
      <div className="flex gap-2">
        {([true, false] as const).map((opt) => (
          <button
            key={String(opt)}
            type="button"
            onClick={() => onChange(opt)}
            className={cn(
              "rounded-lg border px-4 py-2 text-sm font-medium transition-colors",
              value === opt
                ? "border-brand-600 bg-brand-50 text-brand-700"
                : "border-slate-300 bg-white text-slate-600 hover:bg-slate-50"
            )}
          >
            {opt ? "Yes" : "No"}
          </button>
        ))}
      </div>
      {error && <p className="text-xs text-red-600">{error}</p>}
    </div>
  );
}
