"use client";

import { useState, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import {
  Mail, Building2, MessageSquare, User, CheckCircle2,
  AlertCircle, Phone, Tag, Clock, ArrowRight,
} from "lucide-react";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const TOPICS = [
  "Angebot anfordern: Starter",
  "Angebot anfordern: Professional",
  "Angebot anfordern: Enterprise",
  "API-Zugang",
  "Individueller Regelungsumfang",
  "Partnerschaft / Reseller",
  "Technischer Support",
  "Sonstiges",
];

const PLAN_TOPIC: Record<string, string> = {
  starter:      "Angebot anfordern: Starter",
  professional: "Angebot anfordern: Professional",
  enterprise:   "Angebot anfordern: Enterprise",
};

const NEXT_STEPS = [
  { n: "01", text: "Wir lesen Ihre Nachricht und leiten sie an die richtige Person weiter." },
  { n: "02", text: "Sie erhalten innerhalb eines Werktags eine Antwort." },
  { n: "03", text: "Falls es passt, vereinbaren wir ein kurzes Gespräch." },
];

function Field({
  icon: Icon,
  label,
  optional,
  ...props
}: { icon: React.ElementType; label: string; optional?: boolean } & React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="flex items-center gap-2 text-xs font-semibold text-slate-400 uppercase tracking-widest">
        <Icon className="h-3.5 w-3.5" />
        {label}
        {optional && <span className="ml-1 normal-case font-normal text-slate-600">optional</span>}
      </label>
      <input
        {...props}
        className="w-full rounded-xl border border-white/[0.08] bg-white/[0.03] px-4 py-3 text-sm text-white placeholder-slate-600 outline-none focus:border-brand-500/50 focus:ring-2 focus:ring-brand-500/15 transition-all duration-200"
      />
    </div>
  );
}

function ContactInner() {
  const searchParams = useSearchParams();
  const planParam    = searchParams.get("plan") ?? "";
  const preTopic     = PLAN_TOPIC[planParam] ?? "";

  const [sent,    setSent]    = useState(false);
  const [loading, setLoading] = useState(false);
  const [error,   setError]   = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const fd = new FormData(e.currentTarget);
    const body = {
      name:    fd.get("name")    as string,
      email:   fd.get("email")   as string,
      company: fd.get("company") as string || undefined,
      phone:   fd.get("phone")   as string || undefined,
      topic:   fd.get("topic")   as string || undefined,
      message: fd.get("message") as string,
    };

    try {
      const res = await fetch(`${BASE}/api/contact`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail ?? "Etwas ist schiefgelaufen. Bitte versuchen Sie es erneut.");
      }
      setSent(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Etwas ist schiefgelaufen.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="bg-dark-950 min-h-screen pt-24">
      <div className="mx-auto max-w-5xl px-4 sm:px-6 py-12 sm:py-16">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="grid lg:grid-cols-[1fr_1.5fr] gap-10 lg:gap-16 items-start"
        >
          <div className="flex flex-col gap-8">
            <div>
              <p className="text-xs font-bold uppercase tracking-widest text-brand-400 mb-3">Kontakt</p>
              <h1 className="text-3xl font-black text-white tracking-tight mb-4">Schreiben Sie uns</h1>
              <p className="text-sm text-slate-500 leading-relaxed">
                Fragen zu Preisen, Enterprise-Paketen oder technischen Details. Wir antworten innerhalb eines Werktags.
              </p>
            </div>

            <div className="flex flex-col gap-3">
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-xl bg-brand-500/10">
                  <Mail className="h-4 w-4 text-brand-400" />
                </div>
                <div>
                  <p className="text-xs text-slate-500">E-Mail</p>
                  <p className="text-sm font-medium text-white">hellocomplio@gmail.com</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-xl bg-brand-500/10">
                  <Clock className="h-4 w-4 text-brand-400" />
                </div>
                <div>
                  <p className="text-xs text-slate-500">Antwortzeit</p>
                  <p className="text-sm font-medium text-white">Innerhalb 1 Werktag</p>
                </div>
              </div>
            </div>

            <div>
              <p className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-4">Was als nächstes passiert</p>
              <div className="flex flex-col gap-4">
                {NEXT_STEPS.map(({ n, text }) => (
                  <div key={n} className="flex items-start gap-3">
                    <div className="flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full border border-brand-500/30 bg-brand-500/8 text-[11px] font-black text-brand-400">
                      {n}
                    </div>
                    <p className="text-sm text-slate-400 leading-relaxed pt-0.5">{text}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-5">
              <p className="text-xs font-bold text-white mb-1.5">Enterprise-Anfragen</p>
              <p className="text-xs text-slate-500 leading-relaxed">
                Für Unternehmen mit mehreren Einheiten, API-Bedarf oder individuellem Regelungsumfang bieten wir maßgeschneiderte Pakete. Wählen Sie im Formular das Thema Enterprise-Preise.
              </p>
            </div>
          </div>

          <div>
            {sent ? (
              <motion.div
                initial={{ opacity: 0, scale: 0.97 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.35 }}
                className="rounded-2xl border border-emerald-500/25 bg-emerald-500/8 px-8 py-14 text-center"
              >
                <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-500/15">
                  <CheckCircle2 className="h-7 w-7 text-emerald-400" />
                </div>
                <h2 className="text-xl font-bold text-white mb-2">Nachricht gesendet</h2>
                <p className="text-sm text-slate-500 mb-6">Wir melden uns innerhalb eines Werktags bei Ihnen.</p>
                <div className="flex flex-col gap-2 text-sm text-slate-500">
                  {NEXT_STEPS.map(({ n, text }) => (
                    <div key={n} className="flex items-start gap-2 text-left">
                      <ArrowRight className="h-3.5 w-3.5 text-brand-400 flex-shrink-0 mt-0.5" />
                      <span>{text}</span>
                    </div>
                  ))}
                </div>
              </motion.div>
            ) : (
              <form
                onSubmit={handleSubmit}
                className="rounded-2xl border border-white/[0.07] bg-dark-900/60 p-6 sm:p-8 flex flex-col gap-5"
              >
                <div className="grid sm:grid-cols-2 gap-5">
                  <Field icon={User}      label="Name"         type="text"  name="name"    placeholder="Anna Müller"     required />
                  <Field icon={Mail}      label="E-Mail"       type="email" name="email"   placeholder="anna@company.de" required />
                </div>

                <div className="grid sm:grid-cols-2 gap-5">
                  <Field icon={Building2} label="Unternehmen"  type="text" name="company" placeholder="Muster GmbH"     optional />
                  <Field icon={Phone}     label="Telefon"      type="tel"  name="phone"   placeholder="+49 30 12345678" optional />
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="flex items-center gap-2 text-xs font-semibold text-slate-400 uppercase tracking-widest">
                    <Tag className="h-3.5 w-3.5" />
                    Thema
                    <span className="ml-1 normal-case font-normal text-slate-600">optional</span>
                  </label>
                  <select
                    name="topic"
                    defaultValue={preTopic}
                    className="w-full rounded-xl border border-white/[0.08] bg-dark-900 px-4 py-3 text-sm text-slate-300 outline-none focus:border-brand-500/50 focus:ring-2 focus:ring-brand-500/15 transition-all duration-200 appearance-none cursor-pointer"
                  >
                    <option value="" disabled className="text-slate-600">Thema auswählen...</option>
                    {TOPICS.map(t => (
                      <option key={t} value={t} className="bg-dark-900 text-white">{t}</option>
                    ))}
                  </select>
                </div>

                <div className="flex flex-col gap-1.5">
                  <label className="flex items-center gap-2 text-xs font-semibold text-slate-400 uppercase tracking-widest">
                    <MessageSquare className="h-3.5 w-3.5" />
                    Nachricht
                  </label>
                  <textarea
                    name="message"
                    rows={5}
                    required
                    placeholder="Wie können wir Ihnen helfen? Je mehr Details, desto schneller können wir antworten."
                    className="w-full rounded-xl border border-white/[0.08] bg-white/[0.03] px-4 py-3 text-sm text-white placeholder-slate-600 outline-none focus:border-brand-500/50 focus:ring-2 focus:ring-brand-500/15 transition-all duration-200 resize-none"
                  />
                </div>

                {error && (
                  <div className="flex items-start gap-2 rounded-xl bg-red-500/10 border border-red-500/25 px-4 py-3 text-sm text-red-400">
                    <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
                    {error}
                  </div>
                )}

                <button
                  type="submit"
                  disabled={loading}
                  className="rounded-xl bg-brand-600 px-6 py-3.5 text-sm font-semibold text-white hover:bg-brand-500 transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? "Wird gesendet…" : "Nachricht senden"}
                </button>

                <p className="text-xs text-slate-600 text-center">
                  Mit dem Absenden stimmen Sie zu, dass wir Ihre Daten zur Beantwortung Ihrer Anfrage speichern.
                </p>
              </form>
            )}
          </div>
        </motion.div>
      </div>
    </main>
  );
}

export default function ContactPage() {
  return (
    <Suspense fallback={<main className="bg-dark-950 min-h-screen pt-24" />}>
      <ContactInner />
    </Suspense>
  );
}
