"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, FileText, ShieldCheck, Bell, CheckCircle2 } from "lucide-react";

const STEPS = [
  {
    icon: <FileText className="h-5 w-5 text-brand-400" />,
    num: "01",
    title: "Unternehmensprofil ausfüllen",
    desc: "5 Minuten. Branche, Größe, Datenpraktiken. Je mehr Sie angeben, desto präziser der Bericht.",
  },
  {
    icon: <ShieldCheck className="h-5 w-5 text-brand-400" />,
    num: "02",
    title: "Compliance-Bericht erhalten",
    desc: "14 Gesetze automatisch geprüft: DSGVO, NIS2, EU AI Act, LkSG, CSRD und mehr. Mit Score und priorisiertem Maßnahmenplan.",
  },
  {
    icon: <Bell className="h-5 w-5 text-brand-400" />,
    num: "03",
    title: "Automatisch aktuell bleiben",
    desc: "Wir verfolgen Gesetzesänderungen. Wenn sich etwas ändert, das Sie betrifft, werden Sie benachrichtigt.",
  },
];

const REGULATIONS = [
  "GDPR / DSGVO", "BDSG", "NIS2", "EU AI Act", "HinSchG",
  "ArbSchG", "AGG", "MiLoG", "LkSG", "EnEfG / EDL-G", "CSRD",
];

const WHAT_YOU_GET = [
  "Welche der 14 Vorschriften für Ihr Unternehmen gelten",
  "Wo genau Sie Lücken haben und warum",
  "Ein priorisierter Maßnahmenplan mit Aufwandsschätzung",
  "Ein bewerteter PDF-Bericht zur Weitergabe an Berater",
  "Automatische Benachrichtigungen bei Gesetzesänderungen",
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
            Konto erstellt
          </div>
          <h1 className="text-3xl font-black text-white tracking-tight mb-3">
            Willkommen bei Complio
          </h1>
          <p className="text-slate-400 text-sm leading-relaxed max-w-md mx-auto">
            Ihr Compliance-Screening-Tool für deutsches und EU-Recht.
            Hier ist alles, was Sie für den Start brauchen.
          </p>
        </motion.div>

        {/* How it works */}
        <motion.div
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.1 }}
          className="mb-6"
        >
          <p className="text-xs font-bold uppercase tracking-widest text-brand-400 mb-3">So funktioniert es</p>
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
          <p className="text-xs font-bold uppercase tracking-widest text-brand-400 mb-4">Was jeder Bericht enthält</p>
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
          <p className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-3">Abgedeckte Vorschriften</p>
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
            href="/account/billing"
            className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-8 py-4 text-sm font-bold text-white hover:bg-brand-500 transition-all shadow-glow-blue-sm hover:shadow-glow-blue"
          >
            Plan auswählen & starten
            <ArrowRight className="h-4 w-4" />
          </Link>
          <p className="mt-3 text-xs text-slate-600">
            Plan auswählen · Screening sofort verfügbar
          </p>
          <p className="mt-4 text-xs text-slate-700">
            <Link href="/dashboard" className="hover:text-slate-500 transition-colors underline underline-offset-2">
              Zum Dashboard
            </Link>
          </p>
        </motion.div>

      </div>
    </div>
  );
}
