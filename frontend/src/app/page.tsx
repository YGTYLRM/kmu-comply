"use client";

import Link from "next/link";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowRight, CheckCircle2, FileSearch, Zap, ShieldCheck,
  BarChart3, ListChecks, AlertTriangle, Check, Plus, Minus,
  Building2, Factory, Truck, Stethoscope, ShoppingBag, Briefcase,
  FileText,
} from "lucide-react";

const ease = [0.21, 0.47, 0.32, 0.98] as const;

const fadeUp = {
  hidden: { opacity: 0, y: 32 },
  show:   { opacity: 1, y: 0, transition: { duration: 0.6, ease } },
};

const stagger = (delay = 0) => ({
  hidden: { opacity: 0 },
  show: { opacity: 1, transition: { staggerChildren: 0.11, delayChildren: delay } },
});

const REGULATIONS = [
  { name: "GDPR / DSGVO", desc: "Datenschutz" },
  { name: "BDSG",         desc: "Bundesdatenschutz" },
  { name: "LkSG",         desc: "Lieferkettensorgfalt" },
  { name: "EnEfG",        desc: "Energieeffizienz" },
  { name: "CSRD",         desc: "Nachhaltigkeitsberichte" },
  { name: "NIS2",         desc: "Cybersicherheit" },
  { name: "EU AI Act",    desc: "Künstliche Intelligenz" },
  { name: "HinSchG",      desc: "Hinweisgeberschutz" },
  { name: "ArbSchG",      desc: "Arbeitsschutz" },
  { name: "AGG",          desc: "Gleichbehandlung" },
  { name: "MiLoG",        desc: "Mindestlohn" },
  { name: "TTDSG",        desc: "Cookie-Einwilligung" },
  { name: "GwG",          desc: "Geldwäscheprävention" },
  { name: "EU Data Act",  desc: "Datenzugang & -teilung" },
];

const STATS = [
  { value: "14",   label: "deutsche und EU-Vorschriften abgedeckt" },
  { value: "3min", label: "durchschnittliche Zeit bis zum Ergebnis" },
  { value: "100%", label: "automatisiert, kein manueller Aufwand" },
  { value: "3K+",  label: "Rechtsartikel in unserer Wissensdatenbank" },
];

const WHO_FOR = [
  { icon: Building2,   title: "IT und Software",          desc: "DSGVO- und BDSG-Compliance ist für jedes Unternehmen, das personenbezogene Daten verarbeitet, verpflichtend." },
  { icon: Factory,     title: "Produktion",                desc: "LkSG- und EnEfG-Pflichten gelten entlang industrieller Lieferketten." },
  { icon: Truck,       title: "Logistik",                  desc: "Grenzüberschreitende Lieferketten lösen LkSG-Sorgfaltspflichten aus." },
  { icon: Stethoscope, title: "Gesundheitswesen",          desc: "Besondere Datenkategorien nach DSGVO und BDSG erfordern erhöhte Sorgfalt." },
  { icon: ShoppingBag, title: "Handel und E-Commerce",     desc: "Kundendaten unterliegen strenger DSGVO-Prüfung auf allen EU-Märkten." },
  { icon: Briefcase,   title: "Beratung und Dienstleister", desc: "Mandantendaten und Berichtspflichten erstrecken sich über viele Vorschriften." },
];

const STEPS = [
  { n: "01", title: "Profil ausfüllen",              desc: "Fünf kurze Schritte zu Unternehmensgröße, Finanzen, Datenpraktiken, Lieferkette und Governance." },
  { n: "02", title: "KI analysiert Ihre Daten",      desc: "Relevante Rechtsartikel werden abgerufen und mit Ihrem Unternehmensprofil abgeglichen." },
  { n: "03", title: "Lücken werden identifiziert",   desc: "Jede Anforderung wird als konform, teilweise konform oder nicht konform mit vollständiger Begründung bewertet." },
  { n: "04", title: "Maßnahmen werden priorisiert",  desc: "Jede Lücke wird zu einem konkreten Handlungsschritt mit Aufwandsschätzung und Fristhinweis." },
  { n: "05", title: "Screening-Bericht prüfen",      desc: "Ein bewerteter Vorabbericht nach Vorschrift und Priorität mit konkreten nächsten Schritten." },
];

const FEATURES = [
  { icon: FileSearch,    color: "text-blue-400",    bg: "bg-blue-500/10",    title: "Vollständige Abdeckung",     desc: "14 deutsche und EU-Vorschriften in einem Durchlauf — DSGVO, NIS2, KI-Act, LkSG, CSRD, GwG und mehr." },
  { icon: Zap,           color: "text-amber-400",   bg: "bg-amber-500/10",   title: "Ergebnisse in Minuten",       desc: "Automatisiertes Screening. Solide Grundlage vor dem Gang zum Rechtsanwalt." },
  { icon: ListChecks,    color: "text-emerald-400", bg: "bg-emerald-500/10", title: "Konkreter Maßnahmenplan",     desc: "Jede Lücke erhält eine priorisierte Maßnahme von KRITISCH bis NIEDRIG mit Aufwand und Frist." },
  { icon: BarChart3,     color: "text-purple-400",  bg: "bg-purple-500/10",  title: "Bewertung je Vorschrift",     desc: "Compliance-Score pro Gesetz, damit Sie genau wissen, wo Sie zuerst ansetzen müssen." },
  { icon: ShieldCheck,   color: "text-rose-400",    bg: "bg-rose-500/10",    title: "Rechtlich fundiert",          desc: "Das Screening zitiert spezifische Artikel aus offiziellen Gesetzestexten, keine generischen Checklisten." },
  { icon: AlertTriangle, color: "text-orange-400",  bg: "bg-orange-500/10",  title: "Kennzeichnet manuellen Prüfbedarf", desc: "Bei niedriger Konfidenz markiert der Bericht Punkte ausdrücklich zur rechtlichen Überprüfung." },
];

const PLANS = [
  {
    name: "Starter",
    price: "€79",
    period: "pro Bericht",
    desc: "Einmaliges Screening für Unternehmen, die gelegentlich eine Compliance-Prüfung benötigen.",
    highlight: false,
    cta: "Demo anfordern",
    features: [
      "Einzelnes Compliance-Screening",
      "Alle 14 Vorschriften abgedeckt",
      "Vollständige Lückenanalyse",
      "Priorisierter Maßnahmenplan",
      "PDF-Bericht zum Download",
      "30 Tage Ergebniszugriff",
    ],
  },
  {
    name: "Professional",
    price: "€149",
    period: "pro Monat",
    desc: "Unbegrenzte Screenings für Teams, die Compliance kontinuierlich verfolgen.",
    highlight: true,
    cta: "Demo anfordern",
    features: [
      "Unbegrenzte Screenings",
      "Alle 14 Vorschriften abgedeckt",
      "Vollständige Lückenanalyse",
      "Priorisierter Maßnahmenplan",
      "PDF-Bericht zum Download",
      "Historisches Berichtsarchiv",
      "Bevorzugte Verarbeitung",
      "E-Mail-Support",
    ],
  },
  {
    name: "Enterprise",
    price: "Individuell",
    period: "auf Sie zugeschnitten",
    desc: "Für größere Organisationen mit komplexen Anforderungen, mehreren Einheiten oder API-Zugang.",
    highlight: false,
    cta: "Kontakt aufnehmen",
    features: [
      "Alles aus Professional",
      "Multi-Einheiten-Management",
      "API-Zugang",
      "Angepasster Regelungsumfang",
      "White-Label-Option",
      "Fester Ansprechpartner",
      "SLA-Garantie",
    ],
  },
];

const FAQS = [
  {
    q: "Was genau ist ein vorläufiges Compliance-Screening?",
    a: "Es ist eine automatisierte Ersteinschätzung Ihres Unternehmens gegenüber relevanten deutschen und EU-Vorschriften. Der Bericht identifiziert wahrscheinliche Lücken, vergibt einen Compliance-Score und schlägt konkrete nächste Schritte vor. Es handelt sich nicht um eine Rechtsberatung und ersetzt keine qualifizierte juristische Beratung.",
  },
  {
    q: "Welche Vorschriften deckt Complio ab?",
    a: "Aktuell 14: DSGVO, BDSG, LkSG, EnEfG, CSRD, NIS2, EU-KI-Act, HinSchG (Hinweisgeberschutz), ArbSchG (Arbeitsschutz), AGG (Antidiskriminierung), MiLoG (Mindestlohn), TTDSG/TDDDG (Cookie-Einwilligung), GwG (Geldwäsche) und EU Data Act. Jede Vorschrift wird nur angewendet, wenn Ihr Unternehmen die jeweiligen Schwellenwerte erfüllt.",
  },
  {
    q: "Wie genau sind die Ergebnisse?",
    a: "Die Ergebnisse basieren auf Ihren Angaben und sind nur so vollständig wie die bereitgestellten Informationen. Die KI zitiert spezifische Gesetzesartikel und wendet Schwellenwertlogik aus offiziellen Quellen an. Alle Punkte mit geringer Konfidenz werden ausdrücklich zur menschlichen Prüfung markiert.",
  },
  {
    q: "Kann ich den Bericht als Rechtsnachweis verwenden?",
    a: "Nein. Dieses Tool dient als Vorscreening, um Ihre Risikoexposition vor dem Gang zum Rechtsanwalt zu verstehen. Es handelt sich nicht um ein zertifiziertes Audit und stellt keine Rechtsberatung dar.",
  },
  {
    q: "Welche Informationen muss ich angeben?",
    a: "Grundlegende Unternehmensdaten: Branche, Mitarbeiterzahl, Umsatz, ob Sie personenbezogene Daten verarbeiten, Lieferkettenpräsenz, Energieverbrauch und Governance-Praktiken. Das Formular dauert ca. 3 Minuten.",
  },
  {
    q: "Werden meine Daten gespeichert oder weitergegeben?",
    a: "Berichtsdaten werden sicher gespeichert und sind nur über Ihren einzigartigen Berichtslink zugänglich. Wir geben Ihre Daten nicht an Dritte weiter. Enterprise-Kunden können Datenlokalisierung und Löschgarantien anfragen.",
  },
];

function MockReport() {
  return (
    <div
      className="w-full rounded-3xl overflow-hidden border border-white/10 shadow-[0_0_100px_rgba(59,130,246,0.2),0_32px_80px_rgba(0,0,0,0.7)]"
      style={{ background: "rgba(10,22,40,0.92)", backdropFilter: "blur(24px)" }}
    >
      <div className="px-7 py-6 border-b border-white/[0.06] flex items-center justify-between">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-widest text-slate-500">Preliminary Screening</p>
          <p className="text-lg font-bold text-white mt-0.5">Muster GmbH · IT / Software</p>
          <p className="text-xs text-slate-600 mt-0.5">Generated 9 May 2026</p>
        </div>
        <div className="text-right">
          <span className="text-5xl font-black text-amber-400">68%</span>
          <p className="text-[10px] text-slate-500 mt-0.5">overall score</p>
        </div>
      </div>

      <div className="px-7 pt-6 pb-5 space-y-4">
        {[
          { reg: "GDPR / DSGVO", pct: 82, bar: "from-emerald-500 to-emerald-400", status: "Good" },
          { reg: "LkSG",         pct: 55, bar: "from-amber-500 to-amber-400",     status: "Partial" },
          { reg: "EnEfG",        pct: 40, bar: "from-red-500 to-red-400",         status: "Gaps found" },
          { reg: "BDSG",         pct: 75, bar: "from-emerald-400 to-teal-400",    status: "Good" },
          { reg: "CSRD",         pct: 30, bar: "from-red-600 to-red-400",         status: "Critical" },
        ].map(({ reg, pct, bar, status }) => (
          <div key={reg}>
            <div className="flex justify-between items-center text-xs mb-2">
              <span className="font-semibold text-slate-300">{reg}</span>
              <div className="flex items-center gap-3">
                <span className="text-slate-600">{status}</span>
                <span className="text-slate-400 tabular-nums font-bold">{pct}%</span>
              </div>
            </div>
            <div className="h-2 w-full rounded-full bg-white/[0.06]">
              <div className={`h-2 rounded-full bg-gradient-to-r ${bar} transition-all duration-700`} style={{ width: `${pct}%` }} />
            </div>
          </div>
        ))}
      </div>

      <div className="px-7 py-5 border-t border-white/[0.06] bg-white/[0.02]">
        <p className="text-[10px] font-semibold uppercase tracking-widest text-slate-600 mb-3">Action items by priority</p>
        <div className="flex flex-wrap gap-2">
          {[
            { label: "4 CRITICAL", cls: "bg-red-500/15 text-red-400 border-red-500/25" },
            { label: "7 HIGH",     cls: "bg-orange-500/15 text-orange-400 border-orange-500/25" },
            { label: "11 MEDIUM",  cls: "bg-amber-500/15 text-amber-400 border-amber-500/25" },
            { label: "5 LOW",      cls: "bg-green-500/15 text-green-400 border-green-500/25" },
          ].map(({ label, cls }) => (
            <span key={label} className={`rounded-full border px-3 py-1.5 text-[11px] font-bold tracking-wide ${cls}`}>
              {label}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

function DocUploadVisual() {
  return (
    <div className="space-y-4">
      <div
        className="rounded-2xl border border-white/[0.08] p-5"
        style={{ background: "rgba(10,22,40,0.75)" }}
      >
        <p className="text-[10px] font-semibold uppercase tracking-widest text-slate-600 mb-4">Documents attached</p>
        <div className="space-y-2.5">
          {[
            "privacy_policy.pdf",
            "data_processing_agreement.pdf",
            "it_security_policy.pdf",
          ].map((name) => (
            <div key={name} className="flex items-center gap-3 rounded-xl border border-white/[0.06] bg-white/[0.03] px-3.5 py-2.5">
              <FileText className="h-4 w-4 text-slate-500 flex-shrink-0" />
              <span className="text-xs text-slate-400 flex-1 font-mono truncate">{name}</span>
              <div className="flex items-center gap-1 text-emerald-400 flex-shrink-0">
                <CheckCircle2 className="h-3.5 w-3.5" />
                <span className="text-[10px] font-semibold">Indexed</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="flex justify-center">
        <div className="h-7 w-px bg-gradient-to-b from-brand-500/40 to-transparent" />
      </div>

      <div
        className="rounded-2xl border border-brand-500/20 p-5 shadow-glow-blue-sm"
        style={{ background: "rgba(10,22,40,0.88)" }}
      >
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
            <span className="text-xs font-bold text-slate-300">GDPR · Art. 13 · Transparency</span>
          </div>
          <span className="rounded-full border border-amber-500/25 bg-amber-500/15 px-2.5 py-1 text-[10px] font-bold text-amber-400">PARTIAL</span>
        </div>

        <div className="rounded-xl border border-white/[0.06] bg-brand-500/5 px-4 py-3 mb-3">
          <p className="text-[10px] font-semibold uppercase tracking-widest text-brand-400/70 mb-1.5">
            From privacy_policy.pdf
          </p>
          <p className="text-xs text-slate-400 italic leading-relaxed">
            &ldquo;Section 3.1: We inform users of their rights under Articles 12 to 22 of the GDPR and the right to lodge a complaint...&rdquo;
          </p>
        </div>

        <div className="rounded-xl border border-red-500/15 bg-red-500/5 px-4 py-3">
          <p className="text-[10px] font-semibold uppercase tracking-widest text-red-400/70 mb-1.5">Gap identified</p>
          <p className="text-xs text-slate-500 leading-relaxed">
            No retention period stated. Art. 13(2)(a) requires the period for which personal data will be stored.
          </p>
        </div>
      </div>
    </div>
  );
}

function FAQItem({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border-b border-white/[0.06] last:border-0">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex w-full items-center justify-between py-5 text-left gap-6 group"
      >
        <span className="text-sm font-semibold text-white group-hover:text-brand-300 transition-colors">{q}</span>
        <span className="flex-shrink-0 flex h-6 w-6 items-center justify-center rounded-full border border-white/10 bg-white/5">
          {open
            ? <Minus className="h-3 w-3 text-brand-400" />
            : <Plus className="h-3 w-3 text-slate-400" />
          }
        </span>
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25, ease: [0.21, 0.47, 0.32, 0.98] }}
            className="overflow-hidden"
          >
            <p className="pb-5 text-sm text-slate-500 leading-relaxed">{a}</p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

function PricingCTA({ plan }: { plan: typeof PLANS[0] }) {
  const [loading, setLoading] = useState(false);
  const planParam = plan.name.toLowerCase();
  const stripeEnabled = process.env.NEXT_PUBLIC_STRIPE_ENABLED === "true";
  const cls = `w-full text-center rounded-xl py-3 text-sm font-semibold transition-all duration-200 disabled:opacity-60 ${
    plan.highlight
      ? "bg-brand-600 text-white hover:bg-brand-500 shadow-glow-blue-sm hover:shadow-glow-blue"
      : "border border-white/12 bg-white/5 text-slate-300 hover:bg-white/10 hover:text-white"
  }`;

  if (!stripeEnabled || planParam === "enterprise") {
    return (
      <Link href={`/contact?plan=${planParam}`} className={cls}>
        {plan.cta}
      </Link>
    );
  }

  const handleClick = async () => {
    setLoading(true);
    try {
      const { createClient } = await import("@/lib/supabase/client");
      const supabase = createClient();
      const { data: { session } } = await supabase.auth.getSession();
      const base = window.location.origin;
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"}/api/checkout`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(session ? { Authorization: `Bearer ${session.access_token}` } : {}),
        },
        body: JSON.stringify({
          plan: planParam,
          success_url: `${base}/account/billing`,
          cancel_url:  `${base}/#pricing`,
        }),
      });
      const data = await res.json();
      if (data.url) window.location.href = data.url;
    } catch {
      setLoading(false);
    }
  };

  return (
    <button onClick={handleClick} disabled={loading} className={cls}>
      {loading ? "Redirecting…" : plan.cta}
    </button>
  );
}

export default function HomePage() {
  return (
    <main className="bg-dark-950">

      {/* ── Hero ─────────────────────────────────────────────── */}
      <section className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden pt-24 sm:pt-28 pb-12 sm:pb-16">
        <div className="pointer-events-none absolute inset-0">
          <div className="animate-orb-1 absolute -top-32 right-0 h-[700px] w-[700px] rounded-full bg-brand-600/15 blur-[140px]" />
          <div className="animate-orb-2 absolute bottom-0 -left-32 h-[500px] w-[500px] rounded-full bg-cyan-500/8 blur-[120px]" />
        </div>
        <div
          className="pointer-events-none absolute inset-0"
          style={{ backgroundImage: "radial-gradient(circle, rgba(255,255,255,0.05) 1px, transparent 1px)", backgroundSize: "28px 28px" }}
        />
        <div className="pointer-events-none absolute bottom-0 left-0 right-0 h-40 bg-gradient-to-t from-dark-950 to-transparent" />

        <div className="relative mx-auto max-w-5xl px-6 flex flex-col items-center text-center gap-8">
          <motion.div variants={stagger(0.05)} initial="hidden" animate="show" className="flex flex-col items-center gap-7">
            <motion.div variants={fadeUp}>
              <span className="inline-flex items-center gap-2 rounded-full border border-brand-500/30 bg-brand-500/10 px-4 py-1.5 text-xs font-semibold text-brand-300">
                <span className="h-1.5 w-1.5 rounded-full bg-brand-400 animate-pulse-slow" />
                14 deutsche und EU-Vorschriften abgedeckt
              </span>
            </motion.div>

            <motion.h1 variants={fadeUp} className="text-4xl sm:text-5xl lg:text-7xl font-black tracking-tight text-white leading-[1.04]">
              Kennen Sie Ihre{" "}
              <span className="shimmer-text">Compliance-Lücken</span>
              <br />
              bevor sie Sie finden.
            </motion.h1>

            <motion.p variants={fadeUp} className="max-w-2xl text-base sm:text-lg text-slate-400 leading-relaxed px-2 sm:px-0">
              Geben Sie Ihr Unternehmensprofil ein und erhalten Sie in Minuten ein detailliertes Compliance-Screening nach deutschem und EU-Recht. Die solide Grundlage vor jedem Rechtsanwaltsgespräch.
            </motion.p>

            <motion.div variants={fadeUp} className="flex flex-col sm:flex-row gap-3">
              <Link href="/contact" className="group inline-flex items-center justify-center gap-2 rounded-xl bg-brand-600 px-7 py-4 text-base font-semibold text-white shadow-glow-blue-sm hover:shadow-glow-blue hover:bg-brand-500 transition-all duration-300">
                Demo anfordern
                <ArrowRight className="h-4 w-4 group-hover:translate-x-0.5 transition-transform duration-200" />
              </Link>
              <a href="#pricing" className="inline-flex items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/5 px-7 py-4 text-base font-semibold text-slate-300 hover:bg-white/10 hover:text-white transition-all duration-200">
                Preise ansehen
              </a>
            </motion.div>

            <motion.div variants={fadeUp} className="flex flex-wrap justify-center gap-6 text-xs text-slate-500">
              {["Antwort innerhalb 1 Werktag", "Ergebnisse in Minuten", "14 Vorschriften in einem Bericht"].map((t) => (
                <span key={t} className="flex items-center gap-1.5">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
                  {t}
                </span>
              ))}
            </motion.div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 56, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 0.85, delay: 0.5, ease }}
            className="animate-float w-full max-w-2xl mt-4"
          >
            <MockReport />
          </motion.div>
        </div>
      </section>

      {/* ── Stats ─────────────────────────────────────────────── */}
      <section className="border-y border-white/[0.05] bg-dark-900/70 py-14">
        <div className="mx-auto max-w-6xl px-6">
          <motion.div
            variants={stagger()}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true }}
            className="grid grid-cols-2 lg:grid-cols-4 gap-8"
          >
            {STATS.map(({ value, label }) => (
              <motion.div key={label} variants={fadeUp} className="text-center">
                <div className="text-4xl lg:text-5xl font-black text-white mb-2 shimmer-text">{value}</div>
                <div className="text-sm text-slate-500 leading-snug">{label}</div>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ── Regulation strip ──────────────────────────────────── */}
      <motion.section
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{ duration: 0.5 }}
        className="border-b border-white/[0.05] bg-dark-950 py-5"
      >
        <div className="mx-auto max-w-6xl px-6">
          <div className="flex flex-wrap items-center gap-2.5">
            <span className="text-xs font-medium text-slate-600 mr-1">Abgedeckte Vorschriften</span>
            {REGULATIONS.map((r) => (
              <div key={r.name} className="flex items-center gap-1.5 rounded-lg border border-white/[0.07] bg-white/[0.03] px-3 py-1.5 text-xs font-medium text-slate-400">
                <span className="h-1.5 w-1.5 rounded-full bg-brand-500" />
                {r.name}
                <span className="text-slate-600 font-normal">· {r.desc}</span>
              </div>
            ))}
          </div>
        </div>
      </motion.section>

      {/* ── Who it's for ──────────────────────────────────────── */}
      <section className="mx-auto max-w-6xl px-4 sm:px-6 py-16 sm:py-28">
        <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.5 }} className="mb-12 sm:mb-16 text-center">
          <p className="text-xs font-bold uppercase tracking-widest text-brand-400 mb-4">Für wen es gemacht ist</p>
          <h2 className="text-3xl sm:text-4xl font-black text-white tracking-tight mb-4">Entwickelt für deutsche KMU in allen Branchen</h2>
          <p className="text-slate-500 max-w-xl mx-auto">Jedes Unternehmen, das in Deutschland oder der EU tätig ist, sieht sich einem Geflecht überschneidender Vorschriften gegenüber. Complio bringt in Minuten Klarheit.</p>
        </motion.div>

        <motion.div
          variants={stagger()}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: "-60px" }}
          className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4"
        >
          {WHO_FOR.map(({ icon: Icon, title, desc }) => (
            <motion.div
              key={title}
              variants={fadeUp}
              whileHover={{ y: -4, boxShadow: "0 0 0 1px rgba(59,130,246,0.2), 0 0 24px rgba(59,130,246,0.1)", transition: { duration: 0.2 } }}
              className="rounded-2xl border border-white/[0.06] p-6 cursor-default"
              style={{ background: "rgba(10,22,40,0.6)" }}
            >
              <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl bg-brand-500/10">
                <Icon className="h-5 w-5 text-brand-400" />
              </div>
              <h3 className="text-sm font-bold text-white mb-1.5">{title}</h3>
              <p className="text-sm text-slate-500 leading-relaxed">{desc}</p>
            </motion.div>
          ))}
        </motion.div>
      </section>

      {/* ── How it works ──────────────────────────────────────── */}
      <section id="how-it-works" className="border-t border-white/[0.05] bg-dark-900/40 py-16 sm:py-28">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.5 }} className="mb-12 sm:mb-16 text-center">
            <p className="text-xs font-bold uppercase tracking-widest text-brand-400 mb-4">So funktioniert es</p>
            <h2 className="text-3xl sm:text-4xl font-black text-white tracking-tight">Vom Profil zum Bericht in fünf Schritten</h2>
          </motion.div>

          <motion.div variants={stagger()} initial="hidden" whileInView="show" viewport={{ once: true, margin: "-60px" }} className="grid grid-cols-1 sm:grid-cols-5 gap-8 sm:gap-0">
            {STEPS.map(({ n, title, desc }, i) => (
              <motion.div key={n} variants={fadeUp} className="relative flex flex-col gap-3 sm:px-4 pb-2">
                {i < STEPS.length - 1 && (
                  <div className="hidden sm:block absolute top-5 left-[calc(50%+28px)] right-0 h-px bg-gradient-to-r from-brand-500/35 to-transparent" />
                )}
                <div className="relative z-10 flex h-11 w-11 items-center justify-center rounded-full border border-brand-500/35 bg-brand-500/10 text-xs font-black text-brand-400 shadow-glow-blue-sm">
                  {n}
                </div>
                <p className="text-sm font-bold text-white leading-snug">{title}</p>
                <p className="text-xs text-slate-500 leading-relaxed">{desc}</p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ── Document upload explainer ─────────────────────────── */}
      <section className="border-t border-white/[0.05] py-16 sm:py-28">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="grid lg:grid-cols-2 gap-12 lg:gap-20 items-center">

            <motion.div
              initial={{ opacity: 0, x: -24 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, ease }}
            >
              <p className="text-xs font-bold uppercase tracking-widest text-brand-400 mb-4">Dokument-Upload</p>
              <h2 className="text-3xl sm:text-4xl font-black text-white tracking-tight leading-tight mb-6">
                Dokumente hochladen.<br />Echte Befunde erhalten.
              </h2>
              <p className="text-slate-400 leading-relaxed mb-8">
                Profilantworten geben eine solide Basis. Hängen Sie Ihre tatsächlichen Unternehmensdokumente an, und Complio liest sie direkt — mit Zitat konkreter Passagen als Belege. Was sonst unsicher bliebe, wird zu konkreten Befunden.
              </p>

              <div className="space-y-3 mb-10">
                {[
                  "Datenschutzerklärung und Cookie-Hinweis",
                  "Auftragsverarbeitungsverträge (AVV)",
                  "Informationssicherheitsrichtlinie / ISMS",
                  "Personalhandbuch und Arbeitsverträge",
                  "Energieaudit oder Umweltberichte",
                ].map((doc) => (
                  <div key={doc} className="flex items-center gap-3 text-sm text-slate-400">
                    <FileText className="h-4 w-4 flex-shrink-0 text-brand-400" />
                    {doc}
                  </div>
                ))}
              </div>

              <Link
                href="/contact"
                className="group inline-flex items-center gap-2 rounded-xl bg-brand-600 px-6 py-3.5 text-sm font-semibold text-white shadow-glow-blue-sm hover:shadow-glow-blue hover:bg-brand-500 transition-all duration-300"
              >
                Demo anfordern
                <ArrowRight className="h-4 w-4 group-hover:translate-x-0.5 transition-transform duration-200" />
              </Link>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 24 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, ease, delay: 0.12 }}
            >
              <DocUploadVisual />
            </motion.div>

          </div>
        </div>
      </section>

      {/* ── Features ──────────────────────────────────────────── */}
      <section id="features" className="border-t border-white/[0.05] py-16 sm:py-28">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.5 }} className="mb-12 sm:mb-16 text-center">
            <p className="text-xs font-bold uppercase tracking-widest text-brand-400 mb-4">Was Sie erhalten</p>
            <h2 className="text-3xl sm:text-4xl font-black text-white tracking-tight">Alles in einem Bericht</h2>
          </motion.div>

          <motion.div variants={stagger()} initial="hidden" whileInView="show" viewport={{ once: true, margin: "-60px" }} className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {FEATURES.map(({ icon: Icon, color, bg, title, desc }) => (
              <motion.div
                key={title}
                variants={fadeUp}
                whileHover={{ y: -5, boxShadow: "0 0 0 1px rgba(59,130,246,0.22), 0 12px 40px rgba(0,0,0,0.55), 0 0 28px rgba(59,130,246,0.12)", transition: { duration: 0.2 } }}
                className="rounded-2xl border border-white/[0.06] p-7 cursor-default"
                style={{ background: "rgba(10,22,40,0.65)" }}
              >
                <div className={`mb-5 flex h-11 w-11 items-center justify-center rounded-xl ${bg}`}>
                  <Icon className={`h-5 w-5 ${color}`} />
                </div>
                <h3 className="text-sm font-bold text-white mb-2">{title}</h3>
                <p className="text-sm text-slate-500 leading-relaxed">{desc}</p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ── Pricing ───────────────────────────────────────────── */}
      <section id="pricing" className="border-t border-white/[0.05] bg-dark-900/40 py-16 sm:py-28">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.5 }} className="mb-12 sm:mb-16 text-center">
            <p className="text-xs font-bold uppercase tracking-widest text-brand-400 mb-4">Preise</p>
            <h2 className="text-3xl sm:text-4xl font-black text-white tracking-tight mb-4">Einfache, transparente Preise</h2>
            <p className="text-slate-500 max-w-lg mx-auto">Zahlen Sie pro Screening oder abonnieren Sie für laufendes Monitoring. Keine versteckten Kosten, keine Mindestlaufzeit.</p>
          </motion.div>

          <motion.div
            variants={stagger()}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, margin: "-60px" }}
            className="grid lg:grid-cols-3 gap-6 items-start"
          >
            {PLANS.map((plan) => (
              <motion.div
                key={plan.name}
                variants={fadeUp}
                className={`relative rounded-2xl border p-8 flex flex-col gap-6 ${
                  plan.highlight
                    ? "border-brand-500/50 shadow-glow-blue"
                    : "border-white/[0.07]"
                }`}
                style={{ background: plan.highlight ? "rgba(37,99,235,0.08)" : "rgba(10,22,40,0.65)" }}
              >
                {plan.highlight && (
                  <div className="absolute -top-3.5 left-1/2 -translate-x-1/2">
                    <span className="rounded-full bg-brand-600 px-3 py-1 text-[11px] font-bold text-white shadow-glow-blue-sm">
                      Beliebteste Wahl
                    </span>
                  </div>
                )}

                <div>
                  <p className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-2">{plan.name}</p>
                  <div className="flex items-end gap-1.5 mb-3">
                    <span className="text-4xl font-black text-white">{plan.price}</span>
                    <span className="text-sm text-slate-500 mb-1.5">{plan.period}</span>
                  </div>
                  <p className="text-sm text-slate-500 leading-relaxed">{plan.desc}</p>
                </div>

                <ul className="flex flex-col gap-2.5 flex-1">
                  {plan.features.map((f) => (
                    <li key={f} className="flex items-start gap-2.5 text-sm text-slate-300">
                      <Check className="h-4 w-4 text-brand-400 flex-shrink-0 mt-0.5" />
                      {f}
                    </li>
                  ))}
                </ul>

                <PricingCTA plan={plan} />
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ── FAQ ───────────────────────────────────────────────── */}
      <section className="border-t border-white/[0.05] py-16 sm:py-28">
        <div className="mx-auto max-w-3xl px-4 sm:px-6">
          <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.5 }} className="mb-10 sm:mb-14 text-center">
            <p className="text-xs font-bold uppercase tracking-widest text-brand-400 mb-4">Häufige Fragen</p>
            <h2 className="text-3xl sm:text-4xl font-black text-white tracking-tight">Ihre Fragen, unsere Antworten</h2>
          </motion.div>

          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="rounded-2xl border border-white/[0.07] px-4 sm:px-8"
            style={{ background: "rgba(10,22,40,0.65)" }}
          >
            {FAQS.map(({ q, a }) => (
              <FAQItem key={q} q={q} a={a} />
            ))}
          </motion.div>
        </div>
      </section>

      {/* ── CTA ───────────────────────────────────────────────── */}
      <section className="border-t border-white/[0.05] relative overflow-hidden">
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
          <div className="h-[500px] w-[900px] rounded-full bg-brand-600/10 blur-[120px]" />
        </div>
        <div className="relative mx-auto max-w-4xl px-4 sm:px-6 py-20 sm:py-32 flex flex-col items-center text-center gap-8">
          <motion.div initial={{ opacity: 0, y: 24 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.55 }} className="flex flex-col items-center gap-6">
            <h2 className="text-3xl sm:text-4xl lg:text-5xl font-black text-white tracking-tight leading-tight">
              Bereit, Ihre
              <br />
              Compliance-Lücken zu finden?
            </h2>
            <p className="text-base sm:text-lg text-slate-500 max-w-lg">
              Detailliertes Compliance-Screening über 14 deutsche und EU-Vorschriften. Kein Ersatz für Rechtsberatung.
            </p>
            <Link href="/contact" className="group inline-flex items-center gap-2.5 rounded-xl bg-brand-600 px-8 py-4 text-base font-semibold text-white shadow-glow-blue-sm hover:shadow-glow-blue hover:bg-brand-500 transition-all duration-300">
              Demo anfordern
              <ArrowRight className="h-4 w-4 group-hover:translate-x-0.5 transition-transform duration-200" />
            </Link>
          </motion.div>
        </div>
      </section>

      {/* ── Footer ────────────────────────────────────────────── */}
      <footer className="border-t border-white/[0.05] py-10">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-6">
            <img src="/logo-dark-bg.png" alt="Complio" className="h-10 w-auto" />
            <div className="flex flex-wrap justify-center gap-6 text-xs text-slate-600">
              <a href="#how-it-works" className="hover:text-slate-400 transition-colors">How it works</a>
              <a href="#features"     className="hover:text-slate-400 transition-colors">Features</a>
              <a href="#pricing"      className="hover:text-slate-400 transition-colors">Pricing</a>
              <Link href="/contact"   className="hover:text-slate-400 transition-colors">Contact</Link>
              <Link href="/impressum" className="hover:text-slate-400 transition-colors">Impressum</Link>
              <Link href="/privacy"   className="hover:text-slate-400 transition-colors">Privacy Policy</Link>
            </div>
            <p className="text-xs text-slate-600">Not legal advice. For informational purposes only.</p>
          </div>
        </div>
      </footer>

    </main>
  );
}
