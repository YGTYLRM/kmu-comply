"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useState, useEffect, Suspense } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AlertCircle } from "lucide-react";
import { StepIndicator } from "@/components/profile-form/step-indicator";
import { Step1Company } from "@/components/profile-form/step1-company";
import { Step2Financials } from "@/components/profile-form/step2-financials";
import { Step3Data } from "@/components/profile-form/step3-data";
import { Step4SupplyEnergy } from "@/components/profile-form/step4-supply-energy";
import { Step5Governance } from "@/components/profile-form/step5-governance";
import { Step7Privacy } from "@/components/profile-form/step7-privacy";
import { Step8Security } from "@/components/profile-form/step8-security";
import { Step9Workplace } from "@/components/profile-form/step9-workplace";
import { Step6Documents } from "@/components/profile-form/step6-documents";
import { Step10Digital } from "@/components/profile-form/step10-digital";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { api } from "@/lib/api";
import type { CompanyProfile } from "@/lib/types";

const optNum = (label: string) =>
  z.preprocess(
    (v) => (v === "" || v === undefined || v === null ? undefined : Number(v)),
    z.number().positive(`${label} must be positive`).optional()
  );

const optBool = z.boolean().optional();

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
  processes_personal_data:      optBool,
  processes_special_category_data: optBool,
  processing_is_occasional:     optBool,
  has_dpo:                      optBool,
  has_processing_records:       optBool,
  has_supply_chain_abroad:      optBool,
  supply_chain_countries_raw:   z.string().optional(),
  annual_energy_consumption_mwh: optNum("Energy consumption"),
  has_energy_management_system: optBool,
  has_conducted_energy_audit:   optBool,
  is_listed_company:            optBool,
  has_sustainability_report:    optBool,
  is_critical_infrastructure_sector: optBool,
  uses_ai_systems:              optBool,
  // Step 7 — Privacy & Policies
  has_privacy_policy:           optBool,
  has_processor_agreements:     optBool,
  has_data_breach_procedure:    optBool,
  has_tom_documentation:        optBool,
  has_data_retention_policy:    optBool,
  has_data_protection_training: optBool,
  transfers_data_outside_eea:   optBool,
  has_consent_management:       optBool,
  // Step 8 — Security & Technology
  has_information_security_policy:      optBool,
  has_incident_response_plan:           optBool,
  has_business_continuity_plan:         optBool,
  has_vulnerability_management:         optBool,
  has_mfa_implemented:                  optBool,
  has_supply_chain_security_assessment: optBool,
  has_security_awareness_training:      optBool,
  ai_systems_are_high_risk:             optBool,
  has_ai_risk_assessment:               optBool,
  has_ai_usage_documentation:           optBool,
  has_human_oversight_procedure:        optBool,
  // Step 9 — Workplace & HR
  has_gefaehrdungsbeurteilung:           optBool,
  has_gefaehrdungsbeurteilung_documented: optBool,
  has_first_aid_measures:               optBool,
  has_employee_safety_training:         optBool,
  has_anti_discrimination_policy:       optBool,
  has_agc_complaints_procedure:         optBool,
  has_working_time_records:             optBool,
  uses_subcontractors:                  optBool,
  has_whistleblower_channel:            optBool,
  has_whistleblower_policy:             optBool,
  has_lksg_policy_statement:            optBool,
  has_supplier_code_of_conduct:         optBool,
  has_supplier_risk_assessment:         optBool,
  has_lksg_complaints_procedure:        optBool,
  // TTDSG / TDDDG
  has_website:                          optBool,
  has_cookie_banner:                    optBool,
  has_cookie_policy:                    optBool,
  // GwG
  is_aml_obligated_sector:              optBool,
  has_aml_risk_analysis:                optBool,
  has_aml_officer:                      optBool,
  has_kyc_procedures:                   optBool,
  // EU Data Act
  produces_connected_products:          optBool,
  provides_data_processing_services:    optBool,
  has_data_access_mechanism:            optBool,
  existing_compliance_notes:            z.string().optional(),
});

export type ProfileFormData = z.infer<typeof schema>;

const STEP_LABELS = ["Unternehmen", "Finanzen", "Datenschutz", "Lieferkette", "Governance", "Richtlinien", "Sicherheit", "Personal", "Digital", "Dokumente"];

const STEP_FIELDS: (keyof ProfileFormData)[][] = [
  ["company_name", "industry", "employee_count"],
  [], [], [], [], [], [], [], [], [],
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
    is_listed_company:             data.is_listed_company,
    has_sustainability_report:     data.has_sustainability_report,
    is_critical_infrastructure_sector: data.is_critical_infrastructure_sector ?? false,
    uses_ai_systems:               data.uses_ai_systems ?? false,
    // Step 7
    has_privacy_policy:            data.has_privacy_policy,
    has_processor_agreements:      data.has_processor_agreements,
    has_data_breach_procedure:     data.has_data_breach_procedure,
    has_tom_documentation:         data.has_tom_documentation,
    has_data_retention_policy:     data.has_data_retention_policy,
    has_data_protection_training:  data.has_data_protection_training,
    transfers_data_outside_eea:    data.transfers_data_outside_eea,
    has_consent_management:        data.has_consent_management,
    // Step 8
    has_information_security_policy:      data.has_information_security_policy,
    has_incident_response_plan:           data.has_incident_response_plan,
    has_business_continuity_plan:         data.has_business_continuity_plan,
    has_vulnerability_management:         data.has_vulnerability_management,
    has_mfa_implemented:                  data.has_mfa_implemented,
    has_supply_chain_security_assessment: data.has_supply_chain_security_assessment,
    has_security_awareness_training:      data.has_security_awareness_training,
    ai_systems_are_high_risk:             data.ai_systems_are_high_risk,
    has_ai_risk_assessment:               data.has_ai_risk_assessment,
    has_ai_usage_documentation:           data.has_ai_usage_documentation,
    has_human_oversight_procedure:        data.has_human_oversight_procedure,
    // Step 9
    has_gefaehrdungsbeurteilung:            data.has_gefaehrdungsbeurteilung,
    has_gefaehrdungsbeurteilung_documented: data.has_gefaehrdungsbeurteilung_documented,
    has_first_aid_measures:               data.has_first_aid_measures,
    has_employee_safety_training:         data.has_employee_safety_training,
    has_anti_discrimination_policy:       data.has_anti_discrimination_policy,
    has_agc_complaints_procedure:         data.has_agc_complaints_procedure,
    has_working_time_records:             data.has_working_time_records,
    uses_subcontractors:                  data.uses_subcontractors,
    has_whistleblower_channel:            data.has_whistleblower_channel,
    has_whistleblower_policy:             data.has_whistleblower_policy,
    has_lksg_policy_statement:            data.has_lksg_policy_statement,
    has_supplier_code_of_conduct:         data.has_supplier_code_of_conduct,
    has_supplier_risk_assessment:         data.has_supplier_risk_assessment,
    has_lksg_complaints_procedure:        data.has_lksg_complaints_procedure,
    // TTDSG
    has_website:                          data.has_website,
    has_cookie_banner:                    data.has_cookie_banner,
    has_cookie_policy:                    data.has_cookie_policy,
    // GwG
    is_aml_obligated_sector:             data.is_aml_obligated_sector,
    has_aml_risk_analysis:               data.has_aml_risk_analysis,
    has_aml_officer:                     data.has_aml_officer,
    has_kyc_procedures:                  data.has_kyc_procedures,
    // EU Data Act
    produces_connected_products:          data.produces_connected_products,
    provides_data_processing_services:    data.provides_data_processing_services,
    has_data_access_mechanism:            data.has_data_access_mechanism,
    existing_compliance_notes:            data.existing_compliance_notes || undefined,
  };
}

const STEP_TITLES = ["Unternehmen", "Finanzen", "Datenschutz", "Lieferkette & Energie", "Governance", "Datenschutz & Richtlinien", "Sicherheit & Technologie", "Personal & HR", "Digital & AML", "Dokumente"];

function AnalyzeInner() {
  const router       = useRouter();
  const searchParams = useSearchParams();
  const fromJobId    = searchParams.get("from");

  const [step, setStep] = useState(1);
  const [files, setFiles] = useState<File[]>([]);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [prefilling, setPrefilling]   = useState(!!fromJobId);

  const form = useForm<ProfileFormData>({
    resolver: zodResolver(schema),
    defaultValues: {
      company_name: "",
      industry: "",
      country: "",
      processes_personal_data: undefined,
    },
  });

  useEffect(() => {
    if (!fromJobId) return;
    api.getProfile(fromJobId)
      .then((p) => {
        form.reset({
          company_name:                    p.company_name,
          industry:                        p.industry as string,
          country:                         p.country ?? "",
          employee_count:                  p.employee_count,
          annual_revenue_eur:              p.annual_revenue_eur,
          balance_sheet_total_eur:         p.balance_sheet_total_eur,
          processes_personal_data:         p.processes_personal_data,
          processes_special_category_data: p.processes_special_category_data,
          processing_is_occasional:        p.processing_is_occasional,
          has_dpo:                         p.has_dpo,
          has_processing_records:          p.has_processing_records,
          has_supply_chain_abroad:         p.has_supply_chain_abroad,
          supply_chain_countries_raw:      p.supply_chain_countries?.join(", ") ?? "",
          annual_energy_consumption_mwh:   p.annual_energy_consumption_mwh,
          has_energy_management_system:    p.has_energy_management_system,
          has_conducted_energy_audit:      p.has_conducted_energy_audit,
          is_listed_company:               p.is_listed_company,
          has_sustainability_report:       p.has_sustainability_report,
          is_critical_infrastructure_sector: p.is_critical_infrastructure_sector,
          uses_ai_systems:                 p.uses_ai_systems,
          has_privacy_policy:              p.has_privacy_policy,
          has_processor_agreements:        p.has_processor_agreements,
          has_data_breach_procedure:       p.has_data_breach_procedure,
          has_tom_documentation:           p.has_tom_documentation,
          has_data_retention_policy:       p.has_data_retention_policy,
          has_data_protection_training:    p.has_data_protection_training,
          transfers_data_outside_eea:      p.transfers_data_outside_eea,
          has_consent_management:          p.has_consent_management,
          has_information_security_policy:      p.has_information_security_policy,
          has_incident_response_plan:           p.has_incident_response_plan,
          has_business_continuity_plan:         p.has_business_continuity_plan,
          has_vulnerability_management:         p.has_vulnerability_management,
          has_mfa_implemented:                  p.has_mfa_implemented,
          has_supply_chain_security_assessment: p.has_supply_chain_security_assessment,
          has_security_awareness_training:      p.has_security_awareness_training,
          ai_systems_are_high_risk:             p.ai_systems_are_high_risk,
          has_ai_risk_assessment:               p.has_ai_risk_assessment,
          has_ai_usage_documentation:           p.has_ai_usage_documentation,
          has_human_oversight_procedure:        p.has_human_oversight_procedure,
          has_gefaehrdungsbeurteilung:            p.has_gefaehrdungsbeurteilung,
          has_gefaehrdungsbeurteilung_documented: p.has_gefaehrdungsbeurteilung_documented,
          has_first_aid_measures:               p.has_first_aid_measures,
          has_employee_safety_training:         p.has_employee_safety_training,
          has_anti_discrimination_policy:       p.has_anti_discrimination_policy,
          has_agc_complaints_procedure:         p.has_agc_complaints_procedure,
          has_working_time_records:             p.has_working_time_records,
          uses_subcontractors:                  p.uses_subcontractors,
          has_whistleblower_channel:            p.has_whistleblower_channel,
          has_whistleblower_policy:             p.has_whistleblower_policy,
          has_lksg_policy_statement:            p.has_lksg_policy_statement,
          has_supplier_code_of_conduct:         p.has_supplier_code_of_conduct,
          has_supplier_risk_assessment:         p.has_supplier_risk_assessment,
          has_lksg_complaints_procedure:        p.has_lksg_complaints_procedure,
          has_website:                          p.has_website,
          has_cookie_banner:                    p.has_cookie_banner,
          has_cookie_policy:                    p.has_cookie_policy,
          is_aml_obligated_sector:              p.is_aml_obligated_sector,
          has_aml_risk_analysis:                p.has_aml_risk_analysis,
          has_aml_officer:                      p.has_aml_officer,
          has_kyc_procedures:                   p.has_kyc_procedures,
          produces_connected_products:          p.produces_connected_products,
          provides_data_processing_services:    p.provides_data_processing_services,
          has_data_access_mechanism:            p.has_data_access_mechanism,
          existing_compliance_notes:            p.existing_compliance_notes ?? "",
        });
      })
      .catch(() => { /* silently ignore — user can fill manually */ })
      .finally(() => setPrefilling(false));
  }, [fromJobId]); // eslint-disable-line react-hooks/exhaustive-deps

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
      if (fromJobId) sessionStorage.setItem("kmu_prev_job_id", fromJobId);
      else sessionStorage.removeItem("kmu_prev_job_id");
      router.push(`/analyze/processing?jobId=${job_id}`);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Submission failed";
      const isOffline = msg.toLowerCase().includes("fetch") || msg.toLowerCase().includes("network");
      setSubmitError(isOffline
        ? "Server nicht erreichbar. Stellen Sie sicher, dass das Backend läuft, und versuchen Sie es erneut."
        : msg
      );
    }
  });

  return (
    <div className="min-h-screen bg-dark-950 pt-24">
      {/* Page header */}
      <div className="border-b border-white/[0.06] bg-dark-900/60 px-4 sm:px-6 py-6">
        <div className="mx-auto max-w-2xl flex flex-col items-center gap-5">
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y:  0 }}
            transition={{ duration: 0.4 }}
            className="text-center"
          >
            <h1 className="text-xl font-bold text-white tracking-tight">
              {fromJobId ? "Screening wiederholen" : "Unternehmensprofil"}
            </h1>
            <p className="text-sm text-slate-500 mt-1">
              {prefilling ? "Vorheriges Profil wird geladen…" : `Schritt ${step} von 10: ${STEP_TITLES[step - 1]}`}
            </p>
          </motion.div>
          <StepIndicator steps={STEP_LABELS} current={step} />
        </div>
      </div>

      <main className="mx-auto max-w-2xl px-4 sm:px-6 py-8">
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
                  {step === 6 && <Step7Privacy      form={form} />}
                  {step === 7 && <Step8Security     form={form} />}
                  {step === 8 && <Step9Workplace    form={form} />}
                  {step === 9 && <Step10Digital     form={form} />}
                  {step === 10 && <Step6Documents   files={files} onChange={setFiles} />}

                  {submitError && (() => {
                    const isPaywall = submitError.toLowerCase().includes("abonnement") || submitError.toLowerCase().includes("subscription");
                    return isPaywall ? (
                      <div className="mt-5 rounded-xl bg-amber-500/10 border border-amber-500/25 px-4 py-4 flex flex-col gap-3">
                        <div className="flex items-start gap-2">
                          <AlertCircle className="h-4 w-4 text-amber-400 flex-shrink-0 mt-0.5" />
                          <div>
                            <p className="text-sm font-semibold text-amber-300">Abonnement erforderlich</p>
                            <p className="text-xs text-amber-400/70 mt-0.5">
                              Das Compliance-Screening ist nur für aktive Abonnenten verfügbar.
                            </p>
                          </div>
                        </div>
                        <a
                          href="/account/billing"
                          className="self-start rounded-lg bg-amber-500 px-4 py-2 text-xs font-semibold text-black hover:bg-amber-400 transition-colors"
                        >
                          Plan auswählen →
                        </a>
                      </div>
                    ) : (
                      <div className="mt-5 rounded-xl bg-red-500/10 border border-red-500/25 px-4 py-4 flex flex-col gap-2">
                        <div className="flex items-start gap-2">
                          <AlertCircle className="h-4 w-4 text-red-400 flex-shrink-0 mt-0.5" />
                          <p className="text-sm text-red-400">{submitError}</p>
                        </div>
                        <button
                          type="button"
                          onClick={() => setSubmitError(null)}
                          className="self-start text-xs text-red-400/70 hover:text-red-300 underline transition-colors"
                        >
                          Schließen und erneut versuchen
                        </button>
                      </div>
                    );
                  })()}

                  <div className="mt-7 flex justify-between items-center pt-5 border-t border-white/[0.06]">
                    {step > 1 ? (
                      <Button type="button" variant="outline" onClick={() => setStep((s) => s - 1)}>
                        ← Zurück
                      </Button>
                    ) : (
                      <div />
                    )}
                    {step < 10 ? (
                      <Button type="button" onClick={advance} size="md">
                        Weiter →
                      </Button>
                    ) : (
                      <Button type="submit" size="md" disabled={form.formState.isSubmitting}>
                        {form.formState.isSubmitting
                          ? files.length > 0 ? "Dokumente werden hochgeladen…" : "Wird gesendet…"
                          : files.length > 0
                            ? `Screening mit ${files.length} Dok${files.length !== 1 ? "." : "."} starten →`
                            : "Screening starten →"}
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

export default function AnalyzePage() {
  return (
    <Suspense fallback={
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="text-slate-500 text-sm">Wird geladen…</div>
      </div>
    }>
      <AnalyzeInner />
    </Suspense>
  );
}
