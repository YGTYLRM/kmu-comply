import Link from "next/link";
import { Shield, FileSearch, Zap, CheckCircle } from "lucide-react";

const FEATURES = [
  {
    icon: FileSearch,
    title: "Regulation coverage",
    desc: "GDPR/DSGVO, BDSG, LkSG, EnEfG, and CSRD — all in one analysis.",
  },
  {
    icon: Zap,
    title: "Instant results",
    desc: "Submit your company profile and receive a full compliance gap report in minutes.",
  },
  {
    icon: CheckCircle,
    title: "Actionable plan",
    desc: "Every gap comes with a prioritized action item, effort estimate, and deadline guidance.",
  },
];

const HOW_IT_WORKS = [
  { step: "1", title: "Enter your profile", desc: "Five short steps covering your company, finances, data practices, supply chain, and governance." },
  { step: "2", title: "AI analysis runs", desc: "The system retrieves relevant regulation articles and evaluates your company against each requirement." },
  { step: "3", title: "Review your report", desc: "Get a scored report with gap details, an action plan, and per-regulation breakdowns." },
];

export default function HomePage() {
  return (
    <main>
      <section className="mx-auto max-w-6xl px-6 py-24 flex flex-col items-center text-center gap-6">
        <div className="flex items-center gap-2 rounded-full border border-brand-200 bg-brand-50 px-4 py-1.5 text-sm text-brand-700 font-medium">
          <Shield className="h-4 w-4" />
          Regulatory compliance for German SMEs
        </div>
        <h1 className="text-5xl font-bold tracking-tight text-slate-900 max-w-2xl">
          Know where you stand — before regulators do
        </h1>
        <p className="max-w-xl text-lg text-slate-600 leading-relaxed">
          KMU-Comply analyses your company profile against current German and EU regulations and delivers a prioritised, actionable compliance report.
        </p>
        <Link
          href="/analyze"
          className="rounded-xl bg-brand-600 px-8 py-3.5 text-white font-semibold text-lg hover:bg-brand-700 transition-colors shadow-sm"
        >
          Start free analysis
        </Link>
        <p className="text-xs text-slate-400">No account required · Takes about 3 minutes</p>
      </section>

      <section className="border-y border-slate-200 bg-white">
        <div className="mx-auto max-w-6xl px-6 py-16 grid sm:grid-cols-3 gap-8">
          {FEATURES.map(({ icon: Icon, title, desc }) => (
            <div key={title} className="flex flex-col gap-3">
              <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-50 text-brand-600">
                <Icon className="h-5 w-5" />
              </div>
              <h3 className="font-semibold text-slate-900">{title}</h3>
              <p className="text-sm text-slate-600 leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 py-16">
        <h2 className="text-2xl font-bold text-slate-900 mb-10 text-center">How it works</h2>
        <div className="grid sm:grid-cols-3 gap-8">
          {HOW_IT_WORKS.map(({ step, title, desc }) => (
            <div key={step} className="flex flex-col gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-brand-600 text-white font-bold text-sm">
                {step}
              </div>
              <h3 className="font-semibold text-slate-900">{title}</h3>
              <p className="text-sm text-slate-600 leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="border-t border-slate-200 bg-white">
        <div className="mx-auto max-w-6xl px-6 py-12 flex flex-col items-center gap-4 text-center">
          <h2 className="text-2xl font-bold text-slate-900">Ready to check your compliance status?</h2>
          <p className="text-slate-600 max-w-md">Fill in your company profile and get a full report — free, instant, no sign-up.</p>
          <Link
            href="/analyze"
            className="rounded-xl bg-brand-600 px-8 py-3 text-white font-semibold hover:bg-brand-700 transition-colors"
          >
            Start now
          </Link>
        </div>
      </section>

      <footer className="border-t border-slate-200 py-6 text-center text-xs text-slate-400">
        KMU-Comply · Not legal advice · For informational purposes only
      </footer>
    </main>
  );
}
