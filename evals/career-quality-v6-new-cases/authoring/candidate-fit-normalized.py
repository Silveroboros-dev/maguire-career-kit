"""Manual proposition annotations for the authored candidate-fit raw cohort."""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]


def m(kind, unit, lower=None, upper=None, per=None):
    return {"kind": kind, "unit": unit, "lower": lower, "upper": upper, "per": per}


def p(subject, predicate, object, *, scope=None, time=None, measure=None,
      modality="observation", polarity="positive", epistemic_scope="world"):
    return {"subject": subject, "predicate": predicate, "object": object,
            "polarity": polarity, "modality": modality,
            "epistemic_scope": epistemic_scope, "scope": scope or {},
            "time": time or {}, "measure": measure}


def s(number, *facts):
    return {"id": f"s{number}", "facts": list(facts)}


def c(number, quote, *readings, stance="asserted"):
    return {"id": f"c{number}", "quote": quote, "stance": stance,
            "readings": list(readings), "check": None}


def row(number, sources, claims):
    return {"case_id": f"CF6H-{number:02d}", "sources": sources, "claims": claims}


rows = [
    row(1, [
        s(1, p("candidate", "incident_review_facilitation", "museum systems team", scope={"contribution": "personal"}, time={"year": 2025, "month": "2025-05"}, measure=m("count", "review", 3, 3))),
        s(2, p("operations analyst role", "incident_review_facilitation", "incident reviews", modality="requirement"))], [
        c(1, "I personally facilitated three incident reviews for the museum systems team in May 2025", p("candidate", "incident_review_facilitation", "museum systems team", scope={"contribution": "personal"}, time={"year": 2025, "month": "2025-05"}, measure=m("count", "review", 3, 3))),
        c(2, "The role requires incident review facilitation", p("operations analyst role", "incident_review_facilitation", "incident reviews", modality="requirement"))]),
    row(2, [
        s(1, p("support team", "triage_time_reduction", "median alert triage time", time={"year": 2025}, measure=m("rate", "percent", 20, 20)),
          p("record", "personal_attribution", "triage time reduction", polarity="negative", modality="record_assessment", time={"year": 2025})),
        s(2, p("candidate", "runbook_writing", "team alert runbook", scope={"contribution": "personal"}, time={"year": 2025}))], [
        c(1, "I wrote the alert runbook in 2025", p("candidate", "runbook_writing", "team alert runbook", scope={"contribution": "personal"}, time={"year": 2025})),
        c(2, "personally reduced median alert triage time by 20%", p("candidate", "triage_time_reduction", "median alert triage time", scope={"contribution": "personal"}, time={"year": 2025}, measure=m("rate", "percent", 20, 20)))]),
    row(3, [
        s(1, p("candidate", "course_completion", "accessibility testing course", time={"month": "2025-03"})),
        s(2, p("candidate", "guide_writing", "internal accessibility testing guide", scope={"audience": "internal"}, time={"month": "2025-04"})),
        s(3, p("quality analyst role", "accessibility_documentation", "accessibility testing documentation", modality="requirement"))], [
        c(1, "I completed an accessibility testing course in March 2025", p("candidate", "course_completion", "accessibility testing course", time={"month": "2025-03"})),
        c(2, "wrote an internal accessibility testing guide in April 2025", p("candidate", "guide_writing", "internal accessibility testing guide", scope={"audience": "internal"}, time={"month": "2025-04"}))]),
    row(4, [
        s(1, p("candidate", "sql_query", "inventory dataset", scope={"environment": "sandbox"}, time={"month": "2025-06"})),
        s(2, p("data coordinator role", "sql_query", "SQL query experience", modality="requirement"))], [
        c(1, "I ran SQL queries against a sandbox inventory dataset in June 2025", p("candidate", "sql_query", "inventory dataset", scope={"environment": "sandbox"}, time={"month": "2025-06"})),
        c(2, "The role asks for SQL query experience", p("data coordinator role", "sql_query", "SQL query experience", modality="requirement"))]),
    row(5, [
        s(1, p("candidate", "client_onboarding", "two calls", scope={"activity": "shadowing"}, time={"year": 2025}, measure=m("count", "call", 2, 2)),
          p("candidate", "handoff_recording", "subsequent notes", time={"year": 2025})),
        s(2, p("client success lead role", "client_onboarding", "onboarding calls", scope={"activity": "independent_leadership"}, modality="requirement"))], [
        c(1, "I shadowed two client onboarding calls", p("candidate", "client_onboarding", "two calls", scope={"activity": "shadowing"}, time={"year": 2025}, measure=m("count", "call", 2, 2))),
        c(2, "authored their handoff notes", p("candidate", "handoff_recording", "subsequent notes", time={"year": 2025})),
        c(3, "That experience may be relevant to leading onboarding calls independently", p("candidate", "fit_relevance", "leading onboarding calls independently", scope={"basis": "shadowing_and_handoff_notes"}, modality="possibility", epistemic_scope="packet"))]),
    row(6, [
        s(1, p("candidate", "course_completion", "rail-safety operator course", time={"year": 2024})),
        s(2, p("candidate", "certification_exam", "rail-safety operator exam", scope={"result": "passed"}, time={"year": 2024})),
        s(3, p("rail operations role", "training_certification", "course and exam", modality="requirement"))], [
        c(1, "I completed the rail-safety operator course", p("candidate", "course_completion", "rail-safety operator course", time={"year": 2024})),
        c(2, "passed its certification exam in 2024", p("candidate", "certification_exam", "rail-safety operator exam", scope={"result": "passed"}, time={"year": 2024}))]),
    row(7, [
        s(1, p("candidate", "demo_presentation", "product demo", scope={"venue": "team meeting"}, time={"month": "2025-06"}, measure=m("count", "demo", 1, 1), modality="permission"),
          p("record", "delivered_demo_evidence", "team product demo", polarity="negative", modality="record_assessment", time={"month": "2025-06"})),
        s(2, p("product trainer role", "demo_presentation", "delivered demos", modality="requirement"))], [
        c(1, "I was permitted to present a product demo in June 2025", p("candidate", "demo_presentation", "product demo", scope={"venue": "team meeting"}, time={"month": "2025-06"}, measure=m("count", "demo", 1, 1), modality="permission")),
        c(2, "delivered that demo to the team", p("candidate", "demo_presentation", "product demo", scope={"venue": "team meeting"}, time={"month": "2025-06"}, measure=m("count", "demo", 1, 1)))]),
    row(8, [
        s(1, p("candidate", "archive_processing", "archive records", scope={"method": "manual", "project": "catalog migration"}, time={"year": 2025}, measure=m("count", "record", 150, 150))),
        s(2, p("archivist role", "archive_processing", "archive records", modality="requirement"))], [
        c(1, "I manually processed 150 archive records during the 2025 catalog migration", p("candidate", "archive_processing", "archive records", scope={"method": "manual", "project": "catalog migration"}, time={"year": 2025}, measure=m("count", "record", 150, 150))),
        c(2, "The role requires archive processing experience", p("archivist role", "archive_processing", "archive records", modality="requirement"))]),
    row(9, [
        s(1, p("candidate", "rollback_plan_writing", "East Depot vendor cutover", time={"year": 2025})),
        s(2, p("candidate", "cutover_observation", "East Depot vendor cutover", time={"year": 2025}),
          p("candidate", "vendor_cutover_coordination", "East Depot vendor cutover", polarity="negative", time={"year": 2025}))], [
        c(1, "I wrote the rollback plan for the East Depot vendor cutover", p("candidate", "rollback_plan_writing", "East Depot vendor cutover", time={"year": 2025})),
        c(2, "observed the cutover in 2025", p("candidate", "cutover_observation", "East Depot vendor cutover", time={"year": 2025}))]),
    row(10, [
        s(1, p("candidate", "kubernetes_use", "practice service deployment", scope={"environment": "sandbox"}, time={"year": 2023})),
        s(2, p("infrastructure role", "kubernetes_use", "Kubernetes", scope={"environment": "production"}, modality="requirement"))], [
        c(1, "I used Kubernetes in production in 2023 to deploy a service", p("candidate", "kubernetes_use", "service deployment", scope={"environment": "production"}, time={"year": 2023}))]),
    row(11, [
        s(1, p("candidate and colleague", "operator_training", "depot operators on new intake form", scope={"contribution": "joint"}, time={"month": "2025-07"})),
        s(2, p("operations educator role", "operator_training", "operators", modality="requirement"))], [
        c(1, "I jointly trained depot operators on the new intake form in July 2025", p("candidate and colleague", "operator_training", "depot operators on new intake form", scope={"contribution": "joint"}, time={"month": "2025-07"}))]),
    row(12, [
        s(1, p("candidate", "sql_query", "monthly warehouse reports", scope={"frequency": "monthly"}, time={"start": "2022-01", "end": "2024-04"})),
        s(2, p("reporting specialist role", "sql_query", "previous SQL query work", modality="requirement"))], [
        c(1, "I used SQL queries for monthly warehouse reports from January 2022 through April 2024", p("candidate", "sql_query", "monthly warehouse reports", scope={"frequency": "monthly"}, time={"start": "2022-01", "end": "2024-04"}))]),
    row(13, [
        s(1, p("draft", "authorship_attribution", "candidate wrote public incident response guide", scope={"audience": "public"}, modality="record_assessment", epistemic_scope="packet"),
          p("draft", "author_field_accuracy", "public incident response guide", polarity="negative", modality="record_assessment")),
        s(2, p("candidate", "plan_review", "internal incident response plan", scope={"audience": "internal"}, time={"year": 2025}))], [
        c(1, "I reviewed an internal incident response plan in 2025", p("candidate", "plan_review", "internal incident response plan", scope={"audience": "internal"}, time={"year": 2025})),
        c(2, "wrote the public incident response guide", p("candidate", "guide_writing", "public incident response guide", scope={"audience": "public"}))]),
    row(14, [
        s(1, p("candidate", "alert_triage", "incoming alerts", scope={"phase": "pilot"}, time={"year": 2025}),
          p("candidate", "alert_escalation", "severe alerts to duty engineer", scope={"phase": "pilot"}, time={"year": 2025})),
        s(2, p("monitoring role", "alert_triage", "alerts", modality="requirement"),
          p("monitoring role", "alert_escalation", "alerts", modality="requirement"))], [
        c(1, "During the 2025 pilot, I triaged incoming alerts", p("candidate", "alert_triage", "incoming alerts", scope={"phase": "pilot"}, time={"year": 2025})),
        c(2, "escalated severe ones to the duty engineer", p("candidate", "alert_escalation", "severe alerts to duty engineer", scope={"phase": "pilot"}, time={"year": 2025}))]),
    row(15, [
        s(1, p("candidate", "training_demo", "internal staff", scope={"audience": "internal"}, time={"year": 2025})),
        s(2, p("solutions consultant role", "demo_presentation", "customer-facing product demos", scope={"audience": "customer"}, modality="requirement"))], [
        c(1, "I presented a training demo to internal staff in 2025", p("candidate", "training_demo", "internal staff", scope={"audience": "internal"}, time={"year": 2025})),
        c(2, "That practice could prepare me for customer-facing product demos", p("candidate", "fit_relevance", "customer-facing product demos", scope={"basis": "internal_training_demo"}, modality="possibility", epistemic_scope="packet"))]),
    row(16, [
        s(1, p("candidate", "certification_exam", "flood-response exam", scope={"result": "passed"}, time={"month": "2025-08"})),
        s(2, p("candidate", "certificate_status", "flood-response certificate", scope={"status": "pending"}, time={"month": "2025-09"}),
          p("issuing body", "certificate_issuance", "candidate flood-response certificate", polarity="negative", time={"month": "2025-09"}))], [
        c(1, "I passed the flood-response certification exam in August 2025", p("candidate", "certification_exam", "flood-response exam", scope={"result": "passed"}, time={"month": "2025-08"})),
        c(2, "my certificate was still pending in September 2025", p("candidate", "certificate_status", "flood-response certificate", scope={"status": "pending"}, time={"month": "2025-09"}))]),
    row(17, [
        s(1, p("candidate", "checklist_documentation", "vendor cutover checklist", time={"year": 2025})),
        s(2, p("procurement team", "vendor_cutover_coordination", "vendor cutover", time={"year": 2025}),
          p("record", "personal_attribution", "vendor cutover coordination", polarity="negative", modality="record_assessment", time={"year": 2025}))], [
        c(1, "I documented the vendor cutover checklist", p("candidate", "checklist_documentation", "vendor cutover checklist", time={"year": 2025})),
        c(2, "coordinated the vendor cutover in 2025", p("candidate", "vendor_cutover_coordination", "vendor cutover", time={"year": 2025}))]),
    row(18, [
        s(1, p("candidate", "tool_building", "intake tool", scope={"phase": "internal pilot", "duration": "three weeks"}, time={"year": 2025}),
          p("intake tool", "pilot_use", "staff", scope={"phase": "internal pilot", "duration": "three weeks"}, time={"year": 2025}, measure=m("count", "staff", 30, 30))),
        s(2, p("service designer role", "internal_tool_delivery", "internal tool", modality="requirement"))], [
        c(1, "I built an intake tool used by 30 staff in a three-week internal pilot in 2025", p("candidate", "tool_building", "intake tool", scope={"phase": "internal pilot", "duration": "three weeks"}, time={"year": 2025}),
          p("intake tool", "pilot_use", "staff", scope={"phase": "internal pilot", "duration": "three weeks"}, time={"year": 2025}, measure=m("count", "staff", 30, 30)))]),
    row(19, [
        s(1, p("candidate", "guide_writing", "operator guides", time={"year": 2024}, measure=m("count", "guide", 2, 2))),
        s(2, p("peer", "guide_review", "one operator guide", scope={"phase": "before publication"}, time={"year": 2024}, measure=m("count", "guide", 1, 1)))], [
        c(1, "I authored two operator guides in 2024", p("candidate", "guide_writing", "operator guides", time={"year": 2024}, measure=m("count", "guide", 2, 2))),
        c(2, "a peer reviewed one before publication", p("peer", "guide_review", "one operator guide", scope={"phase": "before publication"}, time={"year": 2024}, measure=m("count", "guide", 1, 1)))]),
    row(20, [
        s(1, p("candidate", "incident_handling", "service incidents", scope={"contribution": "personal"}, time={"year": 2024}, measure=m("count", "incident", 12, 12))),
        s(2, p("service team", "incident_handling", "service incidents", time={"year": 2025}, measure=m("count", "incident", 18, 18)),
          p("record", "personal_attribution", "2025 service incidents", polarity="negative", modality="record_assessment", time={"year": 2025}))], [
        c(1, "I personally handled 12 service incidents in 2024", p("candidate", "incident_handling", "service incidents", scope={"contribution": "personal"}, time={"year": 2024}, measure=m("count", "incident", 12, 12))),
        c(2, "personally handled 18 service incidents in 2025", p("candidate", "incident_handling", "service incidents", scope={"contribution": "personal"}, time={"year": 2025}, measure=m("count", "incident", 18, 18)))]),
]

payload = {"schema": "maguire-v6-new-normalized", "family": "candidate-fit",
           "human_approved": False, "exposure": {"checker_code_seen": False,
           "previous_cases_seen": False, "predictions_seen": False}, "rows": rows}
out = BASE / "normalized/candidate-fit.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
