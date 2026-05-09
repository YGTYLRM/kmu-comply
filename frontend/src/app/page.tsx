"use client";

import Link from "next/link";
import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ArrowRight, CheckCircle2, FileSearch, Zap, ShieldCheck,
  BarChart3, ListChecks, AlertTriangle, Check, Plus, Minus,
  Building2, Factory, Truck, Stethoscope, ShoppingBag, Briefcase,
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
  { name: "GDPR / DSGVO", desc: "Data protection" },
  { name: "BDSG",         desc: "German data privacy" },
  { name: "LkSG",         desc: "Supply chain" },
  { name: "EnEfG",        desc: "Energy efficiency" },
  { name: "CSRD",         desc: "Sustainability reporting" },
  { name: "NIS2",         desc: "Cybersecurity" },
  { name: "EU AI Act",    desc: "Artificial intelligence" },
  { name: "HinSchG",      desc: "Whistleblower protection" },
  { name: "ArbSchG",      desc: "Occupational safety" },
  { name: "AGG",          desc: "Equal treatment" },
  { name: "MiLoG",        desc: "Minimum wage" },
];

const STATS = [
  { value: "11",   label: "German and EU regulations covered" },
  { value: "3min", label: "Average time to receive results" },
  { value: "100%", label: "Automated, no manual input needed" },
  { value: "1K+",  label: "Regulation articles in our knowledge base" },
];

const WHO_FOR = [
  { icon: Building2,   title: "IT and Software",        desc: "GDPR and BDSG compliance is critical for any company handling personal data." },
  { icon: Factory,     title: "Manufacturing",           desc: "LkSG and EnEfG obligations apply across industrial supply chains." },
  { icon: Truck,       title: "Logistics",               desc: "Cross-border supply chains trigger LkSG due diligence requirements." },
  { icon: Stethoscope, title: "Healthcare",              desc: "Special category data under GDPR and BDSG demands rigorous compliance." },
  { icon: ShoppingBag, title: "Retail and E-commerce",  desc: "Consumer data practices face strict GDPR scrutiny in every EU market." },
  { icon: Briefcase,   title: "Professional Services",  desc: "Client data handling and reporting obligations span multiple regulations." },
];

const STEPS = [
  { n: "01", title: "Enter your profile",      desc: "Five short steps covering company basics, finances, data practices, supply chain, and governance." },
  { n: "02", title: "AI analyses your data",   desc: "Relevant regulation articles are retrieved and assessed against your company profile." },
  { n: "03", title: "Gaps are identified",     desc: "Each requirement is checked as compliant, partial, or non-compliant with full evidence." },
  { n: "04", title: "Actions are prioritised", desc: "Every gap becomes a concrete action item with effort estimate and deadline guidance." },
  { n: "05", title: "Review your screening",   desc: "A scored preliminary screening report by regulation and priority, with suggested next steps." },
];

const FEATURES = [
  { icon: FileSearch,    color: "text-blue-400",    bg: "bg-blue-500/10",    title: "Full regulation coverage", desc: "GDPR/DSGVO, BDSG, LkSG, EnEfG, and CSRD screened in a single run." },
  { icon: Zap,           color: "text-amber-400",   bg: "bg-amber-500/10",   title: "Results in minutes",       desc: "Automated screening. A solid starting point before engaging a legal consultant." },
  { icon: ListChecks,    color: "text-emerald-400", bg: "bg-emerald-500/10", title: "Concrete action plan",     desc: "Each gap comes with a prioritised action from CRITICAL to LOW, with effort and deadline." },
  { icon: BarChart3,     color: "text-purple-400",  bg: "bg-purple-500/10",  title: "Per-regulation scoring",   desc: "Compliance score per regulation so you know exactly where to focus first." },
  { icon: ShieldCheck,   color: "text-rose-400",    bg: "bg-rose-500/10",    title: "Grounded in law",          desc: "Screening cites specific article numbers from official regulation texts, not generic checklists." },
  { icon: AlertTriangle, color: "text-orange-400",  bg: "bg-orange-500/10",  title: "Flags manual review",      desc: "When confidence is low, the report explicitly marks items for human legal review." },
];

const PLANS = [
  {
    name: "Starter",
    price: "€79",
    period: "per report",
    desc: "One-off screening for companies that need an occasional compliance check.",
    highlight: false,
    cta: "Get started",
    features: [
      "Single compliance screening",
      "All 5 regulations covered",
      "Full gap analysis",
      "Prioritised action plan",
      "PDF report download",
      "30-day result access",
    ],
  },
  {
    name: "Professional",
    price: "€149",
    period: "per month",
    desc: "Unlimited screenings for teams that need to track compliance over time.",
    highlight: true,
    cta: "Get started",
    features: [
      "Unlimited screenings",
      "All 5 regulations covered",
      "Full gap analysis",
      "Prioritised action plan",
      "PDF report download",
      "Historical report archive",
      "Priority processing",
      "Email support",
    ],
  },
  {
    name: "Enterprise",
    price: "Custom",
    period: "tailored to you",
    desc: "For larger organisations with complex needs, multiple entities, or API access.",
    highlight: false,
    cta: "Contact us",
    features: [
      "Everything in Professional",
      "Multi-entity management",
      "API access",
      "Custom regulation scope",
      "White-label option",
      "Dedicated account manager",
      "SLA guarantee",
    ],
  },
];

const FAQS = [
  {
    q: "What exactly is a preliminary compliance screening?",
    a: "It is an automated first-pass assessment of your company against relevant German and EU regulations. The report identifies likely gaps, assigns a compliance score, and suggests concrete next steps. It is not a legal audit and does not replace qualified legal counsel.",
  },
  {
    q: "Which regulations does Complio cover?",
    a: "Currently five: GDPR/DSGVO (data protection), BDSG (German federal data protection), LkSG (supply chain due diligence), EnEfG (energy efficiency), and CSRD (corporate sustainability reporting). Coverage expands as regulations evolve.",
  },
  {
    q: "How accurate are the results?",
    a: "Results are based on your answers and are only as complete as the information you provide. The AI cites specific regulation articles and applies threshold logic built from official guidance. All low-confidence items are explicitly flagged for human review.",
  },
  {
    q: "Can I use this report as legal proof of compliance?",
    a: "No. This is a preliminary screening tool designed to help you understand your exposure before engaging a legal specialist. It is not a certified audit and does not constitute legal advice.",
  },
  {
    q: "What information do I need to provide?",
    a: "Basic company details: industry, employee count, revenue, whether you process personal data, supply chain presence, energy consumption, and governance practices. The form takes roughly 3 minutes to complete.",
  },
  {
    q: "Is my data stored or shared?",
    a: "Report data is stored securely and is only accessible via your unique report link. We do not share your data with third parties. Enterprise customers can request data residency and deletion guarantees.",
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

export default function HomePage() {
  return (
    <main className="bg-dark-950">

      {/* ── Hero ─────────────────────────────────────────────── */}
      <section className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden pt-20 sm:pt-28 pb-12 sm:pb-16">
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
                11 German and EU regulations covered
              </span>
            </motion.div>

            <motion.h1 variants={fadeUp} className="text-4xl sm:text-5xl lg:text-7xl font-black tracking-tight text-white leading-[1.04]">
              Know your{" "}
              <span className="shimmer-text">compliance gaps</span>
              <br />
              before they know you.
            </motion.h1>

            <motion.p variants={fadeUp} className="max-w-2xl text-base sm:text-lg text-slate-400 leading-relaxed px-2 sm:px-0">
              Submit your company profile and receive a detailed compliance screening across German and EU law in minutes. A solid foundation before any legal consultation.
            </motion.p>

            <motion.div variants={fadeUp} className="flex flex-col sm:flex-row gap-3">
              <Link href="/analyze" className="group inline-flex items-center justify-center gap-2 rounded-xl bg-brand-600 px-7 py-4 text-base font-semibold text-white shadow-glow-blue-sm hover:shadow-glow-blue hover:bg-brand-500 transition-all duration-300">
                Get started
                <ArrowRight className="h-4 w-4 group-hover:translate-x-0.5 transition-transform duration-200" />
              </Link>
              <a href="#pricing" className="inline-flex items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/5 px-7 py-4 text-base font-semibold text-slate-300 hover:bg-white/10 hover:text-white transition-all duration-200">
                See pricing
              </a>
            </motion.div>

            <motion.div variants={fadeUp} className="flex flex-wrap justify-center gap-6 text-xs text-slate-500">
              {["No account required", "Results in minutes", "5 regulations in one report"].map((t) => (
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
            <span className="text-xs font-medium text-slate-600 mr-1">Regulations covered</span>
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
          <p className="text-xs font-bold uppercase tracking-widest text-brand-400 mb-4">Who it is for</p>
          <h2 className="text-3xl sm:text-4xl font-black text-white tracking-tight mb-4">Built for German SMEs across every sector</h2>
          <p className="text-slate-500 max-w-xl mx-auto">Any company operating in Germany or the EU faces a web of overlapping regulations. Complio cuts through the complexity in minutes.</p>
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
            <p className="text-xs font-bold uppercase tracking-widest text-brand-400 mb-4">How it works</p>
            <h2 className="text-3xl sm:text-4xl font-black text-white tracking-tight">From profile to report in five steps</h2>
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

      {/* ── Features ──────────────────────────────────────────── */}
      <section id="features" className="border-t border-white/[0.05] py-16 sm:py-28">
        <div className="mx-auto max-w-6xl px-4 sm:px-6">
          <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.5 }} className="mb-12 sm:mb-16 text-center">
            <p className="text-xs font-bold uppercase tracking-widest text-brand-400 mb-4">What you get</p>
            <h2 className="text-3xl sm:text-4xl font-black text-white tracking-tight">Everything in one report</h2>
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
            <p className="text-xs font-bold uppercase tracking-widest text-brand-400 mb-4">Pricing</p>
            <h2 className="text-3xl sm:text-4xl font-black text-white tracking-tight mb-4">Simple, transparent pricing</h2>
            <p className="text-slate-500 max-w-lg mx-auto">Pay per screening or subscribe for ongoing monitoring. No hidden fees, no long-term lock-in.</p>
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
                      Most popular
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

                <Link
                  href={plan.cta === "Contact us" ? "mailto:hello@complio.io" : "/analyze"}
                  className={`w-full text-center rounded-xl py-3 text-sm font-semibold transition-all duration-200 ${
                    plan.highlight
                      ? "bg-brand-600 text-white hover:bg-brand-500 shadow-glow-blue-sm hover:shadow-glow-blue"
                      : "border border-white/12 bg-white/5 text-slate-300 hover:bg-white/10 hover:text-white"
                  }`}
                >
                  {plan.cta}
                </Link>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ── FAQ ───────────────────────────────────────────────── */}
      <section className="border-t border-white/[0.05] py-16 sm:py-28">
        <div className="mx-auto max-w-3xl px-4 sm:px-6">
          <motion.div initial={{ opacity: 0, y: 20 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true }} transition={{ duration: 0.5 }} className="mb-10 sm:mb-14 text-center">
            <p className="text-xs font-bold uppercase tracking-widest text-brand-400 mb-4">FAQ</p>
            <h2 className="text-3xl sm:text-4xl font-black text-white tracking-tight">Common questions</h2>
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
              Ready to find your
              <br />
              compliance gaps?
            </h2>
            <p className="text-base sm:text-lg text-slate-500 max-w-lg">
              Get a detailed compliance screening across 5 German and EU regulations. Not a substitute for legal advice.
            </p>
            <Link href="/analyze" className="group inline-flex items-center gap-2.5 rounded-xl bg-brand-600 px-8 py-4 text-base font-semibold text-white shadow-glow-blue-sm hover:shadow-glow-blue hover:bg-brand-500 transition-all duration-300">
              Get started
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
            </div>
            <p className="text-xs text-slate-600">Not legal advice. For informational purposes only.</p>
          </div>
        </div>
      </footer>

    </main>
  );
}
