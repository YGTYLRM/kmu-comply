import Link from "next/link";
import { ArrowRight, CheckCircle2, FileSearch, Zap, ShieldCheck, BarChart3, ListChecks, AlertTriangle } from "lucide-react";

const REGULATIONS = [
  { name: "GDPR / DSGVO", desc: "Data protection" },
  { name: "BDSG", desc: "German data privacy" },
  { name: "LkSG", desc: "Supply chain due diligence" },
  { name: "EnEfG", desc: "Energy efficiency" },
  { name: "CSRD", desc: "Sustainability reporting" },
];

const STEPS = [
  { n: "01", title: "Enter your profile", desc: "Five short steps covering your company basics, finances, data practices, supply chain, and governance." },
  { n: "02", title: "AI analyses your data", desc: "Relevant regulation articles are retrieved and assessed against your company profile." },
  { n: "03", title: "Gaps are identified", desc: "Each requirement is checked — compliant, partial, or non-compliant — with full evidence." },
  { n: "04", title: "Actions are prioritised", desc: "Every gap becomes a concrete action item with effort estimate and deadline guidance." },
  { n: "05", title: "Review your screening", desc: "A scored, preliminary screening report — by regulation, by priority, with suggested next steps." },
];

const FEATURES = [
  { icon: FileSearch, color: "bg-blue-50 text-blue-600", title: "Full regulation coverage", desc: "GDPR/DSGVO, BDSG, LkSG, EnEfG, and CSRD — all five frameworks screened in a single run." },
  { icon: Zap, color: "bg-amber-50 text-amber-600", title: "Results in minutes", desc: "Automated screening — a useful starting point before engaging a legal consultant." },
  { icon: ListChecks, color: "bg-emerald-50 text-emerald-600", title: "Concrete action plan", desc: "Each gap comes with a prioritised action — CRITICAL to LOW — with effort and deadline." },
  { icon: BarChart3, color: "bg-purple-50 text-purple-600", title: "Per-regulation scoring", desc: "Compliance score per regulation so you know exactly where to focus first." },
  { icon: ShieldCheck, color: "bg-rose-50 text-rose-600", title: "Grounded in law", desc: "Screening cites specific article numbers from official regulation texts — not generic checklists." },
  { icon: AlertTriangle, color: "bg-orange-50 text-orange-600", title: "Flags manual review", desc: "When confidence is low, the report explicitly marks items for human legal review." },
];

function MockReport() {
  return (
    <div className="w-full max-w-sm rounded-2xl border border-slate-200 bg-white shadow-card overflow-hidden text-left select-none">
      <div className="px-5 py-4 border-b border-slate-100 flex items-center justify-between">
        <div>
          <p className="text-[10px] font-semibold uppercase tracking-widest text-slate-400">Preliminary Screening</p>
          <p className="text-sm font-bold text-slate-900 mt-0.5">Muster GmbH · IT / Software</p>
        </div>
        <div className="text-right">
          <span className="text-3xl font-bold text-amber-500">68%</span>
          <p className="text-[10px] text-slate-400">overall score</p>
        </div>
      </div>
      <div className="px-5 pt-4 pb-3 space-y-3">
        {[
          { reg: "GDPR / DSGVO", pct: 82, bar: "bg-emerald-500" },
          { reg: "LkSG", pct: 55, bar: "bg-amber-500" },
          { reg: "EnEfG", pct: 40, bar: "bg-red-500" },
          { reg: "BDSG", pct: 75, bar: "bg-emerald-400" },
        ].map(({ reg, pct, bar }) => (
          <div key={reg}>
            <div className="flex justify-between text-xs mb-1.5">
              <span className="font-medium text-slate-700">{reg}</span>
              <span className="text-slate-400">{pct}%</span>
            </div>
            <div className="h-1.5 w-full rounded-full bg-slate-100">
              <div className={`h-1.5 rounded-full ${bar}`} style={{ width: `${pct}%` }} />
            </div>
          </div>
        ))}
      </div>
      <div className="px-5 py-3.5 border-t border-slate-100 bg-slate-50/60 flex flex-wrap gap-1.5">
        {[
          { label: "3 CRITICAL", cls: "bg-red-50 text-red-700 border-red-200" },
          { label: "5 HIGH", cls: "bg-orange-50 text-orange-700 border-orange-200" },
          { label: "8 MEDIUM", cls: "bg-amber-50 text-amber-700 border-amber-200" },
          { label: "4 LOW", cls: "bg-green-50 text-green-700 border-green-200" },
        ].map(({ label, cls }) => (
          <span key={label} className={`rounded-full border px-2.5 py-1 text-[10px] font-bold ${cls}`}>
            {label}
          </span>
        ))}
      </div>
    </div>
  );
}

export default function HomePage() {
  return (
    <main>
      {/* Hero */}
      <section className="relative overflow-hidden border-b border-slate-100">
        <div className="absolute inset-0 bg-gradient-to-br from-brand-50/70 via-white to-white" />
        <div className="relative mx-auto max-w-6xl px-6 py-20 lg:py-28">
          <div className="grid lg:grid-cols-2 gap-14 items-center">
            <div className="flex flex-col gap-7">
              <div className="inline-flex w-fit items-center gap-2 rounded-full border border-brand-200 bg-brand-50 px-3.5 py-1.5 text-xs font-semibold text-brand-700">
                <span className="h-1.5 w-1.5 rounded-full bg-brand-500" />
                5 German &amp; EU regulations covered
              </div>
              <h1 className="text-4xl lg:text-5xl font-bold tracking-tight text-slate-900 leading-[1.1]">
                Regulatory compliance
                <br />
                screening —{" "}
                <span className="text-brand-600">automated</span>
              </h1>
              <p className="text-lg text-slate-500 leading-relaxed">
                Submit your company profile and get a preliminary compliance screening across German and EU law in minutes — a solid starting point before any legal consultation.
              </p>
              <div className="flex flex-col sm:flex-row gap-3">
                <Link
                  href="/analyze"
                  className="inline-flex items-center justify-center gap-2 rounded-xl bg-brand-600 px-6 py-3 text-sm font-semibold text-white shadow-sm hover:bg-brand-700 transition-colors"
                >
                  Start free screening
                  <ArrowRight className="h-4 w-4" />
                </Link>
                <a
                  href="#how-it-works"
                  className="inline-flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white px-6 py-3 text-sm font-semibold text-slate-700 hover:bg-slate-50 transition-colors"
                >
                  See how it works
                </a>
              </div>
              <div className="flex flex-wrap gap-5 text-xs text-slate-400">
                {["No account required", "Takes ~3 minutes", "Completely free"].map((t) => (
                  <span key={t} className="flex items-center gap-1.5">
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500" />
                    {t}
                  </span>
                ))}
              </div>
            </div>
            <div className="flex justify-center lg:justify-end">
              <MockReport />
            </div>
          </div>
        </div>
      </section>

      {/* Regulations strip */}
      <section className="border-b border-slate-100 bg-slate-50/50 py-4">
        <div className="mx-auto max-w-6xl px-6">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-xs font-medium text-slate-400 mr-1">Regulations covered</span>
            {REGULATIONS.map((r) => (
              <div key={r.name} className="flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 shadow-sm">
                <span className="h-1.5 w-1.5 rounded-full bg-brand-500" />
                {r.name}
                <span className="text-slate-400 font-normal">· {r.desc}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How it works */}
      <section id="how-it-works" className="mx-auto max-w-6xl px-6 py-20">
        <div className="mb-12">
          <p className="text-xs font-bold uppercase tracking-widest text-brand-600 mb-3">How it works</p>
          <h2 className="text-3xl font-bold text-slate-900 tracking-tight">From profile to report in five steps</h2>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-5 gap-6 sm:gap-0">
          {STEPS.map(({ n, title, desc }, i) => (
            <div key={n} className="relative flex flex-col gap-3 sm:px-4 pb-2">
              {i < STEPS.length - 1 && (
                <div className="hidden sm:block absolute top-5 left-[calc(50%+24px)] right-0 h-px bg-slate-200" />
              )}
              <div className="relative z-10 flex h-10 w-10 items-center justify-center rounded-full border-2 border-brand-200 bg-brand-50 text-xs font-bold text-brand-600">
                {n}
              </div>
              <p className="text-sm font-semibold text-slate-900 leading-snug">{title}</p>
              <p className="text-xs text-slate-500 leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Features */}
      <section className="border-t border-slate-100 bg-slate-50/40 py-20">
        <div className="mx-auto max-w-6xl px-6">
          <div className="mb-12">
            <p className="text-xs font-bold uppercase tracking-widest text-brand-600 mb-3">What you get</p>
            <h2 className="text-3xl font-bold text-slate-900 tracking-tight">Everything in one report</h2>
          </div>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {FEATURES.map(({ icon: Icon, color, title, desc }) => (
              <div
                key={title}
                className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-card hover:shadow-card-hover transition-shadow duration-200"
              >
                <div className={`mb-4 flex h-10 w-10 items-center justify-center rounded-xl ${color}`}>
                  <Icon className="h-5 w-5" />
                </div>
                <h3 className="text-sm font-semibold text-slate-900 mb-1.5">{title}</h3>
                <p className="text-sm text-slate-500 leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="border-t border-slate-100">
        <div className="mx-auto max-w-6xl px-6 py-20 flex flex-col lg:flex-row items-start lg:items-center justify-between gap-8">
          <div>
            <h2 className="text-2xl font-bold text-slate-900 tracking-tight mb-2">
              Ready for a preliminary screening?
            </h2>
            <p className="text-slate-500 text-sm">Free, instant, no sign-up. Takes about 3 minutes. Not a substitute for legal advice.</p>
          </div>
          <Link
            href="/analyze"
            className="flex-shrink-0 inline-flex items-center gap-2 rounded-xl bg-brand-600 px-7 py-3.5 text-sm font-semibold text-white shadow-sm hover:bg-brand-700 transition-colors"
          >
            Start free analysis
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </section>

      <footer className="border-t border-slate-100 py-6 text-center text-xs text-slate-400">
        KMU-Comply · Not legal advice · For informational purposes only
      </footer>
    </main>
  );
}
