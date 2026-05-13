import type {
  CompanyProfile,
  AnalyzeResponse,
  StatusResponse,
  ComplianceReport,
} from "./types";
export type { CompanyProfile };

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function accessHeaders(): Record<string, string> {
  if (typeof window === "undefined") return {};
  const token = localStorage.getItem("complio_access_token");
  return token ? { "X-Access-Token": token } : {};
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...accessHeaders() },
    ...init,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string }>("/api/health"),

  validateProfile: (profile: CompanyProfile) =>
    request("/api/profile/validate", {
      method: "POST",
      body: JSON.stringify(profile),
    }),

  uploadDocuments: async (files: File[]): Promise<{ doc_session_id: string; files_saved: string[] }> => {
    const form = new FormData();
    files.forEach((f) => form.append("files", f));
    const res = await fetch(`${BASE}/api/documents`, { method: "POST", body: form });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail ?? `HTTP ${res.status}`);
    }
    return res.json();
  },

  analyze: (profile: CompanyProfile, docSessionId?: string) =>
    request<AnalyzeResponse>("/api/analyze", {
      method: "POST",
      body: JSON.stringify({ profile, doc_session_id: docSessionId ?? null }),
    }),

  getStatus: (jobId: string) =>
    request<StatusResponse>(`/api/status/${jobId}`),

  getReport: (jobId: string) =>
    request<ComplianceReport>(`/api/report/${jobId}`),

  downloadPdf: (jobId: string) =>
    request<Blob>(`/api/report/${jobId}/pdf`, { method: "POST" }),

  listReports: () =>
    request<{ reports: ReportSummary[] }>("/api/reports"),

  getProfile: (jobId: string) =>
    request<CompanyProfile>(`/api/report/${jobId}/profile`),
};

export interface ReportSummary {
  job_id: string;
  company_name: string;
  generated_at: string;
  overall_score_percent: number;
  applicable_regulation_count: number;
}
