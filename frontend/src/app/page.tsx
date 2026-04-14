// Landing page — full implementation in Phase 4.
import Link from "next/link";

export default function HomePage() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-6 p-8">
      <h1 className="text-4xl font-bold text-slate-900">KMU-Comply</h1>
      <p className="max-w-md text-center text-slate-600">
        Autonomous regulatory compliance analysis for German SMEs. Powered by AI, grounded in law.
      </p>
      <Link
        href="/analyze"
        className="rounded-lg bg-brand-600 px-6 py-3 text-white font-medium hover:bg-brand-700 transition-colors"
      >
        Start Analysis
      </Link>
    </main>
  );
}
