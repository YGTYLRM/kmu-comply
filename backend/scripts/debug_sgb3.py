import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from rag.ingest import _RE_GERMAN_A, _RE_GERMAN_B, _strip_gesetze_noise

for fname in ["sgb_3_text.txt", "sgb_6_text.txt"]:
    path = Path("data/regulations/arbschg") / fname
    raw = path.read_text(encoding="utf-8")
    text = _strip_gesetze_noise(raw)

    print(f"\n=== {fname} ===")
    print(f"  Raw length: {len(raw)}, after strip: {len(text)}")

    fa = [m for m in _RE_GERMAN_A.finditer(text) if len(m.group(2).strip()) >= 80]
    print(f"  Format A valid matches: {len(fa)}")

    use_b = len(fa) < 3
    print(f"  use_format_b: {use_b}")

    if use_b:
        fb_all = list(_RE_GERMAN_B.finditer(text))
        fb_valid = [m for m in fb_all if len(m.group(3).strip()) >= 80]
        print(f"  Format B all matches: {len(fb_all)}, valid (body>=80): {len(fb_valid)}")
        if fb_valid:
            m = fb_valid[0]
            print(f"  First valid: §{m.group(1)!r}, title={m.group(2)[:40]!r}, body_len={len(m.group(3).strip())}")
        else:
            # Sample a few to see why bodies are short
            for m in fb_all[:5]:
                print(f"  Sample: §{m.group(1)!r} body_len={len(m.group(3).strip())} body={m.group(3).strip()[:60]!r}")
