"use client";

import Link from "next/link";
import Image from "next/image";
import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";

export function Navbar() {
  const [scrolled, setScrolled] = useState(false);

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
      <div className="mx-auto flex h-24 max-w-7xl items-center gap-10 px-8 py-3">
        {/* Logo — hard left */}
        <Link href="/" className="flex-shrink-0 group">
          <Image
            src="/logo-dark-bg.png"
            alt="Complio"
            width={240}
            height={64}
            className="h-20 w-auto group-hover:opacity-80 transition-opacity duration-200"
            priority
          />
        </Link>

        {/* Nav links — right next to logo */}
        <nav className="hidden md:flex items-center gap-1">
          <a
            href="#how-it-works"
            className="rounded-lg px-4 py-2 text-sm text-slate-400 hover:text-white hover:bg-white/5 transition-colors"
          >
            How it works
          </a>
          <a
            href="#features"
            className="rounded-lg px-4 py-2 text-sm text-slate-400 hover:text-white hover:bg-white/5 transition-colors"
          >
            Features
          </a>
        </nav>

        {/* Spacer pushes CTA to far right */}
        <div className="flex-1" />

        <Link
          href="/analyze"
          className="rounded-xl bg-brand-600 px-6 py-3 text-sm text-white font-semibold hover:bg-brand-500 transition-all duration-200 shadow-glow-blue-sm hover:shadow-glow-blue"
        >
          Get started
        </Link>
      </div>
    </header>
  );
}
