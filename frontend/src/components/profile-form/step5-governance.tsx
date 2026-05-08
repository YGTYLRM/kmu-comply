"use client";

import { Controller, UseFormReturn } from "react-hook-form";
import { Input } from "@/components/ui/input";
import { BoolField } from "./bool-field";
import type { ProfileFormData } from "@/app/analyze/page";

interface Props {
  form: UseFormReturn<ProfileFormData>;
}

export function Step5Governance({ form }: Props) {
  const { register, control } = form;
  return (
    <div className="flex flex-col gap-5">
      <p className="text-sm text-slate-500">
        Governance details help determine CSRD applicability and refine the analysis.
      </p>
      <Controller
        control={control}
        name="is_listed_company"
        render={({ field }) => (
          <BoolField
            label="Is the company listed on a stock exchange?"
            value={field.value}
            onChange={field.onChange}
          />
        )}
      />
      <Controller
        control={control}
        name="has_sustainability_report"
        render={({ field }) => (
          <BoolField
            label="Does the company already publish a sustainability report?"
            value={field.value}
            onChange={field.onChange}
          />
        )}
      />
      <div className="flex flex-col gap-1">
        <label className="text-sm font-medium text-slate-700">Existing compliance notes</label>
        <textarea
          rows={4}
          placeholder="Describe any existing compliance measures, certifications, or ongoing initiatives…"
          className="rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 bg-white focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent resize-none"
          {...register("existing_compliance_notes")}
        />
        <p className="text-xs text-slate-500">Optional — helps the AI model provide more accurate gap analysis</p>
      </div>
    </div>
  );
}
