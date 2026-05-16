import re
from pathlib import Path

text = Path("data/regulations/arbschg/sgb_2_text.txt").read_text(encoding="utf-8")

_RE = re.compile(
    r"(?m)^§\s{1,3}(\d+[a-z]?)\s*\n(.*?)(?=^§\s{1,3}\d+[a-z]?\s*\n|\Z)",
    re.DOTALL,
)

before = len(list(_RE.finditer(text)))
print(f"Matches BEFORE noise strip: {before}")

def strip_noise(text):
    text = re.sub(r"\bzum Seitenanfang\b\s*", "", text)
    text = re.sub(r"\bNichtamtliches Inhaltsverzeichnis\b[^\n]*", "", text)
    text = re.sub(r"\bSeite ausdrucken\b[^\n]*", "", text)
    tail_start = max(0, len(text) - 1000)
    head, tail = text[:tail_start], text[tail_start:]
    tail = re.sub(r"(Impressum|Datenschutz|Barrierefreiheitserkl|Feedback-Formular).*", "", tail, flags=re.DOTALL)
    tail = re.sub(r"[\"']?\s*\)\s*/\*.*?\*/\s*//.*", "", tail, flags=re.DOTALL)
    return head + tail.rstrip()

stripped = strip_noise(text)
after = len(list(_RE.finditer(stripped)))
print(f"Matches AFTER noise strip: {after}")

count = text.count("zum Seitenanfang")
print(f"Occurrences of 'zum Seitenanfang': {count}")

count_ni = text.count("Nichtamtliches Inhaltsverzeichnis")
print(f"Occurrences of 'Nichtamtliches Inhaltsverzeichnis': {count_ni}")

# Show context around first § match in raw text
matches = list(_RE.finditer(text))
if matches:
    m = matches[0]
    print(f"\nFirst match (raw): § {m.group(1)}, body={repr(m.group(2)[:100])}")

# Find where 'zum Seitenanfang' sits relative to a § header
idx = text.find("zum Seitenanfang")
if idx != -1:
    print("\nContext around first 'zum Seitenanfang':")
    print(repr(text[max(0, idx-80):idx+60]))
