"""Hand-authored fictional preference-fit fixtures; stdlib only."""

import json
from pathlib import Path


BASE = Path(__file__).resolve().parent.parent
STAMP = "2026-10-12T09:00:00Z"
DECISION = "2026-10-12T12:00:00Z"


def source(sid, text, kind, status="active", at=STAMP):
    return {"id": sid, "text": text, "kind": kind, "status": status, "observed_at": at}


def row(number, title, sources, answer):
    return {"case_id": f"PF6H-{number:02d}", "title": title,
            "decision_at": DECISION, "sources": sources, "answer": {"text": answer}}


RAW = [
    row(1, "Remote after an induction week", [
        source("p1", "I accept one mandatory induction week on site, then remote work if the employer grants security clearance.", "preference"),
        source("e1", "The role requires five station days in its first induction week. After that week, remote work is permitted when security clearance is granted.", "job_description")],
        "The five station days fit my one-week induction limit. Remote work after induction is permitted if I get security clearance."),
    row(2, "Annual learning allowance below floor", [
        source("p1", "I need a learning allowance of at least EUR 1,800 per calendar year.", "preference"),
        source("e1", "The employer offers a learning allowance of EUR 1,200 per calendar year for this role.", "job_description")],
        "The role offers EUR 1,200 of annual learning allowance. That meets my EUR 1,800 annual minimum."),
    row(3, "Saturday-only call rota", [
        source("p1", "I cannot take on-call duty on any weekday, Monday through Friday.", "preference"),
        source("e1", "For this role, the only required on-call shift is Saturday 10:00–14:00, in the role's local time zone; there are no other on-call shifts.", "job_description")],
        "The required on-call rota is Saturday 10:00–14:00 only, so it does not use a weekday I have ruled out."),
    row(4, "Office access is optional", [
        source("p1", "I want no mandatory office attendance after onboarding, although I may visit voluntarily.", "preference"),
        source("e1", "After onboarding, this role has no required office days. The office remains available for voluntary visits.", "employer_update")],
        "After onboarding there are no mandatory office days. Voluntary office visits remain possible."),
    row(5, "Competing active attendance terms", [
        source("p1", "My limit is one required station day per week after onboarding.", "preference"),
        source("e1", "The role description requires one station day per week after onboarding.", "job_description", at="2026-09-20T09:00:00Z"),
        source("e2", "A recruiting note says the team requires two station days per week after onboarding. It does not state whether the role description has been replaced.", "employer_update", at="2026-10-10T09:00:00Z")],
        "The one-day role description appears to match my limit, but the later two-day note leaves the current attendance rule unresolved."),
    row(6, "Withdrawn transport allowance", [
        source("p1", "I require an active transport stipend of at least CHF 90 per calendar month.", "preference"),
        source("e1", "An early draft offered a CHF 120 transport stipend per calendar month.", "employer_update", status="withdrawn", at="2026-09-15T09:00:00Z"),
        source("e2", "The current offer lists no transport stipend; the earlier draft was withdrawn.", "employer_update")],
        "The early draft listed CHF 120 a month. The current offer therefore meets my transport-stipend requirement."),
    row(7, "Tuesday demo ends before cutoff", [
        source("p1", "I cannot present a required training demo after 16:00 on Tuesday in the role's local time zone.", "preference"),
        source("e1", "The only required training demo is Tuesday 14:30–16:00 in the role's local time zone; no other demo slot is required.", "job_description")],
        "The required Tuesday training demo ends at 16:00, within my Tuesday cutoff."),
    row(8, "Annual budget equivalent to monthly floor", [
        source("p1", "I need a learning budget equivalent to at least EUR 200 per calendar month; an annual budget is acceptable.", "preference"),
        source("e1", "The role's learning budget is EUR 2,400 per calendar year. The employer has not specified when reimbursements are paid.", "job_description")],
        "The EUR 2,400 annual learning budget equals my EUR 200 monthly budget floor. Its reimbursement schedule is unspecified."),
    row(9, "Pending captions procurement", [
        source("p1", "I require live captions for team meetings from my first day.", "preference"),
        source("e1", "Live captions for team meetings are in procurement review. The employer has not approved an activation date or promised availability on the first day.", "employer_update")],
        "Live captions are in procurement review. They are guaranteed to be available for my first-day team meetings."),
    row(10, "Travel pause in first quarter", [
        source("p1", "I cannot take required business travel in my first calendar quarter in the role.", "preference"),
        source("e1", "The role requires no business travel in the employee's first calendar quarter. Travel may be requested later.", "job_description")],
        "The first calendar quarter has no required business travel, which fits my first-quarter travel restriction. Later travel remains possible."),
    row(11, "Two required days misreported as one", [
        source("p1", "After onboarding I can attend the station at most one day per week.", "preference"),
        source("e1", "After onboarding, the role requires two station days every week.", "job_description")],
        "The role requires one station day each week after onboarding. That fits my one-day weekly cap."),
    row(12, "Four-day work pattern", [
        source("p1", "I prefer a four-day workweek with Friday free.", "preference"),
        source("e1", "The written offer sets Monday through Thursday as working days and Friday as a nonworking day each week.", "employer_update")],
        "The written offer sets a four-day, Monday–Thursday week. Friday is free, as I prefer."),
    row(13, "Remote option subject to approval", [
        source("p1", "I need remote work on Wednesdays after onboarding.", "preference"),
        source("e1", "The team may approve remote work on Wednesdays after onboarding case by case. No approval decision has been made for this candidate.", "employer_update")],
        "Wednesday remote work after onboarding looks feasible for me, subject to a manager's decision."),
    row(14, "Specified transport stipend", [
        source("p1", "I need a transport stipend of at least CHF 80 per calendar month.", "preference"),
        source("e1", "The written offer includes a CHF 100 transport stipend per calendar month, effective from the first month.", "employer_update")],
        "The written offer includes CHF 100 monthly for transport from month one. That exceeds my CHF 80 monthly floor."),
    row(15, "Required travel exceeds cap", [
        source("p1", "I can make at most two required overnight trips per calendar month.", "preference"),
        source("e1", "The role requires three overnight trips in each calendar month.", "job_description")],
        "The role requires three overnight trips monthly. This stays within my two-trip monthly limit."),
    row(16, "Conditional remote schedule", [
        source("p1", "I accept up to two required station days per week during onboarding. After onboarding, I accept remote work when client data clearance is granted.", "preference"),
        source("e1", "During onboarding the role requires two station days per week. After onboarding, remote work is permitted when client data clearance is granted.", "job_description")],
        "Two required station days during onboarding fit my cap. After onboarding, remote work is permitted on the clearance condition I accept."),
    row(17, "Superseded schedule", [
        source("p1", "I can attend the office at most three days per week after onboarding.", "preference"),
        source("e1", "An older role term required three office days per week after onboarding.", "job_description", at="2026-09-01T09:00:00Z"),
        source("e2", "This update supersedes the older office-days term: four office days per week are now required after onboarding.", "employer_update")],
        "The older three-day term has been superseded. The current four-day requirement still fits my three-day weekly cap."),
    row(18, "No public demo requirement", [
        source("p1", "I do not want mandatory public demo presentations; internal team demos are acceptable.", "preference"),
        source("e1", "The role requires one internal team demo per month and has no mandatory public demos.", "job_description")],
        "The monthly internal team demo is acceptable to me. The role has no mandatory public demo."),
    row(19, "Weekend-protected support schedule", [
        source("p1", "I cannot provide on-call support on Saturdays or Sundays.", "preference"),
        source("e1", "The required support rota is Monday to Friday 09:00–17:00, role-local time, with no weekend on-call shifts.", "job_description")],
        "The required support rota is weekdays only. It leaves both weekend days free of on-call duty."),
    row(20, "Location restricted to one country", [
        source("p1", "I need to work remotely from Portugal after onboarding.", "preference"),
        source("e1", "The role permits remote work after onboarding from approved EU locations. The employer has not listed which EU countries are approved for this role.", "employer_update")],
        "Portugal might be an approved remote-work location after onboarding, but that needs confirmation from the employer."),
]


if __name__ == "__main__":
    payload = {"schema": "maguire-v6-new-raw", "family": "preference-fit",
               "human_approved": False,
               "exposure": {"checker_code_seen": False, "previous_cases_seen": False,
                            "predictions_seen": False}, "rows": RAW}
    path = BASE / "raw" / "preference-fit.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
