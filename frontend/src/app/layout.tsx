import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Navbar } from "@/components/common/navbar";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "KMU-Comply — Regulatory Compliance for German SMEs",
  description: "Preliminary compliance screening for German SMEs. Find out which regulations apply to your company and where your gaps are.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="de">
      <body className={`${inter.className} min-h-screen bg-white text-slate-900 antialiased`}>
        <Navbar />
        {children}
      </body>
    </html>
  );
}
