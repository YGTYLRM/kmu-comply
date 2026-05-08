"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Shield } from "lucide-react";
import { cn } from "@/lib/utils";

export function Navbar() {
  const path = usePathname();

  return (
    <header className="sticky top-0 z-40 border-b border-white/[0.06] bg-dark-950/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-6">
        <Link href="/" className="flex items-center gap-2.5 group">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 shadow-glow-blue-sm group-hover:shadow-glow-blue transition-shadow duration-300">
            <Shield className="h-4 w-4 text-white" />
          </div>
          <span className="text-sm font-semibold text-white tracking-tight">Complio</span>
        </Link>

        <nav className="flex items-center gap-1">
          <Link
            href="/"
            className={cn(
              "rounded-lg px-3 py-2 text-sm transition-colors",
              path === "/"
                ? "text-white bg-white/8"
                : "text-slate-400 hover:text-white hover:bg-white/5"
            )}
          >
            Home
          </Link>
          <Link
            href="/analyze"
            className="ml-2 rounded-lg bg-brand-600 px-4 py-2 text-sm text-white font-medium hover:bg-brand-500 transition-all duration-200 shadow-glow-blue-sm hover:shadow-glow-blue"
          >
            Start Screening
          </Link>
        </nav>
      </div>
    </header>
  );
}
