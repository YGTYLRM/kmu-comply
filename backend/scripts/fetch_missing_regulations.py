"""
Fetches full regulation texts for LkSG, EnEfG, CSRD, NIS2, and EU AI Act.
Then re-ingests each into ChromaDB.

Run from backend/:  python scripts/fetch_missing_regulations.py
"""
import re
import html as html_module
import urllib.request
from pathlib import Path
import sys

BASE_DIR = Path(__file__).parent.parent / "data" / "regulations"
HEADERS  = {
    "User-Agent": "Mozilla/5.0 (compatible; compliance-research/1.0)",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-GB,en;q=0.9,de;q=0.8",
}


# ── HTML stripper ─────────────────────────────────────────────────────────────

def strip_html(html_text: str) -> str:
    html_text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html_text, flags=re.DOTALL | re.IGNORECASE)
    html_text = re.sub(r"<!--.*?-->", "", html_text, flags=re.DOTALL)
    html_text = re.sub(r"<(br|p|div|tr|li|h[1-6])[^>]*>", "\n", html_text, flags=re.IGNORECASE)
    html_text = re.sub(r"</(p|div|tr|li|h[1-6])>", "\n", html_text, flags=re.IGNORECASE)
    html_text = re.sub(r"<[^>]+>", "", html_text)
    html_text = html_module.unescape(html_text)
    html_text = re.sub(r"\n{3,}", "\n\n", html_text)
    return html_text.strip()


# ── gesetze-im-internet.de fetcher ───────────────────────────────────────────

def fetch_gesetze(prefix: str, dest_dir: Path, label: str) -> bool:
    index_url = f"https://www.gesetze-im-internet.de/{prefix}/"
    print(f"  Fetching index: {index_url}")
    req = urllib.request.Request(index_url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            page = r.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

    # Find the full-text HTML link (BJNR*.html pattern)
    matches = re.findall(r'href="(BJNR[^"]+\.html)"', page)
    if not matches:
        # Try alternative pattern
        matches = re.findall(r'href="([^"]+BJNR[^"]+\.html)"', page)
    if not matches:
        print(f"  ERROR: Could not find full-text link for {prefix}")
        return False

    full_url = f"https://www.gesetze-im-internet.de/{prefix}/{matches[0]}"
    print(f"  Full text URL: {full_url}")

    req2 = urllib.request.Request(full_url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req2, timeout=30) as r:
            raw = r.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  ERROR downloading: {e}")
        return False

    text = strip_html(raw)
    dest_file = dest_dir / f"{prefix}_text.txt"
    header = f"{label}\nSource: {full_url}\n\n"
    dest_file.write_text(header + text, encoding="utf-8")
    print(f"  Saved: {dest_file.name} ({len(text)//1024}KB)")
    return True


# ── EUR-Lex fetcher ───────────────────────────────────────────────────────────

def fetch_eurlex(celex: str, dest_dir: Path, filename: str, label: str, lang: str = "EN") -> bool:
    url = f"https://eur-lex.europa.eu/legal-content/{lang}/TXT/HTML/?uri=CELEX:{celex}"
    print(f"  Fetching EUR-Lex: {url}")
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            raw = r.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

    text = strip_html(raw)

    # Sanity check: must have some article markers
    article_count = len(re.findall(r"(?m)^Article\s+\d+", text))
    artikel_count = len(re.findall(r"(?m)^Artikel\s+\d+", text))
    if article_count + artikel_count < 5:
        print(f"  WARNING: Only {article_count + artikel_count} articles found — text may be incomplete")

    dest_file = dest_dir / filename
    header = f"{label}\nSource: {url}\n\n"
    dest_file.write_text(header + text, encoding="utf-8")
    print(f"  Saved: {dest_file.name} ({len(text)//1024}KB, {article_count} articles found)")
    return True


# ── Ingest ────────────────────────────────────────────────────────────────────

def ingest(regulation: str, reset: bool = True) -> None:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from rag.ingest import ingest_regulation
    print(f"  Ingesting {regulation} (reset={reset})...")
    n = ingest_regulation(regulation, reset=reset)
    print(f"  Done: {n} chunks indexed")


# ── Main ──────────────────────────────────────────────────────────────────────

TASKS = [
    {
        "name": "LkSG",
        "regulation": "lksg",
        "type": "gesetze",
        "prefix": "lksg",
        "label": "LkSG — Lieferkettensorgfaltspflichtengesetz (Supply Chain Due Diligence Act)",
    },
    {
        "name": "EnEfG",
        "regulation": "enefg",
        "type": "gesetze",
        "prefix": "enefg",
        "label": "EnEfG — Energieeffizienzgesetz (Energy Efficiency Act)",
    },
    {
        "name": "CSRD",
        "regulation": "csrd",
        "type": "eurlex",
        "celex": "32022L2464",
        "filename": "csrd_directive.txt",
        "label": "CSRD — Corporate Sustainability Reporting Directive (EU) 2022/2464",
        "lang": "EN",
    },
    {
        "name": "NIS2",
        "regulation": "nis2",
        "type": "eurlex",
        "celex": "32022L2555",
        "filename": "nis2_full_directive.txt",
        "label": "NIS2 — Network and Information Security Directive (EU) 2022/2555",
        "lang": "EN",
    },
    {
        "name": "EU AI Act",
        "regulation": "eu_ai_act",
        "type": "eurlex",
        "celex": "32024R1689",
        "filename": "eu_ai_act_full.txt",
        "label": "EU AI Act — Regulation (EU) 2024/1689 on Artificial Intelligence",
        "lang": "EN",
    },
]


if __name__ == "__main__":
    results = []

    for task in TASKS:
        print(f"\n{'='*60}")
        print(f"Processing: {task['name']}")
        print('='*60)

        dest_dir = BASE_DIR / task["regulation"]
        dest_dir.mkdir(parents=True, exist_ok=True)

        # Fetch
        if task["type"] == "gesetze":
            ok = fetch_gesetze(task["prefix"], dest_dir, task["label"])
        else:
            ok = fetch_eurlex(task["celex"], dest_dir, task["filename"], task["label"], task.get("lang", "EN"))

        if not ok:
            print(f"  SKIPPING ingest for {task['name']} — download failed")
            results.append((task["name"], "FETCH FAILED"))
            continue

        # Ingest
        try:
            ingest(task["regulation"], reset=True)
            results.append((task["name"], "OK"))
        except Exception as e:
            print(f"  Ingest error: {e}")
            results.append((task["name"], f"INGEST FAILED: {e}"))

    print(f"\n{'='*60}")
    print("Summary:")
    for name, status in results:
        print(f"  {name:<15} {status}")

    # Final chunk counts
    print("\nFinal ChromaDB counts:")
    import chromadb
    client = chromadb.PersistentClient(path=str(Path(__file__).parent.parent / "data" / "chroma_db"))
    for task in TASKS:
        try:
            col = client.get_collection(task["regulation"])
            print(f"  {task['regulation']:<20} {col.count()} chunks")
        except Exception:
            print(f"  {task['regulation']:<20} not found")
