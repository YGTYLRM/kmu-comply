"use client";

import { Controller, UseFormReturn, useWatch } from "react-hook-form";
import { Input } from "@/components/ui/input";
import { BoolField } from "./bool-field";
import type { ProfileFormData } from "@/app/analyze/page";

interface Props {
  form: UseFormReturn<ProfileFormData>;
}

export function Step4SupplyEnergy({ form }: Props) {
  const { register, control, formState: { errors } } = form;
  const hasSupplyChainAbroad = useWatch({ control, name: "has_supply_chain_abroad" });

  return (
    <div className="flex flex-col gap-5">
      <p className="text-sm text-slate-500">
        Supply chain reach determines LkSG applicability. Energy data feeds EnEfG checks.
      </p>
      <Controller
        control={control}
        name="has_supply_chain_abroad"
        render={({ field }) => (
          <BoolField
            label="Does the company have suppliers abroad?"
            value={field.value}
            onChange={field.onChange}
          />
        )}
      />
      {hasSupplyChainAbroad && (
        <Input
          label="Supply chain countries"
          placeholder="China, India, Vietnam"
          hint="Comma-separated list of countries"
          {...register("supply_chain_countries_raw")}
        />
      )}
      <Input
        label="Annual energy consumption (MWh)"
        type="number"
        min={0}
        placeholder="7500"
        hint="Required for EnEfG. Leave blank if unknown."
        error={errors.annual_energy_consumption_mwh?.message}
        {...register("annual_energy_consumption_mwh")}
      />
      <Controller
        control={control}
        name="has_energy_management_system"
        render={({ field }) => (
          <BoolField
            label="Does the company have an energy management system (ISO 50001)?"
            value={field.value}
            onChange={field.onChange}
          />
        )}
      />
      <Controller
        control={control}
        name="has_conducted_energy_audit"
        render={({ field }) => (
          <BoolField
            label="Has an energy audit (DIN EN 16247) been conducted?"
            value={field.value}
            onChange={field.onChange}
          />
        )}
      />
    </div>
  );
}
