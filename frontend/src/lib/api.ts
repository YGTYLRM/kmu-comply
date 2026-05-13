import type {
  CompanyProfile,
  AnalyzeResponse,
  StatusResponse,
  ComplianceReport,
} from "./types";
export type { CompanyProfile };

const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function getAuthHeader(): Promise<Record<string, string>> {
  if (typeof window === "undefined") return {};
  try {
    const { createClient } = await import("@/lib/supabase/client");
    const supabase = createClient();
    // getUser() validates the token server-side; getSession() only reads localStorage
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) return {};
    const { data: { user } } = await supabase.auth.getUser();
    if (!user) return {};
    return { Authorization: `Bearer ${session.access_token}` };
  } catch {
    return {};
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const authHeader = await getAuthHeader();
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...authHeader },
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
    const authHeader = await getAuthHeader();
    const res = await fetch(`${BASE}/api/documents`, { method: "POST", body: form, headers: authHeader });
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

  listCompanies: () =>
    request<{ companies: CompanySummary[] }>("/api/companies"),

  getCompany: (companyId: string) =>
    request<{ company: CompanyDetail; reports: CompanyReport[] }>(`/api/companies/${companyId}`),

  listNotifications: () =>
    request<{ notifications: NotificationItem[] }>("/api/notifications"),

  getUnreadCount: () =>
    request<{ count: number }>("/api/notifications/unread-count"),

  markNotificationsRead: () =>
    request<{ ok: boolean }>("/api/notifications/mark-read", { method: "POST" }),
};

export interface CompanySummary {
  id: string;
  name: string;
  industry: string | null;
  employee_count: number | null;
  country: string;
  latest_score: number | null;
  last_report_at: string | null;
  report_count: number;
  created_at: string | null;
}

export interface CompanyDetail {
  id: string;
  name: string;
  industry: string | null;
  employee_count: number | null;
  country: string;
  created_at: string | null;
}

export interface CompanyReport {
  id: string;
  job_id: string | null;
  score: number | null;
  triggered_by: string;
  created_at: string | null;
}

export interface NotificationItem {
  id: string;
  type: string;
  title: string | null;
  message: string;
  read: boolean;
  created_at: string | null;
}

export interface ReportSummary {
  job_id: string;
  company_name: string;
  generated_at: string;
  overall_score_percent: number;
  applicable_regulation_count: number;
}
