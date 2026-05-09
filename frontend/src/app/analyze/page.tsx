"use client";

import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { StepIndicator } from "@/components/profile-form/step-indicator";
import { Step1Company } from "@/components/profile-form/step1-company";
import { Step2Financials } from "@/components/profile-form/step2-financials";
import { Step3Data } from "@/components/profile-form/step3-data";
import { Step4SupplyEnergy } from "@/components/profile-form/step4-supply-energy";
import { Step5Governance } from "@/components/profile-form/step5-governance";
import { Step6Documents } from "@/components/profile-form/step6-documents";
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
  company_name:                 z.string().min(1, "Company name is required"),
  industry:                     z.string().min(1, "Industry is required"),
  country:                      z.string().optional(),
  employee_count:               z.preprocess(
    (v) => (v === "" ? undefined : Number(v)),
    z.number().int().min(1, "Must be at least 1")
  ),
  annual_revenue_eur:           optNum("Revenue"),
  balance_sheet_total_eur:      optNum("Balance sheet total"),
  processes_personal_data:      z.boolean().optional(),
  processes_special_category_data: z.boolean().optional(),
  processing_is_occasional:     z.boolean().optional(),
  has_dpo:                      z.boolean().optional(),
  has_processing_records:       z.boolean().optional(),
  has_supply_chain_abroad:      z.boolean().optional(),
  supply_chain_countries_raw:   z.string().optional(),
  annual_energy_consumption_mwh: optNum("Energy consumption"),
  has_energy_management_system: z.boolean().optional(),
  has_conducted_energy_audit:   z.boolean().optional(),
  is_listed_company:                  z.boolean().optional(),
  has_sustainability_report:          z.boolean().optional(),
  is_critical_infrastructure_sector: z.boolean().optional(),
  uses_ai_systems:                    z.boolean().optional(),
  existing_compliance_notes:          z.string().optional(),
});

export type ProfileFormData = z.infer<typeof schema>;

const STEP_LABELS = ["Company", "Financials", "Data", "Supply & Energy", "Governance", "Documents"];

const STEP_FIELDS: (keyof ProfileFormData)[][] = [
  ["company_name", "industry", "employee_count"],
  [], [], [], [],
];

function toProfile(data: ProfileFormData): CompanyProfile {
  return {
    company_name:      data.company_name,
    industry:          data.industry as CompanyProfile["industry"],
    country:           data.country || undefined,
    employee_count:    data.employee_count as number,
    annual_revenue_eur:        data.annual_revenue_eur,
    balance_sheet_total_eur:   data.balance_sheet_total_eur,
    processes_personal_data:   data.processes_personal_data ?? false,
    processes_special_category_data: data.processes_special_category_data,
    processing_is_occasional:  data.processing_is_occasional,
    has_dpo:                   data.has_dpo,
    has_processing_records:    data.has_processing_records,
    has_supply_chain_abroad:   data.has_supply_chain_abroad,
    supply_chain_countries:    data.supply_chain_countries_raw
      ? data.supply_chain_countries_raw.split(",").map((s) => s.trim()).filter(Boolean)
      : undefined,
    annual_energy_consumption_mwh: data.annual_energy_consumption_mwh,
    has_energy_management_system:  data.has_energy_management_system,
    has_conducted_energy_audit:    data.has_conducted_energy_audit,
    is_listed_company:                  data.is_listed_company,
    has_sustainability_report:          data.has_sustainability_report,
    is_critical_infrastructure_sector: data.is_critical_infrastructure_sector ?? false,
    uses_ai_systems:                    data.uses_ai_systems ?? false,
    existing_compliance_notes:          data.existing_compliance_notes || undefined,
  };
}

const STEP_TITLES = ["Company", "Financials", "Data Protection", "Supply Chain & Energy", "Governance", "Documents"];

export default function AnalyzePage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [files, setFiles] = useState<File[]>([]);
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
    const valid  = fields.length === 0 || (await form.trigger(fields));
    if (valid) setStep((s) => s + 1);
  };

  const onSubmit = form.handleSubmit(async (data) => {
    setSubmitError(null);
    try {
      let docSessionId: string | undefined;
      if (files.length > 0) {
        const { doc_session_id } = await api.uploadDocuments(files);
        docSessionId = doc_session_id;
      }
      const { job_id } = await api.analyze(toProfile(data), docSessionId);
      sessionStorage.setItem("kmu_job_id", job_id);
      router.push(`/analyze/processing?jobId=${job_id}`);
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : "Submission failed");
    }
  });

  return (
    <div className="min-h-[calc(100vh-64px)] bg-dark-950">
      {/* Page header */}
      <div className="border-b border-white/[0.06] bg-dark-900/60 px-6 py-6">
        <div className="mx-auto max-w-2xl flex flex-col items-center gap-5">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y:  0 }}
            transition={{ duration: 0.4 }}
            className="text-center"
          >
            <h1 className="text-xl font-bold text-white tracking-tight">Company Profile</h1>
            <p className="text-sm text-slate-500 mt-1">Step {step} of 5: {STEP_TITLES[step - 1]}</p>
          </motion.div>
          <StepIndicator steps={STEP_LABELS} current={step} />
        </div>
      </div>

      <main className="mx-auto max-w-2xl px-6 py-8">
        <AnimatePresence mode="wait">
          <motion.div
            key={step}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0  }}
            exit={{    opacity: 0, x: -20 }}
            transition={{ duration: 0.25, ease: [0.21, 0.47, 0.32, 0.98] }}
          >
            <Card className="shadow-card-dark">
              <CardContent className="py-7">
                <form onSubmit={onSubmit}>
                  {step === 1 && <Step1Company      form={form} />}
                  {step === 2 && <Step2Financials   form={form} />}
                  {step === 3 && <Step3Data         form={form} />}
                  {step === 4 && <Step4SupplyEnergy form={form} />}
                  {step === 5 && <Step5Governance   form={form} />}
                  {step === 6 && <Step6Documents    files={files} onChange={setFiles} />}

                  {submitError && (
                    <div className="mt-5 rounded-xl bg-red-500/10 border border-red-500/25 px-4 py-3 text-sm text-red-400">
                      {submitError}
                    </div>
                  )}

                  <div className="mt-7 flex justify-between items-center pt-5 border-t border-white/[0.06]">
                    {step > 1 ? (
                      <Button type="button" variant="outline" onClick={() => setStep((s) => s - 1)}>
                        ← Back
                      </Button>
                    ) : (
                      <div />
                    )}
                    {step < 6 ? (
                      <Button type="button" onClick={advance} size="md">
                        Continue →
                      </Button>
                    ) : (
                      <Button type="submit" size="md" disabled={form.formState.isSubmitting}>
                        {form.formState.isSubmitting
                          ? files.length > 0 ? "Uploading docs…" : "Submitting…"
                          : files.length > 0
                            ? `Run screening with ${files.length} doc${files.length !== 1 ? "s" : ""} →`
                            : "Run screening →"}
                      </Button>
                    )}
                  </div>
                </form>
              </CardContent>
            </Card>
          </motion.div>
        </AnimatePresence>
      </main>
    </div>
  );
}
