import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Navbar } from "@/components/common/navbar";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Complio: Regulatory Compliance Screening for German SMEs",
  description: "Preliminary compliance screening for German SMEs. Find which regulations apply to your company and where your gaps are, in minutes.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="de">
      <body className={`${inter.className} min-h-screen bg-dark-950 text-white antialiased`}>
        <Navbar />
        {children}
      </body>
    </html>
  );
}
