import type {
  CompanyProfile,
  AnalyzeResponse,
  StatusResponse,
  ComplianceReport,
} from "./types";
export type { CompanyProfile };

// Use relative URLs so requests go through the Next.js proxy rewrite (/api/* → backend).
// This avoids CORS entirely — the browser sees same-origin requests.
const BASE = "";

async function getAuthHeader(): Promise<Record<string, string>> {
  if (typeof window === "undefined") return {};
  try {
    const { createClient } = await import("@/lib/supabase/client");
    const supabase = createClient();
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) return {};
    return { Authorization: `Bearer ${session.access_token}` };
  } catch {
    return {};
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const authHeader = await getAuthHeader();
  const { headers: extraHeaders, ...restInit } = init ?? {};
  const res = await fetch(`${BASE}${path}`, {
    ...restInit,
    headers: {
      "Content-Type": "application/json",
      ...authHeader,
      ...(extraHeaders as Record<string, string> | undefined),
    },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail ?? `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

/** Authenticated fetch returning raw Response — use when you need full control over parsing. */
export async function authFetch(path: string, init?: RequestInit): Promise<Response> {
  const authHeader = await getAuthHeader();
  const headers: Record<string, string> = {
    ...authHeader,
    ...(init?.headers as Record<string, string> | undefined),
  };
  return fetch(`${BASE}${path}`, { ...init, headers });
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

  downloadPdf: async (jobId: string): Promise<Blob> => {
    const authHeader = await getAuthHeader();
    const res = await fetch(`${BASE}/api/report/${jobId}/pdf`, {
      method: "POST",
      headers: authHeader,
    });
    if (!res.ok) {
      const body = await res.json().catch(() => ({}));
      throw new Error(body.detail ?? `HTTP ${res.status}`);
    }
    return res.blob();
  },

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

  dashboardSummary: () =>
    request<DashboardSummary>("/api/dashboard/summary"),

  adminListExpertReviews: (adminKey: string, status?: string) =>
    request<{ reviews: AdminExpertReview[] }>(
      `/api/admin/expert-reviews${status ? `?status=${status}` : ""}`,
      { headers: { "X-Admin-Key": adminKey } as Record<string, string> }
    ),

  adminUpdateExpertReviewStatus: (adminKey: string, reviewId: string, status: string) =>
    request<{ ok: boolean; id: string; status: string }>(
      `/api/admin/expert-reviews/${reviewId}/status`,
      {
        method: "PATCH",
        headers: { "X-Admin-Key": adminKey } as Record<string, string>,
        body: JSON.stringify({ status }),
      }
    ),

  adminAssignExpertReview: (adminKey: string, reviewId: string, assignedTo: string, notes?: string) =>
    request<{ ok: boolean; id: string; assigned_to: string }>(
      `/api/admin/expert-reviews/${reviewId}/assign`,
      {
        method: "PATCH",
        headers: { "X-Admin-Key": adminKey } as Record<string, string>,
        body: JSON.stringify({ assigned_to: assignedTo, reviewer_notes: notes }),
      }
    ),

  adminListRegulationUpdates: (adminKey: string) =>
    request<{ updates: AdminRegulationUpdate[] }>("/api/admin/regulation-updates", {
      headers: { "X-Admin-Key": adminKey } as Record<string, string>,
    }),

  getBilling: () =>
    request<{ subscription: BillingSubscription | null; stripe_enabled: boolean }>("/api/billing"),
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

export interface TopAction {
  job_id: string;
  priority: "CRITICAL" | "HIGH";
  action: string;
  regulation: string | null;
  deadline: string | null;
}

export interface DashboardSummary {
  company_count: number;
  report_count: number;
  avg_score: number | null;
  recent_notifications: NotificationItem[];
  top_actions?: TopAction[];
}

export interface AdminExpertReview {
  id: string;
  user_id: string;
  job_id: string;
  company_name: string;
  user_email: string | null;
  focus_items: { regulation: string; article_number: string }[] | null;
  message: string | null;
  status: string;
  assigned_to: string | null;
  reviewer_notes: string | null;
  created_at: string | null;
  reviewed_at: string | null;
}

export interface AdminRegulationUpdate {
  id: string;
  regulation: string;
  source_url: string;
  fetched_at: string | null;
  status: string;
  change_summary: string | null;
  new_hash: string;
  previous_hash: string | null;
  reviewed_at: string | null;
}

export interface BillingSubscription {
  plan: string;
  status: string;
  current_period_end: string | null;
  stripe_subscription_id: string | null;
  company_limit: number;
  reassessment_days: number;
}
