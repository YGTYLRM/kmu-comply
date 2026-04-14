"use client";

import { useState, useCallback } from "react";
import { api } from "@/lib/api";
import type { ComplianceReport } from "@/lib/types";

export function useReport(jobId: string | null) {
  const [report, setReport] = useState<ComplianceReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetch = useCallback(async () => {
    if (!jobId) return;
    setLoading(true);
    try {
      const data = await api.getReport(jobId);
      setReport(data);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }, [jobId]);

  return { report, loading, error, fetch };
}
