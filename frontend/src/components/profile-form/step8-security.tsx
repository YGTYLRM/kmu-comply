"use client";

import { Controller, UseFormReturn, useWatch } from "react-hook-form";
import { BoolField } from "./bool-field";
import type { ProfileFormData } from "@/app/analyze/page";

interface Props { form: UseFormReturn<ProfileFormData> }

export function Step8Security({ form }: Props) {
  const { control } = form;
  const usesAI = useWatch({ control, name: "uses_ai_systems" });

  return (
    <div className="flex flex-col gap-5">
      <p className="text-sm text-slate-500">
        NIS2 applies to companies in critical/important sectors. EU AI Act applies to all companies that deploy AI systems. Answer what is applicable.
      </p>

      <div className="flex flex-col gap-4">
        <p className="text-xs font-bold uppercase tracking-widest text-slate-500">Cybersecurity — NIS2 Art. 21</p>

        <Controller control={control} name="has_information_security_policy" render={({ field }) => (
          <BoolField
            label="Does the company have a written information security policy?"
            hint="Documents the company's approach to managing information security risks — Art. 21(2)(a) NIS2."
            value={field.value} onChange={field.onChange}
          />
        )} />

        <Controller control={control} name="has_incident_response_plan" render={({ field }) => (
          <BoolField
            label="Is there a documented incident response and handling plan?"
            hint="Must cover detection, analysis, containment, and recovery from cybersecurity incidents — Art. 21(2)(b) NIS2."
            value={field.value} onChange={field.onChange}
          />
        )} />

        <Controller control={control} name="has_business_continuity_plan" render={({ field }) => (
          <BoolField
            label="Does the company have a business continuity and disaster recovery plan?"
            hint="Including backup management and crisis management procedures — Art. 21(2)(c) NIS2."
            value={field.value} onChange={field.onChange}
          />
        )} />

        <Controller control={control} name="has_vulnerability_management" render={({ field }) => (
          <BoolField
            label="Are regular vulnerability scans or penetration tests conducted?"
            hint="Systematic identification and remediation of security weaknesses — Art. 21(2)(e) NIS2."
            value={field.value} onChange={field.onChange}
          />
        )} />

        <Controller control={control} name="has_mfa_implemented" render={({ field }) => (
          <BoolField
            label="Is multi-factor authentication implemented for critical systems and remote access?"
            hint="MFA or continuous authentication for privileged accounts and remote connections — Art. 21(2)(j) NIS2."
            value={field.value} onChange={field.onChange}
          />
        )} />

        <Controller control={control} name="has_supply_chain_security_assessment" render={({ field }) => (
          <BoolField
            label="Are suppliers and service providers assessed for cybersecurity risks?"
            hint="Due diligence on the security practices of vendors with system access — Art. 21(2)(d) NIS2."
            value={field.value} onChange={field.onChange}
          />
        )} />

        <Controller control={control} name="has_security_awareness_training" render={({ field }) => (
          <BoolField
            label="Do employees receive regular cybersecurity awareness training?"
            hint="Basic cyber hygiene training for all staff — Art. 21(2)(g) NIS2."
            value={field.value} onChange={field.onChange}
          />
        )} />
      </div>

      {usesAI && (
        <div className="flex flex-col gap-4 border-t border-white/[0.06] pt-5">
          <p className="text-xs font-bold uppercase tracking-widest text-slate-500">AI Systems — EU AI Act</p>

          <Controller control={control} name="ai_systems_are_high_risk" render={({ field }) => (
            <BoolField
              label="Do any AI systems fall into a high-risk category?"
              hint="High-risk includes: hiring/HR decisions, credit scoring, biometric identification, safety-critical systems — Annex III EU AI Act."
              value={field.value} onChange={field.onChange}
            />
          )} />

          <Controller control={control} name="has_ai_risk_assessment" render={({ field }) => (
            <BoolField
              label="Has a risk assessment been conducted for AI systems in use?"
              hint="Documented iterative risk management process throughout the AI system lifecycle — Art. 9 EU AI Act."
              value={field.value} onChange={field.onChange}
            />
          )} />

          <Controller control={control} name="has_ai_usage_documentation" render={({ field }) => (
            <BoolField
              label="Is use of AI systems documented (purpose, data inputs, decision logic)?"
              hint="Sufficient transparency documentation for deployers to interpret AI output — Art. 13 EU AI Act."
              value={field.value} onChange={field.onChange}
            />
          )} />

          <Controller control={control} name="has_human_oversight_procedure" render={({ field }) => (
            <BoolField
              label="Are human oversight procedures documented and implemented for AI systems?"
              hint="A designated person must be able to monitor, understand, and override AI decisions — Art. 14 EU AI Act."
              value={field.value} onChange={field.onChange}
            />
          )} />
        </div>
      )}
    </div>
  );
}
