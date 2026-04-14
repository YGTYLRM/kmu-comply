import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "KMU-Comply — Regulatory Compliance for German SMEs",
  description: "AI-powered compliance analysis for German small and medium enterprises.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="de">
      <body className="min-h-screen bg-white text-slate-900 antialiased">{children}</body>
    </html>
  );
}
