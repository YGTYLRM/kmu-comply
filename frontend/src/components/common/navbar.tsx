"use client";

import Link from "next/link";
import Image from "next/image";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import { Menu, X, LogOut, Bell, LayoutDashboard, CreditCard, Settings } from "lucide-react";
import { createClient } from "@/lib/supabase/client";
import { api } from "@/lib/api";

export function Navbar() {
  const [hidden,       setHidden]       = useState(false);
  const [mobileOpen,   setMobileOpen]   = useState(false);
  const [userEmail,    setUserEmail]    = useState<string | null>(null);
  const [unreadCount,  setUnreadCount]  = useState(0);
  const lastY = useRef(0);
  const router = useRouter();

  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getSession().then(({ data: { session } }) => {
      setUserEmail(session?.user?.email ?? null);
    });
    const { data: { subscription } } = supabase.auth.onAuthStateChange((_e, session) => {
      setUserEmail(session?.user?.email ?? null);
      if (session) {
        api.getUnreadCount().then(d => setUnreadCount(d.count)).catch(() => {});
      } else {
        setUnreadCount(0);
      }
    });

    // Poll unread count every 60s when logged in
    const interval = setInterval(() => {
      if (userEmail) api.getUnreadCount().then(d => setUnreadCount(d.count)).catch(() => {});
    }, 60_000);

    return () => { subscription.unsubscribe(); clearInterval(interval); };
  }, []);

  const handleLogout = async () => {
    const supabase = createClient();
    await supabase.auth.signOut();
    router.push("/");
    router.refresh();
  };

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
                So funktioniert es
              </a>
              <a href="/#features" className="rounded-lg px-3.5 py-2 text-sm text-slate-400 hover:text-white hover:bg-white/[0.07] transition-colors">
                Funktionen
              </a>
              <a href="/#pricing" className="rounded-lg px-3.5 py-2 text-sm text-slate-400 hover:text-white hover:bg-white/[0.07] transition-colors">
                Preise
              </a>
              <Link href="/contact" className="rounded-lg px-3.5 py-2 text-sm text-slate-400 hover:text-white hover:bg-white/[0.07] transition-colors">
                Kontakt
              </Link>
              <Link href="/reports" className="rounded-lg px-3.5 py-2 text-sm text-slate-400 hover:text-white hover:bg-white/[0.07] transition-colors">
                Berichte
              </Link>
            </nav>

            <div className="flex-1" />

            {/* Desktop CTA */}
            {userEmail ? (
              <div className="hidden md:flex items-center gap-2">
                <Link href="/dashboard"
                  className="inline-flex items-center gap-1.5 rounded-xl border border-white/10 bg-white/5 px-3.5 py-2 text-sm text-slate-400 hover:text-white hover:bg-white/10 transition-all"
                >
                  <LayoutDashboard className="h-3.5 w-3.5" />
                  Dashboard
                </Link>
                <Link href="/account/billing"
                  className="inline-flex items-center gap-1.5 rounded-xl border border-white/10 bg-white/5 px-3.5 py-2 text-sm text-slate-400 hover:text-white hover:bg-white/10 transition-all"
                >
                  <CreditCard className="h-3.5 w-3.5" />
                  Abrechnung
                </Link>
                <Link href="/account/settings"
                  className="inline-flex items-center gap-1.5 rounded-xl border border-white/10 bg-white/5 px-3.5 py-2 text-sm text-slate-400 hover:text-white hover:bg-white/10 transition-all"
                >
                  <Settings className="h-3.5 w-3.5" />
                  Einstellungen
                </Link>
                <Link href="/dashboard"
                  onClick={() => api.markNotificationsRead().catch(() => {})}
                  className="relative inline-flex items-center justify-center h-9 w-9 rounded-xl border border-white/10 bg-white/5 text-slate-400 hover:text-white hover:bg-white/10 transition-all"
                >
                  <Bell className="h-3.5 w-3.5" />
                  {unreadCount > 0 && (
                    <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-brand-600 text-[10px] font-bold text-white">
                      {unreadCount > 9 ? "9+" : unreadCount}
                    </span>
                  )}
                </Link>
                <button
                  onClick={handleLogout}
                  className="inline-flex items-center gap-1.5 rounded-xl border border-white/10 bg-white/5 px-3.5 py-2 text-sm text-slate-400 hover:text-white hover:bg-white/10 transition-all"
                >
                  <LogOut className="h-3.5 w-3.5" />
                  Sign out
                </button>
              </div>
            ) : (
              <div className="hidden md:flex items-center gap-2">
                <Link href="/login" className="rounded-xl px-4 py-2 text-sm text-slate-400 hover:text-white transition-colors">
                  Anmelden
                </Link>
                <Link
                  href="/contact"
                  className="rounded-xl bg-brand-600 px-5 py-2.5 text-sm text-white font-semibold hover:bg-brand-500 transition-all duration-200 shadow-glow-blue-sm hover:shadow-glow-blue"
                >
                  Demo anfordern
                </Link>
              </div>
            )}

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
                {userEmail ? (
                  <button
                    onClick={() => { setMobileOpen(false); handleLogout(); }}
                    className="mt-2 rounded-xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-slate-300 font-semibold text-center hover:bg-white/10 transition-colors flex items-center justify-center gap-2"
                  >
                    <LogOut className="h-4 w-4" /> Abmelden
                  </button>
                ) : (
                  <>
                    <Link href="/login" onClick={() => setMobileOpen(false)} className="rounded-lg px-4 py-3 text-sm text-slate-400 hover:text-white hover:bg-white/5 transition-colors">
                      Sign in
                    </Link>
                    <Link href="/contact" onClick={() => setMobileOpen(false)} className="mt-2 rounded-xl bg-brand-600 px-4 py-3 text-sm text-white font-semibold text-center hover:bg-brand-500 transition-colors">
                      Request a Demo
                    </Link>
                  </>
                )}
              </nav>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
