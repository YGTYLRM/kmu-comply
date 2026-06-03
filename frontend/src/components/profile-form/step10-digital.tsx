"use client";

import { Controller, UseFormReturn } from "react-hook-form";
import { BoolField } from "./bool-field";
import type { ProfileFormData } from "@/app/analyze/page";

interface Props { form: UseFormReturn<ProfileFormData> }

export function Step10Digital({ form }: Props) {
  const { control } = form;

  return (
    <div className="flex flex-col gap-5">
      <p className="text-sm text-slate-500">
        Diese Fragen betreffen Cookie-Einwilligung (TTDSG/TDDDG), Geldwäscheprävention (GwG) und Datenzugangspflichten (EU Data Act).
      </p>

      {/* TTDSG / TDDDG */}
      <div className="pt-2 pb-1">
        <p className="text-xs font-bold uppercase tracking-widest text-brand-400">Cookie-Einwilligung (TTDSG / TDDDG)</p>
      </div>

      <Controller control={control} name="has_website" render={({ field }) => (
        <BoolField
          label="Betreibt das Unternehmen eine öffentlich zugängliche Website oder App?"
          hint="Jede für Nutzer in Deutschland zugängliche Website löst Pflichten nach § 25 TTDSG aus."
          value={field.value} onChange={field.onChange}
        />
      )} />

      <Controller control={control} name="has_cookie_banner" render={({ field }) => (
        <BoolField
          label="Ist ein Cookie-Einwilligungsbanner implementiert (Opt-in vor dem Tracking)?"
          hint="§ 25 TDDDG erfordert eine informierte Einwilligung BEVOR nicht notwendige Cookies, Pixel oder Fingerprinting-Skripte gesetzt werden."
          value={field.value} onChange={field.onChange}
        />
      )} />

      <Controller control={control} name="has_cookie_policy" render={({ field }) => (
        <BoolField
          label="Gibt es ein dokumentiertes Cookie-/Tracking-Verzeichnis?"
          hint="Eine veröffentlichte Liste aller verwendeten Cookies und Tracking-Technologien mit Zwecken und Speicherdauern."
          value={field.value} onChange={field.onChange}
        />
      )} />

      {/* GwG */}
      <div className="pt-4 pb-1">
        <p className="text-xs font-bold uppercase tracking-widest text-brand-400">Geldwäscheprävention (GwG)</p>
      </div>

      <Controller control={control} name="is_aml_obligated_sector" render={({ field }) => (
        <BoolField
          label="Ist das Unternehmen in einem nach GwG verpflichteten Sektor tätig?"
          hint="Finanzdienstleistungen, Krypto, Immobilienmakler, Rechts-/Notardienstleistungen, Steuerberatung oder Glücksspiel (§ 2 GwG)."
          value={field.value} onChange={field.onChange}
        />
      )} />

      <Controller control={control} name="has_aml_risk_analysis" render={({ field }) => (
        <BoolField
          label="Wurde eine Risikoanalyse zur Geldwäscheprävention durchgeführt?"
          hint="Dokumentierte Risikobewertung für Geldwäsche- und Terrorismusfinanzierungsrisiken (§ 5 GwG)."
          value={field.value} onChange={field.onChange}
        />
      )} />

      <Controller control={control} name="has_aml_officer" render={({ field }) => (
        <BoolField
          label="Ist ein Geldwäschebeauftragter benannt?"
          hint="Pflicht für regulierte Finanzinstitute und größere verpflichtete Unternehmen (§ 7 GwG)."
          value={field.value} onChange={field.onChange}
        />
      )} />

      <Controller control={control} name="has_kyc_procedures" render={({ field }) => (
        <BoolField
          label="Sind KYC-Verfahren (Kundendurchleuchtung) implementiert?"
          hint="Identifizierung und Überprüfung des Kunden vor Aufnahme einer Geschäftsbeziehung (§ 10 GwG)."
          value={field.value} onChange={field.onChange}
        />
      )} />

      {/* EU Data Act */}
      <div className="pt-4 pb-1">
        <p className="text-xs font-bold uppercase tracking-widest text-brand-400">EU Data Act</p>
      </div>

      <Controller control={control} name="produces_connected_products" render={({ field }) => (
        <BoolField
          label="Stellt das Unternehmen vernetzte (IoT-)Produkte her?"
          hint="Smarte Geräte, Industriesensoren, Wearables, vernetzte Fahrzeuge oder andere Produkte, die im Betrieb Daten erzeugen."
          value={field.value} onChange={field.onChange}
        />
      )} />

      <Controller control={control} name="provides_data_processing_services" render={({ field }) => (
        <BoolField
          label="Bietet das Unternehmen Cloud- oder Datenverarbeitungsdienste an?"
          hint="Cloud-Hosting, SaaS-Plattformen, Edge Computing oder andere Datenverarbeitungsdienste mit Wechselpflichten (Art. 23–25 EU Data Act)."
          value={field.value} onChange={field.onChange}
        />
      )} />

      <Controller control={control} name="has_data_access_mechanism" render={({ field }) => (
        <BoolField
          label="Gibt es einen Mechanismus, über den Nutzer auf ihre geräteerzeugten Daten zugreifen können?"
          hint="Nutzer vernetzter Produkte müssen einfach auf die von ihren Geräten erzeugten Daten zugreifen können (Art. 4 EU Data Act)."
          value={field.value} onChange={field.onChange}
        />
      )} />
    </div>
  );
}
