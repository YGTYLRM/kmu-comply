"use client";

import { UseFormReturn } from "react-hook-form";
import { Input } from "@/components/ui/input";
import type { ProfileFormData } from "@/app/analyze/page";

interface Props {
  form: UseFormReturn<ProfileFormData>;
}

export function Step2Financials({ form }: Props) {
  const { register, formState: { errors } } = form;
  return (
    <div className="flex flex-col gap-5">
      <p className="text-sm text-slate-500">
        Finanzkennzahlen bestimmen die Anwendbarkeit von CSRD, EnEfG und LkSG. Leer lassen, falls unbekannt.
      </p>
      <Input
        label="Jahresumsatz (EUR)"
        type="number"
        min={0}
        placeholder="5000000"
        hint="Für CSRD- und LkSG-Schwellenprüfungen"
        error={errors.annual_revenue_eur?.message}
        {...register("annual_revenue_eur")}
      />
      <Input
        label="Bilanzsumme (EUR)"
        type="number"
        min={0}
        placeholder="3000000"
        hint="Für CSRD-Schwellenprüfungen"
        error={errors.balance_sheet_total_eur?.message}
        {...register("balance_sheet_total_eur")}
      />
    </div>
  );
}
