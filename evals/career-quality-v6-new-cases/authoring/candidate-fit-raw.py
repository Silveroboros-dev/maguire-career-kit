"""Hand-authored, fictional candidate-fit raw cohort. No checker imports."""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
WHEN = "2026-10-12T12:00:00Z"


def src(number, text, kind="candidate_fact", status="active", observed="2026-10-01T12:00:00Z"):
    return {"id": f"s{number}", "text": text, "kind": kind,
            "status": status, "observed_at": observed}


def row(number, title, sources, answer):
    return {"case_id": f"CF6H-{number:02d}", "title": title,
            "decision_at": WHEN, "sources": sources, "answer": {"text": answer}}


rows = [
    row(1, "Incident review facilitation", [
        src(1, "The candidate personally facilitated three incident reviews for the museum systems team in May 2025."),
        src(2, "The operations analyst role requires incident review facilitation.", "job_description")],
        "I personally facilitated three incident reviews for the museum systems team in May 2025. The role requires incident review facilitation."),
    row(2, "Team result and personal runbook", [
        src(1, "The support team reduced median alert triage time by 20% in 2025; the record does not assign that reduction to an individual."),
        src(2, "The candidate personally wrote the team's alert runbook in 2025.")],
        "I wrote the alert runbook in 2025 and personally reduced median alert triage time by 20%."),
    row(3, "Accessibility preparation", [
        src(1, "The candidate completed an accessibility testing course in March 2025."),
        src(2, "The candidate wrote an internal accessibility testing guide in April 2025."),
        src(3, "The quality analyst role asks for accessibility testing documentation.", "job_description")],
        "I completed an accessibility testing course in March 2025 and wrote an internal accessibility testing guide in April 2025."),
    row(4, "Scoped database practice", [
        src(1, "The candidate ran SQL queries against a sandbox inventory dataset in June 2025."),
        src(2, "The data coordinator role asks for SQL query experience.", "job_description")],
        "I ran SQL queries against a sandbox inventory dataset in June 2025. The role asks for SQL query experience."),
    row(5, "Onboarding transferability", [
        src(1, "The candidate shadowed two client onboarding calls in 2025 and authored the subsequent handoff notes."),
        src(2, "The client success lead role requires leading onboarding calls independently.", "job_description")],
        "I shadowed two client onboarding calls and authored their handoff notes. That experience may be relevant to leading onboarding calls independently."),
    row(6, "Exam and course completion", [
        src(1, "The candidate completed the rail-safety operator course in 2024."),
        src(2, "The candidate passed the associated certification exam in 2024."),
        src(3, "The rail operations role asks for the course and exam.", "job_description")],
        "I completed the rail-safety operator course and passed its certification exam in 2024."),
    row(7, "Permission versus delivery", [
        src(1, "The candidate was permitted to present one product demo at the June 2025 team meeting; no delivered demo is recorded."),
        src(2, "The product trainer role asks for delivered demos.", "job_description")],
        "I was permitted to present a product demo in June 2025 and delivered that demo to the team."),
    row(8, "Archive processing volume", [
        src(1, "The candidate manually processed 150 archive records during the 2025 catalog migration."),
        src(2, "The archivist role requires experience processing archive records.", "job_description")],
        "I manually processed 150 archive records during the 2025 catalog migration. The role requires archive processing experience."),
    row(9, "Cutover contributions", [
        src(1, "The candidate wrote the rollback plan for the East Depot vendor cutover in 2025."),
        src(2, "The candidate observed the East Depot cutover without coordinating the vendor.")],
        "I wrote the rollback plan for the East Depot vendor cutover and observed the cutover in 2025."),
    row(10, "Sandbox versus production", [
        src(1, "The candidate used Kubernetes to deploy a practice service in a sandbox in 2023."),
        src(2, "The infrastructure role requires production Kubernetes use.", "job_description")],
        "I used Kubernetes in production in 2023 to deploy a service."),
    row(11, "Shared operator training", [
        src(1, "The candidate and a colleague jointly trained depot operators on the new intake form in July 2025."),
        src(2, "The operations educator role asks for operator training.", "job_description")],
        "I jointly trained depot operators on the new intake form in July 2025."),
    row(12, "Dated query work", [
        src(1, "The candidate used SQL queries for monthly warehouse reports from January 2022 through April 2024."),
        src(2, "The reporting specialist role requires previous SQL query work.", "job_description")],
        "I used SQL queries for monthly warehouse reports from January 2022 through April 2024."),
    row(13, "Withdrawn guide draft", [
        src(1, "A draft says the candidate wrote a public incident response guide, but the draft was withdrawn after its author field was found to be incorrect.", status="withdrawn"),
        src(2, "The candidate reviewed an internal incident response plan in 2025.")],
        "I reviewed an internal incident response plan in 2025 and wrote the public incident response guide."),
    row(14, "Alert response and escalation", [
        src(1, "During a 2025 pilot, the candidate triaged incoming alerts and escalated severe ones to the duty engineer."),
        src(2, "The monitoring role requires alert triage and escalation.", "job_description")],
        "During the 2025 pilot, I triaged incoming alerts and escalated severe ones to the duty engineer."),
    row(15, "Internal demo relevance", [
        src(1, "The candidate presented a training demo to internal staff in 2025."),
        src(2, "The solutions consultant role requires customer-facing product demos.", "job_description")],
        "I presented a training demo to internal staff in 2025. That practice could prepare me for customer-facing product demos."),
    row(16, "Pending certificate distinction", [
        src(1, "The candidate passed the flood-response certification exam in August 2025."),
        src(2, "The issuing body marked the candidate's flood-response certificate as pending and had not yet issued it as of September 2025.")],
        "I passed the flood-response certification exam in August 2025; my certificate was still pending in September 2025."),
    row(17, "Documenter versus coordinator", [
        src(1, "The candidate documented the vendor cutover checklist in 2025."),
        src(2, "The procurement team coordinated the vendor cutover in 2025; the record does not assign coordination to the candidate.")],
        "I documented the vendor cutover checklist and coordinated the vendor cutover in 2025."),
    row(18, "Pilot tool delivery", [
        src(1, "The candidate built an intake tool used by 30 staff in a three-week internal pilot in 2025."),
        src(2, "The service designer role asks for internal tool delivery experience.", "job_description")],
        "I built an intake tool used by 30 staff in a three-week internal pilot in 2025."),
    row(19, "Guide authorship and review", [
        src(1, "The candidate authored two operator guides in 2024."),
        src(2, "A peer reviewed one of those operator guides before publication in 2024.")],
        "I authored two operator guides in 2024, and a peer reviewed one before publication."),
    row(20, "Later team incident count", [
        src(1, "The candidate personally handled 12 service incidents in 2024."),
        src(2, "The service team handled 18 service incidents in 2025; individual ownership is not recorded.")],
        "I personally handled 12 service incidents in 2024 and personally handled 18 service incidents in 2025."),
]

payload = {"schema": "maguire-v6-new-raw", "family": "candidate-fit",
           "human_approved": False, "exposure": {"checker_code_seen": False,
           "previous_cases_seen": False, "predictions_seen": False}, "rows": rows}
out = BASE / "raw/candidate-fit.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
