"use client";

import { Controller, UseFormReturn } from "react-hook-form";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import type { ProfileFormData } from "@/app/analyze/page";

const INDUSTRIES = [
  { value: "it_software",   label: "IT / Software" },
  { value: "manufacturing", label: "Herstellung / Produktion" },
  { value: "healthcare",    label: "Gesundheitswesen" },
  { value: "retail",        label: "Einzelhandel" },
  { value: "finance",       label: "Finanzen / Versicherungen" },
  { value: "logistics",     label: "Logistik / Transport" },
  { value: "construction",  label: "Baugewerbe" },
  { value: "energy",        label: "Energie / Versorgung" },
  { value: "food_beverage", label: "Lebensmittel & Getränke" },
  { value: "consulting",    label: "Beratung" },
  { value: "real_estate",   label: "Immobilien" },
  { value: "chemicals",     label: "Chemie / Pharma" },
  { value: "transport",     label: "Transport / Verkehr" },
  { value: "water",         label: "Wasser & Ver-/Entsorgung" },
  { value: "digital",       label: "Digitale Dienste" },
  { value: "government",    label: "Öffentlicher Sektor / Verwaltung" },
  { value: "space",         label: "Luft- und Raumfahrt" },
  { value: "waste",         label: "Entsorgung / Recycling" },
  { value: "research",      label: "Forschung & Bildung" },
  { value: "gambling",      label: "Glücksspiel" },
  { value: "crypto",        label: "Krypto / Blockchain" },
  { value: "other",         label: "Sonstige" },
];

interface Props {
  form: UseFormReturn<ProfileFormData>;
}

export function Step1Company({ form }: Props) {
  const { register, control, formState: { errors } } = form;
  return (
    <div className="flex flex-col gap-5">
      <div className="rounded-lg border border-amber-500/20 bg-amber-500/[0.05] px-4 py-3">
        <p className="text-xs text-amber-400/80 font-semibold uppercase tracking-widest mb-1">Vorläufiges Screening, keine Rechtsberatung</p>
        <p className="text-xs text-slate-500 leading-relaxed">
          Dieses Tool liefert ausschließlich eine automatisierte Ersteinschätzung. Die Ergebnisse stellen keine Rechtsberatung dar und sollten vor Maßnahmen durch einen qualifizierten Rechtsanwalt geprüft werden.
        </p>
      </div>
      <Input
        label="Unternehmensname"
        required
        placeholder="Muster GmbH"
        error={errors.company_name?.message}
        {...register("company_name")}
      />
      <Controller
        control={control}
        name="industry"
        render={({ field }) => (
          <Select
            label="Branche"
            required
            options={INDUSTRIES}
            value={field.value}
            onValueChange={field.onChange}
            error={errors.industry?.message}
          />
        )}
      />
      <Input
        label="Land"
        placeholder="Deutschland"
        hint="Leer lassen, wenn Deutschland"
        {...register("country")}
      />
      <Input
        label="Anzahl der Mitarbeiter"
        required
        type="number"
        min={1}
        placeholder="50"
        error={errors.employee_count?.message}
        {...register("employee_count")}
      />
    </div>
  );
}
