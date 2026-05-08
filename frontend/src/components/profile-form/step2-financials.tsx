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
        Financial figures help determine applicability of CSRD, EnEfG, and LkSG. Leave blank if unknown.
      </p>
      <Input
        label="Annual revenue (EUR)"
        type="number"
        min={0}
        placeholder="5000000"
        hint="Used for CSRD and LkSG threshold checks"
        error={errors.annual_revenue_eur?.message}
        {...register("annual_revenue_eur")}
      />
      <Input
        label="Balance sheet total (EUR)"
        type="number"
        min={0}
        placeholder="3000000"
        hint="Used for CSRD threshold checks"
        error={errors.balance_sheet_total_eur?.message}
        {...register("balance_sheet_total_eur")}
      />
    </div>
  );
}
