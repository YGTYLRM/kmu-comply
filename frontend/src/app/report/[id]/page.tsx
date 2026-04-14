// Compliance report view — full implementation in Phase 4.
export default function ReportPage({ params }: { params: { id: string } }) {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <p className="text-slate-500">Report {params.id} — Phase 4</p>
    </main>
  );
}
