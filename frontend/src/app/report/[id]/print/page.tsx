"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Image from "next/image";
import type { ComplianceReport, ComplianceStatus, Priority } from "@/lib/types";
import { REGULATION_LABEL } from "@/lib/utils";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

const REG_DESC: Record<string, string> = {
  gdpr_dsgvo: "General Data Protection Regulation",
  bdsg:       "Federal Data Protection Act",
  lksg:       "Supply Chain Due Diligence Act",
  enefg:      "Energy Efficiency Act",
  csrd:       "Corporate Sustainability Reporting Directive",
  nis2:       "Network and Information Security Directive 2",
  eu_ai_act:  "EU Artificial Intelligence Act",
  hinschg:    "Whistleblower Protection Act",
  arbschg:    "Occupational Health and Safety Act",
  agg:        "General Equal Treatment Act",
  milog:      "Minimum Wage Act",
};

const STATUS_STYLE: Record<ComplianceStatus, { label: string; color: string; bg: string }> = {
  COMPLIANT:           { label: "Compliant",          color: "#059669", bg: "#d1fae5" },
  PARTIALLY_COMPLIANT: { label: "Partial",             color: "#b45309", bg: "#fef3c7" },
  NON_COMPLIANT:       { label: "Non-Compliant",       color: "#dc2626", bg: "#fee2e2" },
  CANNOT_ASSESS:       { label: "Cannot Assess",       color: "#64748b", bg: "#f1f5f9" },
};

const PRIORITY_STYLE: Record<Priority, { label: string; color: string; bg: string }> = {
  CRITICAL: { label: "CRITICAL", color: "#dc2626", bg: "#fee2e2" },
  HIGH:     { label: "HIGH",     color: "#ea580c", bg: "#ffedd5" },
  MEDIUM:   { label: "MEDIUM",   color: "#b45309", bg: "#fef3c7" },
  LOW:      { label: "LOW",      color: "#059669", bg: "#d1fae5" },
};

function scoreColor(s: number) {
  return s >= 75 ? "#059669" : s >= 50 ? "#b45309" : "#dc2626";
}
function scoreBg(s: number) {
  return s >= 75 ? "#d1fae5" : s >= 50 ? "#fef3c7" : "#fee2e2";
}
function scoreLabel(s: number) {
  return s >= 75 ? "Good compliance posture" : s >= 50 ? "Partial compliance" : "Significant gaps identified";
}

export default function PrintPage() {
  const params = useParams();
  const jobId  = params.id as string;
  const [report, setReport] = useState<ComplianceReport | null>(null);
  const [error,  setError]  = useState<string | null>(null);

  useEffect(() => {
    fetch(`${BASE}/api/report/${jobId}`)
      .then(r => r.json())
      .then(d => {
        setReport(d);
        setTimeout(() => window.print(), 1500);
      })
      .catch(e => setError(String(e)));
  }, [jobId]);

  if (error) return <div style={{ padding: 40, fontFamily: "Inter, sans-serif", color: "#dc2626" }}>Error: {error}</div>;
  if (!report) return (
    <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh", fontFamily: "Inter, sans-serif", color: "#64748b" }}>
      Preparing report...
    </div>
  );

  const date = new Date(report.generated_at).toLocaleDateString("de-DE", { day: "numeric", month: "long", year: "numeric" });
  const applicable = report.applicable_regulations.filter(r => r.applies);
  const notApplicable = report.applicable_regulations.filter(r => !r.applies);
  const scored = report.regulation_scores.filter(s => s.total_requirements > 0);
  const byReg: Record<string, typeof report.gap_analysis> = {};
  report.gap_analysis.forEach(g => { (byReg[g.regulation] ??= []).push(g); });
  const prioOrder: Record<Priority, number> = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3 };
  const actions = [...report.action_plan].sort((a, b) => prioOrder[a.priority] - prioOrder[b.priority]);

  return (
    <>
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

        * { box-sizing: border-box; margin: 0; padding: 0; }

        body {
          font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
          font-size: 9pt;
          color: #0f172a;
          background: white;
          -webkit-print-color-adjust: exact;
          print-color-adjust: exact;
        }

        @page {
          size: A4;
          margin: 0;
        }

        .cover {
          width: 210mm;
          height: 297mm;
          position: relative;
          page-break-after: always;
          overflow: hidden;
        }

        .cover-top {
          background: #0a1637;
          width: 100%;
          height: 160mm;
          position: relative;
          padding: 14mm 16mm 0;
        }

        .cover-accent {
          position: absolute;
          right: 0; top: 0;
          width: 80mm; height: 160mm;
          background: linear-gradient(135deg, transparent 40%, rgba(37,99,235,0.15));
        }

        .cover-dots {
          position: absolute;
          inset: 0;
          background-image: radial-gradient(circle, rgba(255,255,255,0.04) 1px, transparent 1px);
          background-size: 24px 24px;
        }

        .cover-bottom {
          background: white;
          padding: 12mm 16mm;
          flex: 1;
        }

        .report-tag {
          display: inline-block;
          font-size: 7pt;
          font-weight: 600;
          letter-spacing: 0.12em;
          color: #93c5fd;
          text-transform: uppercase;
          margin-bottom: 6mm;
        }

        .cover-company {
          font-size: 26pt;
          font-weight: 800;
          color: white;
          line-height: 1.1;
          margin-bottom: 4mm;
        }

        .cover-date {
          font-size: 9pt;
          color: #94a3b8;
          margin-bottom: 10mm;
        }

        .score-badge-cover {
          position: absolute;
          right: 16mm;
          top: 12mm;
          width: 42mm;
          text-align: center;
        }

        .score-number-cover {
          font-size: 44pt;
          font-weight: 800;
          line-height: 1;
        }

        .score-label-cover {
          font-size: 7.5pt;
          font-weight: 500;
          margin-top: 1mm;
          color: rgba(255,255,255,0.7);
        }

        .stats-row {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 4mm;
          margin-top: 8mm;
          padding-top: 8mm;
          border-top: 1px solid rgba(255,255,255,0.1);
        }

        .stat-item { text-align: center; }
        .stat-value { font-size: 20pt; font-weight: 800; color: white; }
        .stat-label { font-size: 7pt; color: #94a3b8; margin-top: 1mm; }

        .score-summary-box {
          display: flex;
          align-items: center;
          gap: 8mm;
          padding: 8mm;
          border-radius: 3mm;
          margin-bottom: 8mm;
        }

        .score-circle {
          flex-shrink: 0;
          width: 24mm;
          height: 24mm;
          border-radius: 50%;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          font-weight: 800;
        }

        .score-pct { font-size: 16pt; line-height: 1; }
        .score-pct-label { font-size: 6.5pt; opacity: 0.75; margin-top: 0.5mm; }

        .section {
          page-break-inside: avoid;
          margin-bottom: 8mm;
        }

        .section-title {
          font-size: 7pt;
          font-weight: 700;
          letter-spacing: 0.1em;
          text-transform: uppercase;
          color: #3b82f6;
          margin-bottom: 3mm;
          padding-bottom: 2mm;
          border-bottom: 1.5pt solid #3b82f6;
        }

        .chapter-page {
          page-break-before: always;
          padding: 14mm 16mm;
          min-height: 297mm;
        }

        .chapter-header {
          background: #0a1637;
          margin: -14mm -16mm 10mm;
          padding: 10mm 16mm;
          display: flex;
          align-items: center;
          justify-content: space-between;
        }

        .chapter-title { font-size: 16pt; font-weight: 800; color: white; }
        .chapter-subtitle { font-size: 8.5pt; color: #94a3b8; margin-top: 1mm; }

        .chapter-logo { height: 10mm; }

        table {
          width: 100%;
          border-collapse: collapse;
          font-size: 8.5pt;
        }

        th {
          background: #0a1637;
          color: white;
          font-weight: 600;
          padding: 3mm 4mm;
          text-align: left;
          font-size: 7.5pt;
          letter-spacing: 0.03em;
        }

        td {
          padding: 3mm 4mm;
          border-bottom: 0.5pt solid #e2e8f0;
          vertical-align: top;
          line-height: 1.5;
        }

        tr:nth-child(even) td { background: #f8fafc; }

        .pill {
          display: inline-block;
          padding: 0.8mm 3mm;
          border-radius: 20pt;
          font-size: 7pt;
          font-weight: 700;
          letter-spacing: 0.04em;
        }

        .gap-block {
          border-left: 3pt solid;
          padding: 4mm 5mm;
          margin-bottom: 4mm;
          background: #fafafa;
          border-radius: 0 2mm 2mm 0;
          page-break-inside: avoid;
        }

        .gap-header {
          display: flex;
          align-items: center;
          gap: 3mm;
          margin-bottom: 2mm;
          flex-wrap: wrap;
        }

        .gap-article { font-weight: 700; font-size: 9pt; color: #0f172a; }
        .gap-title { font-size: 9pt; color: #334155; }

        .gap-evidence {
          margin-top: 2mm;
        }

        .evidence-label {
          font-size: 7pt;
          font-weight: 700;
          color: #64748b;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          margin-bottom: 1mm;
        }

        .evidence-text {
          font-size: 8.5pt;
          color: #334155;
          line-height: 1.6;
        }

        .deficiency-text {
          font-size: 8.5pt;
          color: #dc2626;
          line-height: 1.6;
          font-style: italic;
          margin-top: 2mm;
        }

        .action-block {
          border-left: 3pt solid;
          padding: 4mm 5mm;
          margin-bottom: 4mm;
          border-radius: 0 2mm 2mm 0;
          page-break-inside: avoid;
        }

        .action-meta {
          display: flex;
          align-items: center;
          gap: 3mm;
          margin-bottom: 2mm;
          flex-wrap: wrap;
        }

        .action-text {
          font-size: 8.5pt;
          color: #0f172a;
          line-height: 1.65;
          margin-bottom: 2mm;
        }

        .action-detail {
          font-size: 7.5pt;
          color: #64748b;
        }

        .bar-bg {
          background: #e2e8f0;
          height: 3mm;
          border-radius: 2pt;
          overflow: hidden;
        }

        .bar-fill {
          height: 100%;
          border-radius: 2pt;
        }

        .reg-heading {
          font-size: 9.5pt;
          font-weight: 700;
          color: #0a1637;
          margin: 6mm 0 3mm;
          padding: 2.5mm 4mm;
          background: #eff6ff;
          border-left: 3pt solid #3b82f6;
          border-radius: 0 2mm 2mm 0;
        }

        .reg-desc {
          font-size: 7.5pt;
          font-weight: 400;
          color: #64748b;
          margin-left: 2mm;
        }

        .disclaimer-box {
          background: #fff7ed;
          border: 1pt solid #fed7aa;
          border-radius: 2mm;
          padding: 5mm;
          margin-top: 6mm;
        }

        .disclaimer-title {
          font-size: 8pt;
          font-weight: 700;
          color: #92400e;
          margin-bottom: 2mm;
        }

        .disclaimer-text {
          font-size: 8pt;
          color: #78350f;
          line-height: 1.6;
        }

        .running-header {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 3mm 16mm;
          background: #0a1637;
          margin: -14mm -16mm 8mm;
        }

        .running-logo { height: 9mm; }

        .running-info {
          text-align: right;
          color: #94a3b8;
          font-size: 7pt;
        }

        @media print {
          .no-print { display: none !important; }
        }
      `}</style>

      {/* ── COVER PAGE ─────────────────────────────────────────── */}
      <div className="cover">
        <div className="cover-top">
          <div className="cover-dots" />
          <div className="cover-accent" />

          {/* Logo — white+teal version on dark, no background box */}
          <div style={{ position: "relative", zIndex: 1, marginBottom: "8mm" }}>
            <img src="/logo-dark-bg.png" alt="Complio" style={{ height: "20mm", width: "auto" }} />
          </div>

          <div style={{ position: "relative", zIndex: 1 }}>
            <span className="report-tag">Preliminary Compliance Screening Report</span>
            <div className="cover-company">{report.company_name}</div>
            <div className="cover-date">Generated on {date}</div>
          </div>

          {/* Score badge */}
          <div className="score-badge-cover" style={{ position: "absolute", right: "16mm", top: "14mm", zIndex: 1 }}>
            <div style={{
              width: "42mm", height: "42mm", borderRadius: "50%",
              background: scoreBg(report.overall_score_percent),
              display: "flex", flexDirection: "column",
              alignItems: "center", justifyContent: "center",
              border: `3pt solid ${scoreColor(report.overall_score_percent)}`,
            }}>
              <span style={{ fontSize: "28pt", fontWeight: 800, color: scoreColor(report.overall_score_percent), lineHeight: 1 }}>
                {report.overall_score_percent.toFixed(0)}%
              </span>
              <span style={{ fontSize: "6.5pt", color: scoreColor(report.overall_score_percent), marginTop: "1mm", fontWeight: 600 }}>
                Overall Score
              </span>
            </div>
            <div style={{ marginTop: "2mm", fontSize: "7pt", color: "#94a3b8", textAlign: "center" }}>
              {scoreLabel(report.overall_score_percent)}
            </div>
          </div>

          {/* Stats */}
          <div className="stats-row" style={{ position: "relative", zIndex: 1 }}>
            {[
              [String(applicable.length) + " of " + String(report.applicable_regulations.length), "regulations apply"],
              [String(report.gap_analysis.length), "requirements assessed"],
              [String(actions.length), "action items"],
              [String(actions.filter(a => a.priority === "CRITICAL").length), "critical findings"],
            ].map(([v, l]) => (
              <div className="stat-item" key={l}>
                <div className="stat-value">{v}</div>
                <div className="stat-label">{l}</div>
              </div>
            ))}
          </div>
        </div>

        {/* Cover bottom — white section */}
        <div className="cover-bottom">
          <div style={{ marginBottom: "6mm" }}>
            <div style={{ fontSize: "7pt", fontWeight: 700, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: "3mm" }}>
              Screening Scope
            </div>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <tbody>
                {[
                  ["Regulations covered", `${report.applicable_regulations.length} total, ${applicable.length} applicable`],
                  ["Requirements assessed", String(report.gap_analysis.length)],
                  ["Action items generated", String(actions.length)],
                  ["Report type", "Preliminary screening (not a legal audit)"],
                  ["Assessment date", date],
                ].map(([k, v]) => (
                  <tr key={k}>
                    <td style={{ padding: "1.5mm 0", fontWeight: 600, color: "#64748b", fontSize: "8pt", width: "55mm", verticalAlign: "top", borderBottom: "0.5pt solid #f1f5f9" }}>{k}</td>
                    <td style={{ padding: "1.5mm 0", color: "#0f172a", fontSize: "8.5pt", borderBottom: "0.5pt solid #f1f5f9" }}>{v}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="disclaimer-box">
            <div className="disclaimer-title">Important: This is a preliminary screening, not a legal audit</div>
            <div className="disclaimer-text">
              This report was generated by an AI system based on information you provided. It does not constitute legal
              advice and cannot replace a qualified legal or compliance professional. All findings should be reviewed
              by a qualified specialist before any compliance decisions are made.
            </div>
          </div>
        </div>
      </div>

      {/* ── EXECUTIVE SUMMARY ─────────────────────────────────── */}
      <div className="chapter-page">
        <div className="running-header">
          <img src="/logo-dark-bg.png" alt="Complio" className="running-logo" />
          <div className="running-info">
            <div style={{ fontWeight: 600, color: "white" }}>{report.company_name}</div>
            <div>Preliminary Screening Report · {date}</div>
          </div>
        </div>

        <div className="section-title">Executive Summary</div>

        {/* Score row */}
        <div className="score-summary-box" style={{ background: scoreBg(report.overall_score_percent), marginBottom: "6mm" }}>
          <div className="score-circle" style={{ background: scoreColor(report.overall_score_percent) }}>
            <span className="score-pct" style={{ color: "white" }}>{report.overall_score_percent.toFixed(0)}%</span>
            <span className="score-pct-label" style={{ color: "rgba(255,255,255,0.8)" }}>Score</span>
          </div>
          <div>
            <div style={{ fontSize: "11pt", fontWeight: 700, color: scoreColor(report.overall_score_percent), marginBottom: "1.5mm" }}>
              {scoreLabel(report.overall_score_percent)}
            </div>
            <div style={{ fontSize: "8.5pt", color: "#475569", lineHeight: 1.5 }}>
              {applicable.length} of {report.applicable_regulations.length} regulations apply &nbsp;·&nbsp;
              {report.gap_analysis.length} requirements assessed &nbsp;·&nbsp;
              {actions.length} action items generated
            </div>
          </div>
        </div>

        {/* Summary text */}
        <div style={{ fontSize: "9pt", lineHeight: 1.75, color: "#1e293b", whiteSpace: "pre-wrap", marginBottom: "6mm" }}>
          {report.executive_summary}
        </div>

        {/* Warnings */}
        {report.validation_warnings.length > 0 && (
          <div style={{ background: "#fffbeb", border: "1pt solid #fde68a", borderRadius: "2mm", padding: "4mm", marginBottom: "5mm" }}>
            <div style={{ fontWeight: 700, fontSize: "8pt", color: "#92400e", marginBottom: "2mm" }}>Profile notes</div>
            {report.validation_warnings.map((w, i) => (
              <div key={i} style={{ fontSize: "8.5pt", color: "#78350f", lineHeight: 1.5, marginBottom: "1mm" }}>· {w}</div>
            ))}
          </div>
        )}
      </div>

      {/* ── APPLICABILITY ─────────────────────────────────────── */}
      <div className="chapter-page">
        <div className="running-header">
          <img src="/logo-dark-bg.png" alt="Complio" className="running-logo" />
          <div className="running-info">
            <div style={{ fontWeight: 600, color: "white" }}>{report.company_name}</div>
            <div>Regulation Applicability</div>
          </div>
        </div>

        <div className="section-title">Regulation Applicability</div>
        <p style={{ fontSize: "8.5pt", color: "#64748b", lineHeight: 1.6, marginBottom: "5mm" }}>
          Applicability is determined by your company profile: employee count, revenue, industry, data processing
          activities, and other factors. Only applicable regulations were assessed in detail.
        </p>

        {/* Applicable */}
        <div style={{ marginBottom: "6mm" }}>
          <div style={{ fontSize: "8pt", fontWeight: 700, color: "#059669", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "3mm" }}>
            {applicable.length} Applicable Regulations
          </div>
          <table>
            <thead>
              <tr>
                <th style={{ width: "30mm" }}>Regulation</th>
                <th style={{ width: "40mm" }}>Full name</th>
                <th>Reason for applicability</th>
                <th style={{ width: "32mm" }}>Key threshold</th>
              </tr>
            </thead>
            <tbody>
              {applicable.map(r => (
                <tr key={r.regulation}>
                  <td style={{ fontWeight: 700, color: "#0a1637" }}>
                    <span style={{ display: "inline-block", width: "2mm", height: "10mm", background: "#059669", borderRadius: "1pt", marginRight: "2mm", verticalAlign: "middle" }} />
                    {REGULATION_LABEL[r.regulation] ?? r.regulation}
                  </td>
                  <td style={{ color: "#64748b", fontSize: "8pt" }}>{REG_DESC[r.regulation] ?? ""}</td>
                  <td style={{ color: "#334155" }}>{r.reason}</td>
                  <td style={{ color: "#64748b", fontSize: "8pt" }}>{r.key_threshold ?? ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Not applicable */}
        {notApplicable.length > 0 && (
          <div>
            <div style={{ fontSize: "8pt", fontWeight: 700, color: "#94a3b8", textTransform: "uppercase", letterSpacing: "0.08em", marginBottom: "3mm" }}>
              {notApplicable.length} Not Applicable
            </div>
            <table>
              <thead>
                <tr>
                  <th style={{ width: "30mm" }}>Regulation</th>
                  <th>Reason</th>
                </tr>
              </thead>
              <tbody>
                {notApplicable.map(r => (
                  <tr key={r.regulation}>
                    <td style={{ color: "#94a3b8", fontWeight: 600 }}>{REGULATION_LABEL[r.regulation] ?? r.regulation}</td>
                    <td style={{ color: "#94a3b8" }}>{r.reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ── SCORES ────────────────────────────────────────────── */}
      {scored.length > 0 && (
        <div className="chapter-page">
          <div className="running-header">
            <img src="/logo-dark-bg.png" alt="Complio" className="running-logo" />
            <div className="running-info">
              <div style={{ fontWeight: 600, color: "white" }}>{report.company_name}</div>
              <div>Compliance Score Breakdown</div>
            </div>
          </div>

          <div className="section-title">Compliance Score Breakdown</div>
          <p style={{ fontSize: "8.5pt", color: "#64748b", lineHeight: 1.6, marginBottom: "5mm" }}>
            Each regulation is scored based on the number of requirements assessed as compliant, partially compliant,
            or non-compliant. Cannot-assess items are excluded from the score. A score below 50% indicates material compliance exposure.
          </p>

          <table>
            <thead>
              <tr>
                <th style={{ width: "35mm" }}>Regulation</th>
                <th style={{ width: "18mm", textAlign: "center" }}>Score</th>
                <th>Progress</th>
                <th style={{ width: "20mm", textAlign: "center" }}>Compliant</th>
                <th style={{ width: "18mm", textAlign: "center" }}>Partial</th>
                <th style={{ width: "20mm", textAlign: "center" }}>Failing</th>
                <th style={{ width: "22mm", textAlign: "center" }}>Unassessed</th>
              </tr>
            </thead>
            <tbody>
              {scored.map(s => (
                <tr key={s.regulation}>
                  <td style={{ fontWeight: 700, color: "#0a1637" }}>{REGULATION_LABEL[s.regulation] ?? s.regulation}</td>
                  <td style={{ textAlign: "center", fontWeight: 800, fontSize: "11pt", color: scoreColor(s.score_percent) }}>
                    {s.score_percent.toFixed(0)}%
                  </td>
                  <td>
                    <div className="bar-bg">
                      <div className="bar-fill" style={{ width: `${s.score_percent}%`, background: scoreColor(s.score_percent) }} />
                    </div>
                  </td>
                  <td style={{ textAlign: "center", color: "#059669", fontWeight: 600 }}>{s.compliant}</td>
                  <td style={{ textAlign: "center", color: "#b45309", fontWeight: 600 }}>{s.partially_compliant}</td>
                  <td style={{ textAlign: "center", color: "#dc2626", fontWeight: 600 }}>{s.non_compliant}</td>
                  <td style={{ textAlign: "center", color: "#94a3b8", fontWeight: 600 }}>{s.cannot_assess}</td>
                </tr>
              ))}
            </tbody>
          </table>

          <p style={{ fontSize: "7.5pt", color: "#94a3b8", marginTop: "4mm" }}>
            Score = (Compliant × 1.0 + Partially Compliant × 0.5) ÷ Total assessed requirements × 100
          </p>
        </div>
      )}

      {/* ── GAP ANALYSIS ──────────────────────────────────────── */}
      {report.gap_analysis.length > 0 && (
        <div className="chapter-page">
          <div className="running-header">
            <img src="/logo-dark-bg.png" alt="Complio" className="running-logo" />
            <div className="running-info">
              <div style={{ fontWeight: 600, color: "white" }}>{report.company_name}</div>
              <div>Gap Analysis · {report.gap_analysis.length} requirements assessed</div>
            </div>
          </div>

          <div className="section-title">Gap Analysis</div>
          <p style={{ fontSize: "8.5pt", color: "#64748b", lineHeight: 1.6, marginBottom: "5mm" }}>
            Each applicable regulatory requirement is assessed against your company profile and any uploaded documents.
            Non-Compliant and Partially Compliant items generate action items in the following section.
          </p>

          {Object.entries(byReg).map(([reg, gaps]) => {
            const nc = gaps.filter(g => g.status === "NON_COMPLIANT").length;
            const pc = gaps.filter(g => g.status === "PARTIALLY_COMPLIANT").length;
            const ok = gaps.filter(g => g.status === "COMPLIANT").length;
            return (
              <div key={reg}>
                <div className="reg-heading">
                  {REGULATION_LABEL[reg] ?? reg}
                  <span className="reg-desc">{REG_DESC[reg] ? ` — ${REG_DESC[reg]}` : ""}</span>
                  <span style={{ float: "right", fontSize: "7.5pt", fontWeight: 400, color: "#64748b" }}>
                    {ok > 0 && <span style={{ color: "#059669" }}>{ok} compliant &nbsp;</span>}
                    {pc > 0 && <span style={{ color: "#b45309" }}>{pc} partial &nbsp;</span>}
                    {nc > 0 && <span style={{ color: "#dc2626" }}>{nc} non-compliant</span>}
                  </span>
                </div>

                {gaps.map((g, i) => {
                  const st = STATUS_STYLE[g.status];
                  return (
                    <div key={i} className="gap-block" style={{ borderColor: st.color }}>
                      <div className="gap-header">
                        <span className="pill" style={{ color: st.color, background: st.bg }}>
                          {st.label}
                        </span>
                        <span className="gap-article">{g.article_number}</span>
                        <span className="gap-title">{g.article_title}</span>
                      </div>

                      {g.evidence && (
                        <div className="gap-evidence">
                          <div className="evidence-label">Evidence</div>
                          <div className="evidence-text">{g.evidence}</div>
                        </div>
                      )}

                      {g.deficiency_description && (
                        <div>
                          <div className="evidence-label" style={{ color: "#dc2626", marginTop: "2mm" }}>Gap identified</div>
                          <div className="deficiency-text">{g.deficiency_description}</div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            );
          })}
        </div>
      )}

      {/* ── ACTION PLAN ───────────────────────────────────────── */}
      {actions.length > 0 && (
        <div className="chapter-page">
          <div className="running-header">
            <img src="/logo-dark-bg.png" alt="Complio" className="running-logo" />
            <div className="running-info">
              <div style={{ fontWeight: 600, color: "white" }}>{report.company_name}</div>
              <div>Action Plan · {actions.length} items</div>
            </div>
          </div>

          <div className="section-title">Prioritised Action Plan</div>
          <p style={{ fontSize: "8.5pt", color: "#64748b", lineHeight: 1.6, marginBottom: "5mm" }}>
            All non-compliant and partially compliant requirements generate at least one action item. Items are sorted by priority.
            CRITICAL and HIGH items represent legal obligations that should be addressed immediately.
          </p>

          {/* Priority summary */}
          <div style={{ display: "flex", gap: "4mm", marginBottom: "6mm" }}>
            {(["CRITICAL", "HIGH", "MEDIUM", "LOW"] as Priority[]).map(p => {
              const count = actions.filter(a => a.priority === p).length;
              if (!count) return null;
              const ps = PRIORITY_STYLE[p];
              return (
                <div key={p} style={{ padding: "2mm 4mm", borderRadius: "2mm", background: ps.bg, border: `1pt solid ${ps.color}` }}>
                  <span style={{ fontWeight: 700, fontSize: "7.5pt", color: ps.color }}>{count} {ps.label}</span>
                </div>
              );
            })}
          </div>

          {actions.map((a, i) => {
            const ps = PRIORITY_STYLE[a.priority];
            return (
              <div key={i} className="action-block" style={{ borderColor: ps.color, background: "#fafafa" }}>
                <div className="action-meta">
                  <span className="pill" style={{ color: ps.color, background: ps.bg, fontSize: "7pt" }}>
                    {ps.label}
                  </span>
                  <span style={{ fontWeight: 700, fontSize: "8.5pt", color: "#0a1637" }}>
                    {REGULATION_LABEL[a.regulation] ?? a.regulation}
                  </span>
                  <span style={{ color: "#64748b", fontSize: "8pt" }}>
                    {a.article_number}
                  </span>
                </div>
                <div className="action-text">{a.action}</div>
                <div className="action-detail">
                  <span>Estimated effort: {a.estimated_effort}</span>
                  {a.deadline && <span style={{ marginLeft: "4mm" }}>Deadline: {a.deadline}</span>}
                  {a.dependencies.length > 0 && (
                    <span style={{ marginLeft: "4mm" }}>Depends on: {a.dependencies.join(", ")}</span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ── CLOSING ───────────────────────────────────────────── */}
      <div className="chapter-page">
        <div className="running-header">
          <img src="/logo-dark-bg.png" alt="Complio" className="running-logo" />
          <div className="running-info">
            <div style={{ fontWeight: 600, color: "white" }}>{report.company_name}</div>
            <div>Closing · {date}</div>
          </div>
        </div>

        <div className="section-title">Recommended Next Steps</div>
        {[
          "Review all CRITICAL and HIGH priority action items with your management team and assign ownership.",
          "Engage a qualified legal or compliance specialist to validate the findings before taking action.",
          "Develop an implementation roadmap starting with CRITICAL items, then HIGH, then MEDIUM.",
          "Upload your company documents (privacy policies, security policies, contracts, audits) to Complio for a more detailed, evidence-backed assessment that cites your actual policies.",
          "Re-run the screening after implementing changes to track your compliance improvement over time.",
        ].map((s, i) => (
          <div key={i} style={{ display: "flex", gap: "3mm", marginBottom: "3mm", alignItems: "flex-start" }}>
            <span style={{ width: "5mm", height: "5mm", borderRadius: "50%", background: "#0a1637", color: "white", fontSize: "7pt", fontWeight: 700, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, marginTop: "0.5mm" }}>{i + 1}</span>
            <span style={{ fontSize: "9pt", color: "#1e293b", lineHeight: 1.6 }}>{s}</span>
          </div>
        ))}

        <div className="disclaimer-box" style={{ marginTop: "8mm" }}>
          <div className="disclaimer-title">Legal Disclaimer</div>
          <div className="disclaimer-text">{report.disclaimer}</div>
        </div>

        <div style={{ marginTop: "10mm", paddingTop: "5mm", borderTop: "0.5pt solid #e2e8f0", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <img src="/logo-dark-bg.png" alt="Complio" style={{ height: "10mm", filter: "brightness(0)" }} />
          <div style={{ fontSize: "7.5pt", color: "#94a3b8", textAlign: "right" }}>
            <div>Complio: Preliminary Compliance Screening</div>
            <div>{date}</div>
          </div>
        </div>
      </div>
    </>
  );
}
