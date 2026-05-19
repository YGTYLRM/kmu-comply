import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Navbar } from "@/components/common/navbar";
import { Footer } from "@/components/common/footer";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Complio: Compliance-Screening für deutsche Unternehmen",
  description: "Automatisiertes Compliance-Screening für deutsche KMU. In Minuten wissen, welche Gesetze gelten und wo Lücken bestehen.",
  openGraph: {
    title: "Complio — Compliance-Screening für deutsche Unternehmen",
    description: "14 deutsche und EU-Vorschriften automatisch geprüft. Compliance-Pflichten kennen — in Minuten, nicht Monaten.",
    type: "website",
    locale: "de_DE",
    siteName: "Complio",
  },
  twitter: {
    card: "summary_large_image",
    title: "Complio — Compliance-Screening für deutsche Unternehmen",
    description: "14 deutsche und EU-Vorschriften automatisch geprüft. Compliance-Pflichten kennen — in Minuten, nicht Monaten.",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="de">
      <body className={`${inter.className} min-h-screen bg-dark-950 text-white antialiased`}>
        <Navbar />
        {children}
        <Footer />
      </body>
    </html>
  );
}
