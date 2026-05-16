"""
Fetch supplementary regulation documents that expand the knowledge base beyond the
core directive/law texts already present.

New documents fetched:
  GDPR         — Recitals (173) from EUR-Lex; essential for legal interpretation
  NIS2         — BSIG (German BSI Act, national NIS2 transposition)
  CSRD         — ESRS 1 & 2 (cross-cutting standards); ESRS E1, S1, G1 topical standards
  LkSG         — BAFA guidance FAQ text
  EnEfG        — EnEG (predecessor energy savings act, provides implementation context)
  EU AI Act    — GPAI obligations annex text (Article 51-56 recitals)

Run from backend/:  python scripts/fetch_supplementary_docs.py [--regulation <name>]
"""
import argparse
import html as html_module
import re
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent / "data" / "regulations"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.9,de;q=0.8",
    "Accept-Encoding": "gzip, deflate",
}


# ---------------------------------------------------------------------------
# HTML utilities
# ---------------------------------------------------------------------------

def strip_html(html_text: str) -> str:
    html_text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html_text, flags=re.DOTALL | re.IGNORECASE)
    html_text = re.sub(r"<!--.*?-->", "", html_text, flags=re.DOTALL)
    html_text = re.sub(r"<(br|p|div|tr|li|h[1-6])[^>]*>", "\n", html_text, flags=re.IGNORECASE)
    html_text = re.sub(r"</(p|div|tr|li|h[1-6])>", "\n", html_text, flags=re.IGNORECASE)
    html_text = re.sub(r"<[^>]+>", "", html_text)
    html_text = html_module.unescape(html_text)
    html_text = re.sub(r"\n{3,}", "\n\n", html_text)
    return html_text.strip()


def fetch_url(url: str, timeout: int = 30) -> str | None:
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
        try:
            return raw.decode("utf-8", errors="replace")
        except Exception:
            return raw.decode("latin-1", errors="replace")
    except Exception as e:
        print(f"  ERROR fetching {url}: {e}")
        return None


def save(dest_dir: Path, filename: str, header: str, text: str) -> Path:
    dest_dir.mkdir(parents=True, exist_ok=True)
    path = dest_dir / filename
    path.write_text(header + "\n\n" + text, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Fetchers
# ---------------------------------------------------------------------------

def fetch_gesetze(prefix: str, dest_dir: Path, filename: str, label: str) -> bool:
    index_url = f"https://www.gesetze-im-internet.de/{prefix}/"
    print(f"  Index: {index_url}")
    page = fetch_url(index_url)
    if not page:
        return False

    matches = re.findall(r'href="(BJNR[^"]+\.html)"', page)
    if not matches:
        matches = re.findall(r'href="([^"]+BJNR[^"]+\.html)"', page)
    if not matches:
        print(f"  ERROR: full-text link not found for {prefix}")
        return False

    full_url = f"https://www.gesetze-im-internet.de/{prefix}/{matches[0]}"
    print(f"  Full text: {full_url}")
    raw = fetch_url(full_url, timeout=45)
    if not raw:
        return False

    text = strip_html(raw)
    # Normalize non-breaking space between section number and title
    text = re.sub(r'(?m)(^§\s*\d+[a-z]?)\xa0', r'\1\n', text)
    path = save(dest_dir, filename, f"{label}\nSource: {full_url}", text)
    print(f"  Saved: {path.name} ({len(text)//1024}KB)")
    return True


def fetch_eurlex_html(celex: str, dest_dir: Path, filename: str, label: str, lang: str = "EN") -> bool:
    url = f"https://eur-lex.europa.eu/legal-content/{lang}/TXT/HTML/?uri=CELEX:{celex}"
    print(f"  EUR-Lex: {url}")
    raw = fetch_url(url, timeout=60)
    if not raw:
        return False

    # Check for WAF block
    if "Request blocked" in raw or "Access Denied" in raw or len(raw) < 5_000:
        print("  EUR-Lex blocked by WAF — skipping. Download PDF manually.")
        return False

    text = strip_html(raw)
    article_count = len(re.findall(r"(?m)^Article\s+\d+", text))
    recital_count = len(re.findall(r"(?m)^\(\d+\)", text))
    if article_count + recital_count < 5:
        print(f"  WARNING: only {article_count} articles + {recital_count} recitals — may be incomplete")

    path = save(dest_dir, filename, f"{label}\nSource: {url}", text)
    print(f"  Saved: {path.name} ({len(text)//1024}KB, {article_count} articles, {recital_count} recitals)")
    return True


# ---------------------------------------------------------------------------
# Task definitions
# ---------------------------------------------------------------------------

TASKS: list[dict] = [
    # GDPR recitals — 173 recitals that explain the legislative intent of each article.
    # Critical for gap analysis: many articles only make sense in context of their recitals.
    {
        "regulation": "gdpr",
        "name": "GDPR Recitals (full text)",
        "type": "eurlex_html",
        "celex": "32016R0679",
        "filename": "gdpr_recitals.txt",
        "label": "GDPR — Regulation (EU) 2016/679 — Full text including recitals",
        "lang": "EN",
    },

    # BSIG — German BSI Act (national cybersecurity authority law, NIS2 transposition basis).
    # Contains obligations for KRITIS operators and digital infrastructure providers.
    {
        "regulation": "nis2",
        "name": "BSIG (BSI-Gesetz — German BSI Act)",
        "type": "gesetze",
        "prefix": "bsig_2009",
        "filename": "bsig_text.txt",
        "label": "BSIG — BSI-Gesetz (Gesetz über das Bundesamt für Sicherheit in der Informationstechnik)",
    },

    # ESRS 1 — General requirements (cross-cutting, applies to all CSRD reporters).
    # Defines materiality assessment, disclosure architecture, and reporting principles.
    {
        "regulation": "csrd",
        "name": "ESRS 1 General Requirements",
        "type": "eurlex_html",
        "celex": "32023R2772",
        "filename": "esrs1_general_requirements.txt",
        "label": "ESRS 1 — General Requirements (Commission Delegated Regulation (EU) 2023/2772, Annex I)",
        "lang": "EN",
    },

    # ESRS 2 — General disclosures (cross-cutting, every Wave 1 reporter must apply this).
    # Covers governance, strategy, materiality assessment, and metrics & targets.
    {
        "regulation": "csrd",
        "name": "ESRS 2 General Disclosures",
        "type": "eurlex_html",
        "celex": "32023R2772",
        "filename": "esrs2_general_disclosures.txt",
        "label": "ESRS 2 — General Disclosures (Commission Delegated Regulation (EU) 2023/2772, Annex II)",
        "lang": "EN",
    },

    # LkSG implementing regulation — defines reporting format and audit requirements.
    {
        "regulation": "lksg",
        "name": "LkSG-Sorgfaltspflichtenverordnung",
        "type": "gesetze",
        "prefix": "lksgsorgfpflv",
        "filename": "lksg_sorgfpflv_text.txt",
        "label": "LkSG-Sorgfaltspflichtenverordnung — Durchführungsverordnung zum LkSG",
    },

    # EnEG — predecessor energy savings framework act, still referenced by EnEfG for definitions.
    {
        "regulation": "enefg",
        "name": "EnEG (Energieeinsparungsgesetz)",
        "type": "gesetze",
        "prefix": "eneg",
        "filename": "eneg_text.txt",
        "label": "EnEG — Gesetz zur Einsparung von Energie und zur Nutzung erneuerbarer Energien zur Wärme- und Kälteerzeugung in Gebäuden",
    },

    # HINSCHG implementing regulation — reporting channel technical requirements.
    {
        "regulation": "hinschg",
        "name": "HinSchG-Meldestellen details (BMWK guidance)",
        "type": "gesetze",
        "prefix": "hinschgmeldv",
        "filename": "hinschg_meldv_text.txt",
        "label": "HinSchG-Meldestellenverordnung — Verordnung über interne Meldestellen",
    },
]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def ingest(regulation: str) -> None:
    from rag.ingest import ingest_regulation
    print(f"  Ingesting {regulation}...")
    n = ingest_regulation(regulation, reset=False)
    print(f"  Done: {n} chunks total in collection")


def main():
    parser = argparse.ArgumentParser(description="Fetch supplementary regulation documents")
    parser.add_argument("--regulation", help="Only fetch docs for this regulation")
    parser.add_argument("--no-ingest", action="store_true", help="Fetch only, do not ingest into ChromaDB")
    parser.add_argument("--list", action="store_true", help="List planned fetches and exit")
    args = parser.parse_args()

    tasks = TASKS
    if args.regulation:
        tasks = [t for t in TASKS if t["regulation"] == args.regulation]

    if args.list:
        print("Planned supplementary fetches:")
        for t in tasks:
            print(f"  [{t['regulation']}]  {t['name']}")
        return

    results = []
    for task in tasks:
        print(f"\n{'='*60}")
        print(f"{task['name']}  →  {task['regulation']}/")
        dest_dir = BASE_DIR / task["regulation"]

        if task["type"] == "gesetze":
            ok = fetch_gesetze(task["prefix"], dest_dir, task["filename"], task["label"])
        else:
            ok = fetch_eurlex_html(task["celex"], dest_dir, task["filename"], task["label"], task.get("lang", "EN"))

        if not ok:
            results.append((task["name"], "FETCH FAILED"))
            continue

        if not args.no_ingest:
            try:
                ingest(task["regulation"])
                results.append((task["name"], "OK"))
            except Exception as e:
                print(f"  Ingest error: {e}")
                results.append((task["name"], f"INGEST ERROR: {e}"))
        else:
            results.append((task["name"], "FETCHED (no ingest)"))

    print(f"\n{'='*60}")
    print("Summary:")
    for name, status in results:
        icon = "OK" if status == "OK" or "FETCHED" in status else "FAIL"
        print(f"  [{icon}]  {name:<45} {status}")


if __name__ == "__main__":
    main()
