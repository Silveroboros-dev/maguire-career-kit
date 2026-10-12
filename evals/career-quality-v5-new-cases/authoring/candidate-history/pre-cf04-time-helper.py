"""Hand-authored fictional candidate-fit v5 cases. Run with python3 -B."""

import json
import sys
from pathlib import Path


BASE = Path(__file__).resolve().parents[1]
FAMILY = "candidate-fit"
DECISION = "2026-10-12T12:00:00Z"
EXPOSURE = {
    "checker_code_seen": False,
    "previous_cases_seen": False,
    "predictions_seen": False,
}


def source(case, number, text, kind="candidate_fact", status="active", observed_at="2026-10-11T12:00:00Z"):
    return {"id": f"CF5H-{case:02d}-s{number}", "text": text, "kind": kind, "status": status, "observed_at": observed_at}


RAW = [
    ("Ledger continuity", [source(1, 1, "From January 2024 through March 2025, Mara maintained the archive migration ledger and recorded weekly handoffs for the archive team.")], "Mara maintained the archive migration ledger for over a year and recorded weekly handoffs."),
    ("Shadowing versus presenting", [source(2, 1, "During the April 2025 pilot, Mara was permitted to shadow two customer demos; she did not present either demo.")], "Mara presented two customer demos during the April 2025 pilot."),
    ("Post-incident review facilitation", [source(3, 1, "Between March and August 2025, Mara facilitated four post-incident reviews for the municipal data service and documented the follow-up owners."), source(3, 2, "This role requires facilitation of post-incident reviews.", "job_description")], "Mara facilitated four post-incident reviews and documented their follow-up owners. The role requires post-incident review facilitation."),
    ("Pilot alert handling", [source(4, 1, "In a six-week service pilot in 2025, Mara triaged 18 alerts and escalated three of them to the SRE team.")], "Mara triaged alerts and escalated three to the SRE team during the six-week service pilot."),
    ("Recorded captions versus live operation", [source(5, 1, "Mara tested caption accuracy in recorded interviews during a 2025 accessibility pilot; she did not operate captions during live interviews."), source(5, 2, "This role requires operating live captions in customer interviews.", "job_description")], "Mara's recorded-caption QA experience is transferable to live-caption operation."),
    ("Historical remote permission", [source(6, 1, "In 2023, Mara's former employer permitted three remote-work days per week; that employment ended in December 2023."), source(6, 2, "This role currently requires office attendance on all five weekdays and permits no remote-work days.", "job_description")], "This role currently permits Mara to work remotely three days a week."),
    ("OCR experience and certificate", [source(7, 1, "Mara used OCR to review scans for indexing during the June–August 2025 pilot. She has not earned an OCR training certificate.")], "Mara has OCR indexing experience, but no OCR training certificate."),
    ("Vendor cutover coordination", [source(8, 1, "During a 2025 pilot, Mara coordinated three vendor cutovers, each under engineering signoff."), source(8, 2, "This role requires vendor cutover coordination.", "job_description")], "Mara coordinated three vendor cutovers under engineering signoff; the role requires cutover coordination."),
    ("Course versus certification", [source(9, 1, "Mara completed an internal security awareness course and has not earned CISSP certification."), source(9, 2, "This role requires CISSP certification.", "job_description")], "Mara holds the CISSP certification required by the role."),
    ("Escalation with decision boundary", [source(10, 1, "During the 2025 service pilot, Mara escalated two severity-one alerts to the incident lead; the lead made the final incident decisions."), source(10, 2, "This role requires incident escalation experience.", "job_description")], "Mara escalated two severity-one alerts to an incident lead during the pilot, while the lead made final decisions. The role requires incident escalation experience."),
    ("Lab versus production", [source(11, 1, "Mara only ran Kubernetes in a personal lab for four weeks and has not operated it in production."), source(11, 2, "Production Kubernetes experience is not required for this role.", "job_description")], "The role does not require production Kubernetes experience, and Mara has only used it in a personal lab."),
    ("Partial archive processing", [source(12, 1, "By September 2025, Mara processed two of the five boxes in the legal archive; the remaining three were unprocessed.")], "Mara processed all five boxes in the legal archive by September 2025."),
    ("Conflicting plan authorship", [source(13, 1, "Mara personally drafted the API migration plan for the 2025 pilot."), source(13, 2, "Mara reviewed, but did not draft, the API migration plan for the 2025 pilot; Jo wrote it.")], "Mara drafted the API migration plan for the 2025 pilot."),
    ("Written bilingual onboarding", [source(14, 1, "Mara wrote three bilingual French/English client onboarding guides; she has not conducted live client onboarding in either language."), source(14, 2, "This role requires bilingual written onboarding guides.", "job_description")], "Mara wrote three bilingual French/English onboarding guides, and the role requires bilingual written onboarding guides."),
    ("Team outcome attribution", [source(15, 1, "As one of six analysts, Mara tagged support tickets. The team reduced mean triage time by 30% that quarter; the report attributed no portion of the reduction to an individual.")], "Mara cut mean triage time by 30% that quarter."),
    ("Pilot rollback planning", [source(16, 1, "Mara wrote rollback plans for three internal pilot deployments; none of the plans were used in production."), source(16, 2, "This role requires documenting deployment rollback plans.", "job_description")], "Mara has written rollback plans for three internal pilots. The role requires rollback-plan documentation."),
    ("Corrected course record", [source(17, 1, "An old draft says Mara was certified in data privacy in May 2025.", status="withdrawn", observed_at="2025-05-30T12:00:00Z"), source(17, 2, "Correction: Mara completed the vendor's data privacy course in May 2025 but did not take the certification exam.")], "Mara completed the data privacy course in May 2025; she did not take the certification exam."),
    ("Sandbox SQL versus production data", [source(18, 1, "Mara ran SQL queries on synthetic data in a sandbox; she has not queried a production customer database."), source(18, 2, "This role requires production customer database query experience.", "job_description")], "Mara has queried production customer databases with SQL, as the role requires."),
    ("Bilingual onboarding", [source(19, 1, "In 2025, Mara handled four client onboarding sessions: two in French and two in English."), source(19, 2, "Bilingual client onboarding is required for this role.", "job_description")], "Mara has handled onboarding in both French and English, and the role requires bilingual onboarding."),
    ("Pilot runbook and training", [source(20, 1, "Mara wrote a runbook for a one-month pilot and trained three operators on it. The runbook was not used in production."), source(20, 2, "The role asks for runbook writing and operator training.", "job_description")], "Mara wrote a pilot runbook and trained three operators on it; the role calls for runbook writing and operator training."),
]


def write(name, schema, rows):
    path = BASE / name / f"{FAMILY}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"schema": schema, "family": FAMILY, "human_approved": False, "exposure": EXPOSURE, "rows": rows}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def p(subject, predicate, obj, *, polarity="positive", modality="self_report", epistemic_scope="world", scope=None, time=None, measure=None):
    return {"subject": subject, "predicate": predicate, "object": obj, "polarity": polarity,
            "modality": modality, "epistemic_scope": epistemic_scope, "scope": scope or {},
            "time": time or {}, "measure": measure}


def m(kind, unit, lower=None, upper=None, per=None):
    return {"kind": kind, "unit": unit, "lower": lower, "upper": upper, "per": per}


def claim(quote, reading, *, stance="asserted", check=None):
    return {"quote": quote, "stance": stance, "readings": [reading], "check": check}


def ref(case, source_number, fact_index=0):
    return {"source_id": f"CF5H-{case:02d}-s{source_number}", "fact_index": fact_index}


NORMAL = {}
GOLD = {}


def add(i, facts, claims, verdict, reason, errors=()):
    if "--raw-only" in sys.argv:
        return
    case_id = f"CF5H-{i:02d}"
    source_ids = [s["id"] for s in RAW[i - 1][1]]
    assert len(facts) == len(source_ids)
    NORMAL[i] = {"case_id": case_id, "sources": [
        {"id": source_id, "facts": source_facts}
        for source_id, source_facts in zip(source_ids, facts)
    ], "claims": [{"id": f"c{j}", **item} for j, item in enumerate(claims, 1)]}
    GOLD[i] = {"case_id": case_id, "verdict": verdict, "reason": reason,
               "error_claim_ids": [f"c{j}" for j in errors]}


add(1, [[
    p("candidate", "ledger_maintenance", "archive migration ledger", scope={"team": "archive"}, time={"start": "2024-01", "end": "2025-03"}),
    p("candidate", "handoff_recording", "archive migration handoffs", scope={"team": "archive"}, time={"start": "2024-01", "end": "2025-03"}, measure=m("frequency", "handoff", 1, 1, "week")),
]], [
    claim("Mara maintained the archive migration ledger for over a year", p("candidate", "ledger_maintenance", "archive migration ledger", scope={"team": "archive", "duration_months_lower": 13}, time={"start": "2024-01", "end": "2025-03"})),
    claim("recorded weekly handoffs", p("candidate", "handoff_recording", "archive migration handoffs", scope={"team": "archive"}, time={"start": "2024-01", "end": "2025-03"}, measure=m("frequency", "handoff", 1, 1, "week"))),
], "pass", "The January 2024–March 2025 interval spans 14 elapsed months, exceeding one year; the same record explicitly states weekly handoffs.")

add(2, [[
    p("candidate", "demo_shadowing", "customer demos", modality="permission", scope={"project": "April 2025 pilot"}, time={"start": "2025-04", "end": "2025-04"}, measure=m("count", "demo", 2, 2)),
    p("candidate", "demo_presentation", "customer demos", polarity="negative", scope={"project": "April 2025 pilot"}, time={"start": "2025-04", "end": "2025-04"}),
]], [
    claim("Mara presented two customer demos during the April 2025 pilot", p("candidate", "demo_presentation", "customer demos", scope={"project": "April 2025 pilot"}, time={"start": "2025-04", "end": "2025-04"}, measure=m("count", "demo", 2, 2))),
], "fail", "Permission to shadow is not presentation experience, and the source explicitly says Mara did not present either demo.", (1,))

add(3, [
    [p("candidate", "incident_review_facilitation", "post-incident reviews", scope={"service": "municipal data service"}, time={"start": "2025-03", "end": "2025-08"}, measure=m("count", "review", 4, 4)),
     p("candidate", "follow_up_documentation", "post-incident review owners", scope={"service": "municipal data service"}, time={"start": "2025-03", "end": "2025-08"})],
    [p("role", "incident_review_facilitation", "post-incident reviews", modality="requirement")],
], [
    claim("Mara facilitated four post-incident reviews", p("candidate", "incident_review_facilitation", "post-incident reviews", scope={"service": "municipal data service"}, time={"start": "2025-03", "end": "2025-08"}, measure=m("count", "review", 4, 4))),
    claim("documented their follow-up owners", p("candidate", "follow_up_documentation", "post-incident review owners", scope={"service": "municipal data service"}, time={"start": "2025-03", "end": "2025-08"})),
    claim("The role requires post-incident review facilitation", p("role", "incident_review_facilitation", "post-incident reviews", modality="requirement")),
], "pass", "Mara's record documents four facilitated reviews and their follow-up owners during the stated period; facilitation is an explicit role requirement.")

add(4, [[
    p("candidate", "alert_triage", "service alerts", scope={"project": "six-week service pilot"}, time={"start": "2025", "end": "2025"}, measure=m("count", "alert", 18, 18)),
    p("candidate", "alert_escalation", "service alerts to SRE team", scope={"project": "six-week service pilot"}, time={"start": "2025", "end": "2025"}, measure=m("count", "alert", 3, 3)),
]], [
    claim("Mara triaged alerts", p("candidate", "alert_triage", "service alerts", scope={"project": "six-week service pilot"}, time={"start": "2025", "end": "2025"})),
    claim("escalated three to the SRE team during the six-week service pilot", p("candidate", "alert_escalation", "service alerts to SRE team", scope={"project": "six-week service pilot"}, time={"start": "2025", "end": "2025"}, measure=m("count", "alert", 3, 3))),
], "pass", "Eighteen actual triages support occurrence without a number; the source separately records three escalations to SRE in the same pilot.")

add(5, [
    [p("candidate", "caption_accuracy_testing", "recorded interview captions", scope={"project": "2025 accessibility pilot", "mode": "recorded"}, time={"year": "2025"}),
     p("candidate", "live_captions", "live interview caption operation", polarity="negative", scope={"event": "live_interview"})],
    [p("role", "live_captions", "customer interview caption operation", modality="requirement", scope={"event": "live_customer_interview"})],
], [
    claim("Mara's recorded-caption QA experience is transferable to live-caption operation", p("candidate", "fit_relevance", "live-caption operation", modality="record_assessment", epistemic_scope="packet", scope={"source_activity": "recorded_caption_accuracy_testing", "target_activity": "live_customer_interview_caption_operation"})),
], "needs_review", "Recorded caption accuracy testing may share some skills with live operation, but the record explicitly excludes live interview operation. The degree of transferability is a judgment the sources do not settle.")

add(6, [
    [p("candidate", "remote_work", "work_location", modality="permission", scope={"employer": "former_employer"}, time={"year": "2023"}, measure=m("frequency", "day", 3, 3, "week")),
     p("candidate", "employment", "former_employer", polarity="negative", time={"start": "2024-01"})],
    [p("role", "station_attendance", "office", modality="requirement", scope={"weekday": "Monday–Friday", "status": "current"}, measure=m("frequency", "day", 5, 5, "week")),
     p("role", "remote_work", "work_location", polarity="negative", modality="permission", scope={"status": "current"}, measure=m("frequency", "day", 0, 0, "week"))],
], [
    claim("This role currently permits Mara to work remotely three days a week", p("role", "remote_work", "work_location", modality="permission", scope={"status": "current"}, measure=m("frequency", "day", 3, 3, "week"))),
], "fail", "The former employer's 2023 permission ended with that job. This role explicitly permits zero remote days and requires all five weekdays in the office.", (1,))

add(7, [[
    p("candidate", "ocr_method", "scan indexing review", scope={"project": "pilot"}, time={"start": "2025-06", "end": "2025-08"}),
    p("candidate", "training_certification", "OCR training certificate", polarity="negative"),
]], [
    claim("Mara has OCR indexing experience", p("candidate", "ocr_method", "scan indexing review", scope={"project": "pilot"}, time={"start": "2025-06", "end": "2025-08"})),
    claim("no OCR training certificate", p("candidate", "training_certification", "OCR training certificate", polarity="negative")),
], "pass", "The pilot records OCR scan review for indexing, and the same source expressly says she has not earned the certificate.")

add(8, [
    [p("candidate", "vendor_cutover_coordination", "vendor cutovers", scope={"project": "2025 pilot", "condition": "engineering_signoff"}, time={"year": "2025"}, measure=m("count", "cutover", 3, 3))],
    [p("role", "vendor_cutover_coordination", "vendor cutovers", modality="requirement")],
], [
    claim("Mara coordinated three vendor cutovers under engineering signoff", p("candidate", "vendor_cutover_coordination", "vendor cutovers", scope={"project": "2025 pilot", "condition": "engineering_signoff"}, time={"year": "2025"}, measure=m("count", "cutover", 3, 3))),
    claim("the role requires cutover coordination", p("role", "vendor_cutover_coordination", "vendor cutovers", modality="requirement")),
], "pass", "The candidate source records three cutovers with engineering signoff, and the role expressly asks for vendor cutover coordination. The answer retains the signoff boundary.")

add(9, [[
    p("candidate", "course_completion", "internal security awareness course"),
    p("candidate", "training_certification", "CISSP certification", polarity="negative"),
], [p("role", "training_certification", "CISSP certification", modality="requirement")]], [
    claim("Mara holds the CISSP certification", p("candidate", "training_certification", "CISSP certification")),
    claim("required by the role", p("role", "training_certification", "CISSP certification", modality="requirement")),
], "fail", "Course completion does not confer CISSP certification, and the candidate source explicitly says Mara has not earned it. The role requirement is accurately stated.", (1,))

add(10, [
    [p("candidate", "alert_escalation", "severity-one service alerts", scope={"project": "2025 service pilot", "recipient": "incident_lead"}, time={"year": "2025"}, measure=m("count", "alert", 2, 2)),
     p("incident lead", "evaluation_authority", "final incident decisions", scope={"project": "2025 service pilot"}, time={"year": "2025"})],
    [p("role", "alert_escalation", "service incidents", modality="requirement")],
], [
    claim("Mara escalated two severity-one alerts to an incident lead during the pilot", p("candidate", "alert_escalation", "severity-one service alerts", scope={"project": "2025 service pilot", "recipient": "incident_lead"}, time={"year": "2025"}, measure=m("count", "alert", 2, 2))),
    claim("the lead made final decisions", p("incident lead", "evaluation_authority", "final incident decisions", scope={"project": "2025 service pilot"}, time={"year": "2025"})),
    claim("The role requires incident escalation experience", p("role", "alert_escalation", "service incidents", modality="requirement")),
], "pass", "Mara performed two severity-one escalations, while decision authority remained with the incident lead. The role asks for escalation experience, not final incident ownership.")

add(11, [
    [p("candidate", "kubernetes_use", "Kubernetes", scope={"environment": "personal_lab", "only": True}, measure=m("count", "week", 4, 4)),
     p("candidate", "kubernetes_use", "Kubernetes", polarity="negative", scope={"environment": "production"})],
    [p("role", "kubernetes_use", "production Kubernetes experience", polarity="negative", modality="requirement", scope={"environment": "production"})],
], [
    claim("The role does not require production Kubernetes experience", p("role", "kubernetes_use", "production Kubernetes experience", polarity="negative", modality="requirement", scope={"environment": "production"})),
    claim("Mara has only used it in a personal lab", p("candidate", "kubernetes_use", "Kubernetes", scope={"environment": "personal_lab", "only": True})),
], "pass", "The role explicitly waives production experience. Mara's record states four weeks of lab use and explicitly excludes production operation.")

add(12, [[
    p("candidate", "archive_processing", "legal archive boxes", scope={"archive_total": 5}, time={"end": "2025-09"}, measure=m("count", "box", 2, 2)),
    p("candidate", "archive_processing", "remaining legal archive boxes", polarity="negative", scope={"archive_total": 5}, time={"end": "2025-09"}, measure=m("count", "box", 3, 3)),
]], [
    claim("Mara processed all five boxes in the legal archive by September 2025", p("candidate", "archive_processing", "legal archive boxes", scope={"archive_total": 5}, time={"end": "2025-09"}, measure=m("count", "box", 5, 5))),
], "fail", "The complete five-box inventory has only two processed boxes; the source explicitly says three remained unprocessed by that date.", (1,))

add(13, [
    [p("candidate", "plan_drafting", "API migration plan", scope={"project": "2025 pilot", "contribution": "personal"}, time={"year": "2025"})],
    [p("candidate", "plan_review", "API migration plan", scope={"project": "2025 pilot"}, time={"year": "2025"}),
     p("candidate", "plan_drafting", "API migration plan", polarity="negative", scope={"project": "2025 pilot", "contribution": "personal"}, time={"year": "2025"}),
     p("Jo", "plan_drafting", "API migration plan", scope={"project": "2025 pilot"}, time={"year": "2025"})],
], [
    claim("Mara drafted the API migration plan for the 2025 pilot", p("candidate", "plan_drafting", "API migration plan", scope={"project": "2025 pilot", "contribution": "personal"}, time={"year": "2025"})),
], "needs_review", "Two active candidate records of equal status directly disagree about authorship. One attributes the draft to Mara; the other says Jo wrote it and Mara only reviewed it. The inventory does not resolve which is correct.")

add(14, [
    [p("candidate", "guide_writing", "bilingual French/English client onboarding guides", scope={"languages": "French,English", "medium": "written"}, measure=m("count", "guide", 3, 3)),
     p("candidate", "client_onboarding", "live client sessions", polarity="negative", scope={"languages": "French,English", "medium": "live"})],
    [p("role", "guide_writing", "bilingual written onboarding guides", modality="requirement", scope={"medium": "written"})],
], [
    claim("Mara wrote three bilingual French/English onboarding guides", p("candidate", "guide_writing", "bilingual French/English client onboarding guides", scope={"languages": "French,English", "medium": "written"}, measure=m("count", "guide", 3, 3))),
    claim("the role requires bilingual written onboarding guides", p("role", "guide_writing", "bilingual written onboarding guides", modality="requirement", scope={"medium": "written"})),
], "pass", "Mara authored three written guides in both named languages, matching the written-guide requirement. The answer does not imply live bilingual onboarding, which her record excludes.")

add(15, [[
    p("candidate", "ticket_tagging", "support tickets", scope={"team_size": 6}),
    p("team", "triage_time_reduction", "mean triage time", modality="observation", scope={"team_size": 6, "period": "that_quarter"}, measure=m("rate", "percent", 30, 30)),
    p("report", "individual_attribution", "triage time reduction", polarity="negative", modality="observation", scope={"period": "that_quarter"}),
]], [
    claim("Mara cut mean triage time by 30% that quarter", p("candidate", "triage_time_reduction", "mean triage time", scope={"period": "that_quarter"}, measure=m("rate", "percent", 30, 30))),
], "fail", "The 30% outcome belongs to the team; Mara's recorded contribution is ticket tagging, and the report gives no individual share of the reduction.", (1,))

add(16, [
    [p("candidate", "rollback_plan_writing", "internal pilot deployment rollback plans", scope={"environment": "internal_pilot"}, measure=m("count", "plan", 3, 3)),
     p("candidate", "rollback_plan_use", "internal pilot rollback plans", polarity="negative", scope={"environment": "production"})],
    [p("role", "rollback_plan_documentation", "deployment rollback plans", modality="requirement")],
], [
    claim("Mara has written rollback plans for three internal pilots", p("candidate", "rollback_plan_writing", "internal pilot deployment rollback plans", scope={"environment": "internal_pilot"}, measure=m("count", "plan", 3, 3))),
    claim("The role requires rollback-plan documentation", p("role", "rollback_plan_documentation", "deployment rollback plans", modality="requirement")),
], "pass", "The candidate source explicitly documents three internal pilot rollback plans. The role requires documenting such plans; the answer does not claim production use.")

add(17, [
    [p("candidate", "training_certification", "data privacy certification", time={"year": "2025", "month": "05"})],
    [p("candidate", "course_completion", "vendor data privacy course", time={"year": "2025", "month": "05"}),
     p("candidate", "certification_exam", "data privacy exam", polarity="negative")],
], [
    claim("Mara completed the data privacy course in May 2025", p("candidate", "course_completion", "vendor data privacy course", time={"year": "2025", "month": "05"})),
    claim("she did not take the certification exam", p("candidate", "certification_exam", "data privacy exam", polarity="negative")),
], "pass", "The active correction confirms course completion in May 2025 and no certification exam. The old certification draft is withdrawn.")

add(18, [[
    p("candidate", "sql_query", "synthetic data", scope={"environment": "sandbox", "data_type": "synthetic"}),
    p("candidate", "sql_query", "production customer database", polarity="negative", scope={"environment": "production", "data_type": "customer"}),
], [p("role", "sql_query", "production customer database", modality="requirement", scope={"environment": "production", "data_type": "customer"})]], [
    claim("Mara has queried production customer databases with SQL", p("candidate", "sql_query", "production customer database", scope={"environment": "production", "data_type": "customer"})),
    claim("as the role requires", p("role", "sql_query", "production customer database", modality="requirement", scope={"environment": "production", "data_type": "customer"})),
], "fail", "Sandbox SQL on synthetic data is not production customer database work, and the candidate source explicitly denies the latter. The role requirement is correctly stated.", (1,))

add(19, [
    [p("candidate", "client_onboarding", "French-language sessions", scope={"language": "French"}, time={"year": "2025"}, measure=m("count", "session", 2, 2)),
     p("candidate", "client_onboarding", "English-language sessions", scope={"language": "English"}, time={"year": "2025"}, measure=m("count", "session", 2, 2)),
     p("candidate", "client_onboarding", "bilingual client onboarding", time={"year": "2025"})],
    [p("role", "client_onboarding", "bilingual client onboarding", modality="requirement")],
], [
    claim("Mara has handled onboarding in both French and English", p("candidate", "client_onboarding", "bilingual client onboarding", time={"year": "2025"})),
    claim("the role requires bilingual onboarding", p("role", "client_onboarding", "bilingual client onboarding", modality="requirement")),
], "pass", "Two actual sessions in each language support the stated bilingual onboarding experience, and the role explicitly requires bilingual client onboarding.")

add(20, [
    [p("candidate", "runbook_writing", "pilot runbook", scope={"project": "one-month pilot"}),
     p("candidate", "operator_training", "pilot runbook", scope={"project": "one-month pilot"}, measure=m("count", "operator", 3, 3)),
     p("candidate", "runbook_use", "pilot runbook", polarity="negative", scope={"environment": "production"})],
    [p("role", "runbook_writing", "runbook", modality="requirement"),
     p("role", "operator_training", "operators", modality="requirement")],
], [
    claim("Mara wrote a pilot runbook", p("candidate", "runbook_writing", "pilot runbook", scope={"project": "one-month pilot"})),
    claim("trained three operators on it", p("candidate", "operator_training", "pilot runbook", scope={"project": "one-month pilot"}, measure=m("count", "operator", 3, 3))),
    claim("the role calls for runbook writing", p("role", "runbook_writing", "runbook", modality="requirement")),
    claim("operator training", p("role", "operator_training", "operators", modality="requirement")),
], "pass", "Mara's pilot runbook and training of three operators are explicitly documented. The role separately calls for both activities; the answer does not imply production deployment.")


if __name__ == "__main__":
    write("raw", "maguire-v5-new-raw", [
        {"case_id": f"CF5H-{i:02d}", "title": title, "decision_at": DECISION, "sources": sources, "answer": {"text": answer}}
        for i, (title, sources, answer) in enumerate(RAW, 1)
    ])
    if "--raw-only" not in sys.argv:
        assert set(NORMAL) == set(GOLD) == set(range(1, 21))
        write("normalized", "maguire-v5-new-normalized", [NORMAL[i] for i in range(1, 21)])
        write("gold", "maguire-v5-new-gold", [GOLD[i] for i in range(1, 21)])
