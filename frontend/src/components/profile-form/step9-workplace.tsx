"use client";

import { Controller, UseFormReturn, useWatch } from "react-hook-form";
import { BoolField } from "./bool-field";
import type { ProfileFormData } from "@/app/analyze/page";

interface Props { form: UseFormReturn<ProfileFormData> }

export function Step9Workplace({ form }: Props) {
  const { control } = form;
  const hasSupplyChain = useWatch({ control, name: "has_supply_chain_abroad" });
  const employeeCount  = useWatch({ control, name: "employee_count" });
  const needsHinSchG   = Number(employeeCount) >= 50;

  return (
    <div className="flex flex-col gap-5">
      <p className="text-sm text-slate-500">
        These obligations apply to all employers in Germany regardless of size or sector.
      </p>

      {/* ArbSchG */}
      <div className="flex flex-col gap-4">
        <p className="text-xs font-bold uppercase tracking-widest text-slate-500">Occupational Safety — ArbSchG</p>

        <Controller control={control} name="has_gefaehrdungsbeurteilung" render={({ field }) => (
          <BoolField
            label="Has a workplace hazard assessment (Gefährdungsbeurteilung) been conducted?"
            hint="Mandatory for every employer regardless of size. Must assess hazards for each type of work activity — §5 ArbSchG."
            value={field.value} onChange={field.onChange}
          />
        )} />

        <Controller control={control} name="has_gefaehrdungsbeurteilung_documented" render={({ field }) => (
          <BoolField
            label="Is the hazard assessment documented in writing?"
            hint="Results, measures taken, and effectiveness review must be recorded — §6 ArbSchG."
            value={field.value} onChange={field.onChange}
          />
        )} />

        <Controller control={control} name="has_first_aid_measures" render={({ field }) => (
          <BoolField
            label="Are first aid measures and designated first aiders in place?"
            hint="Adequate first aid personnel and equipment required for company size — §10 ArbSchG."
            value={field.value} onChange={field.onChange}
          />
        )} />

        <Controller control={control} name="has_employee_safety_training" render={({ field }) => (
          <BoolField
            label="Do employees receive documented safety instructions at onboarding and regularly thereafter?"
            hint="Instructions must be role-specific, in a comprehensible language, and repeated at regular intervals — §12 ArbSchG."
            value={field.value} onChange={field.onChange}
          />
        )} />
      </div>

      {/* AGG */}
      <div className="flex flex-col gap-4 border-t border-white/[0.06] pt-5">
        <p className="text-xs font-bold uppercase tracking-widest text-slate-500">Equal Treatment — AGG</p>

        <Controller control={control} name="has_anti_discrimination_policy" render={({ field }) => (
          <BoolField
            label="Are preventive anti-discrimination measures in place?"
            hint="Includes displaying AGG text, awareness training, and preventive measures — §12 AGG. Required of all employers."
            value={field.value} onChange={field.onChange}
          />
        )} />

        <Controller control={control} name="has_agc_complaints_procedure" render={({ field }) => (
          <BoolField
            label="Is there a formal complaints procedure for discrimination cases?"
            hint="Employees have a statutory right to file complaints; employer must investigate — §13 AGG."
            value={field.value} onChange={field.onChange}
          />
        )} />
      </div>

      {/* MiLoG */}
      <div className="flex flex-col gap-4 border-t border-white/[0.06] pt-5">
        <p className="text-xs font-bold uppercase tracking-widest text-slate-500">Minimum Wage — MiLoG</p>

        <Controller control={control} name="has_working_time_records" render={({ field }) => (
          <BoolField
            label="Are working time records maintained for all employees in covered sectors?"
            hint="Beginning, end, and duration of daily working hours must be recorded within 7 days for mini-jobbers and employees in specific sectors — §17 MiLoG."
            value={field.value} onChange={field.onChange}
          />
        )} />

        <Controller control={control} name="uses_subcontractors" render={({ field }) => (
          <BoolField
            label="Does the company use subcontractors or external service providers who supply labour?"
            hint="Principal contractors are jointly liable for subcontractors failing to pay minimum wage — §13 MiLoG."
            value={field.value} onChange={field.onChange}
          />
        )} />
      </div>

      {/* HinSchG — only ≥50 employees */}
      {needsHinSchG && (
        <div className="flex flex-col gap-4 border-t border-white/[0.06] pt-5">
          <p className="text-xs font-bold uppercase tracking-widest text-slate-500">Whistleblower Protection — HinSchG</p>
          <p className="text-xs text-slate-600">Mandatory for employers with 50 or more employees.</p>

          <Controller control={control} name="has_whistleblower_channel" render={({ field }) => (
            <BoolField
              label="Does the company have an internal whistleblower reporting channel?"
              hint="Must allow written and oral reporting; identity of reporter must be kept confidential — §12/§13 HinSchG."
              value={field.value} onChange={field.onChange}
            />
          )} />

          <Controller control={control} name="has_whistleblower_policy" render={({ field }) => (
            <BoolField
              label="Is there a documented whistleblower protection policy?"
              hint="Describes the reporting process, confidentiality protections, and anti-retaliation guarantees — §13 HinSchG."
              value={field.value} onChange={field.onChange}
            />
          )} />
        </div>
      )}

      {/* LkSG extras — only if supply chain abroad */}
      {hasSupplyChain && (
        <div className="flex flex-col gap-4 border-t border-white/[0.06] pt-5">
          <p className="text-xs font-bold uppercase tracking-widest text-slate-500">Supply Chain Due Diligence — LkSG</p>

          <Controller control={control} name="has_lksg_policy_statement" render={({ field }) => (
            <BoolField
              label="Has the company published an LkSG policy statement (Grundsatzerklärung)?"
              hint="Annual public commitment to human rights and environmental due diligence — §6 LkSG."
              value={field.value} onChange={field.onChange}
            />
          )} />

          <Controller control={control} name="has_supplier_code_of_conduct" render={({ field }) => (
            <BoolField
              label="Does the company have a supplier code of conduct covering human rights and environmental standards?"
              hint="Contractual basis for communicating due diligence expectations to suppliers — §6 LkSG."
              value={field.value} onChange={field.onChange}
            />
          )} />

          <Controller control={control} name="has_supplier_risk_assessment" render={({ field }) => (
            <BoolField
              label="Is a formal risk assessment of direct suppliers conducted at least annually?"
              hint="Assessment of probability and severity of human rights and environmental violations in supply chain — §5 LkSG."
              value={field.value} onChange={field.onChange}
            />
          )} />

          <Controller control={control} name="has_lksg_complaints_procedure" render={({ field }) => (
            <BoolField
              label="Has an LkSG-compliant complaints mechanism been established?"
              hint="Must allow employees and affected third parties to report violations; must be accessible and confidential — §8 LkSG."
              value={field.value} onChange={field.onChange}
            />
          )} />
        </div>
      )}
    </div>
  );
}
