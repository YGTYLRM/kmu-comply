import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AGB — Complio",
};

export default function AGBPage() {
  return (
    <main className="min-h-screen pt-32 pb-20">
      <div className="mx-auto max-w-2xl px-6">
        <h1 className="text-3xl font-bold text-white mb-2">Allgemeine Geschäftsbedingungen (AGB)</h1>
        <p className="text-xs text-slate-600 mb-8">Stand: [Datum eintragen]</p>

        <div className="space-y-8 text-sm text-slate-400 leading-relaxed">

          <section>
            <h2 className="text-white font-semibold text-base mb-3">§ 1 Geltungsbereich und Vertragspartner</h2>
            <p>
              Diese Allgemeinen Geschäftsbedingungen gelten für alle Verträge zwischen [Firma] (&ldquo;Complio&rdquo;,
              &ldquo;wir&rdquo;, &ldquo;uns&rdquo;) und gewerblichen Kunden (&ldquo;Nutzer&rdquo;) über die Nutzung der
              Complio-Plattform. Complio richtet sich ausschließlich an Unternehmer im Sinne des § 14 BGB. Die Nutzung
              durch Verbraucher (§ 13 BGB) ist ausgeschlossen.
            </p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-3">§ 2 Leistungsbeschreibung</h2>
            <p>
              Complio ist eine SaaS-Plattform für automatisierte Compliance-Screenings. Der Dienst analysiert das
              eingereichte Unternehmensprofil gegen 14 deutsche und europäische Rechtsvorschriften und erstellt einen
              vorläufigen Compliance-Bericht mit Gap-Analyse und priorisierten Handlungsempfehlungen.
            </p>
            <p className="mt-2 font-semibold text-amber-400">
              Wichtiger Hinweis: Complio-Berichte sind vorläufige Screening-Ergebnisse und stellen keine Rechtsberatung
              dar. Sie ersetzen nicht die Beratung durch einen qualifizierten Rechtsanwalt. Complio haftet nicht für
              Entscheidungen, die allein auf Basis der Screening-Ergebnisse getroffen werden.
            </p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-3">§ 3 Vertragsschluss und Laufzeit</h2>
            <p>
              Der Vertrag kommt durch Abschluss des Bestellprozesses (Registrierung und Auswahl eines Tarifs) zustande.
              Abonnements laufen monatlich oder jährlich und verlängern sich automatisch, sofern sie nicht rechtzeitig
              gekündigt werden. Die Kündigungsfrist beträgt 30 Tage zum Ende der jeweiligen Laufzeit.
            </p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-3">§ 4 Preise und Zahlung</h2>
            <p>
              Die aktuellen Preise sind auf der Website unter /pricing einsehbar. Alle Preise verstehen sich zuzüglich
              der gesetzlichen Mehrwertsteuer. Zahlungen erfolgen im Voraus über Stripe. Bei Zahlungsverzug behalten
              wir uns vor, den Zugang zum Dienst zu sperren.
            </p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-3">§ 5 Nutzungsrechte und Verbote</h2>
            <p>
              Der Nutzer erhält ein nicht-ausschließliches, nicht übertragbares Recht zur Nutzung der Plattform für
              eigene Compliance-Zwecke. Verboten ist insbesondere: (a) die Weitergabe von Zugangsdaten an Dritte,
              (b) die Nutzung für mehr Unternehmen als im gebuchten Tarif vorgesehen, (c) das automatisierte Abfragen
              der API ohne ausdrückliche Genehmigung, (d) die Verwendung der Berichte als Rechtsberatung gegenüber
              Dritten ohne entsprechende Qualifikation.
            </p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-3">§ 6 Datenschutz und Vertraulichkeit</h2>
            <p>
              Die Verarbeitung personenbezogener Daten erfolgt gemäß unserer Datenschutzerklärung. Der Nutzer
              versichert, dass er berechtigt ist, die hochgeladenen Unternehmensdaten und Dokumente für die Nutzung
              des Dienstes einzureichen.
            </p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-3">§ 7 Haftungsbeschränkung</h2>
            <p>
              Complio haftet unbeschränkt bei Vorsatz und grober Fahrlässigkeit sowie für Schäden aus der Verletzung
              des Lebens, des Körpers oder der Gesundheit. Bei leichter Fahrlässigkeit haftet Complio nur bei Verletzung
              wesentlicher Vertragspflichten, und zwar der Höhe nach beschränkt auf den typischerweise vorhersehbaren
              Schaden. In jedem Fall ist die Haftung auf die Summe der in den letzten 12 Monaten gezahlten
              Abonnementgebühren begrenzt.
            </p>
            <p className="mt-2">
              Complio übernimmt keine Haftung dafür, dass die Berichte für die spezifische Situation des Nutzers
              vollständig oder rechtlich zutreffend sind. Behördliche Bußgelder oder Strafen, die aus einer Nutzung
              der Plattform resultieren, sind nicht erstattungsfähig.
            </p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-3">§ 8 Kündigung und Datenlöschung</h2>
            <p>
              Nach Vertragsende werden Nutzerdaten innerhalb von 30 Tagen gelöscht, sofern keine gesetzlichen
              Aufbewahrungspflichten entgegenstehen. Der Nutzer kann sein Konto und seine Daten jederzeit über die
              Kontoeinstellungen löschen.
            </p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-3">§ 9 Anwendbares Recht und Gerichtsstand</h2>
            <p>
              Es gilt das Recht der Bundesrepublik Deutschland unter Ausschluss des UN-Kaufrechts (CISG). Gerichtsstand
              für alle Streitigkeiten ist [Ort des Firmensitzes], soweit der Nutzer Kaufmann ist.
            </p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-3">§ 10 Schlussbestimmungen</h2>
            <p>
              Sollten einzelne Bestimmungen dieser AGB unwirksam sein, bleibt die Wirksamkeit der übrigen Bestimmungen
              unberührt. Änderungen dieser AGB werden dem Nutzer per E-Mail angekündigt und gelten als genehmigt, sofern
              nicht innerhalb von 30 Tagen widersprochen wird.
            </p>
          </section>
        </div>

        <p className="mt-12 text-xs text-slate-600">
          Diese AGB sind ein Entwurf und müssen vor der Veröffentlichung durch einen auf IT-/Vertragsrecht
          spezialisierten Rechtsanwalt geprüft werden.
        </p>
      </div>
    </main>
  );
}
