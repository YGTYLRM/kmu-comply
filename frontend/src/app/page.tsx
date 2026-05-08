"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  ArrowRight, CheckCircle2, FileSearch, Zap, ShieldCheck,
  BarChart3, ListChecks, AlertTriangle,
} from "lucide-react";

const ease = [0.21, 0.47, 0.32, 0.98] as const;

const fadeUp = {
  hidden: { opacity: 0, y: 28 },
  show:   { opacity: 1, y: 0, transition: { duration: 0.55, ease } },
};

const stagger = (delay = 0) => ({
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.11, delayChildren: delay },
  },
});

const REGULATIONS = [
  { name: "GDPR / DSGVO", desc: "Data protection" },
  { name: "BDSG",         desc: "German data privacy" },
  { name: "LkSG",         desc: "Supply chain due diligence" },
  { name: "EnEfG",        desc: "Energy efficiency" },
  { name: "CSRD",         desc: "Sustainability reporting" },
];

const STEPS = [
  { n: "01", title: "Enter your profile",    desc: "Five short steps: company basics, finances, data practices, supply chain, and governance." },
  { n: "02", title: "AI analyses your data", desc: "Relevant regulation articles are retrieved and assessed against your company profile." },
  { n: "03", title: "Gaps are identified",   desc: "Each requirement is checked — compliant, partial, or non-compliant — with full evidence." },
  { n: "04", title: "Actions are prioritised", desc: "Every gap becomes a concrete action item with effort estimate and deadline guidance." },
  { n: "05", title: "Review your screening", desc: "A scored, preliminary screening report — by regulation, by priority, with suggested next steps." },
];

const FEATURES = [
  { icon: FileSearch,    color: "text-blue-400",   bg: "bg-blue-500/10",    title: "Full regulation coverage", desc: "GDPR/DSGVO, BDSG, LkSG, EnEfG, and CSRD — all five frameworks screened in one run." },
  { icon: Zap,           color: "text-amber-400",  bg: "bg-amber-500/10",   title: "Results in minutes",       desc: "Automated screening — a solid starting point before engaging a legal consultant." },
  { icon: ListChecks,    color: "text-emerald-400",bg: "bg-emerald-500/10", title: "Concrete action plan",     desc: "Each gap comes with a prioritised action — CRITICAL to LOW — with effort and deadline." },
  { icon: BarChart3,     color: "text-purple-400", bg: "bg-purple-500/10",  title: "Per-regulation scoring",   desc: "Compliance score per regulation so you know exactly where to focus first." },
  { icon: ShieldCheck,   color: "text-rose-400",   bg: "bg-rose-500/10",    title: "Grounded in law",          desc: "Screening cites specific article numbers from official regulation texts — not generic checklists." },
  { icon: AlertTriangle, color: "text-orange-400", bg: "bg-orange-500/10",  title: "Flags manual review",      desc: "When confidence is low, the report explicitly marks items for human legal review." },
];

function MockReport() {
  return (
    <motion.div
      initial={{ opacity: 0, x: 48, y: 16 }}
      animate={{ opacity: 1, x: 0,  y: 0  }}
      transition={{ duration: 0.7, delay: 0.4, ease }}
      className="animate-float w-full max-w-sm rounded-2xl overflow-hidden select-none shadow-[0_0_60px_rgba(59,130,246,0.2),0_24px_48px_rgba(0,0,0,0.6)] border border-white/10"
      style={{ background: "rgba(10,22,40,0.85)", backdropFilter: "blur(20px)" }}
    >
      {/* Header */}
      <div className="px-5 py-4 border-b border-white/8 flex items-center justify-between">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-widest text-slate-500">Preliminary Screening</p>
          <p className="text-sm font-bold text-white mt-0.5">Muster GmbH · IT / Software</p>
        </div>
        <div className="text-right">
          <span className="text-3xl font-bold text-amber-400">68%</span>
          <p className="text-[10px] text-slate-500">overall score</p>
        </div>
      </div>

      {/* Bars */}
      <div className="px-5 pt-4 pb-3 space-y-3.5">
        {[
          { reg: "GDPR / DSGVO", pct: 82, bar: "bg-emerald-500" },
          { reg: "LkSG",         pct: 55, bar: "bg-amber-500"   },
          { reg: "EnEfG",        pct: 40, bar: "bg-red-500"     },
          { reg: "BDSG",         pct: 75, bar: "bg-emerald-400" },
        ].map(({ reg, pct, bar }) => (
          <div key={reg}>
            <div className="flex justify-between text-xs mb-1.5">
              <span className="font-medium text-slate-300">{reg}</span>
              <span className="text-slate-500">{pct}%</span>
            </div>
            <div className="h-1.5 w-full rounded-full bg-white/8">
              <div className={`h-1.5 rounded-full ${bar}`} style={{ width: `${pct}%` }} />
            </div>
          </div>
        ))}
      </div>

      {/* Badges */}
      <div className="px-5 py-3.5 border-t border-white/8 bg-white/[0.02] flex flex-wrap gap-1.5">
        {[
          { label: "3 CRITICAL", cls: "bg-red-500/15 text-red-400 border-red-500/25" },
          { label: "5 HIGH",     cls: "bg-orange-500/15 text-orange-400 border-orange-500/25" },
          { label: "8 MEDIUM",   cls: "bg-amber-500/15 text-amber-400 border-amber-500/25" },
          { label: "4 LOW",      cls: "bg-green-500/15 text-green-400 border-green-500/25" },
        ].map(({ label, cls }) => (
          <span key={label} className={`rounded-full border px-2.5 py-1 text-[10px] font-bold ${cls}`}>
            {label}
          </span>
        ))}
      </div>
    </motion.div>
  );
}

export default function HomePage() {
  return (
    <main className="bg-dark-950">
      {/* ── Hero ─────────────────────────────────────────────── */}
      <section className="relative overflow-hidden">
        {/* Background orbs */}
        <div className="pointer-events-none absolute inset-0">
          <div className="animate-orb-1 absolute -top-40 right-0 h-[600px] w-[600px] rounded-full bg-brand-600/20 blur-[120px]" />
          <div className="animate-orb-2 absolute top-60 -left-20 h-[400px] w-[400px] rounded-full bg-cyan-500/10 blur-[100px]" />
        </div>
        {/* Dot grid */}
        <div
          className="pointer-events-none absolute inset-0 opacity-100"
          style={{
            backgroundImage: "radial-gradient(circle, rgba(255,255,255,0.055) 1px, transparent 1px)",
            backgroundSize: "28px 28px",
          }}
        />
        {/* Fade bottom */}
        <div className="pointer-events-none absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-dark-950 to-transparent" />

        <div className="relative mx-auto max-w-6xl px-6 py-24 lg:py-32">
          <div className="grid lg:grid-cols-2 gap-16 items-center">

            {/* Left copy */}
            <motion.div
              variants={stagger(0.1)}
              initial="hidden"
              animate="show"
              className="flex flex-col gap-7"
            >
              <motion.div variants={fadeUp}>
                <span className="inline-flex items-center gap-2 rounded-full border border-brand-500/30 bg-brand-500/10 px-3.5 py-1.5 text-xs font-semibold text-brand-300">
                  <span className="h-1.5 w-1.5 rounded-full bg-brand-400 animate-pulse-slow" />
                  5 German &amp; EU regulations covered
                </span>
              </motion.div>

              <motion.h1
                variants={fadeUp}
                className="text-4xl lg:text-[3.25rem] font-bold tracking-tight text-white leading-[1.08]"
              >
                Regulatory compliance
                <br />
                screening —{" "}
                <span className="shimmer-text">automated</span>
              </motion.h1>

              <motion.p variants={fadeUp} className="text-lg text-slate-400 leading-relaxed">
                Submit your company profile and get a preliminary compliance screening across German and EU law in minutes — a solid starting point before any legal consultation.
              </motion.p>

              <motion.div variants={fadeUp} className="flex flex-col sm:flex-row gap-3">
                <Link
                  href="/analyze"
                  className="group inline-flex items-center justify-center gap-2 rounded-xl bg-brand-600 px-6 py-3.5 text-sm font-semibold text-white shadow-glow-blue-sm hover:shadow-glow-blue hover:bg-brand-500 transition-all duration-300"
                >
                  Start free screening
                  <ArrowRight className="h-4 w-4 group-hover:translate-x-0.5 transition-transform duration-200" />
                </Link>
                <a
                  href="#how-it-works"
                  className="inline-flex items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/5 px-6 py-3.5 text-sm font-semibold text-slate-300 hover:bg-white/10 hover:text-white transition-all duration-200"
                >
                  See how it works
                </a>
              </motion.div>

              <motion.div variants={fadeUp} className="flex flex-wrap gap-5 text-xs text-slate-500">
                {["No account required", "Takes ~3 minutes", "Completely free"].map((t) => (
                  <span key={t} className="flex items-center gap-1.5">
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
                    {t}
                  </span>
                ))}
              </motion.div>
            </motion.div>

            {/* Right mock card */}
            <div className="flex justify-center lg:justify-end">
              <MockReport />
            </div>
          </div>
        </div>
      </section>

      {/* ── Regulations strip ─────────────────────────────────── */}
      <motion.section
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{ duration: 0.5 }}
        className="border-y border-white/[0.06] bg-dark-900/50 py-4"
      >
        <div className="mx-auto max-w-6xl px-6">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-medium text-slate-600 mr-1">Regulations covered</span>
            {REGULATIONS.map((r) => (
              <div
                key={r.name}
                className="flex items-center gap-1.5 rounded-lg border border-white/8 bg-white/[0.04] px-3 py-1.5 text-xs font-medium text-slate-300"
              >
                <span className="h-1.5 w-1.5 rounded-full bg-brand-500" />
                {r.name}
                <span className="text-slate-600 font-normal">· {r.desc}</span>
              </div>
            ))}
          </div>
        </div>
      </motion.section>

      {/* ── How it works ──────────────────────────────────────── */}
      <section id="how-it-works" className="mx-auto max-w-6xl px-6 py-24">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="mb-14"
        >
          <p className="text-xs font-bold uppercase tracking-widest text-brand-400 mb-3">How it works</p>
          <h2 className="text-3xl font-bold text-white tracking-tight">From profile to report in five steps</h2>
        </motion.div>

        <motion.div
          variants={stagger()}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: "-60px" }}
          className="grid grid-cols-1 sm:grid-cols-5 gap-6 sm:gap-0"
        >
          {STEPS.map(({ n, title, desc }, i) => (
            <motion.div key={n} variants={fadeUp} className="relative flex flex-col gap-3 sm:px-4 pb-2">
              {i < STEPS.length - 1 && (
                <div className="hidden sm:block absolute top-5 left-[calc(50%+24px)] right-0 h-px bg-gradient-to-r from-brand-500/40 to-transparent" />
              )}
              <div className="relative z-10 flex h-10 w-10 items-center justify-center rounded-full border border-brand-500/40 bg-brand-500/10 text-xs font-bold text-brand-400 shadow-glow-blue-sm">
                {n}
              </div>
              <p className="text-sm font-semibold text-white leading-snug">{title}</p>
              <p className="text-xs text-slate-500 leading-relaxed">{desc}</p>
            </motion.div>
          ))}
        </motion.div>
      </section>

      {/* ── Features ──────────────────────────────────────────── */}
      <section className="border-t border-white/[0.06] bg-dark-900/40 py-24">
        <div className="mx-auto max-w-6xl px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="mb-14"
          >
            <p className="text-xs font-bold uppercase tracking-widest text-brand-400 mb-3">What you get</p>
            <h2 className="text-3xl font-bold text-white tracking-tight">Everything in one report</h2>
          </motion.div>

          <motion.div
            variants={stagger()}
            initial="hidden"
            whileInView="show"
            viewport={{ once: true, margin: "-60px" }}
            className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4"
          >
            {FEATURES.map(({ icon: Icon, color, bg, title, desc }) => (
              <motion.div
                key={title}
                variants={fadeUp}
                whileHover={{
                  y: -4,
                  boxShadow: "0 0 0 1px rgba(59,130,246,0.25), 0 8px 32px rgba(0,0,0,0.5), 0 0 20px rgba(59,130,246,0.12)",
                  transition: { duration: 0.2 },
                }}
                className="rounded-2xl border border-white/[0.07] p-6 shadow-card-dark cursor-default"
                style={{ background: "rgba(10,22,40,0.7)" }}
              >
                <div className={`mb-4 flex h-10 w-10 items-center justify-center rounded-xl ${bg}`}>
                  <Icon className={`h-5 w-5 ${color}`} />
                </div>
                <h3 className="text-sm font-semibold text-white mb-1.5">{title}</h3>
                <p className="text-sm text-slate-500 leading-relaxed">{desc}</p>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* ── CTA ───────────────────────────────────────────────── */}
      <section className="border-t border-white/[0.06] relative overflow-hidden">
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
          <div className="h-[400px] w-[700px] rounded-full bg-brand-600/10 blur-[100px]" />
        </div>
        <div className="relative mx-auto max-w-6xl px-6 py-24 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-10">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
          >
            <h2 className="text-2xl font-bold text-white tracking-tight mb-2">
              Ready for a preliminary screening?
            </h2>
            <p className="text-slate-500 text-sm">Free, instant, no sign-up. Takes about 3 minutes. Not a substitute for legal advice.</p>
          </motion.div>
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, delay: 0.15 }}
          >
            <Link
              href="/analyze"
              className="group flex-shrink-0 inline-flex items-center gap-2 rounded-xl bg-brand-600 px-8 py-4 text-sm font-semibold text-white shadow-glow-blue-sm hover:shadow-glow-blue hover:bg-brand-500 transition-all duration-300"
            >
              Start free analysis
              <ArrowRight className="h-4 w-4 group-hover:translate-x-0.5 transition-transform duration-200" />
            </Link>
          </motion.div>
        </div>
      </section>

      <footer className="border-t border-white/[0.06] py-6 text-center text-xs text-slate-600">
        Complio · Not legal advice · For informational purposes only
      </footer>
    </main>
  );
}
