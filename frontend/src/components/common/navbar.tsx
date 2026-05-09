"use client";

import Link from "next/link";
import Image from "next/image";
import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";
import { Menu, X } from "lucide-react";

export function Navbar() {
  const [scrolled,    setScrolled]    = useState(false);
  const [mobileOpen,  setMobileOpen]  = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={cn(
        "fixed top-0 left-0 right-0 z-50 transition-all duration-500",
        scrolled
          ? "border-b border-white/[0.06] bg-dark-950/92 backdrop-blur-xl"
          : "bg-transparent"
      )}
    >
      <div className="mx-auto flex h-16 md:h-24 max-w-7xl items-center gap-6 md:gap-10 px-4 md:px-8">
        {/* Logo */}
        <Link href="/" className="flex-shrink-0 group">
          <Image
            src="/logo-dark-bg.png"
            alt="Complio"
            width={240}
            height={64}
            className="h-10 md:h-20 w-auto group-hover:opacity-80 transition-opacity duration-200"
            priority
          />
        </Link>

        {/* Desktop nav links */}
        <nav className="hidden md:flex items-center gap-1">
          <a href="#how-it-works" className="rounded-lg px-4 py-2 text-sm text-slate-400 hover:text-white hover:bg-white/5 transition-colors">
            How it works
          </a>
          <a href="#features" className="rounded-lg px-4 py-2 text-sm text-slate-400 hover:text-white hover:bg-white/5 transition-colors">
            Features
          </a>
          <Link href="/contact" className="rounded-lg px-4 py-2 text-sm text-slate-400 hover:text-white hover:bg-white/5 transition-colors">
            Contact
          </Link>
        </nav>

        <div className="flex-1" />

        {/* Desktop CTA */}
        <Link
          href="/analyze"
          className="hidden md:inline-flex rounded-xl bg-brand-600 px-6 py-3 text-sm text-white font-semibold hover:bg-brand-500 transition-all duration-200 shadow-glow-blue-sm hover:shadow-glow-blue"
        >
          Get started
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

      {/* Mobile dropdown */}
      {mobileOpen && (
        <div className="md:hidden border-t border-white/[0.06] bg-dark-950/96 backdrop-blur-xl px-4 pb-4 pt-2">
          <nav className="flex flex-col gap-1">
            <a
              href="#how-it-works"
              onClick={() => setMobileOpen(false)}
              className="rounded-lg px-4 py-3 text-sm text-slate-400 hover:text-white hover:bg-white/5 transition-colors"
            >
              How it works
            </a>
            <a
              href="#features"
              onClick={() => setMobileOpen(false)}
              className="rounded-lg px-4 py-3 text-sm text-slate-400 hover:text-white hover:bg-white/5 transition-colors"
            >
              Features
            </a>
            <Link
              href="/contact"
              onClick={() => setMobileOpen(false)}
              className="rounded-lg px-4 py-3 text-sm text-slate-400 hover:text-white hover:bg-white/5 transition-colors"
            >
              Contact
            </Link>
            <Link
              href="/analyze"
              onClick={() => setMobileOpen(false)}
              className="mt-2 rounded-xl bg-brand-600 px-4 py-3 text-sm text-white font-semibold text-center hover:bg-brand-500 transition-colors"
            >
              Get started
            </Link>
          </nav>
        </div>
      )}
    </header>
  );
}
