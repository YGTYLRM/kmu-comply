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
        Diese Pflichten gelten für alle Arbeitgeber in Deutschland unabhängig von Größe und Branche.
      </p>

      {/* ArbSchG */}
      <div className="flex flex-col gap-4">
        <p className="text-xs font-bold uppercase tracking-widest text-slate-500">Arbeitsschutz — ArbSchG</p>

        <Controller control={control} name="has_gefaehrdungsbeurteilung" render={({ field }) => (
          <BoolField
            label="Wurde eine Gefährdungsbeurteilung am Arbeitsplatz durchgeführt?"
            hint="Für jeden Arbeitgeber unabhängig von der Betriebsgröße verpflichtend. Gefährdungen je Tätigkeit müssen bewertet werden — §5 ArbSchG."
            value={field.value} onChange={field.onChange}
          />
        )} />

        <Controller control={control} name="has_gefaehrdungsbeurteilung_documented" render={({ field }) => (
          <BoolField
            label="Ist die Gefährdungsbeurteilung schriftlich dokumentiert?"
            hint="Ergebnisse, Maßnahmen und Wirksamkeitskontrolle müssen festgehalten werden — §6 ArbSchG."
            value={field.value} onChange={field.onChange}
          />
        )} />

        <Controller control={control} name="has_first_aid_measures" render={({ field }) => (
          <BoolField
            label="Sind Erste-Hilfe-Maßnahmen und benannte Ersthelfer vorhanden?"
            hint="Angemessene Ersthelfer und Ausstattung entsprechend der Betriebsgröße erforderlich — §10 ArbSchG."
            value={field.value} onChange={field.onChange}
          />
        )} />

        <Controller control={control} name="has_employee_safety_training" render={({ field }) => (
          <BoolField
            label="Erhalten Mitarbeiter bei Einstellung und danach regelmäßig dokumentierte Sicherheitsunterweisungen?"
            hint="Unterweisungen müssen tätigkeitsbezogen, in verständlicher Sprache und in regelmäßigen Abständen wiederholt werden — §12 ArbSchG."
            value={field.value} onChange={field.onChange}
          />
        )} />
      </div>

      {/* AGG */}
      <div className="flex flex-col gap-4 border-t border-white/[0.06] pt-5">
        <p className="text-xs font-bold uppercase tracking-widest text-slate-500">Gleichbehandlung — AGG</p>

        <Controller control={control} name="has_anti_discrimination_policy" render={({ field }) => (
          <BoolField
            label="Sind präventive Antidiskriminierungsmaßnahmen vorhanden?"
            hint="Umfasst Aushang des AGG-Textes, Sensibilisierungsschulungen und Präventivmaßnahmen — §12 AGG. Für alle Arbeitgeber verpflichtend."
            value={field.value} onChange={field.onChange}
          />
        )} />

        <Controller control={control} name="has_agc_complaints_procedure" render={({ field }) => (
          <BoolField
            label="Gibt es ein formelles Beschwerdeverfahren für Diskriminierungsfälle?"
            hint="Beschäftigte haben ein gesetzliches Recht auf Beschwerde; Arbeitgeber muss diese untersuchen — §13 AGG."
            value={field.value} onChange={field.onChange}
          />
        )} />
      </div>

      {/* MiLoG */}
      <div className="flex flex-col gap-4 border-t border-white/[0.06] pt-5">
        <p className="text-xs font-bold uppercase tracking-widest text-slate-500">Mindestlohn — MiLoG</p>

        <Controller control={control} name="has_working_time_records" render={({ field }) => (
          <BoolField
            label="Werden Arbeitszeitaufzeichnungen für alle Beschäftigten in betroffenen Branchen geführt?"
            hint="Beginn, Ende und Dauer der täglichen Arbeitszeit müssen innerhalb von 7 Tagen für Minijobber und Beschäftigte in bestimmten Branchen aufgezeichnet werden — §17 MiLoG."
            value={field.value} onChange={field.onChange}
          />
        )} />

        <Controller control={control} name="uses_subcontractors" render={({ field }) => (
          <BoolField
            label="Setzt das Unternehmen Subunternehmer oder externe Dienstleister ein, die Arbeitskräfte stellen?"
            hint="Auftraggeber haften für Subunternehmer, die den Mindestlohn nicht zahlen — §13 MiLoG."
            value={field.value} onChange={field.onChange}
          />
        )} />
      </div>

      {/* HinSchG — only ≥50 employees */}
      {needsHinSchG && (
        <div className="flex flex-col gap-4 border-t border-white/[0.06] pt-5">
          <p className="text-xs font-bold uppercase tracking-widest text-slate-500">Hinweisgeberschutz — HinSchG</p>
          <p className="text-xs text-slate-600">Pflichtanforderung für Arbeitgeber mit 50 oder mehr Beschäftigten.</p>

          <Controller control={control} name="has_whistleblower_channel" render={({ field }) => (
            <BoolField
              label="Hat das Unternehmen einen internen Hinweisgeberkanal?"
              hint="Muss schriftliche und mündliche Meldungen ermöglichen; Identität des Hinweisgebers muss vertraulich bleiben — §12/§13 HinSchG."
              value={field.value} onChange={field.onChange}
            />
          )} />

          <Controller control={control} name="has_whistleblower_policy" render={({ field }) => (
            <BoolField
              label="Gibt es eine dokumentierte Hinweisgeberrichtlinie?"
              hint="Beschreibt das Meldeverfahren, den Vertraulichkeitsschutz und den Schutz vor Vergeltungsmaßnahmen — §13 HinSchG."
              value={field.value} onChange={field.onChange}
            />
          )} />
        </div>
      )}

      {/* LkSG extras — only if supply chain abroad */}
      {hasSupplyChain && (
        <div className="flex flex-col gap-4 border-t border-white/[0.06] pt-5">
          <p className="text-xs font-bold uppercase tracking-widest text-slate-500">Lieferkettensorgfalt — LkSG</p>

          <Controller control={control} name="has_lksg_policy_statement" render={({ field }) => (
            <BoolField
              label="Hat das Unternehmen eine LkSG-Grundsatzerklärung veröffentlicht?"
              hint="Jährliches öffentliches Bekenntnis zur menschenrechtlichen und umweltbezogenen Sorgfaltspflicht — §6 LkSG."
              value={field.value} onChange={field.onChange}
            />
          )} />

          <Controller control={control} name="has_supplier_code_of_conduct" render={({ field }) => (
            <BoolField
              label="Hat das Unternehmen einen Lieferantenkodex zu Menschenrechts- und Umweltstandards?"
              hint="Vertragliche Grundlage zur Kommunikation von Sorgfaltspflichten an Lieferanten — §6 LkSG."
              value={field.value} onChange={field.onChange}
            />
          )} />

          <Controller control={control} name="has_supplier_risk_assessment" render={({ field }) => (
            <BoolField
              label="Wird mindestens jährlich eine formelle Risikoanalyse der direkten Lieferanten durchgeführt?"
              hint="Bewertung der Wahrscheinlichkeit und Schwere von Menschenrechts- und Umweltverstößen in der Lieferkette — §5 LkSG."
              value={field.value} onChange={field.onChange}
            />
          )} />

          <Controller control={control} name="has_lksg_complaints_procedure" render={({ field }) => (
            <BoolField
              label="Wurde ein LkSG-konformes Beschwerdeverfahren eingerichtet?"
              hint="Muss Beschäftigten und betroffenen Dritten die Meldung von Verstößen ermöglichen; muss zugänglich und vertraulich sein — §8 LkSG."
              value={field.value} onChange={field.onChange}
            />
          )} />
        </div>
      )}
    </div>
  );
}
