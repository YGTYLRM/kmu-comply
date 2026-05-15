"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, FileText, ShieldCheck, Bell, CheckCircle2 } from "lucide-react";

const STEPS = [
  {
    icon: <FileText className="h-5 w-5 text-brand-400" />,
    num: "01",
    title: "Fill in your company profile",
    desc: "5 minutes. Your size, industry, and how you operate. The more you fill in, the more precise the findings.",
  },
  {
    icon: <ShieldCheck className="h-5 w-5 text-brand-400" />,
    num: "02",
    title: "Get your compliance report",
    desc: "11 German and EU regulations checked automatically — GDPR, NIS2, AI Act, EnEfG / EDL-G, LkSG, CSRD and more. Scored, with a prioritized action plan.",
  },
  {
    icon: <Bell className="h-5 w-5 text-brand-400" />,
    num: "03",
    title: "Stay current automatically",
    desc: "We monitor regulation changes and re-run your screening when something that affects you changes. You get notified — no manual work.",
  },
];

const REGULATIONS = [
  "GDPR / DSGVO", "BDSG", "NIS2", "EU AI Act", "HinSchG",
  "ArbSchG", "AGG", "MiLoG", "LkSG", "EnEfG / EDL-G", "CSRD",
];

const WHAT_YOU_GET = [
  "Which of 11 regulations apply to your company",
  "Exactly where you have compliance gaps — and why",
  "A prioritized action plan with effort estimates",
  "A scored PDF report ready to share with advisors",
  "Automatic alerts when regulations change",
];

export default function WelcomePage() {
  return (
    <div className="bg-dark-950 min-h-screen pt-20 pb-16 px-4 sm:px-6">
      <div className="mx-auto max-w-2xl">

        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="text-center py-10"
        >
          <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/25 bg-emerald-500/10 px-4 py-1.5 text-xs font-bold text-emerald-400 mb-6">
            <CheckCircle2 className="h-3.5 w-3.5" />
            Account created — you&apos;re in
          </div>
          <h1 className="text-3xl font-black text-white tracking-tight mb-3">
            Welcome to Complio
          </h1>
          <p className="text-slate-400 text-sm leading-relaxed max-w-md mx-auto">
            Your autonomous compliance screening agent for German SME law.
            Here&apos;s everything you need to know to get started.
          </p>
        </motion.div>

        {/* How it works */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.1 }}
          className="mb-6"
        >
          <p className="text-xs font-bold uppercase tracking-widest text-brand-400 mb-3">How it works</p>
          <div className="flex flex-col gap-3">
            {STEPS.map((s, i) => (
              <div key={i} className="flex gap-4 rounded-2xl border border-white/[0.07] bg-dark-900/60 p-5">
                <div className="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-xl bg-brand-500/10 border border-brand-500/20">
                  {s.icon}
                </div>
                <div>
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-xs font-bold text-brand-500 tracking-widest">{s.num}</span>
                    <h3 className="text-sm font-bold text-white">{s.title}</h3>
                  </div>
                  <p className="text-xs text-slate-500 leading-relaxed">{s.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        {/* What you get */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.2 }}
          className="rounded-2xl border border-white/[0.07] bg-dark-900/60 p-6 mb-6"
        >
          <p className="text-xs font-bold uppercase tracking-widest text-brand-400 mb-4">What you get in every report</p>
          <ul className="flex flex-col gap-2.5">
            {WHAT_YOU_GET.map((item, i) => (
              <li key={i} className="flex items-start gap-2.5 text-sm text-slate-300">
                <CheckCircle2 className="h-4 w-4 text-emerald-400 flex-shrink-0 mt-0.5" />
                {item}
              </li>
            ))}
          </ul>
        </motion.div>

        {/* Regulations covered */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.25 }}
          className="mb-8"
        >
          <p className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-3">Regulations covered</p>
          <div className="flex flex-wrap gap-2">
            {REGULATIONS.map((r) => (
              <span key={r} className="rounded-full border border-white/[0.08] bg-white/[0.03] px-3 py-1 text-xs text-slate-400">
                {r}
              </span>
            ))}
          </div>
        </motion.div>

        {/* CTA */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.3 }}
          className="text-center"
        >
          <Link
            href="/analyze"
            className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-8 py-4 text-sm font-bold text-white hover:bg-brand-500 transition-all shadow-glow-blue-sm hover:shadow-glow-blue"
          >
            Start your first screening
            <ArrowRight className="h-4 w-4" />
          </Link>
          <p className="mt-3 text-xs text-slate-600">
            Takes about 2 minutes · Report is ready instantly
          </p>
          <p className="mt-4 text-xs text-slate-700">
            <Link href="/dashboard" className="hover:text-slate-500 transition-colors underline underline-offset-2">
              Go to dashboard instead
            </Link>
          </p>
        </motion.div>

      </div>
    </div>
  );
}
