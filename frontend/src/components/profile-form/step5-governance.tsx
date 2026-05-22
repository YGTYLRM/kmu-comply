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
        Governance- und Technologieangaben bestimmen die Anwendbarkeit von CSRD, NIS2 und dem EU AI Act.
      </p>

      <Controller
        control={control}
        name="is_listed_company"
        render={({ field }) => (
          <BoolField
            label="Ist das Unternehmen börsennotiert?"
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
            label="Veröffentlicht das Unternehmen bereits einen Nachhaltigkeitsbericht?"
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
            label="Ist das Unternehmen in einem Sektor der kritischen Infrastruktur tätig?"
            hint="Energie, Transport, Banken, Gesundheitswesen, digitale Infrastruktur, Wasser oder öffentliche Verwaltung. Relevant für NIS2-Cybersicherheitspflichten."
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
            label="Entwickelt oder betreibt das Unternehmen KI-Systeme?"
            hint="Einschließlich KI-Tools für HR-Entscheidungen, Kundeninteraktion, Produktempfehlungen oder automatisierte Entscheidungsfindung. Relevant für den EU AI Act."
            value={field.value}
            onChange={field.onChange}
          />
        )}
      />

      <div className="flex flex-col gap-1">
        <label className="text-sm font-medium text-slate-300">Bestehende Compliance-Hinweise</label>
        <textarea
          rows={4}
          placeholder="Beschreiben Sie bestehende Compliance-Maßnahmen, Zertifizierungen oder laufende Initiativen…"
          className="rounded-lg border border-white/12 bg-white/5 px-3 py-2 text-sm text-white placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-brand-500/70 focus:border-brand-500/50 resize-none transition-all duration-200"
          {...register("existing_compliance_notes")}
        />
        <p className="text-xs text-slate-600">Optional. Verbessert die Genauigkeit des Screenings.</p>
      </div>
    </div>
  );
}
