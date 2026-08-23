import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import type { Priority, ComplianceStatus } from "./types";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const PRIORITY_COLOR: Record<Priority, string> = {
  CRITICAL: "text-red-400 bg-red-500/15 border-red-500/30",
  HIGH:     "text-orange-400 bg-orange-500/15 border-orange-500/30",
  MEDIUM:   "text-amber-400 bg-amber-500/15 border-amber-500/30",
  LOW:      "text-emerald-400 bg-emerald-500/15 border-emerald-500/30",
};

export const STATUS_COLOR: Record<ComplianceStatus, string> = {
  COMPLIANT:           "text-emerald-400 bg-emerald-500/15 border-emerald-500/25",
  PARTIALLY_COMPLIANT: "text-amber-400 bg-amber-500/15 border-amber-500/25",
  NON_COMPLIANT:       "text-red-400 bg-red-500/15 border-red-500/25",
  CANNOT_ASSESS:       "text-slate-500 bg-white/5 border-white/10",
};

export const REGULATION_LABEL: Record<string, string> = {
  gdpr_dsgvo:     "GDPR / DSGVO",
  lksg:           "LkSG",
  enefg:          "EnEfG / EDL-G",
  csrd:           "CSRD",
  bdsg:           "BDSG",
  nis2:           "NIS2",
  eu_ai_act:      "EU AI Act",
  hinschg:        "HinSchG",
  arbschg:        "ArbSchG",
  workplace_law:  "Employment & Workplace Law",
  agg:            "AGG",
  milog:          "MiLoG",
  ttdsg:          "TTDSG / TDDDG",
  gwg:            "GwG",
  eu_data_act:    "EU Data Act",
};
