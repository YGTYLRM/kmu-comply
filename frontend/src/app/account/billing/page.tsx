"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { api } from "@/lib/api";
import { CreditCard, CheckCircle2, AlertTriangle, Loader2, ExternalLink, ArrowLeft } from "lucide-react";

const BASE = "";

const PLAN_LABELS: Record<string, { name: string; price: string; features: string[] }> = {
  starter: {
    name: "Starter",
    price: "€129 / Bericht",
    features: ["Einmaliges Compliance-Screening", "Alle 14 Vorschriften", "Vollständige Lückenanalyse", "E-Mail-Benachrichtigungen"],
  },
  professional: {
    name: "Professional",
    price: "€249 / Monat",
    features: ["Unbegrenzte Screenings", "Alle 14 Vorschriften", "Vollständige Lückenanalyse", "Priorisierter Maßnahmenplan", "Berichtshistorie"],
  },
  enterprise: {
    name: "Enterprise",
    price: "Individuell",
    features: ["Unbegrenzte Einheiten", "Individueller Umfang", "Alle 14 Vorschriften", "Dedizierter Ansprechpartner"],
  },
};

interface BillingData {
  subscription: {
    plan: string;
    status: string;
    current_period_end: string | null;
    company_limit: number;
  } | null;
  stripe_enabled: boolean;
}

export default function BillingPage() {
  const [data, setData]       = useState<BillingData | null>(null);
  const [loading, setLoading] = useState(true);
  const [portalLoading, setPortalLoading] = useState(false);

  useEffect(() => {
    fetch(`${BASE}/api/billing`, {
      headers: { "Content-Type": "application/json" },
    })
      .then(r => r.json())
      .then(setData)
      .catch(() => setData({ subscription: null, stripe_enabled: false }))
      .finally(() => setLoading(false));
  }, []);

  const openPortal = async () => {
    setPortalLoading(true);
    try {
      const authHeader = await getAuthHeader();
      const res = await fetch(`${BASE}/api/billing/portal`, {
        method: "POST",
        headers: { "Content-Type": "application/json", ...authHeader },
      });
      const d = await res.json();
      if (d.url) window.location.href = d.url;
    } catch {
      alert("Abrechnungsportal konnte nicht geöffnet werden. Bitte erneut versuchen.");
    } finally {
      setPortalLoading(false);
    }
  };

  if (loading) return (
    <main className="bg-dark-950 min-h-screen flex items-center justify-center">
      <Loader2 className="h-8 w-8 animate-spin text-brand-500" />
    </main>
  );

  const sub     = data?.subscription;
  const plan    = PLAN_LABELS[sub?.plan ?? ""] ?? null;
  const isActive = sub?.status === "active" || sub?.status === "trialing";
  const isPastDue = sub?.status === "past_due";

  return (
    <main className="bg-dark-950 min-h-screen pt-28 pb-16 px-4 sm:px-6">
      <div className="mx-auto max-w-2xl">
        <Link href="/dashboard" className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-white transition-colors mb-6">
          <ArrowLeft className="h-3.5 w-3.5" /> Zurück zum Dashboard
        </Link>

        <div className="mb-8">
          <p className="text-xs font-bold uppercase tracking-widest text-brand-400 mb-1">Konto</p>
          <h1 className="text-2xl font-black text-white tracking-tight">Abrechnung & Tarif</h1>
        </div>

        {!data?.stripe_enabled && (
          <div className="rounded-2xl border border-white/[0.07] bg-dark-900/60 p-8 text-center">
            <p className="text-slate-500 text-sm mb-2">Abrechnung noch nicht aktiv.</p>
            <p className="text-xs text-slate-600">Kontaktieren Sie uns für Ihr Abonnement.</p>
            <Link href="/contact" className="mt-4 inline-flex items-center gap-2 rounded-xl bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-500 transition-all">
              Kontakt aufnehmen
            </Link>
          </div>
        )}

        {data?.stripe_enabled && !sub && (
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
            className="rounded-2xl border border-white/[0.07] bg-dark-900/60 p-8 text-center"
          >
            <CreditCard className="mx-auto h-10 w-10 text-slate-600 mb-4" />
            <h2 className="text-lg font-bold text-white mb-2">Kein aktives Abonnement</h2>
            <p className="text-sm text-slate-500 mb-6">Wählen Sie einen Tarif, um Ihr Compliance-Monitoring zu starten.</p>
            <Link href="/#pricing" className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-6 py-3 text-sm font-semibold text-white hover:bg-brand-500 transition-all">
              Preise ansehen
            </Link>
          </motion.div>
        )}

        {data?.stripe_enabled && sub && (
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
            className="flex flex-col gap-4"
          >
            {isPastDue && (
              <div className="flex items-center gap-3 rounded-xl border border-amber-500/25 bg-amber-500/10 px-5 py-4 text-sm text-amber-400">
                <AlertTriangle className="h-4 w-4 flex-shrink-0" />
                Ihre letzte Zahlung ist fehlgeschlagen. Bitte Zahlungsmethode aktualisieren.
              </div>
            )}

            {/* Plan card */}
            <div className="rounded-2xl border border-white/[0.07] bg-dark-900/60 p-6">
              <div className="flex items-start justify-between gap-4 mb-5">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <h2 className="text-lg font-bold text-white">{plan?.name ?? sub.plan}-Tarif</h2>
                    <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${
                      isActive ? "bg-emerald-500/15 text-emerald-400" :
                      isPastDue ? "bg-amber-500/15 text-amber-400" :
                      "bg-red-500/15 text-red-400"
                    }`}>
                      {sub.status.replace("_", " ")}
                    </span>
                  </div>
                  <p className="text-sm text-slate-500">{plan?.price ?? ""}</p>
                </div>
                <CreditCard className="h-8 w-8 text-brand-400 flex-shrink-0" />
              </div>

              {plan && (
                <ul className="flex flex-col gap-2 mb-5">
                  {plan.features.map(f => (
                    <li key={f} className="flex items-center gap-2 text-sm text-slate-400">
                      <CheckCircle2 className="h-4 w-4 text-emerald-500 flex-shrink-0" /> {f}
                    </li>
                  ))}
                </ul>
              )}

              {sub.current_period_end && (
                <p className="text-xs text-slate-600 mb-5">
                  {isActive ? "Verlängert sich am" : "Zugang bis"}{" "}
                  {new Date(sub.current_period_end).toLocaleDateString("de-DE", {
                    day: "numeric", month: "long", year: "numeric"
                  })}
                </p>
              )}

              <button
                onClick={openPortal}
                disabled={portalLoading}
                className="inline-flex items-center gap-2 rounded-xl border border-white/10 bg-white/5 px-5 py-2.5 text-sm font-medium text-slate-300 hover:bg-white/10 hover:text-white transition-all disabled:opacity-50"
              >
                {portalLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : <ExternalLink className="h-4 w-4" />}
                Abonnement verwalten
              </button>
            </div>

            {/* Upgrade nudge for Starter */}
            {sub.plan === "starter" && (
              <div className="rounded-2xl border border-brand-500/20 bg-brand-500/[0.04] p-5 flex items-center justify-between gap-4">
                <div>
                  <p className="text-sm font-semibold text-white">Mehr Unternehmen benötigt?</p>
                  <p className="text-xs text-slate-500 mt-0.5">Professional bietet unbegrenzte Screenings und vollständige Berichtshistorie.</p>
                </div>
                <Link href="/contact?plan=professional"
                  className="flex-shrink-0 rounded-xl bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-500 transition-all">
                  Upgraden
                </Link>
              </div>
            )}
          </motion.div>
        )}
      </div>
    </main>
  );
}

async function getAuthHeader(): Promise<Record<string, string>> {
  try {
    const { createClient } = await import("@/lib/supabase/client");
    const supabase = createClient();
    const { data: { session } } = await supabase.auth.getSession();
    return session?.access_token ? { Authorization: `Bearer ${session.access_token}` } : {};
  } catch {
    return {};
  }
}
