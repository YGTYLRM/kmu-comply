"""
Comprehensive regulation fetcher — downloads full legal texts from
gesetze-im-internet.de and EUR-Lex for ALL 14 regulated areas.

Run from backend/:
    python scripts/fetch_all_regulations.py              # fetch all
    python scripts/fetch_all_regulations.py --ingest     # fetch + re-ingest into ChromaDB
    python scripts/fetch_all_regulations.py bdsg enefg    # fetch specific regulations only

What it does:
  1. Downloads full legal texts from official sources
  2. Strips HTML, extracts clean text
  3. Saves to backend/data/regulations/<regulation>/
  4. Optionally re-ingests into ChromaDB

Will NOT overwrite existing *_expanded.txt or *_guidance_expanded.txt files —
those are hand-curated and more valuable than raw law text.
"""
import html as html_module
import re
import sys
import urllib.request
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent / "data" / "regulations"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; Complio-compliance-research/1.0)",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "de-DE,de;q=0.9,en;q=0.8",
}


def strip_html(html_text: str) -> str:
    html_text = re.sub(r"<(script|style|noscript)[^>]*>.*?</\1>", "", html_text, flags=re.DOTALL | re.IGNORECASE)
    html_text = re.sub(r"<!--.*?-->", "", html_text, flags=re.DOTALL)
    html_text = re.sub(r"<(br|p|div|tr|li|h[1-6])[^>]*>", "\n", html_text, flags=re.IGNORECASE)
    html_text = re.sub(r"</(p|div|tr|li|h[1-6])>", "\n", html_text, flags=re.IGNORECASE)
    html_text = re.sub(r"<[^>]+>", "", html_text)
    html_text = html_module.unescape(html_text)
    html_text = re.sub(r"\n{3,}", "\n\n", html_text)
    return html_text.strip()


def fetch_gesetze(prefix: str, dest_dir: Path, label: str, filename: str | None = None) -> bool:
    """Fetch full text from gesetze-im-internet.de."""
    index_url = f"https://www.gesetze-im-internet.de/{prefix}/"
    print(f"  Fetching index: {index_url}")
    req = urllib.request.Request(index_url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            page = r.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  ERROR fetching index: {e}")
        return False

    matches = re.findall(r'href="(BJNR[^"]+\.html)"', page)
    if not matches:
        matches = re.findall(r'href="([^"]+BJNR[^"]+\.html)"', page)
    if not matches:
        print(f"  ERROR: Could not find full-text link for {prefix}")
        return False

    full_url = f"https://www.gesetze-im-internet.de/{prefix}/{matches[0]}"
    print(f"  Full text URL: {full_url}")

    req2 = urllib.request.Request(full_url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req2, timeout=60) as r:
            raw = r.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  ERROR downloading full text: {e}")
        return False

    text = strip_html(raw)
    if len(text) < 500:
        print(f"  WARNING: Text too short ({len(text)} chars) — may be a CAPTCHA or error page")
        return False

    fname = filename or f"{prefix}_text.txt"
    dest_file = dest_dir / fname
    header = f"{label}\nSource: {full_url}\n\n"
    dest_file.write_text(header + text, encoding="utf-8")
    print(f"  OK: {dest_file.name} ({len(text) // 1024}KB)")
    return True


def fetch_eurlex(celex: str, dest_dir: Path, filename: str, label: str, lang: str = "EN") -> bool:
    """Fetch full text from EUR-Lex."""
    url = f"https://eur-lex.europa.eu/legal-content/{lang}/TXT/HTML/?uri=CELEX:{celex}"
    print(f"  Fetching EUR-Lex: {url}")
    req = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            raw = r.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

    if "JavaScript" in raw[:500] and "robot" in raw[:500].lower():
        print(f"  WARNING: Got CAPTCHA/JS challenge page — cannot auto-fetch")
        return False

    text = strip_html(raw)
    if len(text) < 1000:
        print(f"  WARNING: Text too short ({len(text)} chars) — likely blocked")
        return False

    article_count = len(re.findall(r"(?m)^Article\s+\d+", text))
    artikel_count = len(re.findall(r"(?m)^Artikel\s+\d+", text))
    total_articles = article_count + artikel_count
    if total_articles < 3:
        print(f"  WARNING: Only {total_articles} articles found — text may be incomplete")

    dest_file = dest_dir / filename
    header = f"{label}\nSource: {url}\n\n"
    dest_file.write_text(header + text, encoding="utf-8")
    print(f"  OK: {dest_file.name} ({len(text) // 1024}KB, {total_articles} articles)")
    return True


# ── Task definitions ─────────────────────────────────────────────────────────
# Each task: regulation key, target directory, sources to fetch

TASKS = [
    # ── GDPR / DSGVO ──────────────────────────────────────────────────────
    {
        "name": "GDPR (German full text)",
        "regulation": "gdpr",
        "dir": "gdpr",
        "type": "eurlex",
        "celex": "32016R0679",
        "filename": "gdpr_dsgvo_full.txt",
        "label": "DSGVO — Datenschutz-Grundverordnung (EU) 2016/679 (German)",
        "lang": "DE",
    },

    # ── BDSG ──────────────────────────────────────────────────────────────
    {
        "name": "BDSG (full text refresh)",
        "regulation": "bdsg",
        "dir": "bdsg",
        "type": "gesetze",
        "prefix": "bdsg_2018",
        "filename": "bdsg_full_text.txt",
        "label": "BDSG — Bundesdatenschutzgesetz 2018",
    },

    # ── LkSG ──────────────────────────────────────────────────────────────
    {
        "name": "LkSG (full text refresh)",
        "regulation": "lksg",
        "dir": "lksg",
        "type": "gesetze",
        "prefix": "lksg",
        "filename": "lksg_text.txt",
        "label": "LkSG — Lieferkettensorgfaltspflichtengesetz",
    },

    # ── EnEfG ─────────────────────────────────────────────────────────────
    {
        "name": "EnEfG (full text refresh)",
        "regulation": "enefg",
        "dir": "enefg",
        "type": "gesetze",
        "prefix": "enefg",
        "filename": "enefg_text.txt",
        "label": "EnEfG — Energieeffizienzgesetz",
    },
    {
        "name": "EDL-G (energy audit law)",
        "regulation": "enefg",
        "dir": "enefg",
        "type": "gesetze",
        "prefix": "edl-g",
        "filename": "edlg_text.txt",
        "label": "EDL-G — Energiedienstleistungsgesetz",
    },

    # ── CSRD ──────────────────────────────────────────────────────────────
    {
        "name": "CSRD Directive (English)",
        "regulation": "csrd",
        "dir": "csrd",
        "type": "eurlex",
        "celex": "32022L2464",
        "filename": "csrd_directive_full.txt",
        "label": "CSRD — Corporate Sustainability Reporting Directive (EU) 2022/2464",
        "lang": "EN",
    },

    # ── NIS2 ──────────────────────────────────────────────────────────────
    {
        "name": "NIS2 Directive (English full text)",
        "regulation": "nis2",
        "dir": "nis2",
        "type": "eurlex",
        "celex": "32022L2555",
        "filename": "nis2_full_directive.txt",
        "label": "NIS2 — Network and Information Security Directive (EU) 2022/2555",
        "lang": "EN",
    },
    {
        "name": "NIS2 Directive (German)",
        "regulation": "nis2",
        "dir": "nis2",
        "type": "eurlex",
        "celex": "32022L2555",
        "filename": "nis2_directive_de.txt",
        "label": "NIS2-Richtlinie (EU) 2022/2555 (German)",
        "lang": "DE",
    },
    {
        "name": "BSIG (German NIS2 implementation)",
        "regulation": "nis2",
        "dir": "nis2",
        "type": "gesetze",
        "prefix": "bsig",
        "filename": "bsig_text.txt",
        "label": "BSIG — Gesetz über das Bundesamt für Sicherheit in der Informationstechnik",
    },

    # ── EU AI Act ─────────────────────────────────────────────────────────
    {
        "name": "EU AI Act (English full text)",
        "regulation": "eu_ai_act",
        "dir": "eu_ai_act",
        "type": "eurlex",
        "celex": "32024R1689",
        "filename": "eu_ai_act_full.txt",
        "label": "EU AI Act — Regulation (EU) 2024/1689",
        "lang": "EN",
    },
    {
        "name": "EU AI Act (German)",
        "regulation": "eu_ai_act",
        "dir": "eu_ai_act",
        "type": "eurlex",
        "celex": "32024R1689",
        "filename": "eu_ai_act_de.txt",
        "label": "KI-Verordnung (EU) 2024/1689 (German)",
        "lang": "DE",
    },

    # ── HinSchG ───────────────────────────────────────────────────────────
    {
        "name": "HinSchG (full text refresh)",
        "regulation": "hinschg",
        "dir": "hinschg",
        "type": "gesetze",
        "prefix": "hinschg",
        "filename": "hinschg_text.txt",
        "label": "HinSchG — Hinweisgeberschutzgesetz",
    },

    # ── Workplace law (ArbSchG family) ────────────────────────────────────
    {
        "name": "ArbSchG (occupational safety)",
        "regulation": "workplace_law",
        "dir": "arbschg",
        "type": "gesetze",
        "prefix": "arbschg",
        "filename": "arbschg_text.txt",
        "label": "ArbSchG — Arbeitsschutzgesetz",
    },
    {
        "name": "ArbZG (working time)",
        "regulation": "workplace_law",
        "dir": "arbschg",
        "type": "gesetze",
        "prefix": "arbzg",
        "filename": "arbzg_text.txt",
        "label": "ArbZG — Arbeitszeitgesetz",
    },
    {
        "name": "MuSchG (maternity protection)",
        "regulation": "workplace_law",
        "dir": "arbschg",
        "type": "gesetze",
        "prefix": "muschg_2018",
        "filename": "muschg_text.txt",
        "label": "MuSchG — Mutterschutzgesetz",
    },
    {
        "name": "JArbSchG (youth employment)",
        "regulation": "workplace_law",
        "dir": "arbschg",
        "type": "gesetze",
        "prefix": "jarbschg",
        "filename": "jarbschg_text.txt",
        "label": "JArbSchG — Jugendarbeitsschutzgesetz",
    },
    {
        "name": "BUrlG (federal leave)",
        "regulation": "workplace_law",
        "dir": "arbschg",
        "type": "gesetze",
        "prefix": "burlg",
        "filename": "burlg_text.txt",
        "label": "BUrlG — Bundesurlaubsgesetz",
    },
    {
        "name": "BBiG (vocational training)",
        "regulation": "workplace_law",
        "dir": "arbschg",
        "type": "gesetze",
        "prefix": "bbig_2005",
        "filename": "bbig_text.txt",
        "label": "BBiG — Berufsbildungsgesetz",
    },
    {
        "name": "NachwG (employment terms notification)",
        "regulation": "workplace_law",
        "dir": "arbschg",
        "type": "gesetze",
        "prefix": "nachwg",
        "filename": "nachwg_text.txt",
        "label": "NachwG — Nachweisgesetz",
    },
    {
        "name": "TzBfG (part-time and fixed-term)",
        "regulation": "workplace_law",
        "dir": "arbschg",
        "type": "gesetze",
        "prefix": "tzbfg",
        "filename": "tzbfg_text.txt",
        "label": "TzBfG — Teilzeit- und Befristungsgesetz",
    },
    {
        "name": "KSchG (dismissal protection)",
        "regulation": "workplace_law",
        "dir": "arbschg",
        "type": "gesetze",
        "prefix": "kschg",
        "filename": "kschg_text.txt",
        "label": "KSchG — Kündigungsschutzgesetz",
    },
    {
        "name": "BetrVG (works constitution)",
        "regulation": "workplace_law",
        "dir": "arbschg",
        "type": "gesetze",
        "prefix": "betrvg",
        "filename": "betrvg_text.txt",
        "label": "BetrVG — Betriebsverfassungsgesetz",
    },
    {
        "name": "EntgFG (continued pay)",
        "regulation": "workplace_law",
        "dir": "arbschg",
        "type": "gesetze",
        "prefix": "entgfg",
        "filename": "entgfg_text.txt",
        "label": "EntgFG — Entgeltfortzahlungsgesetz",
    },

    # ── AGG ───────────────────────────────────────────────────────────────
    {
        "name": "AGG (anti-discrimination)",
        "regulation": "agg",
        "dir": "agg",
        "type": "gesetze",
        "prefix": "agg",
        "filename": "agg_text.txt",
        "label": "AGG — Allgemeines Gleichbehandlungsgesetz",
    },
    {
        "name": "BetrvG for AGG (works constitution)",
        "regulation": "agg",
        "dir": "agg",
        "type": "gesetze",
        "prefix": "betrvg",
        "filename": "betrvg_text.txt",
        "label": "BetrVG — Betriebsverfassungsgesetz (AGG cross-reference)",
    },

    # ── MiLoG ─────────────────────────────────────────────────────────────
    {
        "name": "MiLoG (minimum wage)",
        "regulation": "milog",
        "dir": "milog",
        "type": "gesetze",
        "prefix": "milog",
        "filename": "milog_text.txt",
        "label": "MiLoG — Mindestlohngesetz",
    },

    # ── TTDSG / TDDDG ────────────────────────────────────────────────────
    {
        "name": "TTDSG/TDDDG (telecom data protection)",
        "regulation": "ttdsg",
        "dir": "ttdsg",
        "type": "gesetze",
        "prefix": "ttdsg",
        "filename": "ttdsg_text.txt",
        "label": "TDDDG (TTDSG) — Telekommunikation-Digitale-Dienste-Datenschutz-Gesetz",
    },
    {
        "name": "TMG (telemedia act — legacy reference)",
        "regulation": "ttdsg",
        "dir": "ttdsg",
        "type": "gesetze",
        "prefix": "tmg",
        "filename": "tmg_text.txt",
        "label": "TMG — Telemediengesetz (legacy, partially superseded by TDDDG and DDG)",
    },

    # ── GwG ───────────────────────────────────────────────────────────────
    {
        "name": "GwG (anti-money laundering, refresh)",
        "regulation": "gwg",
        "dir": "gwg",
        "type": "gesetze",
        "prefix": "gwg_2017",
        "filename": "gwg_2017_text.txt",
        "label": "GwG — Geldwäschegesetz 2017",
    },

    # ── EU Data Act ───────────────────────────────────────────────────────
    {
        "name": "EU Data Act (English full text)",
        "regulation": "eu_data_act",
        "dir": "eu_data_act",
        "type": "eurlex",
        "celex": "32023R2854",
        "filename": "eu_data_act_full.txt",
        "label": "EU Data Act — Regulation (EU) 2023/2854",
        "lang": "EN",
    },

    # ── Compliance guides — supplementary laws ────────────────────────────
    {
        "name": "DDG (Digital Services Act Germany)",
        "regulation": "compliance_guides",
        "dir": "compliance_guides",
        "type": "gesetze",
        "prefix": "ddg",
        "filename": "ddg_text.txt",
        "label": "DDG — Digitale-Dienste-Gesetz",
    },
    {
        "name": "UWG (unfair competition)",
        "regulation": "compliance_guides",
        "dir": "compliance_guides",
        "type": "gesetze",
        "prefix": "uwg_2004",
        "filename": "uwg_2004_text.txt",
        "label": "UWG — Gesetz gegen den unlauteren Wettbewerb",
    },
    {
        "name": "HGB (commercial code)",
        "regulation": "compliance_guides",
        "dir": "compliance_guides",
        "type": "gesetze",
        "prefix": "hgb",
        "filename": "hgb_text.txt",
        "label": "HGB — Handelsgesetzbuch",
    },
    {
        "name": "GewO (trade regulation)",
        "regulation": "compliance_guides",
        "dir": "compliance_guides",
        "type": "gesetze",
        "prefix": "gewo",
        "filename": "gewo_text.txt",
        "label": "GewO — Gewerbeordnung",
    },
]


def run(selected: list[str] | None = None, do_ingest: bool = False):
    tasks = TASKS
    if selected:
        selected_lower = {s.lower() for s in selected}
        tasks = [
            t for t in TASKS
            if t["regulation"] in selected_lower
            or t["dir"] in selected_lower
            or t["name"].lower() in selected_lower
        ]
        if not tasks:
            print(f"No tasks match: {selected}")
            print(f"Available: {sorted(set(t['regulation'] for t in TASKS))}")
            return

    results = []
    regs_to_ingest = set()

    for task in tasks:
        print(f"\n{'=' * 60}")
        print(f"Fetching: {task['name']}")
        print("=" * 60)

        dest_dir = BASE_DIR / task["dir"]
        dest_dir.mkdir(parents=True, exist_ok=True)

        if task["type"] == "gesetze":
            ok = fetch_gesetze(task["prefix"], dest_dir, task["label"], task.get("filename"))
        else:
            ok = fetch_eurlex(
                task["celex"], dest_dir, task["filename"],
                task["label"], task.get("lang", "EN"),
            )

        status = "OK" if ok else "FAILED"
        results.append((task["name"], status))
        if ok and do_ingest:
            regs_to_ingest.add(task["regulation"])

    # Summary
    print(f"\n{'=' * 60}")
    print("Fetch Summary:")
    ok_count = sum(1 for _, s in results if s == "OK")
    print(f"  {ok_count}/{len(results)} successful")
    for name, status in results:
        icon = "OK" if status == "OK" else "XX"
        print(f"  {icon} {name}")

    # Ingest
    if do_ingest and regs_to_ingest:
        print(f"\n{'=' * 60}")
        print("Re-ingesting into ChromaDB...")
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from rag.ingest import ingest_regulation, REGULATION_COLLECTIONS

        for reg in sorted(regs_to_ingest):
            collection_name = REGULATION_COLLECTIONS.get(reg)
            if not collection_name:
                print(f"  SKIP {reg}: no collection mapping")
                continue
            try:
                print(f"\n  Ingesting {reg} -> {collection_name}...")
                n = ingest_regulation(reg, reset=True)
                print(f"  Done: {n} chunks indexed into {collection_name}")
            except Exception as e:
                print(f"  ERROR ingesting {reg}: {e}")

    return results


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    do_ingest = "--ingest" in sys.argv
    run(args or None, do_ingest=do_ingest)
