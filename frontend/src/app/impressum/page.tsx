import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Impressum — Complio",
};

export default function ImpressumPage() {
  return (
    <main className="min-h-screen pt-32 pb-20">
      <div className="mx-auto max-w-2xl px-6">
        <h1 className="text-3xl font-bold text-white mb-8">Impressum</h1>

        <div className="space-y-6 text-sm text-slate-400 leading-relaxed">
          <section>
            <h2 className="text-white font-semibold text-base mb-2">Angaben gemäß § 5 DDG</h2>
            <p>
              [Vorname Nachname / Firmenname]<br />
              [Straße und Hausnummer]<br />
              [PLZ Ort]<br />
              Deutschland
            </p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-2">Kontakt</h2>
            <p>
              E-Mail: <a href="mailto:[EMAIL]" className="text-brand-400 hover:text-brand-300">[EMAIL]</a>
            </p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-2">Umsatzsteuer-ID</h2>
            <p>Umsatzsteuer-Identifikationsnummer gemäß § 27a UStG: [USt-ID, falls vorhanden]</p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-2">Handelsregister</h2>
            <p>[Handelsregister und Registernummer, falls zutreffend]</p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-2">Verantwortlich für den Inhalt</h2>
            <p>[Vorname Nachname, Anschrift wie oben]</p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-2">Haftungshinweis</h2>
            <p>
              Die Inhalte dieser Website wurden mit größtmöglicher Sorgfalt erstellt. Complio übernimmt jedoch keine
              Gewähr für die Richtigkeit, Vollständigkeit und Aktualität der bereitgestellten Inhalte. Die
              Compliance-Screenings sind vorläufige Einschätzungen und ersetzen keine Rechtsberatung durch einen
              qualifizierten Rechtsanwalt.
            </p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-2">EU-Streitschlichtung</h2>
            <p>
              Die Europäische Kommission stellt eine Plattform zur Online-Streitbeilegung (OS) bereit:{" "}
              <a
                href="https://ec.europa.eu/consumers/odr/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-brand-400 hover:text-brand-300"
              >
                https://ec.europa.eu/consumers/odr/
              </a>
              . Unsere E-Mail-Adresse finden Sie oben im Impressum. Wir sind nicht bereit oder verpflichtet, an
              Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle teilzunehmen.
            </p>
          </section>
        </div>

        <p className="mt-12 text-xs text-slate-600">
          Bitte ersetzen Sie alle Platzhalter in eckigen Klammern durch Ihre tatsächlichen Angaben.
        </p>
      </div>
    </main>
  );
}
