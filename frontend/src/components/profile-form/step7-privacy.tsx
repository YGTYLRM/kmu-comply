"use client";

import { Controller, UseFormReturn } from "react-hook-form";
import { BoolField } from "./bool-field";
import type { ProfileFormData } from "@/app/analyze/page";

interface Props { form: UseFormReturn<ProfileFormData> }

export function Step7Privacy({ form }: Props) {
  const { control } = form;

  return (
    <div className="flex flex-col gap-5">
      <p className="text-sm text-slate-500">
        These questions map directly to GDPR Art. 13, 28, 32, 33 and BDSG requirements. Each yes/no allows a concrete assessment.
      </p>

      <Controller control={control} name="has_privacy_policy" render={({ field }) => (
        <BoolField
          label="Does the company have a published privacy policy?"
          hint="Datenschutzerklärung accessible to data subjects — required by Art. 13/14 GDPR."
          value={field.value} onChange={field.onChange}
        />
      )} />

      <Controller control={control} name="has_processor_agreements" render={({ field }) => (
        <BoolField
          label="Are data processing agreements in place with all vendors?"
          hint="AVV contracts required with every third party that processes personal data on your behalf — Art. 28 GDPR."
          value={field.value} onChange={field.onChange}
        />
      )} />

      <Controller control={control} name="has_data_breach_procedure" render={({ field }) => (
        <BoolField
          label="Is there a documented data breach response procedure?"
          hint="Must include detection, internal escalation, and 72-hour notification to supervisory authority — Art. 33 GDPR."
          value={field.value} onChange={field.onChange}
        />
      )} />

      <Controller control={control} name="has_tom_documentation" render={({ field }) => (
        <BoolField
          label="Are technical and organisational security measures (TOMs) documented?"
          hint="Written record of measures taken to protect personal data — Art. 32 GDPR."
          value={field.value} onChange={field.onChange}
        />
      )} />

      <Controller control={control} name="has_data_retention_policy" render={({ field }) => (
        <BoolField
          label="Is there a documented data retention and deletion policy?"
          hint="Personal data must not be kept longer than necessary — Art. 5(1)(e) GDPR storage limitation principle."
          value={field.value} onChange={field.onChange}
        />
      )} />

      <Controller control={control} name="has_data_protection_training" render={({ field }) => (
        <BoolField
          label="Do employees who handle personal data receive regular data protection training?"
          hint="Employees acting under the controller's authority must be trained — Art. 29 and Art. 32(4) GDPR."
          value={field.value} onChange={field.onChange}
        />
      )} />

      <Controller control={control} name="transfers_data_outside_eea" render={({ field }) => (
        <BoolField
          label="Does the company transfer personal data outside the EEA?"
          hint="Transfers to non-adequate countries require SCCs or other Art. 46 GDPR safeguards."
          value={field.value} onChange={field.onChange}
        />
      )} />

      <Controller control={control} name="has_consent_management" render={({ field }) => (
        <BoolField
          label="Is consent properly obtained and documented where required?"
          hint="Applies to cookies, marketing emails, non-essential data processing — Art. 6/7 GDPR."
          value={field.value} onChange={field.onChange}
        />
      )} />
    </div>
  );
}
