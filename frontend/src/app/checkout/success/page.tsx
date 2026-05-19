"use client";
import { Suspense, useEffect } from "react";
import { useRouter } from "next/navigation";
import { CheckCircle } from "lucide-react";

function CheckoutSuccessInner() {
  const router = useRouter();

  useEffect(() => {
    // Subscription is activated via Stripe webhook → DB.
    // Give the webhook a moment to land, then send the user to billing.
    const t = setTimeout(() => router.push("/account/billing"), 3000);
    return () => clearTimeout(t);
  }, [router]);

  return (
    <main className="min-h-screen bg-dark-950 flex items-center justify-center px-4">
      <div className="max-w-md w-full rounded-2xl border border-white/[0.07] bg-dark-900/60 p-10 text-center shadow-xl">
        <CheckCircle className="mx-auto h-12 w-12 text-emerald-400 mb-6" />
        <h1 className="text-xl font-bold text-white mb-2">Zahlung bestätigt</h1>
        <p className="text-slate-400 text-sm">
          Ihr Abonnement wird aktiviert. Sie werden zur Abrechnung weitergeleitet.
        </p>
      </div>
    </main>
  );
}

export default function CheckoutSuccessPage() {
  return (
    <Suspense fallback={<main className="min-h-screen bg-dark-950" />}>
      <CheckoutSuccessInner />
    </Suspense>
  );
}
