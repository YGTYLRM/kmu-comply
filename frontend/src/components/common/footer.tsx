"use client";

import Link from "next/link";

export function Footer() {
  return (
    <footer className="border-t border-white/[0.06] bg-dark-950 py-10 mt-20">
      <div className="mx-auto max-w-7xl px-6 md:px-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-xs text-slate-600">
            © {new Date().getFullYear()} Complio. Alle Rechte vorbehalten.
          </p>
          <nav className="flex flex-wrap items-center gap-x-6 gap-y-2 text-xs text-slate-600">
            <Link href="/impressum" className="hover:text-slate-400 transition-colors">Impressum</Link>
            <Link href="/datenschutz" className="hover:text-slate-400 transition-colors">Datenschutz</Link>
            <Link href="/agb" className="hover:text-slate-400 transition-colors">AGB</Link>
            <Link href="/contact" className="hover:text-slate-400 transition-colors">Kontakt</Link>
          </nav>
          <p className="text-xs text-slate-700">
            Vorläufige Einschätzung, keine Rechtsberatung
          </p>
        </div>
      </div>
    </footer>
  );
}
