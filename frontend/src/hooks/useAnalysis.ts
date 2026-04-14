"use client";

import { useState, useCallback } from "react";
import { api } from "@/lib/api";
import type { CompanyProfile, StatusResponse, JobStatus } from "@/lib/types";

interface AnalysisState {
  jobId: string | null;
  status: StatusResponse | null;
  error: string | null;
  loading: boolean;
}

export function useAnalysis() {
  const [state, setState] = useState<AnalysisState>({
    jobId: null,
    status: null,
    error: null,
    loading: false,
  });

  const submit = useCallback(async (profile: CompanyProfile) => {
    setState({ jobId: null, status: null, error: null, loading: true });
    try {
      const { job_id } = await api.analyze(profile);
      setState((s) => ({ ...s, jobId: job_id }));
      return job_id;
    } catch (err) {
      setState((s) => ({ ...s, error: String(err), loading: false }));
      return null;
    }
  }, []);

  const poll = useCallback(async (jobId: string): Promise<JobStatus> => {
    try {
      const status = await api.getStatus(jobId);
      setState((s) => ({ ...s, status, loading: status.status === "running" || status.status === "pending" }));
      return status.status;
    } catch (err) {
      setState((s) => ({ ...s, error: String(err), loading: false }));
      return "failed";
    }
  }, []);

  return { ...state, submit, poll };
}
