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
        Diese Fragen beziehen sich direkt auf Art. 13, 28, 32 und 33 DSGVO sowie die BDSG-Anforderungen.
      </p>

      <Controller control={control} name="has_privacy_policy" render={({ field }) => (
        <BoolField
          label="Hat das Unternehmen eine veröffentlichte Datenschutzerklärung?"
          hint="Datenschutzerklärung für betroffene Personen zugänglich, erforderlich nach Art. 13/14 DSGVO."
          value={field.value} onChange={field.onChange}
        />
      )} />

      <Controller control={control} name="has_processor_agreements" render={({ field }) => (
        <BoolField
          label="Bestehen Auftragsverarbeitungsverträge (AVV) mit allen Dienstleistern?"
          hint="AVV erforderlich mit jedem Dritten, der personenbezogene Daten in Ihrem Auftrag verarbeitet (Art. 28 DSGVO)."
          value={field.value} onChange={field.onChange}
        />
      )} />

      <Controller control={control} name="has_data_breach_procedure" render={({ field }) => (
        <BoolField
          label="Gibt es ein dokumentiertes Verfahren zur Reaktion auf Datenpannen?"
          hint="Muss Erkennung, interne Eskalation und Meldung an die Aufsichtsbehörde innerhalb von 72 Stunden umfassen (Art. 33 DSGVO)."
          value={field.value} onChange={field.onChange}
        />
      )} />

      <Controller control={control} name="has_tom_documentation" render={({ field }) => (
        <BoolField
          label="Sind technische und organisatorische Maßnahmen (TOMs) dokumentiert?"
          hint="Schriftliche Aufzeichnung der Schutzmaßnahmen für personenbezogene Daten (Art. 32 DSGVO)."
          value={field.value} onChange={field.onChange}
        />
      )} />

      <Controller control={control} name="has_data_retention_policy" render={({ field }) => (
        <BoolField
          label="Gibt es eine dokumentierte Richtlinie zur Datenspeicherung und -löschung?"
          hint="Personenbezogene Daten dürfen nicht länger als nötig gespeichert werden; Grundsatz der Speicherbegrenzung Art. 5(1)(e) DSGVO."
          value={field.value} onChange={field.onChange}
        />
      )} />

      <Controller control={control} name="has_data_protection_training" render={({ field }) => (
        <BoolField
          label="Erhalten Mitarbeiter, die personenbezogene Daten verarbeiten, regelmäßige Datenschutzschulungen?"
          hint="Mitarbeiter unter der Verantwortung des Verantwortlichen müssen geschult werden (Art. 29 und Art. 32(4) DSGVO)."
          value={field.value} onChange={field.onChange}
        />
      )} />

      <Controller control={control} name="transfers_data_outside_eea" render={({ field }) => (
        <BoolField
          label="Überträgt das Unternehmen personenbezogene Daten außerhalb des EWR?"
          hint="Übermittlungen in Drittländer ohne Angemessenheitsbeschluss erfordern SCCs oder andere Garantien nach Art. 46 DSGVO."
          value={field.value} onChange={field.onChange}
        />
      )} />

      <Controller control={control} name="has_consent_management" render={({ field }) => (
        <BoolField
          label="Wird die Einwilligung dort, wo erforderlich, ordnungsgemäß eingeholt und dokumentiert?"
          hint="Gilt für Cookies, Marketing-E-Mails und nicht zwingend erforderliche Datenverarbeitungen (Art. 6/7 DSGVO)."
          value={field.value} onChange={field.onChange}
        />
      )} />
    </div>
  );
}
