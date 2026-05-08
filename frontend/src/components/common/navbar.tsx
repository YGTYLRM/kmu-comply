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
      <div className="mx-auto flex h-18 max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="flex items-center group">
          <Image
            src="/logo-transparent.png"
            alt="Complio"
            width={120}
            height={32}
            className="h-8 w-auto brightness-0 invert group-hover:opacity-80 transition-opacity duration-200"
            priority
          />
        </Link>

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

        <Link
          href="/analyze"
          className="rounded-xl bg-brand-600 px-5 py-2.5 text-sm text-white font-semibold hover:bg-brand-500 transition-all duration-200 shadow-glow-blue-sm hover:shadow-glow-blue"
        >
          Get started
        </Link>
      </div>
    </header>
  );
}
