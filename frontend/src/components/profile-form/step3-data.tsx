"use client";

import { Controller, UseFormReturn, useWatch } from "react-hook-form";
import { BoolField } from "./bool-field";
import type { ProfileFormData } from "@/app/analyze/page";

interface Props {
  form: UseFormReturn<ProfileFormData>;
}

export function Step3Data({ form }: Props) {
  const { control, formState: { errors } } = form;
  const processesPersonal = useWatch({ control, name: "processes_personal_data" });

  return (
    <div className="flex flex-col gap-5">
      <p className="text-sm text-slate-500">
        Die Verarbeitung personenbezogener Daten bestimmt die Anwendbarkeit der DSGVO und des BDSG.
      </p>
      <Controller
        control={control}
        name="processes_personal_data"
        render={({ field }) => (
          <BoolField
            label="Verarbeitet das Unternehmen personenbezogene Daten?"
            hint="Kundendaten, Mitarbeiterdaten, Nutzerkonten usw."
            value={field.value}
            onChange={field.onChange}
            error={errors.processes_personal_data?.message}
          />
        )}
      />
      {processesPersonal && (
        <>
          <Controller
            control={control}
            name="processes_special_category_data"
            render={({ field }) => (
              <BoolField
                label="Werden besondere Kategorien personenbezogener Daten verarbeitet?"
                hint="Gesundheitsdaten, biometrische Daten, Herkunft, religiöse Überzeugungen usw. (Art. 9 DSGVO)"
                value={field.value}
                onChange={field.onChange}
              />
            )}
          />
          <Controller
            control={control}
            name="processing_is_occasional"
            render={({ field }) => (
              <BoolField
                label="Erfolgt die Verarbeitung nur gelegentlich?"
                hint="Nicht Kerngeschäft. Unregelmäßig, geringer Umfang."
                value={field.value}
                onChange={field.onChange}
              />
            )}
          />
          <Controller
            control={control}
            name="has_dpo"
            render={({ field }) => (
              <BoolField
                label="Hat das Unternehmen einen Datenschutzbeauftragten (DSB)?"
                value={field.value}
                onChange={field.onChange}
              />
            )}
          />
          <Controller
            control={control}
            name="has_processing_records"
            render={({ field }) => (
              <BoolField
                label="Wird ein Verzeichnis von Verarbeitungstätigkeiten (VVT) geführt?"
                value={field.value}
                onChange={field.onChange}
              />
            )}
          />
        </>
      )}
    </div>
  );
}
