import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Methodik — Complio",
};

export default function MethodikPage() {
  return (
    <main className="min-h-screen pt-32 pb-20">
      <div className="mx-auto max-w-2xl px-6">
        <h1 className="text-3xl font-bold text-white mb-2">Methodik</h1>
        <p className="text-xs text-slate-500 mb-10">Stand: August 2026</p>

        <div className="space-y-10 text-sm text-slate-400 leading-relaxed">

          <section>
            <h2 className="text-white font-semibold text-base mb-4">Was Complio ist — und was nicht</h2>
            <p>
              Complio ist ein automatisiertes Vor-Screening-Werkzeug. Es zeigt auf Basis der von Ihnen
              gemachten Angaben, welche deutschen und europäischen Regulierungen für Ihr Unternehmen
              voraussichtlich relevant sind, und wo mögliche Lücken bestehen könnten.
            </p>
            <p className="mt-3">
              Complio ersetzt keine Rechtsberatung. Der erzeugte Bericht ist eine vorläufige,
              KI-gestützte Einschätzung — kein Rechtsgutachten und keine formelle Bewertung durch
              einen Rechtsanwalt oder Steuerberater. Er begründet kein Mandatsverhältnis. Prüfen Sie
              alle Ergebnisse mit einer qualifizierten Fachperson, bevor Sie Maßnahmen ergreifen oder
              unterlassen.
            </p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-4">Wie eine Analyse abläuft</h2>

            <div className="space-y-6">
              <div>
                <h3 className="text-slate-200 font-semibold mb-2">1. Anwendbarkeit — regelbasiert, nicht geschätzt</h3>
                <p>
                  Ob eine Regulierung für Ihr Unternehmen überhaupt gilt, wird nicht vom KI-Modell
                  entschieden. Ein separates, deterministisches Regelwerk prüft die einschlägigen
                  Schwellenwerte — etwa Mitarbeiterzahl, Jahresumsatz, Bilanzsumme oder
                  Lieferkettenstruktur — gegen feste, im Code hinterlegte Grenzwerte (z. B. die
                  CSRD- oder LkSG-Schwellen). Das Sprachmodell erhält das Ergebnis dieser Prüfung als
                  Vorgabe und ist angewiesen, Schwellenwerte nicht selbst aus abgerufenen Gesetzestexten
                  neu herzuleiten.
                </p>
              </div>

              <div>
                <h3 className="text-slate-200 font-semibold mb-2">2. Wissensbasis — primäre Rechtsquellen</h3>
                <p>
                  Für jede anwendbare Regulierung wird der einschlägige Gesetzestext aus einer
                  eigenen Wissensbasis abgerufen (Retrieval-Augmented Generation). Die Quellen stammen
                  überwiegend direkt von gesetze-im-internet.de und EUR-Lex — nicht von
                  Sekundärquellen oder Zusammenfassungen Dritter. Jeder gespeicherte Textabschnitt
                  trägt Metadaten zu Herkunfts-URL und Rechtsstand (Datum der zugrunde liegenden
                  Gesetzesfassung), die im Bericht sichtbar sind.
                </p>
                <p className="mt-2">
                  Abgedeckt sind aktuell 14 Regulierungen: DSGVO, BDSG, LkSG, EnEfG, CSRD, NIS2,
                  EU AI Act, HinSchG, ArbSchG, AGG, MiLoG, TTDSG, GwG und der EU Data Act. Eine
                  automatisierte Prüfung erkennt Änderungen an den Quelltexten und stößt eine
                  Neuindizierung an, wenn sich eine Gesetzesfassung ändert.
                </p>
              </div>

              <div>
                <h3 className="text-slate-200 font-semibold mb-2">3. Lückenanalyse — evidenzbasiert</h3>
                <p>
                  Das Sprachmodell (derzeit ein Claude-Modell von Anthropic) vergleicht Ihre Angaben
                  mit den abgerufenen Gesetzestexten und optional hochgeladenen Unternehmensdokumenten
                  und bewertet je Pflicht, ob diese erfüllt, teilweise erfüllt oder offen ist. Jede
                  Bewertung muss durch ein wörtliches Zitat aus der Wissensbasis oder Ihren Dokumenten
                  belegt werden — freie Behauptungen ohne Beleg werden nicht akzeptiert.
                </p>
              </div>

              <div>
                <h3 className="text-slate-200 font-semibold mb-2">4. Qualitätsprüfung der Belege</h3>
                <p>
                  Jedes Zitat durchläuft zwei unabhängige Prüfungen: Erstens einen Wortlautabgleich,
                  der sicherstellt, dass das Zitat tatsächlich im Quelltext vorkommt. Zweitens eine
                  separate, modellgestützte Prüfung, ob das Zitat die getroffene Bewertung inhaltlich
                  tatsächlich stützt — ein korrektes, aber aus dem Kontext gerissenes Zitat würde die
                  erste Prüfung bestehen, aber bei der zweiten auffallen. Schlägt diese Prüfung an,
                  wird die Konfidenz der betroffenen Bewertung im Bericht automatisch herabgestuft.
                </p>
              </div>
            </div>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-4">Bekannte Grenzen</h2>
            <p>
              Die Qualität der Rangfolge bei der Textsuche wird fortlaufend gegen einen festen
              Testdatensatz überprüft. Einzelne, bekannte Fälle, in denen erläuternde Begleittexte
              einen einschlägigen Gesetzesartikel im Ranking noch verdrängen, sind erfasst und werden
              nicht ungeprüft "schnellkorrigiert" — eine punktuelle Änderung an der gemeinsamen
              Such- und Bewertungslogik könnte an anderer Stelle unbemerkt neue Fehler einführen.
              Ergebnisse zu Regulierungen mit besonders komplexer Schwellenwertlogik oder wenig
              eindeutiger Gesetzeslage sollten Sie entsprechend kritischer prüfen.
            </p>
            <p className="mt-3">
              Die Wissensbasis spiegelt den Rechtsstand zum Zeitpunkt der letzten Indizierung wider,
              nicht zwingend die aktuellste Gesetzesänderung oder Rechtsprechung. Das
              Aktualisierungsdatum jeder Quelle ist im Bericht ausgewiesen.
            </p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-4">Datenverarbeitung</h2>
            <p>
              Details zur Verarbeitung Ihrer Daten, eingesetzten Auftragsverarbeitern und
              Speicherfristen finden Sie in der{" "}
              <a href="/datenschutz" className="text-brand-400 hover:text-brand-300 transition-colors">
                Datenschutzerklärung
              </a>.
            </p>
          </section>

        </div>
      </div>
    </main>
  );
}
