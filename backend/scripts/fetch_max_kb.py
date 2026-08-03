"""
Maximum knowledge base fetch — pulls authoritative source documents for all 14 regulations.

Priority targets:
  LkSG     — BAFA FAQ + Handreichung Risikoanalyse (real BAFA PDFs, not AI summaries)
  NIS2     — BSIG (German BSI-Gesetz) + KRITIS-DachG from gesetze-im-internet.de
  CSRD     — ESRS E1, S1, G1 topical standards from EUR-Lex
  GDPR     — EDPB guidelines on legitimate interests, cookies, data retention
  GwG      — BaFin AML interpretation guidance
  EU Data Act — EC implementation Q&A
  EnEfG    — EnEG predecessor act + BAFA energy audit obligations
  HinSchG  — HinSchG-Meldestellenverordnung (implementing ordinance)
  MiLoG    — MiLoSiG (enforcement act) from gesetze-im-internet.de
  TTDSG    — TKG 2021 (telecommunications context) from gesetze-im-internet.de
  AGG      — SGB IX (disability), EntgTranspG (pay transparency)

Run from backend/:  python scripts/fetch_max_kb.py [--regulation <name>] [--dry-run]
"""
import argparse
import gzip
import html as html_module
import io
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

BASE_DIR = Path(__file__).parent.parent / "data" / "regulations"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
    "Accept-Encoding": "identity",
}

PDF_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Accept": "application/pdf,*/*;q=0.8",
    "Accept-Language": "de-DE,de;q=0.9",
    "Accept-Encoding": "identity",
    "Referer": "https://www.bafa.de/",
}


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def fetch_bytes(url: str, timeout: int = 45, extra_headers: dict = None) -> bytes | None:
    # Percent-encode non-ASCII path characters — urllib raises UnicodeEncodeError
    # on raw umlauts in URLs (e.g. a slug containing 'ä')
    scheme, rest = url.split("://", 1)
    host, _, path = rest.partition("/")
    url = f"{scheme}://{host}/{urllib.parse.quote(path, safe='/?=&%')}"
    h = {**HEADERS, **(extra_headers or {})}
    req = urllib.request.Request(url, headers=h)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
    except Exception as e:
        print(f"    ERROR fetching {url}: {e}")
        return None
    # Some CDNs (observed on EUR-Lex/CloudFront) send gzip bytes even when
    # Accept-Encoding: identity was requested. Detect by magic number rather
    # than trusting Content-Encoding, since urllib won't auto-decompress here.
    if raw[:2] == b"\x1f\x8b":
        try:
            raw = gzip.decompress(raw)
        except OSError as e:
            print(f"    ERROR gunzipping {url}: {e}")
            return None
    return raw


def fetch_html(url: str, timeout: int = 45) -> str | None:
    raw = fetch_bytes(url, timeout=timeout)
    if raw is None:
        return None
    try:
        text = raw.decode("utf-8", errors="replace")
    except Exception:
        text = raw.decode("latin-1", errors="replace")
    # A high ratio of U+FFFD means we're decoding bytes that were never valid
    # text in the first place (e.g. an undetected compressed/binary payload) —
    # bail instead of silently saving unusable garbage.
    if len(text) > 0 and text.count("�") / len(text) > 0.01:
        print(f"    ERROR: {text.count(chr(0xFFFD))} replacement chars in {len(text)} — payload isn't valid text")
        return None
    return text


def strip_html(html_text: str) -> str:
    html_text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html_text, flags=re.DOTALL | re.IGNORECASE)
    html_text = re.sub(r"<!--.*?-->", "", html_text, flags=re.DOTALL)
    html_text = re.sub(r"<(br|p|div|tr|li|h[1-6])[^>]*>", "\n", html_text, flags=re.IGNORECASE)
    html_text = re.sub(r"</(p|div|tr|li|h[1-6])>", "\n", html_text, flags=re.IGNORECASE)
    html_text = re.sub(r"<[^>]+>", "", html_text)
    html_text = html_module.unescape(html_text)
    html_text = re.sub(r"\n{3,}", "\n\n", html_text)
    return html_text.strip()


def extract_pdf_text(pdf_bytes: bytes) -> str | None:
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            pages = []
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    pages.append(t)
        text = "\n\n".join(pages)
        if len(text) > 500:
            return text
    except Exception as e:
        print(f"    pdfplumber failed: {e}, trying pypdf...")
    try:
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(pdf_bytes))
        pages = [p.extract_text() or "" for p in reader.pages]
        text = "\n\n".join(p for p in pages if p.strip())
        if len(text) > 500:
            return text
    except Exception as e:
        print(f"    pypdf failed: {e}")
    return None


def save_text(dest_dir: Path, filename: str, header: str, text: str) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = dest_dir / filename
    path.write_text(header + "\n\n" + text, encoding="utf-8")
    size_kb = len(text) // 1024
    print(f"    Saved: {filename} ({size_kb}KB, {len(text.splitlines())} lines)")
    return path


def fetch_gesetze_im_internet(prefix: str, dest_dir: Path, filename: str, label: str) -> bool:
    index_url = f"https://www.gesetze-im-internet.de/{prefix}/"
    print(f"    Index: {index_url}")
    page = fetch_html(index_url)
    if not page:
        return False

    matches = re.findall(r'href="(BJNR[^"]+\.html)"', page)
    if not matches:
        matches = re.findall(r'href="([^"]+BJNR[^"]+\.html)"', page)
    if not matches:
        print(f"    ERROR: no full-text link for {prefix}")
        return False

    full_url = f"https://www.gesetze-im-internet.de/{prefix}/{matches[0]}"
    print(f"    Full text: {full_url}")
    raw = fetch_html(full_url, timeout=60)
    if not raw:
        return False

    text = strip_html(raw)
    text = re.sub(r'(?m)(^§\s*\d+[a-z]?)\xa0', r'\1\n', text)
    if len(text) < 1000:
        print(f"    WARNING: only {len(text)} chars — may be empty")
        return False

    save_text(dest_dir, filename, f"{label}\nSource: {full_url}", text)
    return True


def fetch_pdf(url: str, dest_dir: Path, filename: str, label: str, extra_headers: dict = None) -> bool:
    print(f"    PDF: {url}")
    pdf_bytes = fetch_bytes(url, timeout=60, extra_headers=extra_headers or PDF_HEADERS)
    if not pdf_bytes:
        return False
    if len(pdf_bytes) < 5000:
        print(f"    ERROR: PDF too small ({len(pdf_bytes)} bytes) — likely blocked")
        return False

    text = extract_pdf_text(pdf_bytes)
    if not text:
        print("    ERROR: could not extract text from PDF")
        return False

    save_text(dest_dir, filename, f"{label}\nSource: {url}", text)
    return True


def fetch_eurlex_html(celex: str, dest_dir: Path, filename: str, label: str, lang: str = "DE") -> bool:
    url = f"https://eur-lex.europa.eu/legal-content/{lang}/TXT/HTML/?uri=CELEX:{celex}"
    print(f"    EUR-Lex: {url}")
    raw = fetch_html(url, timeout=60)
    if not raw:
        return False
    if "Request blocked" in raw or "Access Denied" in raw or len(raw) < 5000:
        print("    EUR-Lex WAF blocked — skipping")
        return False

    text = strip_html(raw)
    article_count = len(re.findall(r"(?m)^(Artikel|Article)\s+\d+", text))
    if len(text) < 2000:
        print(f"    WARNING: only {len(text)} chars — may be empty")
        return False
    if article_count == 0:
        print("    ERROR: 0 articles found — page structure didn't match expected pattern, refusing to save")
        return False

    save_text(dest_dir, filename, f"{label}\nSource: {url}", text)
    print(f"    Found {article_count} articles")
    return True


# ---------------------------------------------------------------------------
# Source definitions
# ---------------------------------------------------------------------------

TASKS = [

    # ── LkSG ─────────────────────────────────────────────────────────────────
    {
        "regulation": "lksg",
        "name": "LkSG full text (gesetze-im-internet.de)",
        "type": "gesetze",
        "prefix": "lksg",
        "filename": "lksg_full_text.txt",
        "label": "Lieferkettensorgfaltspflichtengesetz (LkSG)\nSource: gesetze-im-internet.de",
    },
    {
        "regulation": "lksg",
        "name": "BAFA FAQ LkSG (official Q&A document)",
        "type": "pdf",
        "url": "https://www.bafa.de/SharedDocs/Downloads/DE/Lieferketten/lksg_faq.pdf?__blob=publicationFile&v=14",
        "filename": "bafa_lksg_faq.pdf.txt",
        "label": "BAFA — Häufig gestellte Fragen zum Lieferkettensorgfaltspflichtengesetz (LkSG)",
        "extra_headers": {"Referer": "https://www.bafa.de/DE/Themen/Lieferketten/lksg.html"},
    },
    {
        "regulation": "lksg",
        "name": "BAFA Handreichung Risikoanalyse LkSG",
        "type": "pdf",
        "url": "https://www.bafa.de/SharedDocs/Downloads/DE/Lieferketten/lksg_handreichung_risikoanalyse.pdf?__blob=publicationFile&v=6",
        "filename": "bafa_lksg_risikoanalyse.pdf.txt",
        "label": "BAFA — Handreichung zur Risikoanalyse nach dem LkSG",
        "extra_headers": {"Referer": "https://www.bafa.de/DE/Themen/Lieferketten/lksg.html"},
    },
    {
        "regulation": "lksg",
        "name": "LkSG-Sorgfaltspflichtenverordnung",
        "type": "gesetze",
        "prefix": "lksgv",
        "filename": "lksgv_text.txt",
        "label": "LkSG-Sorgfaltspflichtenverordnung — Verordnung zu den Sorgfaltspflichten nach dem LkSG",
    },

    # ── NIS2 / BSIG ──────────────────────────────────────────────────────────
    {
        "regulation": "nis2",
        "name": "BSIG (BSI-Gesetz — German cybersecurity act)",
        "type": "gesetze",
        "prefix": "bsig_2009",
        "filename": "bsig_text.txt",
        "label": "BSI-Gesetz (BSIG) — Gesetz über das Bundesamt für Sicherheit in der Informationstechnik",
    },
    {
        "regulation": "nis2",
        "name": "IT-Sicherheitsgesetz 2.0 / KRITIS-DachG",
        "type": "gesetze",
        "prefix": "bsig_2009",
        "filename": "bsig_2009_text.txt",
        "label": "BSI-Gesetz 2009 mit Änderungen durch IT-Sicherheitsgesetz 2.0",
    },

    # ── CSRD / ESRS ──────────────────────────────────────────────────────────
    # NOTE: CELEX:32023R2772's HTML rendering puts ALL topical standards
    # (ESRS 1, ESRS 2, E1-E5, S1-S4, G1) inside a single "ANNEX I", with
    # "ANNEX II" holding the glossary — there is no separate Annex III/XI/XV
    # per standard as earlier task labels assumed. Fetch once; per-topic
    # chunk-level splitting (if wanted) belongs in rag/ingest.py, not here.
    {
        "regulation": "csrd",
        "name": "ESRS full text — all topical standards + glossary",
        "type": "eurlex",
        "celex": "32023R2772",
        "filename": "esrs_annexes_full_text.txt",
        "label": "ESRS — European Sustainability Reporting Standards, full text incl. all topical standards (ESRS 1, ESRS 2, E1-E5, S1-S4, G1) and glossary (Commission Delegated Regulation EU 2023/2772, Annex I + Annex II)",
        "lang": "EN",
    },
    {
        "regulation": "csrd",
        "name": "CSRD Directive full text (EUR-Lex DE)",
        "type": "eurlex",
        "celex": "32022L2464",
        "filename": "csrd_directive_de.txt",
        "label": "CSRD — Richtlinie 2022/2464/EU (Corporate Sustainability Reporting Directive)",
        "lang": "DE",
    },

    # ── GDPR ─────────────────────────────────────────────────────────────────
    {
        "regulation": "gdpr",
        "name": "DSGVO full text in German (EUR-Lex)",
        "type": "eurlex",
        "celex": "32016R0679",
        "filename": "dsgvo_full_de.txt",
        "label": "DSGVO — Verordnung (EU) 2016/679 (Datenschutz-Grundverordnung) — Volltext auf Deutsch",
        "lang": "DE",
    },
    {
        "regulation": "gdpr",
        "name": "EDPB Guidelines on Legitimate Interests (Art. 6(1)(f))",
        "type": "pdf",
        "url": "https://www.edpb.europa.eu/system/files/2024-10/edpb_guidelines_202401_legitimateinterest_en.pdf",
        "filename": "edpb_legitimate_interests_guidelines.pdf.txt",
        "label": "EDPB Guidelines 1/2024 on Article 6(1)(f) GDPR — Legitimate Interests",
        "extra_headers": {"Referer": "https://www.edpb.europa.eu/"},
    },
    {
        "regulation": "gdpr",
        "name": "EDPB Guidelines on Data Breach Notification",
        "type": "pdf",
        "url": "https://www.edpb.europa.eu/system/files/2019-11/wp250rev01_enpdf.pdf",
        "filename": "edpb_data_breach_guidelines.pdf.txt",
        "label": "EDPB Guidelines on personal data breach notification under GDPR",
        "extra_headers": {"Referer": "https://www.edpb.europa.eu/"},
    },
    {
        "regulation": "gdpr",
        "name": "EDPB Guidelines on Data Protection by Design and by Default",
        "type": "pdf",
        "url": "https://www.edpb.europa.eu/system/files/2020-10/edpb_guidelines_202004_dataprotection_by_design_and_by_default_v2.0_en.pdf",
        "filename": "edpb_dpbd_guidelines.pdf.txt",
        "label": "EDPB Guidelines 4/2019 on Data Protection by Design and by Default",
        "extra_headers": {"Referer": "https://www.edpb.europa.eu/"},
    },

    # ── GwG ──────────────────────────────────────────────────────────────────
    {
        "regulation": "gwg",
        "name": "GwG full text (gesetze-im-internet.de)",
        "type": "gesetze",
        "prefix": "gwg_2017",
        "filename": "gwg_full_text.txt",
        "label": "Geldwäschegesetz (GwG) — Volltext",
    },
    {
        "regulation": "gwg",
        "name": "GwGMeldV (Meldepflichten-Verordnung)",
        "type": "gesetze",
        "prefix": "gwgmeldv",
        "filename": "gwgmeldv_text.txt",
        "label": "GwGMeldV — Verordnung zu den Meldepflichten nach dem Geldwäschegesetz",
    },

    # ── EU Data Act ───────────────────────────────────────────────────────────
    {
        "regulation": "eu_data_act",
        "name": "EU Data Act (EUR-Lex DE)",
        "type": "eurlex",
        "celex": "32023R2854",
        "filename": "eu_data_act_de.txt",
        "label": "EU Data Act — Verordnung (EU) 2023/2854 über harmonisierte Vorschriften für den fairen Zugang zu Daten",
        "lang": "DE",
    },

    # ── HinSchG ──────────────────────────────────────────────────────────────
    {
        "regulation": "hinschg",
        "name": "HinSchG full text (gesetze-im-internet.de)",
        "type": "gesetze",
        "prefix": "hinschg",
        "filename": "hinschg_full_text.txt",
        "label": "Hinweisgeberschutzgesetz (HinSchG) — Volltext",
    },

    # ── MiLoG ────────────────────────────────────────────────────────────────
    {
        "regulation": "milog",
        "name": "MiLoG full text (gesetze-im-internet.de)",
        "type": "gesetze",
        "prefix": "milog",
        "filename": "milog_full_text.txt",
        "label": "Mindestlohngesetz (MiLoG) — Volltext",
    },
    {
        "regulation": "milog",
        "name": "MiLoSiG (Mindestlohnsicherungsgesetz — enforcement)",
        "type": "gesetze",
        "prefix": "milosig",
        "filename": "milosig_text.txt",
        "label": "MiLoSiG — Gesetz zur Sicherung von Arbeitnehmerrechten in der Fleischwirtschaft",
    },

    # ── TTDSG ────────────────────────────────────────────────────────────────
    {
        "regulation": "ttdsg",
        "name": "TDDDG full text (gesetze-im-internet.de)",
        "type": "gesetze",
        "prefix": "tdddg",
        "filename": "tdddg_full_text.txt",
        "label": "TDDDG — Telekommunikation-Digitale-Dienste-Datenschutz-Gesetz (TTDSG Nachfolger)",
    },
    {
        "regulation": "ttdsg",
        "name": "TKG 2021 (Telekommunikationsgesetz)",
        "type": "gesetze",
        "prefix": "tkg_2021",
        "filename": "tkg_2021_text.txt",
        "label": "TKG 2021 — Telekommunikationsgesetz (2021)",
    },

    # ── AGG ──────────────────────────────────────────────────────────────────
    {
        "regulation": "agg",
        "name": "SGB IX (disability inclusion obligations)",
        "type": "gesetze",
        "prefix": "sgb_9",
        "filename": "sgb_ix_text.txt",
        "label": "SGB IX — Sozialgesetzbuch Neuntes Buch — Rehabilitation und Teilhabe",
    },
    {
        "regulation": "agg",
        "name": "EntgTranspG (pay transparency act)",
        "type": "gesetze",
        "prefix": "entgtranspg",
        "filename": "entgtranspg_text.txt",
        "label": "EntgTranspG — Entgelttransparenzgesetz — Gesetz zur Förderung der Entgelttransparenz",
    },

    # ── EnEfG ────────────────────────────────────────────────────────────────
    {
        "regulation": "enefg",
        "name": "EnEfG full text (gesetze-im-internet.de)",
        "type": "gesetze",
        "prefix": "enefg",
        "filename": "enefg_full_text.txt",
        "label": "EnEfG — Gesetz zur Steigerung der Energieeffizienz in Deutschland — Volltext",
    },
    {
        "regulation": "enefg",
        "name": "EDL-G full text (energy services law)",
        "type": "gesetze",
        "prefix": "edl-g",
        "filename": "edlg_full_text.txt",
        "label": "EDL-G — Gesetz über Energiedienstleistungen und andere Effizienzmaßnahmen",
    },

    # ── BDSG ─────────────────────────────────────────────────────────────────
    {
        "regulation": "bdsg",
        "name": "BDSG full text (gesetze-im-internet.de)",
        "type": "gesetze",
        "prefix": "bdsg_2018",
        "filename": "bdsg_full_text2.txt",
        "label": "BDSG 2018 — Bundesdatenschutzgesetz — Volltext",
    },

    # ── Workplace law ─────────────────────────────────────────────────────────
    {
        "regulation": "workplace_law",
        "name": "ArbSchG full text (gesetze-im-internet.de)",
        "type": "gesetze",
        "prefix": "arbschg",
        "filename": "arbschg_full_text.txt",
        "label": "ArbSchG — Arbeitsschutzgesetz — Volltext",
    },
    {
        "regulation": "workplace_law",
        "name": "ASiG (Arbeitssicherheitsgesetz)",
        "type": "gesetze",
        "prefix": "asig",
        "filename": "asig_text.txt",
        "label": "ASiG — Gesetz über Betriebsärzte, Sicherheitsingenieure und andere Fachkräfte für Arbeitssicherheit",
    },
    {
        "regulation": "workplace_law",
        "name": "ArbStättV (Arbeitsstättenverordnung)",
        "type": "gesetze",
        # gesetze-im-internet.de replaces umlauts with underscores in URL slugs
        "prefix": "arbst_ttv_2004",
        "filename": "arbstaettv_text.txt",
        "label": "ArbStättV — Verordnung über Arbeitsstätten",
    },
]


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_task(task: dict, dry_run: bool = False) -> tuple[str, bool]:
    name = task["name"]
    regulation = task["regulation"]
    dest_dir = BASE_DIR / ("arbschg" if regulation == "workplace_law" else regulation)

    print(f"\n  [{regulation.upper()}] {name}")

    if dry_run:
        print(f"    Would save to: {dest_dir / task['filename']}")
        return name, True

    # Skip if already exists and is large enough
    target = dest_dir / task["filename"]
    if target.exists() and target.stat().st_size > 10_000:
        print(f"    Already exists ({target.stat().st_size // 1024}KB) — skipping")
        return name, True

    task_type = task["type"]

    if task_type == "gesetze":
        ok = fetch_gesetze_im_internet(task["prefix"], dest_dir, task["filename"], task["label"])
    elif task_type == "pdf":
        ok = fetch_pdf(task["url"], dest_dir, task["filename"], task["label"],
                       extra_headers=task.get("extra_headers"))
    elif task_type == "eurlex":
        ok = fetch_eurlex_html(task["celex"], dest_dir, task["filename"], task["label"],
                               lang=task.get("lang", "EN"))
    else:
        print(f"    Unknown type: {task_type}")
        ok = False

    return name, ok


def ingest(regulation: str) -> int:
    from rag.ingest import ingest_regulation
    print(f"  Ingesting {regulation}...")
    n = ingest_regulation(regulation, reset=True)
    print(f"  {regulation}: {n} chunks")
    return n


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--regulation", help="Only fetch/ingest this regulation")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--fetch-only", action="store_true", help="Fetch but do not ingest")
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()

    tasks = TASKS
    if args.regulation:
        tasks = [t for t in TASKS if t["regulation"] == args.regulation]

    if args.list:
        regs = {}
        for t in tasks:
            regs.setdefault(t["regulation"], []).append(t["name"])
        for reg, names in sorted(regs.items()):
            print(f"\n{reg.upper()}:")
            for n in names:
                print(f"  - {n}")
        return

    print(f"\n{'='*65}")
    print(f"  Complio KB Fetch — {len(tasks)} source documents")
    print(f"{'='*65}")

    results = []
    touched_regs = set()

    for task in tasks:
        name, ok = run_task(task, dry_run=args.dry_run)
        results.append((task["regulation"], name, ok))
        if ok and not args.dry_run:
            touched_regs.add(task["regulation"])

    # Ingest all touched regulations
    if not args.dry_run and not args.fetch_only and touched_regs:
        print(f"\n{'='*65}")
        print(f"  Ingesting {len(touched_regs)} regulation(s)...")
        print(f"{'='*65}")
        for reg in sorted(touched_regs):
            try:
                ingest(reg)
            except Exception as e:
                print(f"  ERROR ingesting {reg}: {e}")

    # Summary
    print(f"\n{'='*65}")
    print("  Results:")
    by_reg = {}
    for reg, name, ok in results:
        by_reg.setdefault(reg, []).append((name, ok))
    for reg in sorted(by_reg):
        successes = sum(1 for _, ok in by_reg[reg] if ok)
        total = len(by_reg[reg])
        print(f"\n  {reg.upper()} ({successes}/{total} fetched):")
        for name, ok in by_reg[reg]:
            icon = "OK" if ok else "!!"
            print(f"    [{icon}] {name}")

    # Also run kb_health at the end
    if not args.dry_run and not args.fetch_only:
        print(f"\n{'='*65}")
        print("  Final KB health:")
        try:
            from scripts.kb_health import check_kb
            check_kb()
        except Exception:
            pass


if __name__ == "__main__":
    main()
