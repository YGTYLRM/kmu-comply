import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Datenschutzerklärung — Complio",
};

export default function DatenschutzPage() {
  return (
    <main className="min-h-screen pt-32 pb-20">
      <div className="mx-auto max-w-2xl px-6">
        <h1 className="text-3xl font-bold text-white mb-2">Datenschutzerklärung</h1>
        <p className="text-xs text-slate-500 mb-10">Stand: Mai 2026</p>

        <div className="space-y-10 text-sm text-slate-400 leading-relaxed">

          <section>
            <h2 className="text-white font-semibold text-base mb-4">§ 1 Verantwortlicher und Kontakt</h2>
            <p>
              Verantwortlicher im Sinne der Datenschutz-Grundverordnung (DSGVO) und des
              Bundesdatenschutzgesetzes (BDSG) ist:
            </p>
            {/* TODO BEFORE LAUNCH: Add real street + postcode (must match Impressum) */}
            <p className="mt-3 leading-7">
              Complio<br />
              Musterstraße 1<br />
              64283 Darmstadt<br />
              Deutschland<br />
              E-Mail:{" "}
              <a href="mailto:hellocomplio@gmail.com" className="text-brand-400 hover:text-brand-300 transition-colors">
                hellocomplio@gmail.com
              </a>
            </p>
            <p className="mt-3">
              Bei Fragen zur Verarbeitung Ihrer personenbezogenen Daten wenden Sie sich bitte unter
              der oben genannten E-Mail-Adresse an uns.
            </p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-4">§ 2 Grundsätze der Datenverarbeitung</h2>
            <p>
              Complio verarbeitet personenbezogene Daten nur, soweit dies zur Erbringung unserer
              Dienstleistung erforderlich ist oder eine sonstige Rechtsgrundlage nach Art. 6 DSGVO
              vorliegt. Wir verarbeiten keine personenbezogenen Daten zu Werbezwecken oder für die
              Erstellung von Nutzerprofilen zu Marketingzwecken.
            </p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-4">§ 3 Verarbeitungstätigkeiten im Einzelnen</h2>

            <div className="space-y-6">
              <div>
                <h3 className="text-slate-200 font-semibold mb-2">3.1 Nutzerkonto und Authentifizierung</h3>
                <p>
                  Bei der Registrierung erheben wir Ihre E-Mail-Adresse sowie ein verschlüsseltes Passwort.
                  Diese Daten werden ausschließlich zur Bereitstellung des Nutzerzugangs verarbeitet.
                </p>
                <p className="mt-2">
                  <span className="text-slate-300 font-medium">Rechtsgrundlage:</span>{" "}
                  Art. 6 Abs. 1 lit. b DSGVO (Vertragserfüllung).<br />
                  <span className="text-slate-300 font-medium">Speicherdauer:</span>{" "}
                  Bis zur Löschung des Kontos durch den Nutzer.
                </p>
              </div>

              <div>
                <h3 className="text-slate-200 font-semibold mb-2">3.2 Unternehmensprofile und Compliance-Berichte</h3>
                <p>
                  Zur Erstellung von Compliance-Screenings verarbeiten wir die von Ihnen eingegebenen
                  Unternehmensdaten, insbesondere Branche, Mitarbeiterzahl, Jahresumsatz,
                  Bilanzsumme, Datenpraktiken, Lieferkettenstruktur und Energieverbrauch. Diese Angaben
                  sind für die Erbringung des Dienstes zwingend erforderlich.
                </p>
                <p className="mt-2">
                  <span className="text-slate-300 font-medium">Rechtsgrundlage:</span>{" "}
                  Art. 6 Abs. 1 lit. b DSGVO (Vertragserfüllung).<br />
                  <span className="text-slate-300 font-medium">Speicherdauer:</span>{" "}
                  Bis zur Löschung durch den Nutzer oder Kontolöschung.
                </p>
              </div>

              <div>
                <h3 className="text-slate-200 font-semibold mb-2">3.3 Hochgeladene Dokumente</h3>
                <p>
                  Dokumente, die Sie optional für eine vertiefte Analyse hochladen (z. B.
                  Datenschutzerklärungen, AVV, Sicherheitsrichtlinien), werden AES-256-verschlüsselt
                  gespeichert und nach Ablauf von 7 Tagen automatisch und unwiderruflich gelöscht.
                  Die Dokumente werden ausschließlich für das jeweilige Screening-Verfahren verwendet
                  und nicht dauerhaft archiviert.
                </p>
                <p className="mt-2">
                  <span className="text-slate-300 font-medium">Rechtsgrundlage:</span>{" "}
                  Art. 6 Abs. 1 lit. b DSGVO (Vertragserfüllung).<br />
                  <span className="text-slate-300 font-medium">Speicherdauer:</span>{" "}
                  7 Tage ab Upload, danach automatische Löschung.
                </p>
              </div>

              <div>
                <h3 className="text-slate-200 font-semibold mb-2">3.4 KI-gestützte Verarbeitung (Anthropic API)</h3>
                <p>
                  Zur automatisierten Erstellung der Gap-Analysen werden anonymisierte Unternehmensprofile
                  an die API von Anthropic PBC (USA) übermittelt. Anthropic verarbeitet diese Daten
                  ausschließlich im Rahmen der vereinbarten Auftragsverarbeitung und nicht für eigene
                  Zwecke. Die Übermittlung in die USA erfolgt auf Grundlage von
                  EU-Standardvertragsklauseln gemäß Art. 46 Abs. 2 lit. c DSGVO.
                </p>
                <p className="mt-2">
                  <span className="text-slate-300 font-medium">Rechtsgrundlage:</span>{" "}
                  Art. 6 Abs. 1 lit. b DSGVO (Vertragserfüllung).
                </p>
              </div>

              <div>
                <h3 className="text-slate-200 font-semibold mb-2">3.5 Zahlungsabwicklung</h3>
                <p>
                  Zahlungen werden vollständig über Stripe Inc. (USA) abgewickelt. Complio speichert
                  keine Zahlungskarteninformationen. Stripe verarbeitet Zahlungsdaten als eigenständig
                  datenschutzrechtlich Verantwortlicher gemäß den Stripe-Datenschutzrichtlinien. Die
                  Datenübermittlung in die USA erfolgt auf Grundlage von EU-Standardvertragsklauseln.
                </p>
                <p className="mt-2">
                  <span className="text-slate-300 font-medium">Rechtsgrundlage:</span>{" "}
                  Art. 6 Abs. 1 lit. b und lit. c DSGVO (Vertragserfüllung und rechtliche Verpflichtung).<br />
                  <span className="text-slate-300 font-medium">Speicherdauer:</span>{" "}
                  Rechnungsdaten werden gemäß § 147 AO zehn Jahre aufbewahrt.
                </p>
              </div>

              <div>
                <h3 className="text-slate-200 font-semibold mb-2">3.6 Server-Logs und Fehlertracking</h3>
                <p>
                  Zur Sicherstellung eines stabilen Betriebs und zur Fehlerbehebung werden
                  serverseitig technische Log-Daten erfasst (IP-Adresse, Zeitstempel der Anfrage,
                  aufgerufene URL, HTTP-Statuscode, übertragene Datenmenge). Darüber hinaus setzen
                  wir Sentry (Functional Software Inc., USA) für das Fehler-Monitoring ein.
                  Sentry-Berichte enthalten ggf. anonymisierte Stack-Traces, jedoch keine
                  personenbezogenen Nutzerinhalte.
                </p>
                <p className="mt-2">
                  <span className="text-slate-300 font-medium">Rechtsgrundlage:</span>{" "}
                  Art. 6 Abs. 1 lit. f DSGVO (berechtigtes Interesse an Betriebsstabilität und Sicherheit).<br />
                  <span className="text-slate-300 font-medium">Speicherdauer:</span>{" "}
                  Server-Logs: 30 Tage. Sentry-Ereignisse: 90 Tage.
                </p>
              </div>

              <div>
                <h3 className="text-slate-200 font-semibold mb-2">3.7 Transaktionale E-Mails</h3>
                <p>
                  Für den Versand systemgenerierter E-Mails (z. B. Berichtsbenachrichtigungen,
                  Kontobestätigungen) setzen wir Resend Inc. (USA) ein. Dabei wird Ihre
                  E-Mail-Adresse an Resend übermittelt. Die Übermittlung erfolgt auf Grundlage von
                  EU-Standardvertragsklauseln.
                </p>
                <p className="mt-2">
                  <span className="text-slate-300 font-medium">Rechtsgrundlage:</span>{" "}
                  Art. 6 Abs. 1 lit. b DSGVO (Vertragserfüllung).
                </p>
              </div>
            </div>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-4">§ 4 Auftragsverarbeiter und Drittlandsübermittlungen</h2>
            <p className="mb-4">
              Complio setzt folgende Auftragsverarbeiter ein. Für jeden Auftragsverarbeiter
              werden Vereinbarungen zur Auftragsverarbeitung gemäß Art. 28 DSGVO abgeschlossen
              bzw. sind bereits vorhanden:
            </p>
            <div className="overflow-x-auto rounded-lg border border-white/[0.07]">
              <table className="w-full text-xs border-collapse">
                <thead>
                  <tr className="border-b border-white/[0.07] bg-white/[0.02]">
                    <th className="text-left text-slate-300 font-semibold py-3 px-4">Anbieter</th>
                    <th className="text-left text-slate-300 font-semibold py-3 px-4">Zweck</th>
                    <th className="text-left text-slate-300 font-semibold py-3 px-4">Sitz / Transfermechanismus</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.05]">
                  <tr className="hover:bg-white/[0.02] transition-colors">
                    <td className="py-3 px-4 text-slate-300 font-medium">Supabase Inc.</td>
                    <td className="py-3 px-4">Datenbank, Authentifizierung</td>
                    <td className="py-3 px-4">USA / SCC (Art. 46 Abs. 2 lit. c DSGVO)</td>
                  </tr>
                  <tr className="hover:bg-white/[0.02] transition-colors">
                    <td className="py-3 px-4 text-slate-300 font-medium">Anthropic PBC</td>
                    <td className="py-3 px-4">KI-Inferenz für Gap-Analysen</td>
                    <td className="py-3 px-4">USA / SCC</td>
                  </tr>
                  <tr className="hover:bg-white/[0.02] transition-colors">
                    <td className="py-3 px-4 text-slate-300 font-medium">Stripe Inc.</td>
                    <td className="py-3 px-4">Zahlungsabwicklung</td>
                    <td className="py-3 px-4">USA / SCC</td>
                  </tr>
                  <tr className="hover:bg-white/[0.02] transition-colors">
                    <td className="py-3 px-4 text-slate-300 font-medium">Resend Inc.</td>
                    <td className="py-3 px-4">Transaktionale E-Mails</td>
                    <td className="py-3 px-4">USA / SCC</td>
                  </tr>
                  <tr className="hover:bg-white/[0.02] transition-colors">
                    <td className="py-3 px-4 text-slate-300 font-medium">Functional Software Inc. (Sentry)</td>
                    <td className="py-3 px-4">Fehler-Monitoring</td>
                    <td className="py-3 px-4">USA / SCC</td>
                  </tr>
                  <tr className="hover:bg-white/[0.02] transition-colors">
                    <td className="py-3 px-4 text-slate-300 font-medium">Vercel Inc.</td>
                    <td className="py-3 px-4">Frontend-Hosting und CDN</td>
                    <td className="py-3 px-4">USA / SCC</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-4">§ 5 Speicherfristen</h2>
            <div className="overflow-x-auto rounded-lg border border-white/[0.07]">
              <table className="w-full text-xs border-collapse">
                <thead>
                  <tr className="border-b border-white/[0.07] bg-white/[0.02]">
                    <th className="text-left text-slate-300 font-semibold py-3 px-4">Datenkategorie</th>
                    <th className="text-left text-slate-300 font-semibold py-3 px-4">Speicherdauer</th>
                    <th className="text-left text-slate-300 font-semibold py-3 px-4">Rechtsgrundlage</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/[0.05]">
                  <tr><td className="py-3 px-4 text-slate-300">Hochgeladene Dokumente</td><td className="py-3 px-4">7 Tage (automatische Löschung)</td><td className="py-3 px-4">Auftragserfüllung</td></tr>
                  <tr><td className="py-3 px-4 text-slate-300">Compliance-Berichte</td><td className="py-3 px-4">Bis zur Kontolöschung</td><td className="py-3 px-4">Auftragserfüllung</td></tr>
                  <tr><td className="py-3 px-4 text-slate-300">Unternehmensprofile</td><td className="py-3 px-4">Bis zur Löschung durch den Nutzer</td><td className="py-3 px-4">Auftragserfüllung</td></tr>
                  <tr><td className="py-3 px-4 text-slate-300">Nutzerkonto (E-Mail)</td><td className="py-3 px-4">Bis zur Kündigung + 30 Tage</td><td className="py-3 px-4">Auftragserfüllung</td></tr>
                  <tr><td className="py-3 px-4 text-slate-300">Rechnungsdaten</td><td className="py-3 px-4">10 Jahre (§ 147 AO)</td><td className="py-3 px-4">Gesetzliche Pflicht</td></tr>
                  <tr><td className="py-3 px-4 text-slate-300">Server-Logs</td><td className="py-3 px-4">30 Tage</td><td className="py-3 px-4">Berechtigtes Interesse</td></tr>
                </tbody>
              </table>
            </div>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-4">§ 6 Ihre Rechte als betroffene Person</h2>
            <p className="mb-4">
              Ihnen stehen gegenüber Complio als Verantwortlichem folgende Rechte zu, soweit die
              gesetzlichen Voraussetzungen jeweils erfüllt sind:
            </p>
            <ul className="space-y-3">
              <li className="flex gap-3">
                <span className="text-slate-300 font-semibold min-w-fit">Art. 15 DSGVO</span>
                <span>Recht auf Auskunft über die von uns zu Ihrer Person gespeicherten Daten sowie deren Herkunft, Empfänger und Verarbeitungszweck.</span>
              </li>
              <li className="flex gap-3">
                <span className="text-slate-300 font-semibold min-w-fit">Art. 16 DSGVO</span>
                <span>Recht auf Berichtigung unrichtiger oder Vervollständigung unvollständiger personenbezogener Daten.</span>
              </li>
              <li className="flex gap-3">
                <span className="text-slate-300 font-semibold min-w-fit">Art. 17 DSGVO</span>
                <span>Recht auf Löschung Ihrer Daten. Sie können Ihr Konto und alle zugehörigen Daten jederzeit eigenständig über die Kontoeinstellungen löschen.</span>
              </li>
              <li className="flex gap-3">
                <span className="text-slate-300 font-semibold min-w-fit">Art. 18 DSGVO</span>
                <span>Recht auf Einschränkung der Verarbeitung, sofern die Voraussetzungen des Art. 18 Abs. 1 DSGVO vorliegen.</span>
              </li>
              <li className="flex gap-3">
                <span className="text-slate-300 font-semibold min-w-fit">Art. 20 DSGVO</span>
                <span>Recht auf Datenübertragbarkeit in einem strukturierten, gängigen, maschinenlesbaren Format.</span>
              </li>
              <li className="flex gap-3">
                <span className="text-slate-300 font-semibold min-w-fit">Art. 21 DSGVO</span>
                <span>Widerspruchsrecht gegen die Verarbeitung auf Grundlage berechtigter Interessen (Art. 6 Abs. 1 lit. f DSGVO).</span>
              </li>
              <li className="flex gap-3">
                <span className="text-slate-300 font-semibold min-w-fit">Art. 77 DSGVO</span>
                <span>Beschwerderecht bei der zuständigen Datenschutz-Aufsichtsbehörde. Für Hessen ist dies der Hessische Beauftragte für Datenschutz und Informationsfreiheit (HBDI).</span>
              </li>
            </ul>
            <p className="mt-4">
              Zur Geltendmachung Ihrer Rechte wenden Sie sich bitte per E-Mail an:{" "}
              <a href="mailto:hellocomplio@gmail.com" className="text-brand-400 hover:text-brand-300 transition-colors">
                hellocomplio@gmail.com
              </a>
              . Wir bearbeiten Anfragen innerhalb von 30 Tagen.
            </p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-4">§ 7 Keine automatisierte Einzelentscheidung</h2>
            <p>
              Die von Complio erstellten Compliance-Berichte sind vorläufige, informatorische Einschätzungen
              und dienen ausschließlich als Entscheidungsunterstützung. Es findet keine automatisierte
              Einzelentscheidung im Sinne von Art. 22 DSGVO statt, die rechtliche oder ähnlich
              erhebliche Auswirkungen auf natürliche Personen hätte. Alle Berichte sind ausschließlich
              an Unternehmer im Sinne des § 14 BGB gerichtet.
            </p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-4">§ 8 Cookies und technische Speicherung</h2>
            <p>
              Complio verwendet ausschließlich technisch notwendige Cookies und vergleichbare
              Technologien, die für die Authentifizierung und den sicheren Betrieb der Plattform
              erforderlich sind (Session-Cookie via Supabase Auth). Es werden keine Analyse-,
              Marketing- oder Tracking-Cookies eingesetzt. Für technisch notwendige Cookies ist
              keine Einwilligung nach § 25 Abs. 2 Nr. 2 TTDSG erforderlich.
            </p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-4">§ 9 Aktualität und Änderungen</h2>
            <p>
              Complio behält sich vor, diese Datenschutzerklärung bei wesentlichen Änderungen des
              Dienstangebots oder der gesetzlichen Anforderungen anzupassen. Registrierte Nutzer
              werden über erhebliche Änderungen per E-Mail informiert. Die jeweils aktuelle Fassung
              ist unter{" "}
              <a href="/datenschutz" className="text-brand-400 hover:text-brand-300 transition-colors">
                complio.de/datenschutz
              </a>{" "}
              abrufbar.
            </p>
          </section>

        </div>
      </div>
    </main>
  );
}
