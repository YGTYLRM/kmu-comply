import re
from pathlib import Path

_RE_B = re.compile(
    r"(?m)^§[ \t\xa0]{0,3}(\d+[a-z]?)([^\n]*)\n(.*?)(?=^§[ \t\xa0]{0,3}\d+[a-z]?|\Z)",
    re.DOTALL,
)

for fname in ["sgb_3_text.txt", "sgb_6_text.txt"]:
    path = Path("data/regulations/arbschg") / fname
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    # Find lines that start with §
    sec_lines = [(i, line) for i, line in enumerate(lines) if line.startswith("§")]
    print(f"\n{fname}: {len(sec_lines)} lines starting with §")
    for i, line in sec_lines[:5]:
        print(f"  Line {i}: {repr(line[:80])}")
        for j, c in enumerate(line[:6]):
            print(f"    [{j}] ord={ord(c)} repr={repr(c)}")

    matches = list(_RE_B.finditer(text))
    valid = [m for m in matches if len(m.group(3).strip()) >= 80]
    print(f"  Format B matches: {len(matches)}, valid (body>=80): {len(valid)}")
    if valid:
        print(f"  First valid: §{valid[0].group(1)}, title={repr(valid[0].group(2)[:40])}")
