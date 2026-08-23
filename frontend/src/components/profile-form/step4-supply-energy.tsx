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
        Die internationale Lieferkette bestimmt die LkSG-Pflichten. Energiedaten werden für die EnEfG-Prüfung benötigt.
      </p>
      <Controller
        control={control}
        name="has_supply_chain_abroad"
        render={({ field }) => (
          <BoolField
            label="Hat das Unternehmen Lieferanten im Ausland?"
            value={field.value}
            onChange={field.onChange}
          />
        )}
      />
      {hasSupplyChainAbroad && (
        <Input
          label="Lieferantenländer"
          placeholder="China, Indien, Vietnam"
          hint="Kommagetrennte Liste der Länder"
          {...register("supply_chain_countries_raw")}
        />
      )}
      <Input
        label="Jährlicher Energieverbrauch (MWh)"
        type="number"
        min={0}
        placeholder="7500"
        hint="Erforderlich für EnEfG. Leer lassen, falls unbekannt."
        error={errors.annual_energy_consumption_mwh?.message}
        {...register("annual_energy_consumption_mwh")}
      />
      <Controller
        control={control}
        name="has_energy_management_system"
        render={({ field }) => (
          <BoolField
            label="Hat das Unternehmen ein Energiemanagementsystem (ISO 50001)?"
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
            label="Wurde ein Energieaudit (DIN EN 16247) durchgeführt?"
            value={field.value}
            onChange={field.onChange}
          />
        )}
      />
    </div>
  );
}
