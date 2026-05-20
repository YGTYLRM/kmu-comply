import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Impressum — Complio",
};

export default function ImpressumPage() {
  return (
    <main className="min-h-screen pt-32 pb-20">
      <div className="mx-auto max-w-2xl px-6">
        <h1 className="text-3xl font-bold text-white mb-10">Impressum</h1>

        <div className="space-y-8 text-sm text-slate-400 leading-relaxed">

          {/*
            BEFORE LAUNCH — § 5 DDG requires a COMPLETE postal address (street + postcode).
            Replace the placeholder lines below with the real address before going live.
            Using a virtual office (e.g. Regus, Spaces, Davinci) is legally acceptable.
            Operating without a complete address exposes the site to Abmahnung under UWG.
          */}
          <section>
            <h2 className="text-white font-semibold text-base mb-3">Angaben gemäß § 5 DDG</h2>
            <p className="leading-7">
              Complio<br />
              Mathildenstraße 39<br />
              64285 Darmstadt<br />
              Deutschland
            </p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-3">Kontakt</h2>
            <p>
              E-Mail:{" "}
              <a href="mailto:hellocomplio@gmail.com" className="text-brand-400 hover:text-brand-300 transition-colors">
                hellocomplio@gmail.com
              </a>
            </p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-3">Umsatzsteuer-Identifikationsnummer</h2>
            <p>
              {/*
                TODO BEFORE LAUNCH: Add your USt-IdNr. (§ 27a UStG) once you have one.
                If not yet VAT-registered, replace this section with:
                "Umsatzsteuerliche Registrierung folgt nach Aufnahme der gewerblichen Tätigkeit."
              */}
              Umsatzsteuer-Identifikationsnummer gemäß § 27a UStG: DE[XXXXXXXXX]
            </p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-3">Inhaltlich verantwortlich</h2>
            <p>
              {/* TODO BEFORE LAUNCH: Replace with the full name of the natural person responsible for content */}
              [Vollständiger Name], Darmstadt
            </p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-3">Haftung für Inhalte</h2>
            <p>
              Als Diensteanbieter sind wir gemäß § 7 Abs. 1 TMG für eigene Inhalte auf diesen Seiten nach den
              allgemeinen Gesetzen verantwortlich. Nach §§ 8 bis 10 TMG sind wir als Diensteanbieter jedoch nicht
              verpflichtet, übermittelte oder gespeicherte fremde Informationen zu überwachen oder nach Umständen
              zu forschen, die auf eine rechtswidrige Tätigkeit hinweisen.
            </p>
            <p className="mt-3">
              Die über Complio erstellten Compliance-Berichte sind automatisierte Ersteinschätzungen auf Basis
              der eingegebenen Unternehmensdaten. Sie stellen keine Rechtsberatung im Sinne des
              Rechtsdienstleistungsgesetzes (RDG) dar und ersetzen nicht die Beratung durch einen zugelassenen
              Rechtsanwalt.
            </p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-3">Haftung für Links</h2>
            <p>
              Unser Angebot enthält Links zu externen Websites Dritter, auf deren Inhalte wir keinen Einfluss
              haben. Deshalb können wir für diese fremden Inhalte auch keine Gewähr übernehmen. Für die Inhalte
              der verlinkten Seiten ist stets der jeweilige Anbieter oder Betreiber der Seiten verantwortlich.
            </p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-3">Streitbeilegung</h2>
            <p>
              Die Europäische Kommission stellt eine Plattform zur Online-Streitbeilegung (OS) bereit:{" "}
              <a
                href="https://ec.europa.eu/consumers/odr/"
                target="_blank"
                rel="noopener noreferrer"
                className="text-brand-400 hover:text-brand-300 transition-colors"
              >
                https://ec.europa.eu/consumers/odr/
              </a>
              . Wir sind nicht bereit oder verpflichtet, an Streitbeilegungsverfahren vor einer
              Verbraucherschlichtungsstelle teilzunehmen. Complio richtet sich ausschließlich an Unternehmer
              im Sinne des § 14 BGB.
            </p>
          </section>

        </div>
      </div>
    </main>
  );
}
