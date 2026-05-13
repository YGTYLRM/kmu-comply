"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  Mail, Building2, MessageSquare, User, CheckCircle2,
  AlertCircle, Phone, Tag, Clock, ArrowRight,
} from "lucide-react";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const TOPICS = [
  "Enterprise pricing",
  "API access",
  "Custom regulation scope",
  "Partnership or reseller",
  "Technical support",
  "Other",
];

const NEXT_STEPS = [
  { n: "01", text: "We read your message and route it to the right person." },
  { n: "02", text: "You receive a reply within one business day." },
  { n: "03", text: "If it is a fit, we schedule a short call to go deeper." },
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

export default function ContactPage() {
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
        throw new Error(data.detail ?? "Something went wrong. Please try again.");
      }
      setSent(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
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
          {/* ── Left: info panel ── */}
          <div className="flex flex-col gap-8">
            <div>
              <p className="text-xs font-bold uppercase tracking-widest text-brand-400 mb-3">Get in touch</p>
              <h1 className="text-3xl font-black text-white tracking-tight mb-4">Contact us</h1>
              <p className="text-sm text-slate-500 leading-relaxed">
                Whether you need enterprise pricing, a custom regulation scope, or just have a question — we are happy to help.
              </p>
            </div>

            {/* Contact details */}
            <div className="flex flex-col gap-3">
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-xl bg-brand-500/10">
                  <Mail className="h-4 w-4 text-brand-400" />
                </div>
                <div>
                  <p className="text-xs text-slate-500">Email</p>
                  <p className="text-sm font-medium text-white">hellocomplio@gmail.com</p>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-xl bg-brand-500/10">
                  <Clock className="h-4 w-4 text-brand-400" />
                </div>
                <div>
                  <p className="text-xs text-slate-500">Response time</p>
                  <p className="text-sm font-medium text-white">Within 1 business day</p>
                </div>
              </div>
            </div>

            {/* What happens next */}
            <div>
              <p className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-4">What happens next</p>
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

            {/* Enterprise note */}
            <div className="rounded-2xl border border-white/[0.06] bg-white/[0.02] p-5">
              <p className="text-xs font-bold text-white mb-1.5">Enterprise inquiries</p>
              <p className="text-xs text-slate-500 leading-relaxed">
                For organisations with multiple entities, API integration needs, or a custom regulation scope, we offer tailored packages. Use the form and select Enterprise pricing as your topic.
              </p>
            </div>
          </div>

          {/* ── Right: form ── */}
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
                <h2 className="text-xl font-bold text-white mb-2">Message sent</h2>
                <p className="text-sm text-slate-500 mb-6">We will get back to you within one business day.</p>
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
                  <Field icon={User}      label="Name"    type="text"  name="name"    placeholder="Anna Müller"     required />
                  <Field icon={Mail}      label="Email"   type="email" name="email"   placeholder="anna@company.de" required />
                </div>

                <div className="grid sm:grid-cols-2 gap-5">
                  <Field icon={Building2} label="Company" type="text" name="company" placeholder="Muster GmbH" optional />
                  <Field icon={Phone}     label="Phone"   type="tel"  name="phone"   placeholder="+49 30 12345678" optional />
                </div>

                {/* Topic selector */}
                <div className="flex flex-col gap-1.5">
                  <label className="flex items-center gap-2 text-xs font-semibold text-slate-400 uppercase tracking-widest">
                    <Tag className="h-3.5 w-3.5" />
                    Topic
                    <span className="ml-1 normal-case font-normal text-slate-600">optional</span>
                  </label>
                  <select
                    name="topic"
                    defaultValue=""
                    className="w-full rounded-xl border border-white/[0.08] bg-dark-900 px-4 py-3 text-sm text-slate-300 outline-none focus:border-brand-500/50 focus:ring-2 focus:ring-brand-500/15 transition-all duration-200 appearance-none cursor-pointer"
                  >
                    <option value="" disabled className="text-slate-600">Select a topic...</option>
                    {TOPICS.map(t => (
                      <option key={t} value={t} className="bg-dark-900 text-white">{t}</option>
                    ))}
                  </select>
                </div>

                {/* Message */}
                <div className="flex flex-col gap-1.5">
                  <label className="flex items-center gap-2 text-xs font-semibold text-slate-400 uppercase tracking-widest">
                    <MessageSquare className="h-3.5 w-3.5" />
                    Message
                  </label>
                  <textarea
                    name="message"
                    rows={5}
                    required
                    placeholder="Tell us how we can help. The more detail you share, the faster we can respond."
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
                  className="rounded-xl bg-brand-600 px-6 py-3.5 text-sm font-semibold text-white hover:bg-brand-500 transition-colors duration-200 shadow-glow-blue-sm hover:shadow-glow-blue disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? "Sending..." : "Send message"}
                </button>

                <p className="text-xs text-slate-600 text-center">
                  By submitting you agree that we store your details to respond to your inquiry.
                </p>
              </form>
            )}
          </div>
        </motion.div>
      </div>
    </main>
  );
}
