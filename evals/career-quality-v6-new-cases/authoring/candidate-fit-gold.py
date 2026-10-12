"""Semantic gold judgments for the fictional candidate-fit cohort."""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]

JUDGMENTS = [
    ("pass", "The candidate's personal count and month match the active fact; the role requirement is stated directly.", []),
    ("fail", "Runbook authorship is supported, but the 20% triage improvement belongs to the team and is not personally attributed to the candidate.", ["c2"]),
    ("pass", "The course completion and internal guide authorship are both directly supported, with their respective months and scope.", []),
    ("pass", "The answer retains the sandbox limit on the SQL work and accurately restates the role's SQL requirement.", []),
    ("needs_review", "Shadowing and handoff authorship are supported; whether they are relevant preparation for independent onboarding leadership is a qualitative transferability judgment.", []),
    ("pass", "Both course completion and passing the related exam are recorded for 2024; the answer does not claim an issued certificate.", []),
    ("fail", "Permission to present is supported, but the complete inventory records no delivered demo; the answer asserts delivery as an accomplished event.", ["c2"]),
    ("pass", "The candidate's manual processing count, project and year match the active record, and the role requirement is directly quoted in substance.", []),
    ("pass", "The candidate wrote the rollback plan and observed the cutover; the answer does not claim vendor coordination.", []),
    ("fail", "The only Kubernetes deployment is explicitly a sandbox practice service; production use is unsupported and conflicts with that scope.", ["c1"]),
    ("pass", "The answer accurately describes joint operator training, including the audience, intake form and month.", []),
    ("pass", "The reported SQL work and its January 2022–April 2024 interval are directly supported.", []),
    ("fail", "Plan review is supported, but the sole guide-authorship record was withdrawn because its author field was wrong; active evidence does not support the public guide claim.", ["c2"]),
    ("pass", "The pilot scope, triage activity and escalation to the duty engineer are all explicitly recorded.", []),
    ("needs_review", "The internal training demo is supported; its preparation value for customer-facing product demos is a plausible but unsettled qualitative judgment.", []),
    ("pass", "The exam pass and still-pending certificate are separate, directly recorded statuses at the stated months.", []),
    ("fail", "Checklist documentation is the candidate's work; vendor coordination is attributed only to the procurement team, not this candidate.", ["c2"]),
    ("pass", "The candidate built the intake tool, and its 30-user, three-week internal pilot is directly supported without a production claim.", []),
    ("pass", "Two guides were authored by the candidate, and a peer reviewed one before publication, exactly as stated.", []),
    ("fail", "The candidate's personal 2024 count is supported, but the 2025 count belongs to the service team and has no individual attribution.", ["c2"]),
]

rows = [
    {"case_id": f"CF6H-{i:02d}", "verdict": verdict,
     "reason": reason, "error_claim_ids": errors}
    for i, (verdict, reason, errors) in enumerate(JUDGMENTS, 1)
]
payload = {"schema": "maguire-v6-new-gold", "family": "candidate-fit",
           "human_approved": False, "exposure": {"checker_code_seen": False,
           "previous_cases_seen": False, "predictions_seen": False}, "rows": rows}
out = BASE / "gold/candidate-fit.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
