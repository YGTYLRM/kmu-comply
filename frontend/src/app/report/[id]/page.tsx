"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { useReport } from "@/hooks/useReport";
import { ExecutiveSummary } from "@/components/report/executive-summary";
import { ApplicabilityMatrix } from "@/components/report/applicability-matrix";
import { ScoreBreakdown } from "@/components/report/score-breakdown";
import { GapAnalysis } from "@/components/report/gap-analysis";
import { ActionPlan } from "@/components/report/action-plan";
import { DocumentNudge } from "@/components/report/document-nudge";
import { DocumentTemplates } from "@/components/report/document-templates";
import { ExpertReview } from "@/components/report/expert-review";
import { Button } from "@/components/ui/button";
import { Loader2, ArrowLeft, Download, AlertTriangle, Link2, Check, RefreshCw, TrendingUp, TrendingDown, Minus, Database, ChevronDown, ShieldAlert, X, BookOpen } from "lucide-react";
import { api } from "@/lib/api";
import type { ComplianceReport } from "@/lib/types";

export default function ReportPage() {
  const params       = useParams();
  const router       = useRouter();
  const searchParams = useSearchParams();
  const jobId        = params.id as string;
  const prevJobId    = searchParams.get("prev");
  const { report, loading, error, fetch: loadReport } = useReport(jobId);
  const [prevReport, setPrevReport] = useState<ComplianceReport | null>(null);
  const [headerOpacity, setHeaderOpacity] = useState(1);
  const [copied, setCopied] = useState(false);
  const [pdfWarningOpen, setPdfWarningOpen] = useState(false);

  const copyLink = () => {
    navigator.clipboard.writeText(window.location.href).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  useEffect(() => { loadReport(); }, [loadReport]);
  useEffect(() => {
    if (prevJobId) {
      api.getReport(prevJobId).then(setPrevReport).catch(() => {});
    }
  }, [prevJobId]);

  useEffect(() => {
    const onScroll = () => {
      setHeaderOpacity(Math.max(0, 1 - window.scrollY / 220));
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  if (loading) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center pt-24">
        <div className="flex flex-col items-center gap-4">
          <div className="h-12 w-12 rounded-2xl bg-brand-500/10 border border-brand-500/25 flex items-center justify-center shadow-glow-blue-sm">
            <Loader2 className="h-6 w-6 animate-spin text-brand-400" />
          </div>
          <p className="text-sm text-slate-500">Bericht wird geladen…</p>
        </div>
      </div>
    );
  }

  if (error || !report) {
    const isNotFound = error?.includes("404") || error?.includes("not found");
    const isOffline  = error?.toLowerCase().includes("fetch") || error?.toLowerCase().includes("network");
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-6 pt-24 px-6">
        <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-red-500/10 border border-red-500/20">
          <AlertTriangle className="h-8 w-8 text-red-400" />
        </div>
        <div className="text-center max-w-sm">
          <h2 className="text-lg font-bold text-white mb-2">
            {isNotFound ? "Bericht nicht gefunden" : isOffline ? "Server nicht erreichbar" : "Etwas ist schiefgelaufen"}
          </h2>
          <p className="text-sm text-slate-500 leading-relaxed">
            {isNotFound
              ? "Dieser Bericht wurde nicht gefunden. Der Link ist möglicherweise ungültig oder das Screening wurde nicht abgeschlossen."
              : isOffline
              ? "Der Server antwortet nicht. Bitte stellen Sie sicher, dass er auf Port 8000 läuft und laden Sie die Seite neu."
              : (error ?? "Ein unerwarteter Fehler ist aufgetreten.")}
          </p>
        </div>
        <div className="flex flex-col sm:flex-row gap-3">
          <Button variant="outline" onClick={() => loadReport()}>
            Erneut versuchen
          </Button>
          <Button onClick={() => router.push("/analyze")}>
            Neues Screening
          </Button>
        </div>
      </div>
    );
  }

  const score      = report.overall_score_percent;
  const scoreColor = score >= 75 ? "text-emerald-400" : score >= 50 ? "text-amber-400" : "text-red-400";
  const scoreBg    = score >= 75 ? "bg-emerald-500/10 border-emerald-500/25" : score >= 50 ? "bg-amber-500/10 border-amber-500/25" : "bg-red-500/10 border-red-500/25";

  return (
    <div className="bg-dark-950 min-h-screen pt-24">
      {/* Report header — geometric diagonal bottom, fades on scroll */}
      <div style={{ opacity: headerOpacity, transition: "opacity 0.1s linear" }}>
        <div
          className="bg-dark-900/85 backdrop-blur-sm"
          style={{ clipPath: "polygon(0 0, 100% 0, 100% calc(100% - 22px), 0 100%)" }}
        >
          <div className="mx-auto max-w-5xl px-4 sm:px-6 pt-6 pb-12">
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y:  0 }}
              transition={{ duration: 0.4 }}
              className="flex items-start justify-between gap-4 flex-wrap"
            >
              <div className="flex items-start gap-4">
                <div className={`flex h-14 w-14 flex-shrink-0 items-center justify-center rounded-2xl border ${scoreBg}`}>
                  <span className={`text-xl font-bold ${scoreColor}`}>{score}%</span>
                </div>
                <div>
                  <h1 className="text-xl font-bold text-white tracking-tight">{report.company_name}</h1>
                  <p className="text-sm text-slate-500 mt-0.5">
                    Compliance-Screening ·{" "}
                    {new Date(report.generated_at).toLocaleDateString("de-DE", {
                      day: "numeric", month: "short", year: "numeric",
                    })}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2 flex-wrap">
                <button
                  onClick={copyLink}
                  className="inline-flex items-center gap-1.5 rounded-xl border border-white/[0.10] bg-white/[0.04] px-4 py-2 text-sm font-medium text-slate-300 hover:bg-white/[0.08] hover:text-white transition-all duration-200"
                >
                  {copied ? <Check className="h-3.5 w-3.5 text-emerald-400" /> : <Link2 className="h-3.5 w-3.5" />}
                  {copied ? "Kopiert!" : "Link kopieren"}
                </button>
                {report.requires_manual_review && report.requires_manual_review.length > 0 ? (
                  <button
                    onClick={() => setPdfWarningOpen(true)}
                    className="inline-flex items-center gap-1.5 rounded-xl border border-amber-500/30 bg-amber-500/[0.08] px-4 py-2 text-sm font-medium text-amber-400 hover:bg-amber-500/[0.14] transition-all duration-200"
                  >
                    <ShieldAlert className="h-3.5 w-3.5" />
                    Unvollständiger Bericht
                  </button>
                ) : (
                  <a
                    href={`/report/${jobId}/print`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 rounded-xl border border-white/[0.10] bg-white/[0.04] px-4 py-2 text-sm font-medium text-slate-300 hover:bg-white/[0.08] hover:text-white transition-all duration-200"
                  >
                    <Download className="h-3.5 w-3.5" />
                    PDF herunterladen
                  </a>
                )}
                <Button variant="outline" size="sm" onClick={() => router.push(`/analyze?from=${jobId}`)}>
                  <RefreshCw className="h-3.5 w-3.5" />
                  Neu ausführen
                </Button>
                <Button variant="outline" size="sm" onClick={() => router.push("/analyze")}>
                  <ArrowLeft className="h-3.5 w-3.5" />
                  Neues Screening
                </Button>
              </div>
            </motion.div>
          </div>
        </div>
      </div>

      <main className="mx-auto max-w-5xl px-4 sm:px-6 py-8">
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="flex flex-col gap-5"
        >
          {prevReport && <DeltaBanner current={report} prev={prevReport} prevJobId={prevJobId!} />}

          {/* Partial report warning */}
          {report.requires_manual_review && report.requires_manual_review.length > 0 && (
            <div className="rounded-xl border border-amber-500/30 bg-amber-500/[0.06] px-5 py-4">
              <div className="flex items-start gap-3">
                <ShieldAlert className="h-5 w-5 text-amber-400 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-bold text-amber-300 mb-1">
                    Unvollständiger Bericht — {report.requires_manual_review.length} Schritt{report.requires_manual_review.length !== 1 ? "e" : ""} erfordern manuelle Prüfung
                  </p>
                  <p className="text-xs text-slate-400 leading-relaxed mb-2">
                    Die folgenden Analyseschritte sind fehlgeschlagen und die Ergebnisse können unvollständig sein.
                    Verwenden Sie diesen Bericht nicht ohne Überprüfung der Lücken für Compliance-Entscheidungen.
                  </p>
                  <ul className="flex flex-wrap gap-2">
                    {report.requires_manual_review.map(step => (
                      <li key={step} className="rounded-full bg-amber-500/10 border border-amber-500/20 px-3 py-0.5 text-xs text-amber-400 font-mono">
                        {step}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}

          {/* PDF blocked modal */}
          {pdfWarningOpen && (
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 px-4">
              <div className="w-full max-w-md rounded-2xl border border-amber-500/25 bg-dark-900 p-6 shadow-2xl">
                <div className="flex items-start justify-between gap-3 mb-4">
                  <div className="flex items-center gap-3">
                    <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-amber-500/10 border border-amber-500/20">
                      <ShieldAlert className="h-5 w-5 text-amber-400" />
                    </div>
                    <h3 className="text-base font-bold text-white">PDF-Export gesperrt</h3>
                  </div>
                  <button onClick={() => setPdfWarningOpen(false)} className="text-slate-600 hover:text-slate-300 transition-colors">
                    <X className="h-4 w-4" />
                  </button>
                </div>
                <p className="text-sm text-slate-400 leading-relaxed mb-4">
                  Dieser Bericht ist unvollständig — {report.requires_manual_review?.length} Analyseschritt{(report.requires_manual_review?.length ?? 0) !== 1 ? "e" : ""} fehlgeschlagen.
                  Der Export eines unvollständigen Berichts kann irreführend sein und sollte nicht an Prüfer oder Rechtsberater weitergegeben werden.
                </p>
                <p className="text-xs text-slate-500 mb-5">
                  Fehlgeschlagene Schritte: <span className="text-amber-400">{report.requires_manual_review?.join(", ")}</span>
                </p>
                <div className="flex gap-3">
                  <button
                    onClick={() => setPdfWarningOpen(false)}
                    className="flex-1 rounded-xl border border-white/[0.08] px-4 py-2.5 text-sm font-medium text-slate-400 hover:text-white hover:border-white/20 transition-colors"
                  >
                    Abbrechen
                  </button>
                  <a
                    href={`/report/${jobId}/print`}
                    target="_blank"
                    rel="noopener noreferrer"
                    onClick={() => setPdfWarningOpen(false)}
                    className="flex-1 text-center rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-2.5 text-sm font-medium text-amber-400 hover:bg-amber-500/20 transition-colors"
                  >
                    Trotzdem exportieren (nicht empfohlen)
                  </a>
                </div>
              </div>
            </div>
          )}

          {/* Profile completeness warning — shown when < 70% of relevant fields were answered */}
          {report.profile_completeness && report.profile_completeness.score_percent < 70 && (
            <div className="rounded-xl border border-orange-500/30 bg-orange-500/[0.06] px-5 py-4 flex gap-3 items-start">
              <AlertTriangle className="h-4 w-4 text-orange-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-sm font-semibold text-orange-300 mb-1">
                  Berichtsvollständigkeit: {report.profile_completeness.score_percent}%
                </p>
                <p className="text-xs text-slate-400 leading-relaxed">
                  {report.profile_completeness.unanswered_count === 1
                    ? `${report.profile_completeness.unanswered_count} compliance-relevantes Feld wurde nicht angegeben.`
                    : `${report.profile_completeness.unanswered_count} compliance-relevante Felder wurden nicht angegeben.`}{" "}
                  Einige Ergebnisse basieren möglicherweise auf Annahmen statt auf bestätigten Daten.{" "}
                  <button
                    onClick={() => router.push(`/analyze?from=${jobId}`)}
                    className="text-orange-400 hover:text-orange-300 underline underline-offset-2 transition-colors"
                  >
                    Mit mehr Daten neu ausführen
                  </button>{" "}
                  für mehr Genauigkeit.
                </p>
              </div>
            </div>
          )}

          <DocumentNudge report={report} />
          <ExecutiveSummary report={report} />
          <div className="grid lg:grid-cols-2 gap-5">
            <ApplicabilityMatrix report={report} />
            <ScoreBreakdown report={report} />
          </div>
          <GapAnalysis report={report} />
          <ActionPlan report={report} />
          <DocumentTemplates jobId={jobId} />
          <ExpertReview report={report} jobId={jobId} />

          {/* Source grounding coverage */}
          {report.regulation_coverage && Object.keys(report.regulation_coverage).length > 0 && (
            <SourceCoverage coverage={report.regulation_coverage} />
          )}

          {/* Legal database versions */}
          {report.knowledge_base_versions && Object.keys(report.knowledge_base_versions).length > 0 && (
            <KnowledgeBaseVersions versions={report.knowledge_base_versions} />
          )}

          {/* Legal disclaimer */}
          <div className="rounded-xl border border-amber-500/20 bg-amber-500/[0.05] px-5 py-4">
            <p className="text-xs text-amber-400/80 font-semibold uppercase tracking-widest mb-1">Preliminary screening only — not legal advice</p>
            <p className="text-xs text-slate-500 leading-relaxed">{report.disclaimer}</p>
          </div>
        </motion.div>
      </main>
    </div>
  );
}

const REG_DISPLAY: Record<string, string> = {
  gdpr_dsgvo: "GDPR / DSGVO", bdsg: "BDSG", nis2: "NIS2", eu_ai_act: "EU AI Act",
  hinschg: "HinSchG", workplace_law: "Employment & Workplace Law", agg: "AGG",
  milog: "MiLoG", lksg: "LkSG", enefg: "EnEfG / EDL-G", csrd: "CSRD",
  ttdsg: "TTDSG / TDDDG", gwg: "GwG", eu_data_act: "EU Data Act",
};

function KnowledgeBaseVersions({ versions }: { versions: Record<string, { fetched_at: string; source_file_hash: string; source_url: string }> }) {
  const [open, setOpen] = useState(false);
  const entries = Object.entries(versions);

  return (
    <div className="rounded-xl border border-white/[0.07] bg-white/[0.02]">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between px-5 py-3.5 text-left"
      >
        <div className="flex items-center gap-2.5">
          <Database className="h-3.5 w-3.5 text-slate-500" />
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-widest">Rechtsquellen-Versionen</span>
          <span className="text-xs text-slate-600">— welche Gesetzesversion für diesen Bericht verwendet wurde</span>
        </div>
        <ChevronDown className={`h-3.5 w-3.5 text-slate-600 transition-transform duration-200 ${open ? "rotate-180" : ""}`} />
      </button>
      {open && (
        <div className="border-t border-white/[0.05] px-5 pb-4 pt-3">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-slate-600 uppercase tracking-wider">
                <th className="text-left pb-2 font-medium">Vorschrift</th>
                <th className="text-left pb-2 font-medium">Abgerufen am</th>
                <th className="text-left pb-2 font-medium">Datei-Hash</th>
                <th className="text-left pb-2 font-medium">Quelle</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.03]">
              {entries.map(([reg, meta]) => (
                <tr key={reg}>
                  <td className="py-1.5 pr-4 text-slate-300 font-medium">{REG_DISPLAY[reg] ?? reg}</td>
                  <td className="py-1.5 pr-4 text-slate-500 font-mono">
                    {meta.fetched_at !== "unknown" ? meta.fetched_at.split("T")[0] : "unknown"}
                  </td>
                  <td className="py-1.5 pr-4 text-slate-600 font-mono">{meta.source_file_hash.slice(0, 8)}</td>
                  <td className="py-1.5 text-slate-600">
                    {meta.source_url
                      ? <a href={meta.source_url} target="_blank" rel="noopener noreferrer" className="hover:text-brand-400 transition-colors underline underline-offset-2">offizieller Text</a>
                      : "—"}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-3 text-xs text-slate-600 leading-relaxed">
            Dieser Bericht wurde auf Basis der oben aufgeführten Rechtstexte erstellt. Wenn eine Vorschrift nach dem angezeigten Datum geändert wurde, starten Sie das Screening erneut für eine aktualisierte Bewertung.
          </p>
        </div>
      )}
    </div>
  );
}

function SourceCoverage({ coverage }: { coverage: Record<string, { law_chunks: number; guidance_chunks: number; total_chunks: number; unique_articles: number }> }) {
  const [open, setOpen] = useState(false);
  const entries = Object.entries(coverage).sort((a, b) => b[1].total_chunks - a[1].total_chunks);
  const maxChunks = Math.max(...entries.map(([, v]) => v.total_chunks), 1);

  return (
    <div className="rounded-xl border border-white/[0.07] bg-white/[0.02]">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-full flex items-center justify-between px-5 py-3.5 text-left"
      >
        <div className="flex items-center gap-2.5">
          <BookOpen className="h-3.5 w-3.5 text-slate-500" />
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-widest">Quellenabdeckung</span>
          <span className="text-xs text-slate-600">— wie viele Gesetzestexte pro Regelwerk ausgewertet wurden</span>
        </div>
        <ChevronDown className={`h-3.5 w-3.5 text-slate-600 transition-transform duration-200 ${open ? "rotate-180" : ""}`} />
      </button>
      {open && (
        <div className="border-t border-white/[0.05] px-5 pb-5 pt-3 flex flex-col gap-3">
          {entries.map(([reg, v]) => (
            <div key={reg}>
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-medium text-slate-300">{REG_DISPLAY[reg] ?? reg}</span>
                <span className="text-xs text-slate-500 font-mono">
                  {v.total_chunks} Abschnitte · {v.unique_articles} Artikel
                </span>
              </div>
              <div className="h-1.5 w-full rounded-full bg-white/[0.06] overflow-hidden">
                <div
                  className="h-full rounded-full bg-brand-500/60"
                  style={{ width: `${(v.total_chunks / maxChunks) * 100}%` }}
                />
              </div>
              <div className="flex gap-3 mt-1">
                <span className="text-[10px] text-slate-600">{v.law_chunks} Gesetzestexte</span>
                <span className="text-[10px] text-slate-600">{v.guidance_chunks} Leitlinien</span>
              </div>
            </div>
          ))}
          <p className="text-xs text-slate-600 leading-relaxed mt-1">
            Zeigt, wie viele Wissensbank-Abschnitte pro Regelwerk abgerufen wurden. Mehr Abschnitte bedeuten eine breitere Quellenbasis für die Bewertung.
          </p>
        </div>
      )}
    </div>
  );
}

function DeltaBanner({ current, prev, prevJobId }: { current: ComplianceReport; prev: ComplianceReport; prevJobId: string }) {
  const delta = current.overall_score_percent - prev.overall_score_percent;
  const absD  = Math.abs(delta).toFixed(1);

  const prevStatuses = Object.fromEntries(
    prev.gap_analysis.map((g) => [`${g.regulation}:${g.article_number}`, g.status])
  );
  let improved = 0, regressed = 0;
  for (const g of current.gap_analysis) {
    const key = `${g.regulation}:${g.article_number}`;
    const was = prevStatuses[key];
    if (!was) continue;
    const rank = (s: string) => s === "COMPLIANT" ? 2 : s === "PARTIALLY_COMPLIANT" ? 1 : 0;
    if (rank(g.status) > rank(was)) improved++;
    if (rank(g.status) < rank(was)) regressed++;
  }

  const deltaColor = delta > 0 ? "text-emerald-400" : delta < 0 ? "text-red-400" : "text-slate-400";
  const borderColor = delta > 0 ? "border-emerald-500/25 bg-emerald-500/[0.04]"
    : delta < 0 ? "border-red-500/25 bg-red-500/[0.04]"
    : "border-white/[0.07] bg-white/[0.02]";

  return (
    <div className={`rounded-xl border px-5 py-4 flex items-center justify-between gap-4 flex-wrap ${borderColor}`}>
      <div className="flex items-center gap-3">
        {delta > 0 ? <TrendingUp className="h-5 w-5 text-emerald-400 flex-shrink-0" />
          : delta < 0 ? <TrendingDown className="h-5 w-5 text-red-400 flex-shrink-0" />
          : <Minus className="h-5 w-5 text-slate-500 flex-shrink-0" />}
        <div>
          <p className="text-sm font-semibold text-white">
            {delta > 0 ? `+${absD}%` : delta < 0 ? `-${absD}%` : "Keine Änderung"}{" "}
            <span className={`${deltaColor}`}>
              {delta > 0 ? "Verbesserung" : delta < 0 ? "Rückgang" : "im Score"}
            </span>
            {" "}seit dem letzten Screening
          </p>
          <p className="text-xs text-slate-500 mt-0.5">
            {improved > 0 && `${improved} Lücke${improved !== 1 ? "n" : ""} behoben`}
            {improved > 0 && regressed > 0 && " · "}
            {regressed > 0 && `${regressed} Lücke${regressed !== 1 ? "n" : ""} verschlechtert`}
            {improved === 0 && regressed === 0 && "Keine Statusänderungen bei Lücken"}
          </p>
        </div>
      </div>
      <a href={`/report/${prevJobId}`} className="text-xs text-slate-500 hover:text-slate-300 transition-colors underline underline-offset-2 flex-shrink-0">
        Vorherigen Bericht ansehen
      </a>
    </div>
  );
}
