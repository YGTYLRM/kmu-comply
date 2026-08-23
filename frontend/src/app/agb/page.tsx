import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Allgemeine Geschäftsbedingungen — Complio",
};

export default function AGBPage() {
  return (
    <main className="min-h-screen pt-32 pb-20">
      <div className="mx-auto max-w-2xl px-6">
        <h1 className="text-3xl font-bold text-white mb-2">Allgemeine Geschäftsbedingungen</h1>
        <p className="text-xs text-slate-500 mb-10">Stand: Mai 2026</p>

        <div className="space-y-10 text-sm text-slate-400 leading-relaxed">

          <section>
            <h2 className="text-white font-semibold text-base mb-4">§ 1 Geltungsbereich</h2>
            <p>
              Diese Allgemeinen Geschäftsbedingungen (AGB) gelten für alle Verträge zwischen Complio,
              Darmstadt (&ldquo;Complio&rdquo;, &ldquo;Anbieter&rdquo;) und seinen Kunden
              (&ldquo;Nutzer&rdquo;, &ldquo;Kunde&rdquo;) über die Nutzung der Complio-Plattform
              unter complio.de sowie aller zugehörigen Dienste.
            </p>
            <p className="mt-3">
              Complio richtet sich ausschließlich an Unternehmer im Sinne des § 14 BGB: juristische
              Personen des öffentlichen oder privaten Rechts sowie natürliche Personen, die in Ausübung
              ihrer gewerblichen oder selbstständigen beruflichen Tätigkeit handeln. Die Nutzung durch
              Verbraucher im Sinne des § 13 BGB ist ausgeschlossen.
            </p>
            <p className="mt-3">
              Abweichende, entgegenstehende oder ergänzende Allgemeine Geschäftsbedingungen des Nutzers
              werden nicht Vertragsbestandteil, es sei denn, ihrer Geltung wird ausdrücklich
              schriftlich zugestimmt.
            </p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-4">§ 2 Leistungsgegenstand</h2>
            <p>
              Complio ist eine Software-as-a-Service-Plattform (SaaS) für automatisierte
              Compliance-Screenings. Der Dienst verarbeitet das vom Nutzer eingegebene
              Unternehmensprofil und erstellt auf dieser Grundlage einen vorläufigen Compliance-Bericht
              (Gap-Analyse) gegenüber ausgewählten deutschen und europäischen Rechtsvorschriften,
              einschließlich priorisierter Handlungsempfehlungen.
            </p>
            <p className="mt-3">
              Der aktuelle Regelungsumfang umfasst 14 Vorschriften, darunter DSGVO, BDSG, NIS2,
              EU AI Act, LkSG, EnEfG, CSRD, HinSchG, ArbSchG, AGG, MiLoG, TTDSG/TDDDG, GwG und
              EU Data Act. Complio behält sich vor, den Umfang der analysierten Vorschriften
              anzupassen und wird wesentliche Änderungen rechtzeitig ankündigen.
            </p>
            <p className="mt-3 text-amber-400/90 font-medium">
              Complio-Berichte sind automatisierte Ersteinschätzungen auf Basis der eingegebenen
              Unternehmensdaten. Sie stellen keine Rechtsberatung im Sinne des
              Rechtsdienstleistungsgesetzes (RDG) dar, begründen kein Mandatsverhältnis und ersetzen
              nicht die Beratung durch einen zugelassenen Rechtsanwalt. Der Nutzer ist verpflichtet,
              die Ergebnisse eigenverantwortlich zu prüfen und gegebenenfalls rechtlichen Rat einzuholen.
            </p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-4">§ 3 Vertragsschluss</h2>
            <p>
              Der Nutzungsvertrag kommt nicht durch einen automatisierten Online-Bestellprozess
              zustande. Interessenten fordern über complio.de ein individuelles Angebot an; der
              Vertrag kommt erst durch beiderseitige Bestätigung des im Angebot festgelegten
              Leistungsumfangs und Preises zustande (in Textform, z. B. per E-Mail).
            </p>
            <p className="mt-3">
              Die konkrete Vertragslaufzeit (Einzelauftrag oder Abonnement mit automatischer
              Verlängerung) wird im jeweiligen Angebot festgelegt.
            </p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-4">§ 4 Tarife, Preise und Zahlung</h2>
            <p>
              Complio bietet die Tarife Starter, Professional und Enterprise an. Der Leistungsumfang
              je Tarif ist auf complio.de/#pricing beschrieben. Aktuell werden keine pauschalen
              Listenpreise angeboten — der Preis wird individuell im Angebot auf Anfrage genannt und
              gilt erst nach beiderseitiger Bestätigung gemäß § 3.
            </p>
            <p className="mt-4">
              Alle Preise verstehen sich zuzüglich der gesetzlichen Umsatzsteuer, sofern im Angebot
              nicht anders angegeben. Die Zahlungsmodalitäten werden im jeweiligen Angebot festgelegt.
              Bei Zahlungsverzug ist Complio berechtigt, den Zugang zum Dienst nach vorheriger
              Ankündigung zu sperren. Complio behält sich das Recht vor, Preise für neue Angebote
              jederzeit anzupassen; bestehende Verträge sind davon bis zum Ende der vereinbarten
              Laufzeit nicht betroffen.
            </p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-4">§ 5 Pflichten und Obliegenheiten des Nutzers</h2>
            <p>Der Nutzer ist verpflichtet:</p>
            <ul className="mt-3 space-y-2 list-disc list-inside">
              <li>vollständige und zutreffende Angaben im Unternehmensprofil zu machen, da die Qualität der Berichte unmittelbar von der Datenqualität abhängt;</li>
              <li>Zugangsdaten vertraulich zu behandeln und Dritten nicht zugänglich zu machen;</li>
              <li>Complio unverzüglich zu informieren, sofern ein Missbrauch des Zugangs festgestellt wird;</li>
              <li>die Plattform ausschließlich für eigene Compliance-Zwecke und nicht für Zwecke Dritter zu nutzen, sofern der gebuchte Tarif keine Mehrfachnutzung vorsieht;</li>
              <li>die Ergebnisse nicht als Rechtsberatung gegenüber Dritten darzustellen oder zu verwenden.</li>
            </ul>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-4">§ 6 Nutzungsrechte</h2>
            <p>
              Complio räumt dem Nutzer für die Dauer des Vertragsverhältnisses ein einfaches,
              nicht übertragbares und nicht unterlizenzierbares Recht zur Nutzung der Plattform
              und der erstellten Berichte für interne Compliance-Zwecke ein. Die Berichte dürfen
              intern weitergegeben werden; eine Weitergabe an Dritte gegen Entgelt oder als
              vermeintliche Rechtsberatung ist untersagt.
            </p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-4">§ 7 Verfügbarkeit und Wartung</h2>
            <p>
              Complio strebt eine Verfügbarkeit des Dienstes von 99 % im Jahresdurchschnitt an,
              ausgenommen geplante Wartungsfenster, höhere Gewalt und Umstände außerhalb des
              Einflussbereichs von Complio (z. B. Ausfälle von Drittanbietern). Ein Anspruch auf
              ununterbrochene Verfügbarkeit besteht nicht, sofern kein gesondertes SLA vereinbart
              ist.
            </p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-4">§ 8 Datenschutz und Vertraulichkeit</h2>
            <p>
              Die Verarbeitung personenbezogener Daten erfolgt gemäß der{" "}
              <a href="/datenschutz" className="text-brand-400 hover:text-brand-300 transition-colors">
                Datenschutzerklärung von Complio
              </a>
              , die Bestandteil dieser AGB ist. Der Nutzer versichert, dass er berechtigt ist, die
              im Rahmen des Dienstes übermittelten Unternehmensdaten und Dokumente einzureichen,
              und stellt Complio von Ansprüchen Dritter frei, die aus einer unberechtigten
              Dateneinreichung entstehen.
            </p>
            <p className="mt-3">
              Complio verpflichtet sich, alle vom Nutzer bereitgestellten Informationen vertraulich
              zu behandeln und nicht an unbefugte Dritte weiterzugeben.
            </p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-4">§ 9 Gewährleistung und Haftung</h2>
            <p>
              Complio haftet unbeschränkt für Schäden, die auf Vorsatz oder grober Fahrlässigkeit
              von Complio oder seinen Erfüllungsgehilfen beruhen, sowie für Schäden aus der
              Verletzung des Lebens, des Körpers oder der Gesundheit.
            </p>
            <p className="mt-3">
              Bei einfacher Fahrlässigkeit haftet Complio nur bei Verletzung einer wesentlichen
              Vertragspflicht (Kardinalpflicht), deren Erfüllung die ordnungsgemäße Durchführung
              des Vertrags überhaupt erst ermöglicht und auf deren Einhaltung der Nutzer regelmäßig
              vertrauen darf. In diesem Fall ist die Haftung auf den typischerweise vorhersehbaren
              Schaden begrenzt, höchstens jedoch auf die Summe der in den letzten zwölf Monaten
              tatsächlich entrichteten Entgelte.
            </p>
            <p className="mt-3">
              Complio übernimmt keine Haftung dafür, dass die erstellten Berichte für die
              konkrete rechtliche Situation des Nutzers vollständig oder abschließend zutreffend
              sind. Behördliche Bußgelder, Sanktionen oder sonstige hoheitliche Maßnahmen, die
              trotz oder aufgrund einer Complio-Nutzung verhängt werden, begründen keinen
              Erstattungsanspruch gegenüber Complio.
            </p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-4">§ 10 Laufzeit und Kündigung</h2>
            <p>
              Abonnements (Professional, Enterprise) laufen auf unbestimmte Zeit und können von
              beiden Parteien mit einer Frist von 30 Tagen zum Ende des jeweiligen
              Abrechnungsmonats ordentlich gekündigt werden. Die Kündigung ist per E-Mail an{" "}
              <a href="mailto:hellocomplio@gmail.com" className="text-brand-400 hover:text-brand-300 transition-colors">
                hellocomplio@gmail.com
              </a>{" "}
              oder über die Kontoeinstellungen möglich.
            </p>
            <p className="mt-3">
              Das Recht zur außerordentlichen Kündigung aus wichtigem Grund bleibt unberührt.
              Ein wichtiger Grund liegt für Complio insbesondere vor, wenn der Nutzer gegen
              wesentliche Nutzungspflichten aus § 5 dieser AGB verstößt.
            </p>
            <p className="mt-3">
              Nach Vertragsende werden Nutzerdaten innerhalb von 30 Tagen gelöscht, sofern
              keine gesetzlichen Aufbewahrungspflichten entgegenstehen (§ 147 AO für
              Rechnungsdaten: 10 Jahre). Der Nutzer kann Daten und Berichte vor Vertragsende
              eigenständig exportieren oder löschen.
            </p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-4">§ 11 Änderungen der AGB</h2>
            <p>
              Complio ist berechtigt, diese AGB mit einer Ankündigungsfrist von mindestens 30 Tagen
              vor Inkrafttreten zu ändern. Die Ankündigung erfolgt per E-Mail an die im Nutzerkonto
              hinterlegte Adresse. Widerspricht der Nutzer nicht innerhalb von 30 Tagen nach
              Zugang der Änderungsmitteilung, gelten die geänderten AGB als angenommen. Auf die
              Bedeutung des Schweigens wird in der Ankündigungs-E-Mail gesondert hingewiesen.
            </p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-4">§ 12 Anwendbares Recht und Gerichtsstand</h2>
            <p>
              Es gilt ausschließlich das Recht der Bundesrepublik Deutschland unter Ausschluss des
              Einheitlichen UN-Kaufrechts (CISG). Gerichtsstand für alle Streitigkeiten aus oder
              im Zusammenhang mit diesem Vertrag ist Darmstadt, sofern der Nutzer Kaufmann,
              juristische Person des öffentlichen Rechts oder öffentlich-rechtliches
              Sondervermögen ist.
            </p>
          </section>

          <section>
            <h2 className="text-white font-semibold text-base mb-4">§ 13 Salvatorische Klausel</h2>
            <p>
              Sollten einzelne Bestimmungen dieser AGB ganz oder teilweise unwirksam oder
              undurchführbar sein oder werden, berührt dies die Wirksamkeit der übrigen
              Bestimmungen nicht. Anstelle der unwirksamen oder undurchführbaren Bestimmung gilt
              diejenige wirksame und durchführbare Regelung als vereinbart, die dem wirtschaftlichen
              Zweck der unwirksamen Bestimmung am nächsten kommt.
            </p>
          </section>

        </div>
      </div>
    </main>
  );
}
