"use client";

import Link from "next/link";
import { useState } from "react";
import { ArrowRight, CheckCircle2, XCircle, AlertCircle, ChevronDown, RotateCcw } from "lucide-react";

const INDUSTRIES = [
  { value: "it_software",   label: "IT und Software" },
  { value: "manufacturing", label: "Produktion und Industrie" },
  { value: "healthcare",    label: "Gesundheitswesen" },
  { value: "retail",        label: "Handel und E-Commerce" },
  { value: "finance",       label: "Finanzdienstleistungen" },
  { value: "real_estate",   label: "Immobilien" },
  { value: "logistics",     label: "Logistik und Transport" },
  { value: "construction",  label: "Bau" },
  { value: "energy",        label: "Energie und Versorgung" },
  { value: "food_beverage", label: "Lebensmittel und Getränke" },
  { value: "consulting",    label: "Beratung und Dienstleister" },
  { value: "other",         label: "Sonstiges" },
];

interface ApplicabilityResult {
  regulation: string;
  name: string;
  reason: string;
}

interface CheckResult {
  applicable_count: number;
  applicable: ApplicabilityResult[];
  not_applicable: ApplicabilityResult[];
  disclaimer: string;
}

function getGermanReason(reg: ApplicabilityResult, employees: number): string {
  switch (reg.regulation) {
    case "gdpr_dsgvo":
      return "Ihr Unternehmen verarbeitet personenbezogene Daten. Die DSGVO gilt für jedes Unternehmen, das Daten von EU-Bürgern verarbeitet, unabhängig von der Größe (Art. 2 DSGVO).";
    case "bdsg":
      return `BDSG gilt ergänzend zur DSGVO für alle deutschen Unternehmen, die personenbezogene Daten verarbeiten (§ 1 BDSG).${employees >= 20 ? " Ab 20 Mitarbeitern ist in der Regel ein Datenschutzbeauftragter zu benennen (§ 38 BDSG)." : ""}`;
    case "lksg":
      return `Mit ${employees.toLocaleString("de-DE")} Beschäftigten wird der Schwellenwert von 1.000 Mitarbeitern überschritten. Das Lieferkettensorgfaltspflichtengesetz gilt seit dem 1. Januar 2024 für Unternehmen dieser Größe (§ 1 LkSG).`;
    case "enefg":
      return "Ihr Unternehmen überschreitet die Nicht-KMU-Schwellenwerte (mind. 250 Mitarbeiter, über 50 Mio. EUR Umsatz oder über 43 Mio. EUR Bilanzsumme). Das Energieeffizienzgesetz (EnEfG) und das EDL-G sind anwendbar.";
    case "csrd":
      return "Ihr Unternehmen erfüllt mindestens zwei der drei CSRD-Größenkriterien. Eine verpflichtende Nachhaltigkeitsberichterstattung nach EU-Richtlinie 2022/2464 gilt für Ihr Unternehmen.";
    case "nis2":
      return "Ihr Unternehmen ist in einem kritischen oder wichtigen Sektor tätig und überschreitet den Schwellenwert für mittlere Unternehmen. Die NIS2-Richtlinie ist in Deutschland über das BSIG umgesetzt.";
    case "eu_ai_act":
      return "Ihr Unternehmen entwickelt oder setzt KI-Systeme ein. Der EU AI Act ist anwendbar (Art. 2). Das Verbot bestimmter KI-Praktiken gilt seit Februar 2025, GPAI-Regeln seit August 2025.";
    case "hinschg":
      return `Mit ${employees.toLocaleString("de-DE")} Beschäftigten wird der Schwellenwert von 50 Mitarbeitern überschritten. Ein interner Hinweisgeberkanal ist nach dem Hinweisgeberschutzgesetz verpflichtend (§ 12 HinSchG).`;
    case "workplace_law":
      return "Das ArbSchG gilt für alle Arbeitgeber in Deutschland, unabhängig von der Betriebsgröße. Gefährdungsbeurteilung (§ 5), Dokumentation (§ 6) und regelmäßige Mitarbeiterunterweisung (§ 12) sind gesetzlich vorgeschrieben.";
    case "agg":
      return "Das Allgemeine Gleichbehandlungsgesetz gilt für alle Arbeitgeber. Aktive Präventionsmaßnahmen gegen Diskriminierung und ein internes Beschwerdeverfahren für Mitarbeiter sind verpflichtend (§§ 12, 13 AGG).";
    case "milog":
      return `Das MiLoG gilt für alle Arbeitgeber in Deutschland. Seit dem 1. Januar 2026 beträgt der gesetzliche Mindestlohn 13,90 EUR pro Stunde (§ 1 MiLoG). Arbeitszeitnachweise sind für Geringverdienende verpflichtend (§ 17 MiLoG).`;
    case "ttdsg":
      return "Ihr Unternehmen betreibt eine Website und verarbeitet Nutzerdaten. Das TTDSG gilt (§ 25 TDDDG): Vor dem Setzen nicht notwendiger Cookies, Tracking-Skripte oder Analysewerkzeuge ist eine ausdrückliche Einwilligung erforderlich.";
    case "gwg":
      return "Ihr Unternehmen ist in einem nach dem Geldwäschegesetz verpflichteten Sektor tätig (§ 2 GwG). Risikoanalyse, Kundensorgfaltspflichten (KYC), Verdachtsmeldungen an die FIU und interne Sicherungsmaßnahmen sind verpflichtend.";
    case "eu_data_act":
      return "Ihr Unternehmen stellt vernetzte Produkte oder Datenverarbeitungsdienste bereit. Der EU Data Act ist anwendbar (Verordnung (EU) 2023/2854, gültig seit September 2025). Nutzerdatenzugang und Anbieterwechselpflichten gelten.";
    default:
      return reg.reason;
  }
}

const defaultForm = {
  employee_count: "",
  industry: "it_software",
  annual_revenue_eur: "",
  processes_personal_data: true,
  has_website: true,
  has_supply_chain_abroad: false,
  is_aml_obligated_sector: false,
  uses_ai_systems: false,
  is_critical_infrastructure_sector: false,
};

export default function QuickCheckPage() {
  const [form, setForm] = useState(defaultForm);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<CheckResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
      const payload: Record<string, unknown> = {
        employee_count: parseInt(form.employee_count) || 1,
        industry: form.industry,
        processes_personal_data: form.processes_personal_data,
        has_website: form.has_website,
        has_supply_chain_abroad: form.has_supply_chain_abroad,
        is_aml_obligated_sector: form.is_aml_obligated_sector,
        uses_ai_systems: form.uses_ai_systems,
        is_critical_infrastructure_sector: form.is_critical_infrastructure_sector,
      };
      if (form.annual_revenue_eur) {
        payload.annual_revenue_eur = parseFloat(form.annual_revenue_eur.replace(/[^0-9.]/g, ""));
      }

      const res = await fetch(`${apiUrl}/api/quick-check`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (res.status === 429) {
        setError("Zu viele Anfragen. Bitte versuchen Sie es in einer Stunde erneut.");
        return;
      }
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setError(data.detail ?? "Fehler bei der Anfrage. Bitte versuchen Sie es erneut.");
        return;
      }

      const data: CheckResult = await res.json();
      setResult(data);
    } catch {
      setError("Verbindungsfehler. Bitte überprüfen Sie Ihre Internetverbindung.");
    } finally {
      setLoading(false);
    }
  };

  const inputCls = "w-full rounded-xl border border-white/[0.09] bg-white/[0.04] px-4 py-3 text-sm text-white placeholder-slate-600 focus:outline-none focus:border-brand-500/60 focus:bg-white/[0.06] transition-colors";
  const labelCls = "block text-xs font-semibold text-slate-400 mb-2";
  const employees = parseInt(form.employee_count) || 1;

  return (
    <main className="min-h-screen pt-28 pb-20 bg-dark-950">
      <div className="mx-auto max-w-2xl px-4 sm:px-6">

        <div className="mb-10">
          <span className="inline-flex items-center gap-2 rounded-full border border-brand-500/25 bg-brand-500/8 px-3.5 py-1.5 text-xs font-semibold text-brand-300 mb-5">
            Kostenlose Vorprüfung
          </span>
          <h1 className="text-3xl sm:text-4xl font-black text-white tracking-tight mb-4">
            Welche Gesetze gelten für Ihr Unternehmen?
          </h1>
          <p className="text-slate-400 leading-relaxed">
            Geben Sie einige Eckdaten ein. Die Vorprüfung läuft sofort und kostenlos, ohne Registrierung.
            Das Ergebnis zeigt, welche der 14 Vorschriften auf Basis der Schwellenwerte anwendbar sind.
            Für die vollständige Lückenanalyse ist ein bezahltes Screening erforderlich.
          </p>
        </div>

        {!result && (
          <form
            onSubmit={handleSubmit}
            className="rounded-2xl border border-white/[0.07] p-6 sm:p-8 space-y-6 mb-8"
            style={{ background: "rgba(6,14,48,0.70)" }}
          >
            <div className="grid sm:grid-cols-2 gap-5">
              <div>
                <label className={labelCls}>Mitarbeiterzahl *</label>
                <input
                  type="number"
                  min="1"
                  max="1000000"
                  required
                  placeholder="z. B. 85"
                  value={form.employee_count}
                  onChange={(e) => setForm({ ...form, employee_count: e.target.value })}
                  className={inputCls}
                />
              </div>
              <div>
                <label className={labelCls}>Branche *</label>
                <div className="relative">
                  <select
                    required
                    value={form.industry}
                    onChange={(e) => setForm({ ...form, industry: e.target.value })}
                    className={`${inputCls} appearance-none pr-10`}
                  >
                    {INDUSTRIES.map((i) => (
                      <option key={i.value} value={i.value} style={{ background: "#060e30" }}>
                        {i.label}
                      </option>
                    ))}
                  </select>
                  <ChevronDown className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
                </div>
              </div>
            </div>

            <div>
              <label className={labelCls}>Jahresumsatz (EUR, optional)</label>
              <input
                type="text"
                placeholder="z. B. 12000000 für 12 Mio. EUR"
                value={form.annual_revenue_eur}
                onChange={(e) => setForm({ ...form, annual_revenue_eur: e.target.value })}
                className={inputCls}
              />
              <p className="mt-1.5 text-xs text-slate-600">Relevant für CSRD und EnEfG: Schwellenwertprüfung.</p>
            </div>

            <div className="space-y-3.5 pt-1">
              <p className={labelCls}>Weitere Eigenschaften</p>
              {[
                { key: "processes_personal_data",           label: "Das Unternehmen verarbeitet personenbezogene Daten (Kunden, Mitarbeiter, etc.)" },
                { key: "has_website",                       label: "Das Unternehmen betreibt eine öffentliche Website oder App" },
                { key: "has_supply_chain_abroad",           label: "Das Unternehmen hat Lieferanten oder Hersteller im Ausland" },
                { key: "uses_ai_systems",                   label: "Das Unternehmen entwickelt oder setzt KI-Systeme ein" },
                { key: "is_critical_infrastructure_sector", label: "Das Unternehmen ist in einem kritischen Sektor tätig (Energie, Verkehr, Gesundheit, Bankwesen, digitale Infrastruktur)" },
                { key: "is_aml_obligated_sector",           label: "Das Unternehmen ist im Finanz-, Immobilien-, Glücksspiel- oder Kryptobereich tätig (GwG § 2)" },
              ].map(({ key, label }) => (
                <label key={key} className="flex items-start gap-3 cursor-pointer group">
                  <div className="mt-0.5 flex-shrink-0">
                    <input
                      type="checkbox"
                      checked={form[key as keyof typeof form] as boolean}
                      onChange={(e) => setForm({ ...form, [key]: e.target.checked })}
                      className="h-4 w-4 rounded border-white/20 bg-white/5 text-brand-500 focus:ring-brand-500/30"
                    />
                  </div>
                  <span className="text-sm text-slate-400 group-hover:text-slate-300 transition-colors leading-relaxed">{label}</span>
                </label>
              ))}
            </div>

            <button
              type="submit"
              disabled={loading || !form.employee_count}
              className="w-full inline-flex items-center justify-center gap-2 rounded-xl bg-brand-600 px-6 py-3.5 text-sm font-semibold text-white hover:bg-brand-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? "Wird geprüft…" : "Vorprüfung starten"}
              {!loading && <ArrowRight className="h-4 w-4" />}
            </button>
          </form>
        )}

        {error && (
          <div className="rounded-xl border border-red-500/20 bg-red-500/8 px-5 py-4 text-sm text-red-300 mb-8">
            {error}
          </div>
        )}

        {result && (
          <div className="space-y-6">
            <div className="rounded-2xl border border-brand-500/25 bg-brand-500/6 px-6 py-5">
              <p className="text-xs font-bold uppercase tracking-widest text-brand-400 mb-1">Ergebnis</p>
              <p className="text-2xl font-black text-white">
                {result.applicable_count} von 14 Vorschriften{" "}
                <span className="text-brand-400">anwendbar</span>
              </p>
              <p className="text-xs text-slate-500 mt-1">{result.disclaimer}</p>
            </div>

            {result.applicable.length > 0 && (
              <div>
                <p className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-3">Anwendbar auf Ihr Unternehmen</p>
                <div className="space-y-2.5">
                  {result.applicable.map((reg) => (
                    <div
                      key={reg.regulation}
                      className="rounded-xl border border-white/[0.07] px-5 py-4"
                      style={{ background: "rgba(6,14,48,0.65)" }}
                    >
                      <div className="flex items-start gap-3">
                        <CheckCircle2 className="h-4 w-4 text-amber-400 flex-shrink-0 mt-0.5" />
                        <div>
                          <p className="text-sm font-bold text-white mb-1">{reg.name}</p>
                          <p className="text-xs text-slate-500 leading-relaxed">{getGermanReason(reg, employees)}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {result.not_applicable.length > 0 && (
              <div>
                <p className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-3">Nicht anwendbar</p>
                <div className="space-y-2">
                  {result.not_applicable.map((reg) => (
                    <div
                      key={reg.regulation}
                      className="rounded-xl border border-white/[0.04] px-5 py-3.5"
                      style={{ background: "rgba(6,14,48,0.40)" }}
                    >
                      <div className="flex items-start gap-3">
                        <XCircle className="h-4 w-4 text-slate-600 flex-shrink-0 mt-0.5" />
                        <div>
                          <p className="text-xs font-semibold text-slate-500">{reg.name}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="rounded-xl border border-amber-500/15 bg-amber-500/6 px-5 py-4 flex gap-3">
              <AlertCircle className="h-4 w-4 text-amber-400 flex-shrink-0 mt-0.5" />
              <p className="text-xs text-slate-400 leading-relaxed">
                Diese Vorprüfung zeigt nur, ob die Schwellenwerte erreicht werden, nicht wo konkret Lücken bestehen.
                Für die vollständige Lückenanalyse mit Artikelzitaten, Bewertung und Maßnahmenplan ist das bezahlte Screening erforderlich.
              </p>
            </div>

            <div className="flex flex-col sm:flex-row gap-3 pt-2">
              <Link
                href="/register"
                className="inline-flex items-center justify-center gap-2 rounded-xl bg-brand-600 px-6 py-3.5 text-sm font-semibold text-white hover:bg-brand-500 transition-colors"
              >
                Vollständiges Screening starten
                <ArrowRight className="h-4 w-4" />
              </Link>
              <button
                onClick={() => { setResult(null); setForm(defaultForm); }}
                className="inline-flex items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/5 px-6 py-3.5 text-sm font-semibold text-slate-300 hover:bg-white/10 transition-colors"
              >
                <RotateCcw className="h-4 w-4" />
                Neue Prüfung starten
              </button>
            </div>
          </div>
        )}

      </div>
    </main>
  );
}
