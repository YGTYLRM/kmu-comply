# -*- coding: utf-8 -*-
"""One-off script: expand the GwG retrieval-eval set from 5 to 18 questions.
Baseline (thesis Table 4): gwg had only 5 hand-labelled questions, too small
a sample to trust the reported 60% Top-5 figure. New questions are grounded
in the actual GwG statute text and BaFin guidance already in the repo
(backend/data/regulations/gwg/)."""
import json
from pathlib import Path

EVAL_FILE = Path(__file__).parent.parent / "data" / "retrieval_eval.json"

NEW_GWG_CASES = [
    {
        "id": "gwg-006",
        "regulation": "gwg",
        "collection": "gwg",
        "question": "Who qualifies as the beneficial owner of a legal entity under GwG, and what happens when no natural person meets the ownership threshold?",
        "expected_articles": ["§ 3"],
        "notes": "Beneficial owner definition, 25% threshold, fictive beneficial owner"
    },
    {
        "id": "gwg-007",
        "regulation": "gwg",
        "collection": "gwg",
        "question": "When must an obligated entity apply enhanced due diligence for a politically exposed person, and what measures are required?",
        "expected_articles": ["§ 13"],
        "notes": "PEP enhanced due diligence"
    },
    {
        "id": "gwg-008",
        "regulation": "gwg",
        "collection": "gwg",
        "question": "Under what conditions may an obligated entity apply simplified due diligence instead of standard customer due diligence?",
        "expected_articles": ["§ 14"],
        "notes": "Simplified CDD for lower-risk customers"
    },
    {
        "id": "gwg-009",
        "regulation": "gwg",
        "collection": "gwg",
        "question": "What must an obligated entity do when it forms a suspicion that a transaction may be related to money laundering?",
        "expected_articles": ["§ 43"],
        "notes": "Suspicious activity reporting to the FIU"
    },
    {
        "id": "gwg-010",
        "regulation": "gwg",
        "collection": "gwg",
        "question": "How long must an obligated entity retain customer due diligence documents and transaction records under GwG?",
        "expected_articles": ["§ 8"],
        "notes": "Record-keeping retention periods"
    },
    {
        "id": "gwg-011",
        "regulation": "gwg",
        "collection": "gwg",
        "question": "What training and whistleblowing measures must an obligated entity's internal AML safeguards include?",
        "expected_articles": ["§ 6"],
        "notes": "Internal safeguards distinct from MLRO appointment under §7"
    },
    {
        "id": "gwg-012",
        "regulation": "gwg",
        "collection": "gwg",
        "question": "What are the maximum administrative fines BaFin can impose for serious or systematic GwG violations?",
        "expected_articles": ["§ 56"],
        "notes": "AML administrative fines framework"
    },
    {
        "id": "gwg-013",
        "regulation": "gwg",
        "collection": "gwg",
        "question": "Is a bank required to appoint a deputy money laundering officer in addition to the primary MLRO?",
        "expected_articles": ["§ 7"],
        "notes": "MLRO deputy appointment requirement"
    },
    {
        "id": "gwg-014",
        "regulation": "gwg",
        "collection": "gwg",
        "question": "At what transaction value must an obligated entity apply customer due diligence for an occasional transaction outside an existing business relationship?",
        "expected_articles": ["§ 10"],
        "notes": "Occasional-transaction CDD threshold"
    },
    {
        "id": "gwg-015",
        "regulation": "gwg",
        "collection": "gwg",
        "question": "When must an obligated entity update its AML risk analysis under GwG, beyond the periodic annual review?",
        "expected_articles": ["§ 5"],
        "notes": "Risk analysis update triggers"
    },
    {
        "id": "adv-gwg-001",
        "regulation": "gwg",
        "collection": "gwg",
        "question": "A real estate agent mediates the rental of an apartment for an annual rent of €12,000. Is the agent subject to GwG obligations, and which provision defines them as an obligated entity?",
        "expected_articles": ["§ 2"],
        "notes": "Real estate agent scope, rent threshold above €10,000"
    },
    {
        "id": "adv-gwg-002",
        "regulation": "gwg",
        "collection": "gwg",
        "question": "A crypto exchange operating in Germany wants to know which provision brings virtual asset service providers into scope of AML obligations.",
        "expected_articles": ["§ 2"],
        "notes": "VASP obligated-entity scope"
    },
    {
        "id": "adv-gwg-003",
        "regulation": "gwg",
        "collection": "gwg",
        "question": "A payment institution's customer requests a large fund transfer to a high-risk third country flagged by the EU Commission. What enhanced measures must the institution apply?",
        "expected_articles": ["§ 15"],
        "notes": "Enhanced due diligence trigger for high-risk third countries"
    },
]

data = json.loads(EVAL_FILE.read_text(encoding="utf-8"))

# insert right after the last existing gwg-0xx entry, before whatever follows
insert_at = None
for i, case in enumerate(data):
    if case["regulation"] == "gwg":
        insert_at = i + 1
data = data[:insert_at] + NEW_GWG_CASES + data[insert_at:]

EVAL_FILE.write_text(
    json.dumps(data, indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8"
)
print(f"Inserted {len(NEW_GWG_CASES)} new GwG cases at index {insert_at}. Total cases now: {len(data)}")
