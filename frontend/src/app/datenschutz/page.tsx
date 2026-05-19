import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Datenschutzerklärung — Complio",
};

export default function DatenschutzPage() {
  return (
    <main className="min-h-screen pt-32 pb-20">
      <div className="mx-auto max-w-2xl px-6">
        <h1 className="text-3xl font-bold text-white mb-2">Datenschutzerklärung</h1>
        <p className="text-xs text-slate-600 mb-8">Stand: [Datum eintragen]</p>

        <div className="space-y-8 text-sm text-slate-400 leading-relaxed">

          <section>
            <h2 className="text-white font-semibold text-base mb-3">1. Verantwortlicher</h2>
            <p>
              Verantwortlicher im Sinne der DSGVO ist:<br /><br />
              [Name / Firma]<br />
              [Anschrift]<br />
              E-Mail: [E-Mail-Adresse]
            </p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-3">2. Erhobene Daten und Verarbeitungszwecke</h2>
            <div className="space-y-3">
              <div>
                <h3 className="text-slate-300 font-medium mb-1">Registrierung und Nutzerkonto (Art. 6 Abs. 1 lit. b DSGVO)</h3>
                <p>Bei der Registrierung erheben wir Ihren Namen, Ihre E-Mail-Adresse und ein Passwort. Diese Daten sind für die Vertragserfüllung (Bereitstellung des Dienstes) erforderlich.</p>
              </div>
              <div>
                <h3 className="text-slate-300 font-medium mb-1">Unternehmensprofile und Compliance-Berichte (Art. 6 Abs. 1 lit. b DSGVO)</h3>
                <p>Die von Ihnen eingegebenen Unternehmensdaten (Mitarbeiterzahl, Branche, Umsatz etc.) werden zur Erstellung Ihrer Compliance-Screenings verarbeitet und für die Dauer Ihrer Mitgliedschaft gespeichert.</p>
              </div>
              <div>
                <h3 className="text-slate-300 font-medium mb-1">Hochgeladene Dokumente (Art. 6 Abs. 1 lit. b DSGVO)</h3>
                <p>Dokumente, die Sie für eine vertiefte Analyse hochladen, werden verschlüsselt gespeichert und nach 7 Tagen automatisch gelöscht. Sie werden ausschließlich für das jeweilige Screening verwendet.</p>
              </div>
              <div>
                <h3 className="text-slate-300 font-medium mb-1">KI-Verarbeitung (Art. 6 Abs. 1 lit. b DSGVO)</h3>
                <p>Zur Erstellung der Gap-Analysen werden Ihre Unternehmensdaten an die Anthropic API (claude.ai) übermittelt. Anthropic verarbeitet diese Daten als Auftragsverarbeiter gemäß den geltenden Datenschutzbestimmungen.</p>
              </div>
              <div>
                <h3 className="text-slate-300 font-medium mb-1">Zahlungsdaten (Art. 6 Abs. 1 lit. b und c DSGVO)</h3>
                <p>Zahlungen werden über Stripe Inc. abgewickelt. Wir speichern keine vollständigen Kartendaten. Stripe verarbeitet Zahlungsdaten als eigenständig Verantwortlicher gemäß seiner Datenschutzrichtlinie.</p>
              </div>
              <div>
                <h3 className="text-slate-300 font-medium mb-1">Server-Logs und Fehlertracking (Art. 6 Abs. 1 lit. f DSGVO)</h3>
                <p>Zur Sicherung und Fehlerbehebung werden serverseitig Log-Daten (IP-Adresse, Anfrage-Zeitstempel, HTTP-Statuscode) sowie Fehler-Traces über Sentry erfasst. Grundlage ist unser berechtigtes Interesse an einem stabilen Betrieb.</p>
              </div>
            </div>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-3">3. Auftragsverarbeiter (Subprozessoren)</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-xs border-collapse">
                <thead>
                  <tr className="border-b border-white/10">
                    <th className="text-left text-slate-300 py-2 pr-4">Anbieter</th>
                    <th className="text-left text-slate-300 py-2 pr-4">Zweck</th>
                    <th className="text-left text-slate-300 py-2">Sitz</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  <tr><td className="py-2 pr-4">Supabase Inc.</td><td className="py-2 pr-4">Datenbank, Authentifizierung</td><td className="py-2">USA (SCC)</td></tr>
                  <tr><td className="py-2 pr-4">Anthropic PBC</td><td className="py-2 pr-4">KI-Inferenz (Gap-Analyse)</td><td className="py-2">USA (SCC)</td></tr>
                  <tr><td className="py-2 pr-4">Stripe Inc.</td><td className="py-2 pr-4">Zahlungsabwicklung</td><td className="py-2">USA (SCC)</td></tr>
                  <tr><td className="py-2 pr-4">Resend Inc.</td><td className="py-2 pr-4">Transaktionale E-Mails</td><td className="py-2">USA (SCC)</td></tr>
                  <tr><td className="py-2 pr-4">Sentry (Functional Software)</td><td className="py-2 pr-4">Fehler-Monitoring</td><td className="py-2">USA (SCC)</td></tr>
                  <tr><td className="py-2 pr-4">Vercel Inc.</td><td className="py-2 pr-4">Frontend-Hosting</td><td className="py-2">USA (SCC)</td></tr>
                </tbody>
              </table>
            </div>
            <p className="mt-2 text-xs text-slate-600">SCC = EU-Standardvertragsklauseln gemäß Art. 46 Abs. 2 lit. c DSGVO</p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-3">4. Speicherdauer</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-xs border-collapse">
                <thead>
                  <tr className="border-b border-white/10">
                    <th className="text-left text-slate-300 py-2 pr-4">Datenkategorie</th>
                    <th className="text-left text-slate-300 py-2">Speicherdauer</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5">
                  <tr><td className="py-2 pr-4">Hochgeladene Dokumente</td><td className="py-2">7 Tage, danach automatische Löschung</td></tr>
                  <tr><td className="py-2 pr-4">Compliance-Berichte</td><td className="py-2">Bis zur Löschung des Kontos durch den Nutzer</td></tr>
                  <tr><td className="py-2 pr-4">Unternehmensprofile</td><td className="py-2">Bis zur Löschung durch den Nutzer</td></tr>
                  <tr><td className="py-2 pr-4">Nutzerkonto</td><td className="py-2">Bis zur Kündigung/Löschung + gesetzliche Aufbewahrungsfristen</td></tr>
                  <tr><td className="py-2 pr-4">Rechnungsdaten</td><td className="py-2">10 Jahre (§ 147 AO)</td></tr>
                  <tr><td className="py-2 pr-4">Server-Logs</td><td className="py-2">30 Tage</td></tr>
                </tbody>
              </table>
            </div>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-3">5. Ihre Rechte</h2>
            <p className="mb-2">Sie haben folgende Rechte bezüglich Ihrer personenbezogenen Daten:</p>
            <ul className="list-disc list-inside space-y-1">
              <li><strong className="text-slate-300">Auskunft</strong> über die von uns verarbeiteten Daten (Art. 15 DSGVO)</li>
              <li><strong className="text-slate-300">Berichtigung</strong> unrichtiger Daten (Art. 16 DSGVO)</li>
              <li><strong className="text-slate-300">Löschung</strong> Ihrer Daten (Art. 17 DSGVO) — jederzeit über Ihre Kontoeinstellungen</li>
              <li><strong className="text-slate-300">Einschränkung</strong> der Verarbeitung (Art. 18 DSGVO)</li>
              <li><strong className="text-slate-300">Datenübertragbarkeit</strong> (Art. 20 DSGVO)</li>
              <li><strong className="text-slate-300">Widerspruch</strong> gegen die Verarbeitung (Art. 21 DSGVO)</li>
              <li><strong className="text-slate-300">Beschwerde</strong> bei einer Aufsichtsbehörde (Art. 77 DSGVO)</li>
            </ul>
            <p className="mt-3">
              Zur Ausübung Ihrer Rechte wenden Sie sich bitte an:{" "}
              <a href="mailto:[EMAIL]" className="text-brand-400 hover:text-brand-300">[EMAIL]</a>
            </p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-3">6. Keine automatisierte Entscheidungsfindung</h2>
            <p>
              Die von Complio erstellten Compliance-Screenings sind vorläufige, informatorische Einschätzungen und keine
              rechtsverbindlichen Entscheidungen. Es findet keine automatisierte Entscheidungsfindung im Sinne von Art. 22
              DSGVO statt.
            </p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-3">7. Cookies</h2>
            <p>
              Complio verwendet ausschließlich technisch notwendige Cookies für die Authentifizierung (Supabase
              Session-Cookie). Es werden keine Marketing- oder Tracking-Cookies gesetzt. Eine gesonderte Einwilligung
              nach § 25 TTDSG ist für technisch notwendige Cookies nicht erforderlich.
            </p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-3">8. Änderungen dieser Datenschutzerklärung</h2>
            <p>
              Wir behalten uns vor, diese Datenschutzerklärung bei Änderungen des Dienstes oder der Rechtslage
              anzupassen. Die aktuelle Version ist stets auf dieser Seite abrufbar.
            </p>
          </section>
        </div>

        <p className="mt-12 text-xs text-slate-600">
          Diese Datenschutzerklärung ist ein Entwurf und muss vor der Veröffentlichung durch einen auf Datenschutzrecht
          spezialisierten Rechtsanwalt geprüft und angepasst werden.
        </p>
      </div>
    </main>
  );
}
