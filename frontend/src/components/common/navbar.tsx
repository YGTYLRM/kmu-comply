import Link from "next/link";
import { Shield } from "lucide-react";

export function Navbar() {
  return (
    <header className="sticky top-0 z-40 border-b border-slate-200/70 bg-white/95 backdrop-blur-sm">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
        <Link href="/" className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 shadow-sm">
            <Shield className="h-4 w-4 text-white" />
          </div>
          <span className="text-sm font-semibold text-slate-900 tracking-tight">KMU-Comply</span>
        </Link>
        <nav className="flex items-center gap-1">
          <Link
            href="/"
            className="rounded-lg px-3 py-2 text-sm text-slate-500 hover:text-slate-900 hover:bg-slate-50 transition-colors"
          >
            Home
          </Link>
          <Link
            href="/analyze"
            className="ml-2 rounded-lg bg-brand-600 px-4 py-2 text-sm text-white font-medium hover:bg-brand-700 transition-colors shadow-sm"
          >
            Start Screening
          </Link>
        </nav>
      </div>
    </header>
  );
}
