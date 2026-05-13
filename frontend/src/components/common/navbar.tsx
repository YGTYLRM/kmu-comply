"use client";

import Link from "next/link";
import Image from "next/image";
import { useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";
import { Menu, X } from "lucide-react";

export function Navbar() {
  const [hidden,     setHidden]     = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const lastY = useRef(0);

  useEffect(() => {
    const onScroll = () => {
      const y = window.scrollY;
      setHidden(y > 80 && y > lastY.current);
      lastY.current = y;
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <div className={cn(
      "fixed top-0 left-0 right-0 z-50 px-4 md:px-8 pt-3 md:pt-4 pointer-events-none transition-transform duration-300",
      hidden && "-translate-y-full"
    )}>
      <div className="mx-auto max-w-7xl pointer-events-auto">
        {/* Floating pill */}
        <div
          className="rounded-[20px] border border-white/[0.10] shadow-[0_4px_24px_rgba(0,0,0,0.5)]"
          style={{
            background: "rgba(14, 21, 40, 0.92)",
            backdropFilter: "blur(20px)",
            WebkitBackdropFilter: "blur(20px)",
          }}
        >
          <div className="flex h-16 md:h-20 items-center gap-4 md:gap-6 px-5 md:px-7">

            {/* Logo */}
            <Link href="/" className="flex-shrink-0 group">
              <Image
                src="/logo-dark-bg.png"
                alt="Complio"
                width={240}
                height={64}
                className="h-10 md:h-14 w-auto opacity-90 group-hover:opacity-100 transition-opacity duration-200"
                priority
              />
            </Link>

            {/* Desktop nav links */}
            <nav className="hidden md:flex items-center gap-0.5 ml-3">
              <a href="/#how-it-works" className="rounded-lg px-3.5 py-2 text-sm text-slate-400 hover:text-white hover:bg-white/[0.07] transition-colors">
                How it works
              </a>
              <a href="/#features" className="rounded-lg px-3.5 py-2 text-sm text-slate-400 hover:text-white hover:bg-white/[0.07] transition-colors">
                Features
              </a>
              <a href="/#pricing" className="rounded-lg px-3.5 py-2 text-sm text-slate-400 hover:text-white hover:bg-white/[0.07] transition-colors">
                Pricing
              </a>
              <Link href="/contact" className="rounded-lg px-3.5 py-2 text-sm text-slate-400 hover:text-white hover:bg-white/[0.07] transition-colors">
                Contact
              </Link>
              <Link href="/reports" className="rounded-lg px-3.5 py-2 text-sm text-slate-400 hover:text-white hover:bg-white/[0.07] transition-colors">
                Reports
              </Link>
            </nav>

            <div className="flex-1" />

            {/* Desktop CTA */}
            <Link
              href="/contact"
              className="hidden md:inline-flex rounded-xl bg-brand-600 px-5 py-2.5 text-sm text-white font-semibold hover:bg-brand-500 transition-all duration-200 shadow-glow-blue-sm hover:shadow-glow-blue"
            >
              Request a Demo
            </Link>

            {/* Mobile hamburger */}
            <button
              type="button"
              onClick={() => setMobileOpen(!mobileOpen)}
              className="md:hidden flex h-9 w-9 items-center justify-center rounded-lg bg-white/5 border border-white/10 text-slate-400 hover:text-white transition-colors"
              aria-label="Toggle menu"
            >
              {mobileOpen ? <X className="h-4 w-4" /> : <Menu className="h-4 w-4" />}
            </button>
          </div>

          {/* Mobile dropdown — inside the pill */}
          {mobileOpen && (
            <div className="md:hidden border-t border-white/[0.08] px-4 pb-4 pt-2">
              <nav className="flex flex-col gap-1">
                <a href="/#how-it-works" onClick={() => setMobileOpen(false)} className="rounded-lg px-4 py-3 text-sm text-slate-400 hover:text-white hover:bg-white/5 transition-colors">
                  How it works
                </a>
                <a href="/#features" onClick={() => setMobileOpen(false)} className="rounded-lg px-4 py-3 text-sm text-slate-400 hover:text-white hover:bg-white/5 transition-colors">
                  Features
                </a>
                <a href="/#pricing" onClick={() => setMobileOpen(false)} className="rounded-lg px-4 py-3 text-sm text-slate-400 hover:text-white hover:bg-white/5 transition-colors">
                  Pricing
                </a>
                <Link href="/contact" onClick={() => setMobileOpen(false)} className="rounded-lg px-4 py-3 text-sm text-slate-400 hover:text-white hover:bg-white/5 transition-colors">
                  Contact
                </Link>
                <Link href="/reports" onClick={() => setMobileOpen(false)} className="rounded-lg px-4 py-3 text-sm text-slate-400 hover:text-white hover:bg-white/5 transition-colors">
                  Reports
                </Link>
                <Link href="/contact" onClick={() => setMobileOpen(false)} className="mt-2 rounded-xl bg-brand-600 px-4 py-3 text-sm text-white font-semibold text-center hover:bg-brand-500 transition-colors">
                  Request a Demo
                </Link>
              </nav>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
