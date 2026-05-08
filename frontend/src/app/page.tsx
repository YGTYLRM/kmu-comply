"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  ArrowRight, CheckCircle2, FileSearch, Zap, ShieldCheck,
  BarChart3, ListChecks, AlertTriangle,
} from "lucide-react";

const ease = [0.21, 0.47, 0.32, 0.98] as const;

const fadeUp = {
  hidden: { opacity: 0, y: 32 },
  show:   { opacity: 1, y: 0, transition: { duration: 0.6, ease } },
};

const stagger = (delay = 0) => ({
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: { staggerChildren: 0.13, delayChildren: delay },
  },
});

const REGULATIONS = [
  { name: "GDPR / DSGVO", desc: "Data protection" },
  { name: "BDSG",         desc: "German data privacy" },
  { name: "LkSG",         desc: "Supply chain" },
  { name: "EnEfG",        desc: "Energy efficiency" },
  { name: "CSRD",         desc: "Sustainability reporting" },
];

const STEPS = [
  { n: "01", title: "Enter your profile",    desc: "Five short steps covering company basics, finances, data practices, supply chain, and governance." },
  { n: "02", title: "AI analyses your data", desc: "Relevant regulation articles are retrieved and assessed against your company profile." },
  { n: "03", title: "Gaps are identified",   desc: "Each requirement is checked — compliant, partial, or non-compliant — with full evidence." },
  { n: "04", title: "Actions are prioritised", desc: "Every gap becomes a concrete action item with effort estimate and deadline guidance." },
  { n: "05", title: "Review your screening", desc: "A scored preliminary screening report by regulation and priority, with suggested next steps." },
];

const FEATURES = [
  { icon: FileSearch,    color: "text-blue-400",    bg: "bg-blue-500/10",     title: "Full regulation coverage", desc: "GDPR/DSGVO, BDSG, LkSG, EnEfG, and CSRD screened in a single run." },
  { icon: Zap,           color: "text-amber-400",   bg: "bg-amber-500/10",    title: "Results in minutes",       desc: "Automated screening. A solid starting point before engaging a legal consultant." },
  { icon: ListChecks,    color: "text-emerald-400", bg: "bg-emerald-500/10",  title: "Concrete action plan",     desc: "Each gap comes with a prioritised action from CRITICAL to LOW, with effort and deadline." },
  { icon: BarChart3,     color: "text-purple-400",  bg: "bg-purple-500/10",   title: "Per-regulation scoring",   desc: "Compliance score per regulation so you know exactly where to focus first." },
  { icon: ShieldCheck,   color: "text-rose-400",    bg: "bg-rose-500/10",     title: "Grounded in law",          desc: "Screening cites specific article numbers from official regulation texts, not generic checklists." },
  { icon: AlertTriangle, color: "text-orange-400",  bg: "bg-orange-500/10",   title: "Flags manual review",      desc: "When confidence is low, the report explicitly marks items for human legal review." },
];

function MockReport() {
  return (
    <div
      className="w-full max-w-lg rounded-3xl overflow-hidden border border-white/10 shadow-[0_0_80px_rgba(59,130,246,0.25),0_32px_64px_rgba(0,0,0,0.7)]"
      style={{ background: "rgba(10,22,40,0.9)", backdropFilter: "blur(24px)" }}
    >
      <div className="px-6 py-5 border-b border-white/[0.06] flex items-center justify-between">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-widest text-slate-500">Preliminary Screening</p>
          <p className="text-base font-bold text-white mt-0.5">Muster GmbH · IT / Software</p>
        </div>
        <div className="text-right">
          <span className="text-4xl font-black text-amber-400">68%</span>
          <p className="text-[10px] text-slate-500 mt-0.5">overall score</p>
        </div>
      </div>
      <div className="px-6 pt-5 pb-4 space-y-4">
        {[
          { reg: "GDPR / DSGVO", pct: 82, bar: "from-emerald-500 to-emerald-400" },
          { reg: "LkSG",         pct: 55, bar: "from-amber-500 to-amber-400"   },
          { reg: "EnEfG",        pct: 40, bar: "from-red-500 to-red-400"       },
          { reg: "BDSG",         pct: 75, bar: "from-emerald-400 to-teal-400"  },
        ].map(({ reg, pct, bar }) => (
          <div key={reg}>
            <div className="flex justify-between text-xs mb-2">
              <span className="font-semibold text-slate-300">{reg}</span>
              <span className="text-slate-500 tabular-nums">{pct}%</span>
            </div>
            <div className="h-2 w-full rounded-full bg-white/[0.06]">
              <div className={`h-2 rounded-full bg-gradient-to-r ${bar}`} style={{ width: `${pct}%` }} />
            </div>
          </div>
        ))}
      </div>
      <div className="px-6 py-4 border-t border-white/[0.06] bg-white/[0.02] flex flex-wrap gap-2">
        {[
          { label: "3 CRITICAL", cls: "bg-red-500/15 text-red-400 border-red-500/25" },
          { label: "5 HIGH",     cls: "bg-orange-500/15 text-orange-400 border-orange-500/25" },
          { label: "8 MEDIUM",   cls: "bg-amber-500/15 text-amber-400 border-amber-500/25" },
          { label: "4 LOW",      cls: "bg-green-500/15 text-green-400 border-green-500/25" },
        ].map(({ label, cls }) => (
          <span key={label} className={`rounded-full border px-3 py-1 text-[10px] font-bold tracking-wide ${cls}`}>
            {label}
          </span>
        ))}
      </div>
    </div>
  );
}

export default function HomePage() {
  return (
    <main className="bg-dark-950">

      {/* ── Hero ─────────────────────────────────────────────── */}
      <section className="relative min-h-screen flex flex-col items-center justify-center overflow-hidden pt-24 pb-16">
        {/* Orbs */}
        <div className="pointer-events-none absolute inset-0">
          <div className="animate-orb-1 absolute -top-32 right-0 h-[700px] w-[700px] rounded-full bg-brand-600/15 blur-[140px]" />
          <div className="animate-orb-2 absolute bottom-0 -left-32 h-[500px] w-[500px] rounded-full bg-cyan-500/8 blur-[120px]" />
        </div>
        {/* Dot grid */}
        <div
          className="pointer-events-none absolute inset-0"
          style={{
            backgroundImage: "radial-gradient(circle, rgba(255,255,255,0.05) 1px, transparent 1px)",
            backgroundSize: "28px 28px",
          }}
        />
        <div className="pointer-events-none absolute bottom-0 left-0 right-0 h-40 bg-gradient-to-t from-dark-950 to-transparent" />

        <div className="relative mx-auto max-w-5xl px-6 flex flex-col items-center text-center gap-8">
          <motion.div
            variants={stagger(0.05)}
            initial="hidden"
            animate="show"
            className="flex flex-col items-center gap-7"
          >
            {/* Badge */}
            <motion.div variants={fadeUp}>
              <span className="inline-flex items-center gap-2 rounded-full border border-brand-500/30 bg-brand-500/10 px-4 py-1.5 text-xs font-semibold text-brand-300">
                <span className="h-1.5 w-1.5 rounded-full bg-brand-400 animate-pulse-slow" />
                5 German and EU regulations covered
              </span>
            </motion.div>

            {/* H1 */}
            <motion.h1
              variants={fadeUp}
              className="text-5xl sm:text-6xl lg:text-7xl font-black tracking-tight text-white leading-[1.04]"
            >
              Know your{" "}
              <span className="shimmer-text">compliance gaps</span>
              <br />
              before they know you.
            </motion.h1>

            {/* Subtext */}
            <motion.p variants={fadeUp} className="max-w-2xl text-lg text-slate-400 leading-relaxed">
              Submit your company profile and receive a detailed compliance screening across German and EU law in minutes. A solid foundation before any legal consultation.
            </motion.p>

            {/* CTAs */}
            <motion.div variants={fadeUp} className="flex flex-col sm:flex-row gap-3">
              <Link
                href="/analyze"
                className="group inline-flex items-center justify-center gap-2 rounded-xl bg-brand-600 px-7 py-4 text-base font-semibold text-white shadow-glow-blue-sm hover:shadow-glow-blue hover:bg-brand-500 transition-all duration-300"
              >
                Get started
                <ArrowRight className="h-4 w-4 group-hover:translate-x-0.5 transition-transform duration-200" />
              </Link>
              <a
                href="#how-it-works"
                className="inline-flex items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/5 px-7 py-4 text-base font-semibold text-slate-300 hover:bg-white/10 hover:text-white transition-all duration-200"
              >
                How it works
              </a>
            </motion.div>

            {/* Trust row */}
            <motion.div variants={fadeUp} className="flex flex-wrap justify-center gap-6 text-xs text-slate-500">
              {["No account required", "Results in minutes", "5 regulations in one report"].map((t) => (
                <span key={t} className="flex items-center gap-1.5">
                  <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
                  {t}
                </span>
              ))}
            </motion.div>
          </motion.div>

          {/* Product shot */}
          <motion.div
            initial={{ opacity: 0, y: 48, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            transition={{ duration: 0.8, delay: 0.5, ease }}
            className="animate-float w-full flex justify-center mt-6"
          >
            <MockReport />
          </motion.div>
        </div>
      </section>

      {/* ── Regulation strip ─────────────────────────────────── */}
      <motion.section
        initial={{ opacity: 0 }}
        whileInView={{ opacity: 1 }}
        viewport={{ once: true }}
        transition={{ duration: 0.5 }}
        className="border-y border-white/[0.05] bg-dark-900/60 py-5"
      >
        <div className="mx-auto max-w-6xl px-6">
          <div className="flex flex-wrap items-center gap-2.5">
            <span className="text-xs font-medium text-slate-600 mr-1">Regulations covered</span>
            {REGULATIONS.map((r) => (
              <div
                key={r.name}
                className="flex items-center gap-1.5 rounded-lg border border-white/[0.07] bg-white/[0.03] px-3 py-1.5 text-xs font-medium text-slate-400"
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
      <section id="how-it-works" className="mx-auto max-w-6xl px-6 py-28">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="mb-16 text-center"
        >
          <p className="text-xs font-bold uppercase tracking-widest text-brand-400 mb-4">How it works</p>
          <h2 className="text-4xl font-black text-white tracking-tight">From profile to report in five steps</h2>
        </motion.div>

        <motion.div
          variants={stagger()}
          initial="hidden"
          whileInView="show"
          viewport={{ once: true, margin: "-60px" }}
          className="grid grid-cols-1 sm:grid-cols-5 gap-8 sm:gap-0"
        >
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
      </section>

      {/* ── Features ──────────────────────────────────────────── */}
      <section id="features" className="border-t border-white/[0.05] bg-dark-900/40 py-28">
        <div className="mx-auto max-w-6xl px-6">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
            className="mb-16 text-center"
          >
            <p className="text-xs font-bold uppercase tracking-widest text-brand-400 mb-4">What you get</p>
            <h2 className="text-4xl font-black text-white tracking-tight">Everything in one report</h2>
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
                  y: -5,
                  boxShadow: "0 0 0 1px rgba(59,130,246,0.22), 0 12px 40px rgba(0,0,0,0.55), 0 0 28px rgba(59,130,246,0.12)",
                  transition: { duration: 0.2 },
                }}
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

      {/* ── CTA ───────────────────────────────────────────────── */}
      <section className="border-t border-white/[0.05] relative overflow-hidden">
        <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
          <div className="h-[500px] w-[900px] rounded-full bg-brand-600/10 blur-[120px]" />
        </div>
        <div className="relative mx-auto max-w-4xl px-6 py-32 flex flex-col items-center text-center gap-8">
          <motion.div
            initial={{ opacity: 0, y: 24 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.55 }}
            className="flex flex-col items-center gap-6"
          >
            <h2 className="text-4xl lg:text-5xl font-black text-white tracking-tight leading-tight">
              Ready to find your
              <br />
              compliance gaps?
            </h2>
            <p className="text-lg text-slate-500 max-w-lg">
              Get a detailed compliance screening across 5 German and EU regulations. Not a substitute for legal advice.
            </p>
            <Link
              href="/analyze"
              className="group inline-flex items-center gap-2.5 rounded-xl bg-brand-600 px-8 py-4 text-base font-semibold text-white shadow-glow-blue-sm hover:shadow-glow-blue hover:bg-brand-500 transition-all duration-300"
            >
              Get started
              <ArrowRight className="h-4 w-4 group-hover:translate-x-0.5 transition-transform duration-200" />
            </Link>
          </motion.div>
        </div>
      </section>

      {/* ── Footer ────────────────────────────────────────────── */}
      <footer className="border-t border-white/[0.05] py-8">
        <div className="mx-auto max-w-6xl px-6 flex flex-col sm:flex-row items-center justify-between gap-4">
          <img src="/logo-transparent.png" alt="Complio" className="h-7 w-auto brightness-0 invert" />
          <p className="text-xs text-slate-600">Not legal advice. For informational purposes only.</p>
        </div>
      </footer>

    </main>
  );
}
