import { Suspense } from "react";
import { ProcessingView } from "./processing-view";

export default function ProcessingPage() {
  return (
    <Suspense fallback={
      <main className="flex min-h-[60vh] items-center justify-center">
        <div className="text-slate-500 text-sm">Loading…</div>
      </main>
    }>
      <ProcessingView />
    </Suspense>
  );
}
