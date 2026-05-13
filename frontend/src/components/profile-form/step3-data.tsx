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
        Data processing determines GDPR / DSGVO and BDSG applicability.
      </p>
      <Controller
        control={control}
        name="processes_personal_data"
        render={({ field }) => (
          <BoolField
            label="Does the company process personal data?"
            hint="Customer records, employee data, user accounts, etc."
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
                label="Does it process special category data?"
                hint="Health, biometric, racial/ethnic origin, religious beliefs, etc. (Art. 9 GDPR)"
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
                label="Is processing only occasional?"
                hint="Not core business. Infrequent, limited scope."
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
                label="Does the company have a Data Protection Officer?"
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
                label="Are Records of Processing Activities (RoPA) maintained?"
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
