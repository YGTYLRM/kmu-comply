import Link from "next/link";
import { Shield } from "lucide-react";

export function Navbar() {
  return (
    <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/90 backdrop-blur-sm">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-6">
        <Link href="/" className="flex items-center gap-2 font-semibold text-slate-900">
          <Shield className="h-5 w-5 text-brand-600" />
          KMU-Comply
        </Link>
        <nav className="flex items-center gap-6 text-sm">
          <Link href="/" className="text-slate-600 hover:text-slate-900 transition-colors">
            Home
          </Link>
          <Link
            href="/analyze"
            className="rounded-lg bg-brand-600 px-4 py-1.5 text-white font-medium hover:bg-brand-700 transition-colors"
          >
            Start Analysis
          </Link>
        </nav>
      </div>
    </header>
  );
}
