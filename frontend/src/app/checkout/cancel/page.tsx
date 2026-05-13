"use client";
import { useRouter } from "next/navigation";
import { XCircle } from "lucide-react";

export default function CheckoutCancelPage() {
  const router = useRouter();
  return (
    <main className="min-h-screen bg-dark-950 flex items-center justify-center px-4">
      <div className="max-w-md w-full rounded-2xl border border-white/[0.07] bg-dark-900/60 p-10 text-center shadow-xl">
        <XCircle className="mx-auto h-12 w-12 text-slate-500 mb-6" />
        <h1 className="text-xl font-bold text-white mb-2">Payment cancelled</h1>
        <p className="text-slate-400 text-sm mb-8">No charge was made. You can start a screening whenever you are ready.</p>
        <button
          onClick={() => router.push("/#pricing")}
          className="rounded-xl bg-brand-600 px-6 py-3 text-sm font-semibold text-white hover:bg-brand-500 transition"
        >
          Back to pricing
        </button>
      </div>
    </main>
  );
}
