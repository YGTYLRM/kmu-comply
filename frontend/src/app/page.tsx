"use client";

import Link from "next/link";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowRight, CheckCircle2, Check, Plus, Minus, FileText,
  Scale, Clock, ClipboardCheck, BarChart2, BookOpen, Eye,
  Monitor, Factory, Truck, Activity, Store, Briefcase, Users,
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
  { value: "14",      label: "Gesetze auf einen Blick" },
  { value: "~5–10 Min.", label: "bis zum fertigen Bericht" },
  { value: "100%",    label: "ohne manuellen Aufwand" },
  { value: "3.000+",  label: "Rechtstexte in der Wissensdatenbank" },
];

const WHO_FOR = [
  { icon: Monitor,   title: "IT und Software",           desc: "Wer personenbezogene Daten verarbeitet, braucht DSGVO und BDSG. Hinzu kommen NIS2 für Netzwerkbetreiber und der EU AI Act für KI-Systeme.", tags: ["DSGVO", "BDSG", "NIS2", "EU AI Act"] },
  { icon: Factory,   title: "Produktion und Industrie",  desc: "Ab 1.000 Mitarbeitern greift das LkSG. Viele Unternehmen unterschätzen auch den EnEfG, der bereits ab 7,5 GWh Jahresverbrauch gilt.", tags: ["LkSG", "EnEfG", "CSRD"] },
  { icon: Truck,     title: "Logistik und Transport",    desc: "Lieferanten in Risikoländern lösen LkSG-Sorgfaltspflichten aus. NIS2 gilt zusätzlich für Betreiber kritischer Verkehrsinfrastruktur.", tags: ["LkSG", "NIS2", "ArbSchG"] },
  { icon: Activity,  title: "Gesundheitswesen",          desc: "Gesundheitsdaten sind die sensibelste Datenkategorie unter der DSGVO. Die Anforderungen an Einwilligung und Sicherheitsmaßnahmen sind strenger als in anderen Branchen.", tags: ["DSGVO", "BDSG", "HinSchG"] },
  { icon: Store,     title: "Handel und E-Commerce",     desc: "Cookie-Banner ist nicht gleich TTDSG-konform. Dazu kommen DSGVO-Pflichten bei Kundendaten, AGG im Personalbereich und GwG bei größeren Bargeschäften.", tags: ["DSGVO", "TTDSG", "GwG", "AGG"] },
  { icon: Users,     title: "Beratung und Dienstleister", desc: "Mandantendaten, HinSchG ab 50 Mitarbeitern, AGG, MiLoG bei Subunternehmern: Beratungsunternehmen haben mehr Pflichten als sie oft wissen.", tags: ["DSGVO", "HinSchG", "AGG", "MiLoG"] },
];

const STEPS = [
  { n: "01", title: "Profil ausfüllen",           desc: "Branche, Größe, Umsatz, Datenpraktiken, Lieferkette. Dauert etwa 5 Minuten." },
  { n: "02", title: "Dokumente hochladen",         desc: "Optional: Datenschutzerklärung, AVV, ISMS oder Personalhandbuch. Complio liest sie direkt." },
  { n: "03", title: "Gesetzesabgleich läuft",      desc: "Für jede anwendbare Vorschrift werden die relevanten Artikel abgerufen und gegen Ihr Profil geprüft." },
  { n: "04", title: "Lücken und Risiken sehen",    desc: "Jede Anforderung wird einzeln bewertet. Sie sehen, was fehlt, warum es fehlt und wie kritisch es ist." },
  { n: "05", title: "Bericht herunterladen",       desc: "PDF mit priorisiertem Maßnahmenplan. Als Vorbereitung für den Anwalt oder die interne Umsetzung." },
];

const FEATURES = [
  { icon: Scale,         title: "14 Gesetze, ein Bericht",       desc: "DSGVO, NIS2, LkSG, EU AI Act, CSRD, GwG und acht weitere Vorschriften. Jede wird nur geprüft, wenn Ihr Unternehmen die Schwellenwerte erfüllt." },
  { icon: Clock,         title: "Ergebnis in Minuten",            desc: "Kein wochenlanger Fragebogen. Profil ausfüllen, Bericht erhalten. Als Vorbereitung auf das Anwaltsgespräch." },
  { icon: ClipboardCheck,title: "Maßnahmen mit Priorität",        desc: "Jede Lücke wird zu einer Aufgabe. Kritisch, Hoch, Mittel oder Niedrig. Mit Aufwandsschätzung und Frist." },
  { icon: BarChart2,     title: "Score je Vorschrift",            desc: "Sie sehen nicht nur, ob Sie compliant sind, sondern wie weit Sie bei jedem einzelnen Gesetz noch davon entfernt sind." },
  { icon: BookOpen,      title: "Echte Gesetzeszitate",           desc: "Jede Bewertung verweist auf den konkreten Artikel. Keine generischen Checklisten, keine vagen Empfehlungen." },
  { icon: Eye,           title: "Unsicherheiten klar markiert",   desc: "Wenn eine Aussage auf unvollständigen Angaben basiert, steht das im Bericht. Kein falsches Sicherheitsgefühl." },
];

const PLANS = [
  {
    name: "Starter",
    price: "€129",
    period: "pro Bericht",
    desc: "Einmaliges Screening. Kein Abo, kein Vertrag.",
    highlight: false,
    cta: "Jetzt starten",
    features: [
      "Einmaliges Compliance-Screening",
      "Alle 14 Vorschriften abgedeckt",
      "Vollständige Lückenanalyse",
      "Priorisierter Maßnahmenplan",
      "PDF-Bericht zum Download",
      "60 Tage Ergebniszugriff",
    ],
  },
  {
    name: "Professional",
    price: "€249",
    period: "pro Monat",
    desc: "Für Unternehmen, die Compliance aktiv im Blick behalten.",
    highlight: true,
    cta: "Jetzt starten",
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
    price: "Kontakt",
    period: "",
    desc: "Mehrere Standorte, eigene Anforderungen oder API-Anbindung.",
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
    q: "Was ist ein Compliance-Screening und was ist es nicht?",
    a: "Ein Screening zeigt Ihnen, wo Ihr Unternehmen wahrscheinlich Lücken hat. Es basiert auf Ihren Angaben, zitiert konkrete Gesetzesartikel und priorisiert Handlungsbedarf. Die im Bericht genannten gesetzlichen Fristen sind Orientierungswerte — keine rechtsverbindliche Auskunft für Ihre konkrete Situation. Es ist kein Rechtsgutachten, kein zertifiziertes Audit und ersetzt nicht den Rechtsanwalt. Es ist der Schritt davor.",
  },
  {
    q: "Welche Gesetze prüft Complio?",
    a: "Aktuell 14: DSGVO, BDSG, NIS2, EU AI Act, LkSG, EnEfG, CSRD, HinSchG, ArbSchG, AGG, MiLoG, TTDSG, GwG und EU Data Act. Jedes Gesetz wird nur ausgewertet, wenn Ihr Unternehmen die jeweiligen Schwellenwerte tatsächlich erfüllt.",
  },
  {
    q: "Wie verlässlich sind die Ergebnisse?",
    a: "So verlässlich wie Ihre Angaben. Je genauer das Profil, desto präziser der Bericht. Punkte, bei denen Informationen fehlen oder die Konfidenz niedrig ist, werden im Bericht explizit markiert. Kein falsches Sicherheitsgefühl.",
  },
  {
    q: "Kann ich den Bericht einem Prüfer oder Anwalt vorlegen?",
    a: "Als Arbeitsbasis ja. Als Rechtsnachweis nein. Der Bericht ist kein zertifiziertes Audit und stellt keine Rechtsberatung dar. Er ist dafür gedacht, dass Sie gut vorbereitet in das Gespräch mit dem Anwalt gehen.",
  },
  {
    q: "Was muss ich ausfüllen?",
    a: "Branche, Mitarbeiterzahl, Jahresumsatz, ob Sie personenbezogene Daten verarbeiten, Lieferkettenstruktur, Energieverbrauch und bestehende Maßnahmen. Dauert etwa 5 Minuten. Dokumente können optional hochgeladen werden.",
  },
  {
    q: "Was passiert mit meinen Daten?",
    a: "Ihre Daten werden verschlüsselt gespeichert und sind nur über Ihren Zugang abrufbar. Wir geben nichts weiter. Hochgeladene Dokumente werden nach 7 Tagen automatisch gelöscht. Sie können Ihr Konto und alle Daten jederzeit selbst löschen.",
  },
];

function MockReport() {
  return (
    <div className="w-full rounded-2xl overflow-hidden border border-white/[0.09]" style={{ background: "rgba(6,14,48,0.97)" }}>
      <div className="px-6 py-5 border-b border-white/[0.06] flex items-center justify-between">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-widest text-slate-500 mb-1">Compliance-Screening</p>
          <p className="text-base font-bold text-white">Muster GmbH · IT / Software</p>
          <p className="text-xs text-slate-600 mt-0.5">9. Mai 2026</p>
        </div>
        <div className="text-right">
          <span className="text-4xl font-bold text-amber-400">68%</span>
          <p className="text-[10px] text-slate-500 mt-0.5">Gesamtscore</p>
        </div>
      </div>
      <div className="px-6 pt-5 pb-4 space-y-3.5">
        {[
          { reg: "GDPR / DSGVO", pct: 82, color: "#34d399", label: "Konform" },
          { reg: "LkSG",         pct: 55, color: "#fbbf24", label: "Teilweise" },
          { reg: "EnEfG",        pct: 40, color: "#f87171", label: "Lücken" },
          { reg: "BDSG",         pct: 75, color: "#34d399", label: "Konform" },
          { reg: "CSRD",         pct: 30, color: "#f87171", label: "Kritisch" },
        ].map(({ reg, pct, color, label }) => (
          <div key={reg}>
            <div className="flex justify-between items-center text-xs mb-1.5">
              <span className="font-medium text-slate-300">{reg}</span>
              <div className="flex items-center gap-2.5">
                <span className="text-slate-600 text-[11px]">{label}</span>
                <span className="tabular-nums font-semibold" style={{ color }}>{pct}%</span>
              </div>
            </div>
            <div className="h-1.5 w-full rounded-full bg-white/[0.06]">
              <div className="h-1.5 rounded-full transition-all" style={{ width: `${pct}%`, backgroundColor: color }} />
            </div>
          </div>
        ))}
      </div>
      <div className="px-6 py-4 border-t border-white/[0.06]">
        <p className="text-[10px] font-medium text-slate-600 mb-2.5">Maßnahmen nach Priorität</p>
        <div className="flex flex-wrap gap-1.5">
          {[
            { label: "4 Kritisch", cls: "bg-red-500/10 text-red-400 border-red-500/20" },
            { label: "7 Hoch",     cls: "bg-orange-500/10 text-orange-400 border-orange-500/20" },
            { label: "11 Mittel",  cls: "bg-amber-500/10 text-amber-400 border-amber-500/20" },
            { label: "5 Niedrig",  cls: "bg-green-500/10 text-green-400 border-green-500/20" },
          ].map(({ label, cls }) => (
            <span key={label} className={`rounded-full border px-2.5 py-1 text-[11px] font-semibold ${cls}`}>{label}</span>
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
        style={{ background: "rgba(6,14,48,0.80)" }}
      >
        <p className="text-[10px] font-semibold uppercase tracking-widest text-slate-600 mb-4">Hochgeladene Dokumente</p>
        <div className="space-y-2.5">
          {[
            "datenschutzerklaerung.pdf",
            "auftragsverarbeitungsvertrag.pdf",
            "it_sicherheitsrichtlinie.pdf",
          ].map((name) => (
            <div key={name} className="flex items-center gap-3 rounded-xl border border-white/[0.06] bg-white/[0.03] px-3.5 py-2.5">
              <FileText className="h-4 w-4 text-slate-500 flex-shrink-0" />
              <span className="text-xs text-slate-400 flex-1 font-mono truncate">{name}</span>
              <div className="flex items-center gap-1 text-emerald-400 flex-shrink-0">
                <CheckCircle2 className="h-3.5 w-3.5" />
                <span className="text-[10px] font-semibold">Indexiert</span>
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
        style={{ background: "rgba(6,14,48,0.92)" }}
      >
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
            <span className="text-xs font-bold text-slate-300">DSGVO · Art. 13 · Transparenzpflichten</span>
          </div>
          <span className="rounded-full border border-amber-500/25 bg-amber-500/15 px-2.5 py-1 text-[10px] font-bold text-amber-400">Teilweise</span>
        </div>

        <div className="rounded-xl border border-white/[0.06] bg-brand-500/5 px-4 py-3 mb-3">
          <p className="text-[10px] font-semibold uppercase tracking-widest text-brand-400/70 mb-1.5">
            Aus datenschutzerklaerung.pdf
          </p>
          <p className="text-xs text-slate-400 italic leading-relaxed">
            &ldquo;Abschnitt 3.1: Wir informieren Nutzer über ihre Rechte nach Art. 12–22 DSGVO und das Recht auf Beschwerde...&rdquo;
          </p>
        </div>

        <div className="rounded-xl border border-red-500/15 bg-red-500/5 px-4 py-3">
          <p className="text-[10px] font-semibold uppercase tracking-widest text-red-400/70 mb-1.5">Festgestellte Lücke</p>
          <p className="text-xs text-slate-500 leading-relaxed">
            Speicherdauer nicht angegeben. Art. 13 Abs. 2 lit. a DSGVO verlangt die Angabe der Speicherfrist.
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

  if (planParam === "enterprise") {
    return <Link href="/contact?plan=enterprise" className={cls}>{plan.cta}</Link>;
  }

  if (!stripeEnabled) {
    return <Link href="/register" className={cls}>{plan.cta}</Link>;
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
      <section className="relative overflow-hidden pt-28 pb-16 sm:pt-32 sm:pb-20">
        <div className="pointer-events-none absolute top-0 right-0 w-[600px] h-[500px] bg-brand-600/10 blur-[120px] rounded-full" />
        <div className="relative mx-auto max-w-6xl px-4 sm:px-6">
          <div className="grid lg:grid-cols-2 gap-12 lg:gap-16 items-center">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <span className="inline-flex items-center gap-2 rounded-full border border-brand-500/25 bg-brand-500/8 px-3.5 py-1.5 text-xs font-semibold text-brand-300 mb-6">
                14 deutsche und EU-Vorschriften
              </span>
              <h1 className="text-4xl sm:text-5xl font-black tracking-tight text-white leading-[1.08] mb-5">
                Kennen Sie Ihre<br />
                <span className="text-brand-400">Compliance-Lücken?</span>
              </h1>
              <p className="text-lg text-slate-400 leading-relaxed mb-8 max-w-lg">
                Complio prüft Ihr Unternehmen gegen 14 Gesetze und liefert einen vollständigen Bericht mit konkreten Lücken, priorisierten Maßnahmen und echten Gesetzeszitaten. In unter 10 Minuten.
              </p>
              <div className="flex flex-col sm:flex-row gap-3 mb-8">
                <Link href="/contact" className="inline-flex items-center justify-center gap-2 rounded-xl bg-brand-600 px-7 py-3.5 text-base font-semibold text-white hover:bg-brand-500 transition-colors">
                  Demo anfordern
                  <ArrowRight className="h-4 w-4" />
                </Link>
                <Link href="/check" className="inline-flex items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/5 px-7 py-3.5 text-base font-semibold text-slate-300 hover:bg-white/10 hover:text-white transition-colors">
                  Kostenlose Vorprüfung
                </Link>
              </div>
              <div className="flex flex-wrap gap-5 text-xs text-slate-500">
                {["Antwort innerhalb 1 Werktag", "Kein Jahresvertrag", "14 Gesetze abgedeckt"].map((t) => (
                  <span key={t} className="flex items-center gap-1.5">
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500 flex-shrink-0" />
                    {t}
                  </span>
                ))}
                <a href="#pricing" className="flex items-center gap-1.5 hover:text-slate-400 transition-colors">
                  <ArrowRight className="h-3.5 w-3.5 flex-shrink-0" />
                  Preise ansehen
                </a>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 24 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.15 }}
            >
              <MockReport />
            </motion.div>
          </div>
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
                <div className="text-4xl lg:text-5xl font-bold text-white mb-2">{value}</div>
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
          <h2 className="text-3xl sm:text-4xl font-black text-white tracking-tight mb-4">Jede Branche, eigene Pflichten</h2>
          <p className="text-slate-500 max-w-xl mx-auto">Welche Gesetze für Sie gelten, hängt von Branche, Größe und Geschäftsmodell ab. Complio prüft das automatisch.</p>
        </motion.div>

        <motion.div
          variants={stagger()}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: "-60px" }}
          className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4"
        >
          {WHO_FOR.map(({ icon: Icon, title, desc, tags }) => (
            <motion.div
              key={title}
              variants={fadeUp}
              className="rounded-2xl border border-white/[0.06] p-6 hover:border-white/[0.12] transition-colors cursor-default flex flex-col gap-4"
              style={{ background: "rgba(6,14,48,0.65)" }}
            >
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg bg-brand-500/10 border border-brand-500/15">
                  <Icon className="h-4 w-4 text-white/80" strokeWidth={1.5} />
                </div>
                <h3 className="text-sm font-bold text-white">{title}</h3>
              </div>
              <p className="text-sm text-slate-500 leading-relaxed">{desc}</p>
              <div className="flex flex-wrap gap-1.5 mt-auto pt-1">
                {tags.map(t => (
                  <span key={t} className="rounded-md border border-white/[0.07] bg-white/[0.03] px-2 py-0.5 text-[10px] font-medium text-slate-500">{t}</span>
                ))}
              </div>
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
                Bestehende Dokumente einbeziehen
              </h2>
              <p className="text-slate-400 leading-relaxed mb-8">
                Laden Sie Ihre Datenschutzerklärung, AVV oder Sicherheitsrichtlinien hoch. Complio liest sie direkt aus und zitiert konkrete Passagen im Bericht. So sehen Sie nicht nur, was fehlt, sondern auch, was bereits abgedeckt ist.
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
            {FEATURES.map(({ icon: Icon, title, desc }) => (
              <motion.div
                key={title}
                variants={fadeUp}
                className="rounded-2xl border border-white/[0.06] hover:border-brand-500/30 p-7 cursor-default transition-colors"
                style={{ background: "rgba(6,14,48,0.70)" }}
              >
                <div className="mb-5 flex h-10 w-10 items-center justify-center rounded-lg bg-brand-500/10 border border-brand-500/15">
                  <Icon className="h-5 w-5 text-white/80" strokeWidth={1.5} />
                </div>
                <h3 className="text-sm font-bold text-white mb-2">{title}</h3>
                <p className="text-sm text-slate-500 leading-relaxed">{desc}</p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ── Comparison table ──────────────────────────────────── */}
      <section className="border-t border-white/[0.05] py-16 sm:py-28">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.5 }} className="mb-12 sm:mb-16 text-center">
            <p className="text-xs font-bold uppercase tracking-widest text-brand-400 mb-4">Warum Complio</p>
            <h2 className="text-3xl sm:text-4xl font-black text-white tracking-tight mb-4">Der richtige erste Schritt</h2>
            <p className="text-slate-500 max-w-xl mx-auto">Complio ersetzt keinen Rechtsanwalt. Aber es macht das Gespräch mit ihm deutlich kürzer und günstiger.</p>
          </motion.div>

          <motion.div initial={{ opacity: 0, y: 16 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.5, delay: 0.1 }}>
            <div className="overflow-x-auto rounded-2xl border border-white/[0.07]" style={{ background: "rgba(6,14,48,0.70)" }}>
              <table className="w-full text-sm border-collapse">
                <thead>
                  <tr className="border-b border-white/[0.08]">
                    <th className="text-left py-4 px-6 text-slate-500 font-medium text-xs w-[40%]" />
                    <th className="py-4 px-6 text-center w-[20%]">
                      <span className="rounded-full bg-brand-600 px-3 py-1 text-xs font-bold text-white">Complio</span>
                    </th>
                    <th className="py-4 px-6 text-center text-slate-500 font-medium text-xs w-[20%]">Compliance-<br />Plattform</th>
                    <th className="py-4 px-6 text-center text-slate-500 font-medium text-xs w-[20%]">Rechtsanwalt</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.05]">
                  {([
                    { label: "Abgedeckte Vorschriften",                    complio: "14",             platforms: "1–3",             lawyer: "auf Anfrage" },
                    { label: "Zeit bis zum ersten Ergebnis",               complio: "~5–10 Min.",     platforms: "1–4 Wochen",      lawyer: "2–6 Wochen" },
                    { label: "Gesamtkosten Einstieg",                      complio: "€ 129 einmalig", platforms: "€ 1.400+ (2 J.)", lawyer: "€ 600–1.500" },
                    { label: "Vertragsbindung",                            complio: "✓",              platforms: "✗",               lawyer: "✓" },
                    { label: "Schwellenwertprüfung nach Unternehmensgröße",complio: "✓",              platforms: "◐",               lawyer: "✓" },
                    { label: "Analyse eigener Dokumente (AVV, DSGVO, ISMS)",complio: "✓",             platforms: "◐",               lawyer: "✓" },
                    { label: "Artikelgenaue Quellenangaben",               complio: "✓",              platforms: "◐",               lawyer: "✓" },
                    { label: "Maßnahmenplan mit Priorität und Aufwand",    complio: "✓",              platforms: "◐",               lawyer: "✗" },
                    { label: "Bußgeldrisiko je Vorschrift",                complio: "✓",              platforms: "◐",               lawyer: "✓" },
                    { label: "Monitoring bei Gesetzesänderungen",          complio: "✓",              platforms: "✓",               lawyer: "✗" },
                    { label: "Rechtsverbindliche Auskunft",                complio: "✗",              platforms: "✗",               lawyer: "✓" },
                  ] as const).map(({ label, complio, platforms, lawyer }) => {
                    const cell = (val: string, highlight: boolean) => {
                      const isCheck = val === "✓";
                      const isCross = val === "✗";
                      const isPartial = val === "◐";
                      return (
                        <td key={val + label} className={`py-3.5 px-6 text-center text-sm ${highlight ? "bg-brand-500/[0.04]" : ""}`}>
                          <span className={
                            isCheck ? "text-emerald-400 font-bold"
                            : isCross ? "text-red-500/60"
                            : isPartial ? "text-amber-400"
                            : highlight ? "text-white font-semibold"
                            : "text-slate-400"
                          }>
                            {val}
                          </span>
                        </td>
                      );
                    };
                    return (
                      <tr key={label} className="hover:bg-white/[0.02] transition-colors">
                        <td className="py-3.5 px-6 text-slate-300 font-medium text-sm">{label}</td>
                        {cell(complio, true)}
                        {cell(platforms, false)}
                        {cell(lawyer, false)}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <div className="mt-3 flex items-center gap-5 text-xs text-slate-600 justify-end">
              <span className="flex items-center gap-1.5"><span className="text-emerald-400 font-bold">✓</span> Ja</span>
              <span className="flex items-center gap-1.5"><span className="text-amber-400">◐</span> Teilweise</span>
              <span className="flex items-center gap-1.5"><span className="text-red-500/60">✗</span> Nein</span>
            </div>
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
                style={{ background: plan.highlight ? "rgba(26,69,212,0.10)" : "rgba(6,14,48,0.70)" }}
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
            style={{ background: "rgba(6,14,48,0.70)" }}
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
            <p className="text-sm font-semibold text-slate-400">Complio</p>
            <div className="flex flex-wrap justify-center gap-6 text-xs text-slate-600">
              <a href="#how-it-works" className="hover:text-slate-400 transition-colors">So funktioniert es</a>
              <a href="#features"     className="hover:text-slate-400 transition-colors">Funktionen</a>
              <a href="#pricing"      className="hover:text-slate-400 transition-colors">Preise</a>
              <Link href="/contact"   className="hover:text-slate-400 transition-colors">Kontakt</Link>
              <Link href="/impressum" className="hover:text-slate-400 transition-colors">Impressum</Link>
              <Link href="/datenschutz" className="hover:text-slate-400 transition-colors">Datenschutz</Link>
              <Link href="/agb"       className="hover:text-slate-400 transition-colors">AGB</Link>
            </div>
            <p className="text-xs text-slate-600">Vorläufige Einschätzung — keine Rechtsberatung</p>
          </div>
        </div>
      </footer>

    </main>
  );
}
