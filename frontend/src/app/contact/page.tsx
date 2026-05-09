"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Mail, Building2, MessageSquare, User, CheckCircle2, AlertCircle } from "lucide-react";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function Field({
  icon: Icon,
  label,
  ...props
}: { icon: React.ElementType; label: string } & React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="flex items-center gap-2 text-xs font-semibold text-slate-400 uppercase tracking-widest">
        <Icon className="h-3.5 w-3.5" />
        {label}
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
      <div className="mx-auto max-w-xl px-4 sm:px-6 py-12 sm:py-16">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <div className="mb-10 text-center">
            <p className="text-xs font-bold uppercase tracking-widest text-brand-400 mb-3">Get in touch</p>
            <h1 className="text-3xl font-black text-white tracking-tight mb-3">Contact us</h1>
            <p className="text-sm text-slate-500 leading-relaxed max-w-sm mx-auto">
              Questions about enterprise pricing, custom regulation scope, or API access? We will get back to you within one business day.
            </p>
          </div>

          {sent ? (
            <motion.div
              initial={{ opacity: 0, scale: 0.97 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.35 }}
              className="rounded-2xl border border-emerald-500/25 bg-emerald-500/8 px-8 py-12 text-center"
            >
              <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-500/15">
                <CheckCircle2 className="h-7 w-7 text-emerald-400" />
              </div>
              <h2 className="text-xl font-bold text-white mb-2">Message sent</h2>
              <p className="text-sm text-slate-500">We will get back to you within one business day.</p>
            </motion.div>
          ) : (
            <form
              onSubmit={handleSubmit}
              className="rounded-2xl border border-white/[0.07] bg-dark-900/60 p-6 sm:p-8 flex flex-col gap-5"
            >
              <Field icon={User}      label="Name"    type="text"  name="name"    placeholder="Anna Müller"       required />
              <Field icon={Mail}      label="Email"   type="email" name="email"   placeholder="anna@company.de"   required />
              <Field icon={Building2} label="Company" type="text"  name="company" placeholder="Muster GmbH" />

              <div className="flex flex-col gap-1.5">
                <label className="flex items-center gap-2 text-xs font-semibold text-slate-400 uppercase tracking-widest">
                  <MessageSquare className="h-3.5 w-3.5" />
                  Message
                </label>
                <textarea
                  name="message"
                  rows={5}
                  required
                  placeholder="Tell us how we can help..."
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
            </form>
          )}
        </motion.div>
      </div>
    </main>
  );
}
