"use client";

import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useState } from "react";
import { StepIndicator } from "@/components/profile-form/step-indicator";
import { Step1Company } from "@/components/profile-form/step1-company";
import { Step2Financials } from "@/components/profile-form/step2-financials";
import { Step3Data } from "@/components/profile-form/step3-data";
import { Step4SupplyEnergy } from "@/components/profile-form/step4-supply-energy";
import { Step5Governance } from "@/components/profile-form/step5-governance";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { api } from "@/lib/api";
import type { CompanyProfile } from "@/lib/types";

const optNum = (label: string) =>
  z.preprocess(
    (v) => (v === "" || v === undefined || v === null ? undefined : Number(v)),
    z.number().positive(`${label} must be positive`).optional()
  );

const schema = z.object({
  company_name: z.string().min(1, "Company name is required"),
  industry: z.string().min(1, "Industry is required"),
  country: z.string().optional(),
  employee_count: z.preprocess(
    (v) => (v === "" ? undefined : Number(v)),
    z.number().int().min(1, "Must be at least 1")
  ),
  annual_revenue_eur: optNum("Revenue"),
  balance_sheet_total_eur: optNum("Balance sheet total"),
  processes_personal_data: z.boolean().optional(),
  processes_special_category_data: z.boolean().optional(),
  processing_is_occasional: z.boolean().optional(),
  has_dpo: z.boolean().optional(),
  has_processing_records: z.boolean().optional(),
  has_supply_chain_abroad: z.boolean().optional(),
  supply_chain_countries_raw: z.string().optional(),
  annual_energy_consumption_mwh: optNum("Energy consumption"),
  has_energy_management_system: z.boolean().optional(),
  has_conducted_energy_audit: z.boolean().optional(),
  is_listed_company: z.boolean().optional(),
  has_sustainability_report: z.boolean().optional(),
  existing_compliance_notes: z.string().optional(),
});

export type ProfileFormData = z.infer<typeof schema>;

const STEP_LABELS = ["Company", "Financials", "Data", "Supply & Energy", "Governance"];

const STEP_FIELDS: (keyof ProfileFormData)[][] = [
  ["company_name", "industry", "employee_count"],
  [],
  [],
  [],
  [],
];

function toProfile(data: ProfileFormData): CompanyProfile {
  return {
    company_name: data.company_name,
    industry: data.industry as CompanyProfile["industry"],
    country: data.country || undefined,
    employee_count: data.employee_count as number,
    annual_revenue_eur: data.annual_revenue_eur,
    balance_sheet_total_eur: data.balance_sheet_total_eur,
    processes_personal_data: data.processes_personal_data ?? false,
    processes_special_category_data: data.processes_special_category_data,
    processing_is_occasional: data.processing_is_occasional,
    has_dpo: data.has_dpo,
    has_processing_records: data.has_processing_records,
    has_supply_chain_abroad: data.has_supply_chain_abroad,
    supply_chain_countries: data.supply_chain_countries_raw
      ? data.supply_chain_countries_raw.split(",").map((s) => s.trim()).filter(Boolean)
      : undefined,
    annual_energy_consumption_mwh: data.annual_energy_consumption_mwh,
    has_energy_management_system: data.has_energy_management_system,
    has_conducted_energy_audit: data.has_conducted_energy_audit,
    is_listed_company: data.is_listed_company,
    has_sustainability_report: data.has_sustainability_report,
    existing_compliance_notes: data.existing_compliance_notes || undefined,
  };
}

export default function AnalyzePage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const form = useForm<ProfileFormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      company_name: "",
      industry: "",
      country: "",
      processes_personal_data: undefined,
    },
  });

  const advance = async () => {
    const fields = STEP_FIELDS[step - 1];
    const valid = fields.length === 0 || (await form.trigger(fields));
    if (valid) setStep((s) => s + 1);
  };

  const onSubmit = form.handleSubmit(async (data) => {
    setSubmitError(null);
    try {
      const { job_id } = await api.analyze(toProfile(data));
      sessionStorage.setItem("kmu_job_id", job_id);
      router.push(`/analyze/processing?jobId=${job_id}`);
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : "Submission failed");
    }
  });

  return (
    <main className="mx-auto max-w-2xl px-6 py-12">
      <div className="mb-8 flex flex-col items-center gap-4">
        <h1 className="text-2xl font-bold text-slate-900">Company Profile</h1>
        <StepIndicator steps={STEP_LABELS} current={step} />
      </div>

      <Card>
        <CardContent className="py-6">
          <form onSubmit={onSubmit}>
            {step === 1 && <Step1Company form={form} />}
            {step === 2 && <Step2Financials form={form} />}
            {step === 3 && <Step3Data form={form} />}
            {step === 4 && <Step4SupplyEnergy form={form} />}
            {step === 5 && <Step5Governance form={form} />}

            {submitError && (
              <p className="mt-4 rounded-lg bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
                {submitError}
              </p>
            )}

            <div className="mt-6 flex justify-between">
              {step > 1 ? (
                <Button type="button" variant="outline" onClick={() => setStep((s) => s - 1)}>
                  Back
                </Button>
              ) : (
                <div />
              )}
              {step < 5 ? (
                <Button type="button" onClick={advance}>
                  Next
                </Button>
              ) : (
                <Button type="submit" disabled={form.formState.isSubmitting}>
                  {form.formState.isSubmitting ? "Submitting…" : "Run analysis"}
                </Button>
              )}
            </div>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
