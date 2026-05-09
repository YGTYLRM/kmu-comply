"use client";

import { Controller, UseFormReturn } from "react-hook-form";
import { BoolField } from "./bool-field";
import type { ProfileFormData } from "@/app/analyze/page";

interface Props {
  form: UseFormReturn<ProfileFormData>;
}

export function Step5Governance({ form }: Props) {
  const { register, control } = form;
  return (
    <div className="flex flex-col gap-6">
      <p className="text-sm text-slate-500">
        Governance and technology details help determine CSRD, NIS2, and EU AI Act applicability.
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

      <Controller
        control={control}
        name="is_critical_infrastructure_sector"
        render={({ field }) => (
          <BoolField
            label="Is the company in a critical infrastructure sector?"
            hint="Energy, transport, banking, healthcare, digital infrastructure, water, or public administration. Relevant for NIS2 cybersecurity obligations."
            value={field.value}
            onChange={field.onChange}
          />
        )}
      />

      <Controller
        control={control}
        name="uses_ai_systems"
        render={({ field }) => (
          <BoolField
            label="Does the company develop or deploy AI systems?"
            hint="Includes AI tools used for HR decisions, customer interactions, product recommendations, or any automated decision-making. Relevant for EU AI Act."
            value={field.value}
            onChange={field.onChange}
          />
        )}
      />

      <div className="flex flex-col gap-1">
        <label className="text-sm font-medium text-slate-300">Existing compliance notes</label>
        <textarea
          rows={4}
          placeholder="Describe any existing compliance measures, certifications, or ongoing initiatives..."
          className="rounded-lg border border-white/12 bg-white/5 px-3 py-2 text-sm text-white placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-brand-500/70 focus:border-brand-500/50 resize-none transition-all duration-200"
          {...register("existing_compliance_notes")}
        />
        <p className="text-xs text-slate-600">Optional. Helps produce a more accurate screening.</p>
      </div>
    </div>
  );
}
