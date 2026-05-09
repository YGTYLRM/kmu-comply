"""
Systematic downloader for gesetze-im-internet.de full-text law files.
Fetches official German federal law texts and saves them to regulation directories.

Usage:  python fetch_laws.py
"""
import re
import html as html_module
import urllib.request
import urllib.parse
from pathlib import Path

BASE_DIR = Path(__file__).parent / "data" / "regulations"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; compliance-research/1.0)"}

# (dest_collection, law_prefix, source_note)
# dest_collection must be an existing regulations directory
LAWS_TO_FETCH = [
    # ── Employment / HR ──────────────────────────────────────────────────────
    ("arbschg", "aentg_2009",   "AEntG — Arbeitnehmer-Entsendegesetz (Posted Workers Act)"),
    ("arbschg", "sgb_3",        "SGB III — Kurzarbeit / unemployment insurance"),
    ("arbschg", "sgb_7",        "SGB VII — Statutory accident insurance (Unfallversicherung)"),
    ("arbschg", "sgb_11",       "SGB XI — Long-term care insurance (Pflegeversicherung)"),
    # ── Consumer / Commercial ────────────────────────────────────────────────
    ("compliance_guides", "uwg_2004",    "UWG — Gesetz gegen den unlauteren Wettbewerb (Unfair Competition)"),
    ("compliance_guides", "gmbhg",       "GmbHG — GmbH-Gesetz (Private Limited Companies Act)"),
    ("compliance_guides", "tvg",         "TVG — Tarifvertragsgesetz (Collective Agreements Act)"),
    ("compliance_guides", "hwo",         "HwO — Handwerksordnung (Skilled Trades Act)"),
    ("compliance_guides", "netzdg",      "NetzDG — Network Enforcement Act (social media platforms)"),
    ("compliance_guides", "ustg_1980",   "UStG — Umsatzsteuergesetz (VAT Act)"),
    # ── Environmental / Product ──────────────────────────────────────────────
    ("compliance_guides", "battg",       "BattG — Batteriegesetz (Batteries Act)"),
    ("compliance_guides", "elektrog_2015", "ElektroG — Elektro- und Elektronikgerätegesetz (WEEE)"),
    ("compliance_guides", "krwg",        "KrWG — Kreislaufwirtschaftsgesetz (Waste Management Act)"),
]

def get_full_text_url(prefix: str) -> str | None:
    url = f"https://www.gesetze-im-internet.de/{prefix}/"
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            page = r.read().decode("utf-8", errors="replace")
        matches = re.findall(r'href="(BJNR[^"]+\.html)"', page)
        if matches:
            return f"https://www.gesetze-im-internet.de/{prefix}/{matches[0]}"
    except Exception as e:
        print(f"  Could not get index for {prefix}: {e}")
    return None


def strip_html(html_text: str) -> str:
    """Strip HTML tags and decode entities, keeping structure readable."""
    # Remove script/style blocks
    html_text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html_text, flags=re.DOTALL | re.IGNORECASE)
    # Remove HTML comments
    html_text = re.sub(r"<!--.*?-->", "", html_text, flags=re.DOTALL)
    # Remove navigation noise patterns common on gesetze-im-internet.de
    html_text = re.sub(r"zur.ck\s+weiter", "", html_text)
    html_text = re.sub(r"Nichtamtliches Inhaltsverzeichnis", "", html_text)
    # Replace common block tags with newlines
    html_text = re.sub(r"<(br|p|div|tr|li|h[1-6])[^>]*>", "\n", html_text, flags=re.IGNORECASE)
    html_text = re.sub(r"</(p|div|tr|li|h[1-6])>", "\n", html_text, flags=re.IGNORECASE)
    # Strip all remaining tags
    html_text = re.sub(r"<[^>]+>", "", html_text)
    # Decode HTML entities
    html_text = html_module.unescape(html_text)
    # Collapse multiple blank lines
    html_text = re.sub(r"\n{3,}", "\n\n", html_text)
    return html_text.strip()


def download_law(prefix: str, dest_dir: Path, label: str) -> bool:
    full_text_url = get_full_text_url(prefix)
    if not full_text_url:
        print(f"  SKIP {prefix}: could not find full-text URL")
        return False

    dest_file = dest_dir / f"{prefix}_text.txt"
    if dest_file.exists():
        print(f"  SKIP {prefix}: already downloaded ({dest_file.name})")
        return True

    print(f"  Downloading: {label}")
    print(f"  URL: {full_text_url}")
    req = urllib.request.Request(full_text_url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            raw = r.read().decode("utf-8", errors="replace")
        text = strip_html(raw)
        # Add source header
        header = f"{label}\nSource: {full_text_url}\n\n"
        dest_file.write_text(header + text, encoding="utf-8")
        size = len(text) // 1024
        print(f"  Saved: {dest_file.name} ({size}KB)")
        return True
    except Exception as e:
        print(f"  ERROR downloading {prefix}: {e}")
        return False


if __name__ == "__main__":
    ok, skip, fail = 0, 0, 0
    for dest_coll, prefix, label in LAWS_TO_FETCH:
        dest_dir = BASE_DIR / dest_coll
        if not dest_dir.exists():
            print(f"SKIP {prefix}: directory {dest_dir} does not exist")
            fail += 1
            continue
        print(f"\n{prefix} -> {dest_coll}/")
        result = download_law(prefix, dest_dir, label)
        if result:
            # Check if file was newly created or skipped
            fname = dest_dir / f"{prefix}_text.txt"
            if "already downloaded" in str(result):
                skip += 1
            else:
                ok += 1
        else:
            fail += 1

    print(f"\n{'='*50}")
    print(f"Done: {ok} downloaded, {skip} skipped, {fail} failed")
    print("\nRun ingest next:")
    print('  python -c "from rag.ingest import ingest_regulation; [ingest_regulation(r, reset=True) for r in [\'arbschg\', \'compliance_guides\']]"')
