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
        NIS2 gilt für Unternehmen in kritischen und wichtigen Sektoren. Der EU AI Act gilt für alle Unternehmen, die KI-Systeme einsetzen. Bitte nur das Zutreffende beantworten.
      </p>

      <div className="flex flex-col gap-4">
        <p className="text-xs font-bold uppercase tracking-widest text-slate-500">Cybersicherheit — NIS2 Art. 21</p>

        <Controller control={control} name="has_information_security_policy" render={({ field }) => (
          <BoolField
            label="Hat das Unternehmen eine schriftliche Informationssicherheitsrichtlinie?"
            hint="Dokumentiert den Ansatz des Unternehmens zum Management von Informationssicherheitsrisiken — Art. 21(2)(a) NIS2."
            value={field.value} onChange={field.onChange}
          />
        )} />

        <Controller control={control} name="has_incident_response_plan" render={({ field }) => (
          <BoolField
            label="Gibt es einen dokumentierten Plan zur Reaktion auf Sicherheitsvorfälle?"
            hint="Muss Erkennung, Analyse, Eindämmung und Wiederherstellung nach Cybersicherheitsvorfällen abdecken — Art. 21(2)(b) NIS2."
            value={field.value} onChange={field.onChange}
          />
        )} />

        <Controller control={control} name="has_business_continuity_plan" render={({ field }) => (
          <BoolField
            label="Hat das Unternehmen einen Business-Continuity- und Notfallwiederherstellungsplan?"
            hint="Einschließlich Backup-Management und Krisenmanagementverfahren — Art. 21(2)(c) NIS2."
            value={field.value} onChange={field.onChange}
          />
        )} />

        <Controller control={control} name="has_vulnerability_management" render={({ field }) => (
          <BoolField
            label="Werden regelmäßige Schwachstellenscans oder Penetrationstests durchgeführt?"
            hint="Systematische Identifikation und Behebung von Sicherheitsschwachstellen — Art. 21(2)(e) NIS2."
            value={field.value} onChange={field.onChange}
          />
        )} />

        <Controller control={control} name="has_mfa_implemented" render={({ field }) => (
          <BoolField
            label="Ist Multi-Faktor-Authentifizierung (MFA) für kritische Systeme und Fernzugriff implementiert?"
            hint="MFA oder kontinuierliche Authentifizierung für privilegierte Konten und Remote-Verbindungen — Art. 21(2)(j) NIS2."
            value={field.value} onChange={field.onChange}
          />
        )} />

        <Controller control={control} name="has_supply_chain_security_assessment" render={({ field }) => (
          <BoolField
            label="Werden Lieferanten und Dienstleister auf Cybersicherheitsrisiken geprüft?"
            hint="Sorgfaltspflicht bei den Sicherheitspraktiken von Lieferanten mit Systemzugang — Art. 21(2)(d) NIS2."
            value={field.value} onChange={field.onChange}
          />
        )} />

        <Controller control={control} name="has_security_awareness_training" render={({ field }) => (
          <BoolField
            label="Erhalten Mitarbeiter regelmäßige Schulungen zur Cybersicherheit?"
            hint="Grundlegende Cyber-Hygiene-Schulungen für alle Mitarbeiter — Art. 21(2)(g) NIS2."
            value={field.value} onChange={field.onChange}
          />
        )} />
      </div>

      {usesAI && (
        <div className="flex flex-col gap-4 border-t border-white/[0.06] pt-5">
          <p className="text-xs font-bold uppercase tracking-widest text-slate-500">KI-Systeme — EU AI Act</p>

          <Controller control={control} name="ai_systems_are_high_risk" render={({ field }) => (
            <BoolField
              label="Fallen KI-Systeme in eine Hochrisiko-Kategorie?"
              hint="Hochrisiko umfasst: Personal-/HR-Entscheidungen, Kreditwürdigkeitsprüfung, biometrische Identifikation, sicherheitskritische Systeme — Anhang III EU AI Act."
              value={field.value} onChange={field.onChange}
            />
          )} />

          <Controller control={control} name="has_ai_risk_assessment" render={({ field }) => (
            <BoolField
              label="Wurde eine Risikobewertung für eingesetzte KI-Systeme durchgeführt?"
              hint="Dokumentierter iterativer Risikomanagementprozess über den gesamten KI-Systemlebenszyklus — Art. 9 EU AI Act."
              value={field.value} onChange={field.onChange}
            />
          )} />

          <Controller control={control} name="has_ai_usage_documentation" render={({ field }) => (
            <BoolField
              label="Ist der Einsatz von KI-Systemen dokumentiert (Zweck, Dateneingaben, Entscheidungslogik)?"
              hint="Ausreichende Transparenzdokumentation, damit Betreiber KI-Ausgaben interpretieren können — Art. 13 EU AI Act."
              value={field.value} onChange={field.onChange}
            />
          )} />

          <Controller control={control} name="has_human_oversight_procedure" render={({ field }) => (
            <BoolField
              label="Sind menschliche Aufsichtsverfahren für KI-Systeme dokumentiert und umgesetzt?"
              hint="Eine benannte Person muss KI-Entscheidungen überwachen, verstehen und außer Kraft setzen können — Art. 14 EU AI Act."
              value={field.value} onChange={field.onChange}
            />
          )} />
        </div>
      )}
    </div>
  );
}
