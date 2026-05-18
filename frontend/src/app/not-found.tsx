import Link from "next/link";

export default function NotFound() {
  return (
    <div className="min-h-screen bg-dark-950 flex items-center justify-center px-4">
      <div className="text-center max-w-sm">
        <p className="text-7xl font-black text-brand-500/30 mb-4">404</p>
        <h1 className="text-xl font-bold text-white mb-2">Page not found</h1>
        <p className="text-sm text-slate-500 mb-8">
          The page you&apos;re looking for doesn&apos;t exist or has been moved.
        </p>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
          <Link
            href="/dashboard"
            className="rounded-xl bg-brand-600 px-6 py-2.5 text-sm font-semibold text-white hover:bg-brand-500 transition-colors"
          >
            Go to dashboard
          </Link>
          <Link
            href="/"
            className="rounded-xl border border-white/[0.08] px-6 py-2.5 text-sm font-medium text-slate-400 hover:text-white hover:border-white/20 transition-colors"
          >
            Back to home
          </Link>
        </div>
      </div>
    </div>
  );
}
