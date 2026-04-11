import type {
  CompanyProfile,
  AnalyzeResponse,
  StatusResponse,
  ComplianceReport,
} from "./types";

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
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

  analyze: (profile: CompanyProfile) =>
    request<AnalyzeResponse>("/api/analyze", {
      method: "POST",
      body: JSON.stringify(profile),
    }),

  getStatus: (jobId: string) =>
    request<StatusResponse>(`/api/status/${jobId}`),

  getReport: (jobId: string) =>
    request<ComplianceReport>(`/api/report/${jobId}`),

  downloadPdf: (jobId: string) =>
    request<Blob>(`/api/report/${jobId}/pdf`, { method: "POST" }),
};
