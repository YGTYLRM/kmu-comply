"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { motion } from "framer-motion";
import { api, type CompanyDetail, type CompanyReport, type NotificationItem } from "@/lib/api";
import {
  ArrowLeft, Plus, FileText, Bell, TrendingUp, TrendingDown,
  Minus, Loader2, AlertCircle, Calendar, RefreshCw, Zap,
} from "lucide-react";

// ── Score trend SVG chart ─────────────────────────────────────────────────────

function ScoreTrendChart({ reports }: { reports: CompanyReport[] }) {
  const points = [...reports]
    .filter(r => r.score !== null)
    .reverse()
    .slice(-10);

  if (points.length < 2) {
    return (
      <div className="flex h-40 items-center justify-center text-sm text-slate-600">
        Run at least 2 screenings to see a trend.
      </div>
    );
  }

  const W = 480, H = 140, PAD = 24;
  const scores = points.map(p => p.score as number);
  const minS = Math.max(0, Math.min(...scores) - 10);
  const maxS = Math.min(100, Math.max(...scores) + 10);
  const xStep = (W - PAD * 2) / (points.length - 1);

  const toX = (i: number) => PAD + i * xStep;
  const toY = (s: number) => PAD + ((maxS - s) / (maxS - minS)) * (H - PAD * 2);

  const pathD = points.map((p, i) =>
    `${i === 0 ? "M" : "L"}${toX(i).toFixed(1)},${toY(p.score as number).toFixed(1)}`
  ).join(" ");

  const areaD = `${pathD} L${toX(points.length - 1).toFixed(1)},${H} L${toX(0).toFixed(1)},${H} Z`;

  const scoreColor = (s: number) => s >= 75 ? "#10b981" : s >= 50 ? "#f59e0b" : "#ef4444";
  const lastScore = scores[scores.length - 1];

  return (
    <div className="w-full overflow-x-auto">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full" style={{ minWidth: 260 }}>
        <defs>
          <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={scoreColor(lastScore)} stopOpacity="0.18" />
            <stop offset="100%" stopColor={scoreColor(lastScore)} stopOpacity="0" />
          </linearGradient>
        </defs>
        {/* Grid lines */}
        {[25, 50, 75, 100].map(v => (
          <line key={v}
            x1={PAD} y1={toY(v).toFixed(1)} x2={W - PAD} y2={toY(v).toFixed(1)}
            stroke="rgba(255,255,255,0.05)" strokeWidth="1"
          />
        ))}
        {/* Area fill */}
        <path d={areaD} fill="url(#areaGrad)" />
        {/* Line */}
        <path d={pathD} fill="none" stroke={scoreColor(lastScore)} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        {/* Dots + labels */}
        {points.map((p, i) => (
          <g key={i}>
            <circle cx={toX(i)} cy={toY(p.score as number)} r="4"
              fill={scoreColor(p.score as number)} stroke="#03071a" strokeWidth="2" />
            <text x={toX(i)} y={H - 4} textAnchor="middle" fontSize="9" fill="#475569">
              {p.created_at ? new Date(p.created_at).toLocaleDateString("en-GB", { day: "numeric", month: "short" }) : ""}
            </text>
          </g>
        ))}
      </svg>
    </div>
  );
}

// ── Report history row ────────────────────────────────────────────────────────

function ReportRow({ report, prev }: { report: CompanyReport; prev: CompanyReport | undefined }) {
  const delta = prev?.score != null && report.score != null ? report.score - prev.score : null;
  const scoreColor = (s: number) => s >= 75 ? "text-emerald-400" : s >= 50 ? "text-amber-400" : "text-red-400";
  const TriggerIcon = report.triggered_by === "reg_change" ? Zap
    : report.triggered_by === "scheduled" ? RefreshCw : FileText;

  return (
    <div className="flex items-center gap-4 py-3 border-b border-white/[0.05] last:border-0">
      <div className="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-lg bg-white/[0.04]">
        <TriggerIcon className="h-3.5 w-3.5 text-slate-500" />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-white font-medium">
          {report.triggered_by === "reg_change" ? "Regulation update re-assessment"
            : report.triggered_by === "scheduled" ? "Monthly screening"
            : "Manual screening"}
        </p>
        <p className="text-xs text-slate-600 mt-0.5 flex items-center gap-1">
          <Calendar className="h-3 w-3" />
          {report.created_at ? new Date(report.created_at).toLocaleDateString("en-GB", {
            day: "numeric", month: "long", year: "numeric"
          }) : "Unknown date"}
        </p>
      </div>
      <div className="flex items-center gap-3 flex-shrink-0">
        {delta !== null && (
          <span className={`text-xs flex items-center gap-0.5 ${delta > 0 ? "text-emerald-400" : delta < 0 ? "text-red-400" : "text-slate-500"}`}>
            {delta > 0 ? <TrendingUp className="h-3 w-3" /> : delta < 0 ? <TrendingDown className="h-3 w-3" /> : <Minus className="h-3 w-3" />}
            {delta > 0 ? `+${delta.toFixed(1)}%` : `${delta.toFixed(1)}%`}
          </span>
        )}
        {report.score !== null && (
          <span className={`text-sm font-bold ${scoreColor(report.score)}`}>
            {report.score.toFixed(1)}%
          </span>
        )}
        {report.job_id && (
          <Link href={`/report/${report.job_id}`}
            className="text-xs text-brand-400 hover:text-brand-300 transition-colors underline underline-offset-2">
            View
          </Link>
        )}
      </div>
    </div>
  );
}

// ── Notification row ──────────────────────────────────────────────────────────

function NotifRow({ notif }: { notif: NotificationItem }) {
  return (
    <div className={`py-3 border-b border-white/[0.05] last:border-0 ${notif.read ? "opacity-60" : ""}`}>
      <div className="flex items-start gap-3">
        <div className={`mt-0.5 h-2 w-2 flex-shrink-0 rounded-full ${notif.read ? "bg-slate-700" : "bg-brand-500"}`} />
        <div>
          {notif.title && <p className="text-sm font-medium text-white">{notif.title}</p>}
          <p className="text-xs text-slate-500 mt-0.5">{notif.message}</p>
          <p className="text-xs text-slate-700 mt-1">
            {notif.created_at ? new Date(notif.created_at).toLocaleDateString("en-GB", {
              day: "numeric", month: "short", year: "numeric"
            }) : ""}
          </p>
        </div>
      </div>
    </div>
  );
}

// ── Main page ─────────────────────────────────────────────────────────────────

type Tab = "overview" | "history" | "notifications";

export default function CompanyDetailPage() {
  const { companyId } = useParams<{ companyId: string }>();
  const router = useRouter();

  const [company, setCompany]   = useState<CompanyDetail | null>(null);
  const [reports, setReports]   = useState<CompanyReport[]>([]);
  const [notifs, setNotifs]     = useState<NotificationItem[]>([]);
  const [tab, setTab]           = useState<Tab>("overview");
  const [loading, setLoading]   = useState(true);
  const [error, setError]       = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      api.getCompany(companyId),
      api.listNotifications(),
    ])
      .then(([companyData, notifData]) => {
        setCompany(companyData.company);
        setReports(companyData.reports);
        // Filter notifications to those mentioning this company
        setNotifs(notifData.notifications.filter(n =>
          n.title?.includes(companyData.company.name) ||
          n.message?.includes(companyData.company.name)
        ));
      })
      .catch(() => setError("Failed to load company data."))
      .finally(() => setLoading(false));
  }, [companyId]);

  if (loading) return (
    <main className="bg-dark-950 min-h-screen flex items-center justify-center">
      <Loader2 className="h-8 w-8 animate-spin text-brand-500" />
    </main>
  );

  if (error || !company) return (
    <main className="bg-dark-950 min-h-screen flex items-center justify-center px-4">
      <div className="flex items-center gap-3 rounded-xl border border-red-500/25 bg-red-500/10 px-5 py-4 text-sm text-red-400">
        <AlertCircle className="h-4 w-4" /> {error ?? "Company not found."}
      </div>
    </main>
  );

  const latestReport = reports[0];
  const latestScore  = latestReport?.score ?? null;
  const scoreColor   = latestScore === null ? "#64748b"
    : latestScore >= 75 ? "#10b981" : latestScore >= 50 ? "#f59e0b" : "#ef4444";

  const TABS: { id: Tab; label: string }[] = [
    { id: "overview",      label: "Overview" },
    { id: "history",       label: `History (${reports.length})` },
    { id: "notifications", label: `Alerts (${notifs.filter(n => !n.read).length} new)` },
  ];

  return (
    <main className="bg-dark-950 min-h-screen pt-28 pb-16 px-4 sm:px-6">
      <div className="mx-auto max-w-4xl">

        {/* Back */}
        <Link href="/dashboard" className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-white transition-colors mb-6">
          <ArrowLeft className="h-3.5 w-3.5" /> All companies
        </Link>

        {/* Company header */}
        <div className="flex items-start justify-between gap-4 mb-6 flex-wrap">
          <div>
            <h1 className="text-2xl font-black text-white tracking-tight">{company.name}</h1>
            <p className="text-sm text-slate-500 mt-1">
              {[company.industry, company.employee_count ? `${company.employee_count} employees` : null, company.country]
                .filter(Boolean).join(" · ")}
            </p>
          </div>
          <Link
            href={`/analyze?from=${latestReport?.job_id ?? ""}`}
            className="inline-flex items-center gap-2 rounded-xl bg-brand-600 px-5 py-2.5 text-sm font-semibold text-white hover:bg-brand-500 transition-all shadow-glow-blue-sm"
          >
            <Plus className="h-4 w-4" /> Re-run screening
          </Link>
        </div>

        {/* Score summary strip */}
        <div className="grid grid-cols-3 gap-3 mb-6">
          <div className="rounded-2xl border border-white/[0.07] bg-dark-900/60 p-4 text-center">
            <p className="text-2xl font-black" style={{ color: scoreColor }}>
              {latestScore !== null ? `${latestScore.toFixed(1)}%` : "—"}
            </p>
            <p className="text-xs text-slate-500 mt-1">Current score</p>
          </div>
          <div className="rounded-2xl border border-white/[0.07] bg-dark-900/60 p-4 text-center">
            <p className="text-2xl font-black text-white">{reports.length}</p>
            <p className="text-xs text-slate-500 mt-1">Total screenings</p>
          </div>
          <div className="rounded-2xl border border-white/[0.07] bg-dark-900/60 p-4 text-center">
            <p className="text-2xl font-black text-white">{notifs.filter(n => !n.read).length}</p>
            <p className="text-xs text-slate-500 mt-1">Unread alerts</p>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 rounded-xl border border-white/[0.07] bg-white/[0.02] p-1 mb-6">
          {TABS.map(t => (
            <button
              key={t.id}
              onClick={() => setTab(t.id)}
              className={`flex-1 rounded-lg py-2 text-sm font-medium transition-all ${
                tab === t.id
                  ? "bg-brand-600 text-white shadow-glow-blue-sm"
                  : "text-slate-400 hover:text-white"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Tab content */}
        <motion.div key={tab} initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2 }}>

          {tab === "overview" && (
            <div className="flex flex-col gap-5">
              <div className="rounded-2xl border border-white/[0.07] bg-dark-900/60 p-5">
                <p className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-4">Score trend</p>
                <ScoreTrendChart reports={reports} />
              </div>
              {latestReport && (
                <div className="rounded-2xl border border-white/[0.07] bg-dark-900/60 p-5">
                  <p className="text-xs font-bold uppercase tracking-widest text-slate-500 mb-3">Latest screening</p>
                  <ReportRow report={latestReport} prev={reports[1]} />
                </div>
              )}
            </div>
          )}

          {tab === "history" && (
            <div className="rounded-2xl border border-white/[0.07] bg-dark-900/60 p-5">
              {reports.length === 0
                ? <p className="text-sm text-slate-600 py-8 text-center">No reports yet.</p>
                : reports.map((r, i) => <ReportRow key={r.id} report={r} prev={reports[i + 1]} />)
              }
            </div>
          )}

          {tab === "notifications" && (
            <div className="rounded-2xl border border-white/[0.07] bg-dark-900/60 p-5">
              {notifs.length === 0
                ? <p className="text-sm text-slate-600 py-8 text-center">No alerts for this company yet.</p>
                : notifs.map(n => <NotifRow key={n.id} notif={n} />)
              }
            </div>
          )}

        </motion.div>
      </div>
    </main>
  );
}
