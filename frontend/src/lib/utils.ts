import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import type { Priority, ComplianceStatus } from "./types";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const PRIORITY_COLOR: Record<Priority, string> = {
  CRITICAL: "text-red-700 bg-red-50 border-red-200",
  HIGH:     "text-orange-700 bg-orange-50 border-orange-200",
  MEDIUM:   "text-yellow-700 bg-yellow-50 border-yellow-200",
  LOW:      "text-green-700 bg-green-50 border-green-200",
};

export const STATUS_COLOR: Record<ComplianceStatus, string> = {
  COMPLIANT:          "text-green-700 bg-green-50",
  PARTIALLY_COMPLIANT:"text-yellow-700 bg-yellow-50",
  NON_COMPLIANT:      "text-red-700 bg-red-50",
  CANNOT_ASSESS:      "text-slate-600 bg-slate-50",
};

export const REGULATION_LABEL: Record<string, string> = {
  gdpr_dsgvo: "GDPR / DSGVO",
  lksg:       "LkSG",
  enefg:      "EnEfG",
  csrd:       "CSRD",
  bdsg:       "BDSG",
};
