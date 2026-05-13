"use client";
import { Suspense, useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { CheckCircle, Loader2, XCircle } from "lucide-react";

function CheckoutSuccessInner() {
  const params = useSearchParams();
  const router = useRouter();
  const [status, setStatus] = useState<"loading" | "ok" | "error">("loading");

  useEffect(() => {
    const sessionId = params.get("session_id");
    if (!sessionId) { setStatus("error"); return; }

    fetch(`/api/backend/checkout/verify?session_id=${sessionId}`)
      .then((r) => r.json())
      .then((data) => {
        if (data.token) {
          localStorage.setItem("complio_access_token", data.token);
          setStatus("ok");
          setTimeout(() => router.push("/analyze"), 2000);
        } else {
          setStatus("error");
        }
      })
      .catch(() => setStatus("error"));
  }, [params, router]);

  return (
    <main className="min-h-screen bg-dark-950 flex items-center justify-center px-4">
      <div className="max-w-md w-full rounded-2xl border border-white/[0.07] bg-dark-900/60 p-10 text-center shadow-xl">
        {status === "loading" && (
          <>
            <Loader2 className="mx-auto h-12 w-12 text-brand-400 animate-spin mb-6" />
            <h1 className="text-xl font-bold text-white mb-2">Confirming your payment</h1>
            <p className="text-slate-500 text-sm">Just a moment while we verify with Stripe.</p>
          </>
        )}
        {status === "ok" && (
          <>
            <CheckCircle className="mx-auto h-12 w-12 text-emerald-400 mb-6" />
            <h1 className="text-xl font-bold text-white mb-2">Payment confirmed</h1>
            <p className="text-slate-400 text-sm">Taking you to your screening now.</p>
          </>
        )}
        {status === "error" && (
          <>
            <XCircle className="mx-auto h-12 w-12 text-red-400 mb-6" />
            <h1 className="text-xl font-bold text-white mb-2">Something went wrong</h1>
            <p className="text-slate-400 text-sm mb-6">
              Payment may still have gone through. Check your email or{" "}
              <a href="/contact" className="text-brand-400 hover:underline">contact us</a>.
            </p>
            <button
              onClick={() => router.push("/#pricing")}
              className="rounded-xl bg-white/5 border border-white/10 px-6 py-2.5 text-sm text-slate-300 hover:bg-white/10 transition"
            >
              Back to pricing
            </button>
          </>
        )}
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
