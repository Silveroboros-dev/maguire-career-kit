"""Manually transcribed propositions and semantic gold for fictional cases."""

import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent


def m(kind, unit, lower=None, upper=None, per=None):
    return {"kind": kind, "unit": unit, "lower": lower, "upper": upper, "per": per}


def p(subject, predicate, obj, *, polarity="positive", modality="observation",
      epistemic_scope="world", scope=None, time=None, measure=None):
    return {"subject": subject, "predicate": predicate, "object": obj,
            "polarity": polarity, "modality": modality,
            "epistemic_scope": epistemic_scope,
            "scope": scope or {}, "time": time or {}, "measure": measure}


def c(cid, quote, *readings, stance="asserted"):
    return {"id": cid, "quote": quote, "stance": stance,
            "readings": list(readings), "check": None}


def assessment(predicate, obj, *, polarity="positive", scope=None, time=None,
               modality="record_assessment"):
    return p("candidate", predicate, obj, polarity=polarity, modality=modality,
             epistemic_scope="packet", scope=scope, time=time)


N = [
    (1, {
        "p1": [p("candidate", "station_attendance", "first induction week", modality="preference_constraint", scope={"phase": "induction", "limit": "one week"}),
               p("candidate", "remote_work", "after induction", modality="preference_constraint", scope={"phase": "after_induction", "condition": "security clearance granted"})],
        "e1": [p("role", "station_attendance", "first induction week", modality="requirement", scope={"phase": "induction"}, measure=m("count", "day", 5, 5, "week")),
               p("role", "remote_work", "after induction", modality="permission", scope={"phase": "after_induction", "condition": "security clearance granted"})]}, [
        c("c1", "The five station days", p("role", "station_attendance", "first induction week", modality="requirement", scope={"phase": "induction"}, measure=m("count", "day", 5, 5, "week"))),
        c("c2", "fit my one-week induction limit.", assessment("station_attendance_fit", "first induction week", scope={"phase": "induction", "required_days": 5, "preference_limit": "one week"})),
        c("c3", "Remote work after induction is permitted if I get security clearance.", p("role", "remote_work", "after induction", modality="permission", scope={"phase": "after_induction", "condition": "security clearance granted"}))]),
    (2, {
        "p1": [p("candidate", "learning_allowance", "annual minimum", modality="preference_constraint", measure=m("amount", "EUR", 1800, None, "calendar_year"))],
        "e1": [p("role", "learning_allowance", "annual offer", modality="commitment", measure=m("amount", "EUR", 1200, 1200, "calendar_year"))]}, [
        c("c1", "The role offers EUR 1,200 of annual learning allowance.", p("role", "learning_allowance", "annual offer", modality="commitment", measure=m("amount", "EUR", 1200, 1200, "calendar_year"))),
        c("c2", "That meets my EUR 1,800 annual minimum.", assessment("learning_allowance_fit", "annual minimum", scope={"currency": "EUR", "period": "calendar_year", "offered": 1200, "minimum": 1800}))]),
    (3, {
        "p1": [p("candidate", "on_call", "Monday through Friday", polarity="negative", modality="preference_constraint", time={"weekday": "weekday"})],
        "e1": [p("role", "on_call", "Saturday shift", modality="requirement", scope={"only": True, "zone": "role_local"}, time={"weekday": "Saturday", "start_minute": 600, "end_minute": 840}),
               p("role", "on_call", "other shifts", polarity="negative", modality="requirement", scope={"only": True})]}, [
        c("c1", "The required on-call rota is Saturday 10:00–14:00 only", p("role", "on_call", "Saturday shift", modality="requirement", scope={"only": True, "zone": "role_local"}, time={"weekday": "Saturday", "start_minute": 600, "end_minute": 840})),
        c("c2", "it does not use a weekday I have ruled out.", assessment("on_call_fit", "weekday prohibition", scope={"only": True, "zone": "role_local"}, time={"weekday": "Saturday", "start_minute": 600, "end_minute": 840}))]),
    (4, {
        "p1": [p("candidate", "station_attendance", "mandatory office days", polarity="negative", modality="preference_constraint", time={"phase": "after_onboarding"}),
               p("candidate", "station_attendance", "voluntary office visits", modality="permission", time={"phase": "after_onboarding"})],
        "e1": [p("role", "station_attendance", "mandatory office days", polarity="negative", modality="requirement", time={"phase": "after_onboarding"}),
               p("role", "station_attendance", "voluntary office visits", modality="permission", time={"phase": "after_onboarding"})]}, [
        c("c1", "After onboarding there are no mandatory office days.", p("role", "station_attendance", "mandatory office days", polarity="negative", modality="requirement", time={"phase": "after_onboarding"})),
        c("c2", "Voluntary office visits remain possible.", p("role", "station_attendance", "voluntary office visits", modality="permission", time={"phase": "after_onboarding"}))]),
    (5, {
        "p1": [p("candidate", "station_attendance", "weekly cap", modality="preference_constraint", time={"phase": "after_onboarding"}, measure=m("count", "day", None, 1, "week"))],
        "e1": [p("role", "station_attendance", "weekly requirement", modality="requirement", time={"phase": "after_onboarding"}, measure=m("count", "day", 1, 1, "week"))],
        "e2": [p("role", "station_attendance", "weekly requirement", modality="requirement", time={"phase": "after_onboarding"}, measure=m("count", "day", 2, 2, "week")),
               p("recruiting note", "supersession_status", "not stated", modality="observation", scope={"target": "role description"})]}, [
        c("c1", "The one-day role description appears to match my limit", assessment("station_attendance_fit", "role description", scope={"source": "e1", "qualified": "appears"}, time={"phase": "after_onboarding"})),
        c("c2", "the later two-day note leaves the current attendance rule unresolved.", assessment("attendance_rule_resolution", "current rule", scope={"competing_sources": "e1,e2", "resolved": False}, time={"phase": "after_onboarding"}))]),
    (6, {
        "p1": [p("candidate", "stipend", "transport", modality="preference_constraint", scope={"status": "active", "category": "transport"}, measure=m("amount", "CHF", 90, None, "calendar_month"))],
        "e1": [p("role", "stipend", "transport", modality="commitment", scope={"draft": "early", "category": "transport"}, measure=m("amount", "CHF", 120, 120, "calendar_month"))],
        "e2": [p("role", "stipend", "transport", polarity="negative", modality="observation", scope={"status": "current", "category": "transport"}),
               p("employer", "withdraws", "early draft", modality="observation") ]}, [
        c("c1", "The early draft listed CHF 120 a month.", p("role", "stipend", "transport", modality="commitment", scope={"draft": "early", "category": "transport"}, measure=m("amount", "CHF", 120, 120, "calendar_month"))),
        c("c2", "The current offer therefore meets my transport-stipend requirement.", assessment("stipend_fit", "transport", scope={"status": "current", "category": "transport", "currency": "CHF", "minimum_monthly": 90}))]),
    (7, {
        "p1": [p("candidate", "training_demo", "presentation after 16:00", polarity="negative", modality="preference_constraint", scope={"zone": "role_local", "required": True}, time={"weekday": "Tuesday", "after_minute": 960})],
        "e1": [p("role", "training_demo", "presentation", modality="requirement", scope={"only": True, "zone": "role_local"}, time={"weekday": "Tuesday", "start_minute": 870, "end_minute": 960})]}, [
        c("c1", "The required Tuesday training demo ends at 16:00", p("role", "training_demo", "presentation", modality="requirement", scope={"only": True, "zone": "role_local"}, time={"weekday": "Tuesday", "start_minute": 870, "end_minute": 960})),
        c("c2", "within my Tuesday cutoff.", assessment("training_demo_schedule_fit", "Tuesday cutoff", scope={"only": True, "zone": "role_local"}, time={"weekday": "Tuesday", "end_minute": 960, "cutoff_minute": 960}))]),
    (8, {
        "p1": [p("candidate", "learning_allowance", "budget equivalent", modality="preference_constraint", scope={"annual_acceptable": True}, measure=m("amount", "EUR", 200, None, "calendar_month"))],
        "e1": [p("role", "learning_allowance", "annual budget", modality="commitment", measure=m("amount", "EUR", 2400, 2400, "calendar_year")),
               p("employer", "reimbursement_schedule", "specified", polarity="negative", modality="observation") ]}, [
        c("c1", "The EUR 2,400 annual learning budget", p("role", "learning_allowance", "annual budget", modality="commitment", measure=m("amount", "EUR", 2400, 2400, "calendar_year"))),
        c("c2", "equals my EUR 200 monthly budget floor.", assessment("learning_allowance_fit", "budget equivalent", scope={"currency": "EUR", "annual_budget": 2400, "monthly_floor": 200, "annual_acceptable": True})),
        c("c3", "Its reimbursement schedule is unspecified.", p("employer", "reimbursement_schedule", "specified", polarity="negative", modality="observation"))]),
    (9, {
        "p1": [p("candidate", "live_captions", "team meetings", modality="preference_constraint", scope={"meeting_type": "team"}, time={"phase": "first_day"})],
        "e1": [p("role", "live_captions", "team meetings", modality="observation", scope={"status": "pending_procurement", "meeting_type": "team"}),
               p("employer", "activation_date_promised", "first day", polarity="negative", modality="observation"),
               p("employer", "live_captions_approval", "team meetings", polarity="negative", modality="observation") ]}, [
        c("c1", "Live captions are in procurement review.", p("role", "live_captions", "team meetings", modality="observation", scope={"status": "pending_procurement", "meeting_type": "team"})),
        c("c2", "They are guaranteed to be available for my first-day team meetings.", p("role", "live_captions", "team meetings", modality="guarantee", time={"phase": "first_day"}, scope={"meeting_type": "team"}))]),
    (10, {
        "p1": [p("candidate", "business_travel", "required travel", polarity="negative", modality="preference_constraint", time={"phase": "first_calendar_quarter"})],
        "e1": [p("role", "business_travel", "required travel", polarity="negative", modality="requirement", time={"phase": "first_calendar_quarter"}),
                p("role", "business_travel", "later travel", modality="possibility", time={"phase": "after_first_calendar_quarter"})]}, [
        c("c1", "The first calendar quarter has no required business travel", p("role", "business_travel", "required travel", polarity="negative", modality="requirement", time={"phase": "first_calendar_quarter"})),
        c("c2", "which fits my first-quarter travel restriction.", assessment("business_travel_fit", "first-quarter restriction", time={"phase": "first_calendar_quarter"})),
        c("c3", "Later travel remains possible.", p("role", "business_travel", "later travel", modality="possibility", time={"phase": "after_first_calendar_quarter"}))]),
    (11, {
        "p1": [p("candidate", "station_attendance", "weekly cap", modality="preference_constraint", time={"phase": "after_onboarding"}, measure=m("count", "day", None, 1, "week"))],
        "e1": [p("role", "station_attendance", "weekly requirement", modality="requirement", time={"phase": "after_onboarding"}, measure=m("count", "day", 2, 2, "week"))]}, [
        c("c1", "The role requires one station day each week after onboarding.", p("role", "station_attendance", "weekly requirement", modality="requirement", time={"phase": "after_onboarding"}, measure=m("count", "day", 1, 1, "week"))),
        c("c2", "That fits my one-day weekly cap.", assessment("station_attendance_fit", "weekly cap", time={"phase": "after_onboarding"}, scope={"required_days": 1, "cap_days": 1}))]),
    (12, {
        "p1": [p("candidate", "work_pattern", "four-day week", modality="preference_constraint", scope={"working_days": "Monday-Thursday", "free_day": "Friday"})],
        "e1": [p("role", "work_pattern", "four-day week", modality="commitment", scope={"working_days": "Monday-Thursday", "free_day": "Friday", "written_offer": True})]}, [
        c("c1", "The written offer sets a four-day, Monday–Thursday week.", p("role", "work_pattern", "four-day week", modality="commitment", scope={"working_days": "Monday-Thursday", "written_offer": True})),
        c("c2", "Friday is free, as I prefer.", assessment("work_pattern_fit", "Friday free", scope={"free_day": "Friday", "working_days": "Monday-Thursday"}))]),
    (13, {
        "p1": [p("candidate", "remote_work", "Wednesdays", modality="preference_constraint", time={"phase": "after_onboarding", "weekday": "Wednesday"})],
        "e1": [p("team", "remote_work_approval", "Wednesdays", modality="possibility", scope={"case_by_case": True, "decision": "not_made"}, time={"phase": "after_onboarding", "weekday": "Wednesday"})]}, [
        c("c1", "Wednesday remote work after onboarding looks feasible for me, subject to a manager's decision.",
          assessment("remote_work_fit", "Wednesdays", scope={"condition": "approval", "decision": "not_made", "qualified": "looks feasible"}, time={"phase": "after_onboarding", "weekday": "Wednesday"}),
          p("manager", "remote_work_approval_authority", "Wednesdays", modality="observation", time={"phase": "after_onboarding", "weekday": "Wednesday"}))]),
    (14, {
        "p1": [p("candidate", "stipend", "transport", modality="preference_constraint", scope={"category": "transport"}, measure=m("amount", "CHF", 80, None, "calendar_month"))],
        "e1": [p("role", "stipend", "transport", modality="commitment", scope={"category": "transport", "written_offer": True}, time={"phase": "first_month"}, measure=m("amount", "CHF", 100, 100, "calendar_month"))]}, [
        c("c1", "The written offer includes CHF 100 monthly for transport from month one.", p("role", "stipend", "transport", modality="commitment", scope={"category": "transport", "written_offer": True}, time={"phase": "first_month"}, measure=m("amount", "CHF", 100, 100, "calendar_month"))),
        c("c2", "That exceeds my CHF 80 monthly floor.", assessment("stipend_fit", "transport", scope={"category": "transport", "currency": "CHF", "monthly_offer": 100, "monthly_floor": 80}))]),
    (15, {
        "p1": [p("candidate", "overnight_travel", "required trips", modality="preference_constraint", measure=m("count", "trip", None, 2, "calendar_month"))],
        "e1": [p("role", "overnight_travel", "required trips", modality="requirement", measure=m("count", "trip", 3, 3, "calendar_month"))]}, [
        c("c1", "The role requires three overnight trips monthly.", p("role", "overnight_travel", "required trips", modality="requirement", measure=m("count", "trip", 3, 3, "calendar_month"))),
        c("c2", "This stays within my two-trip monthly limit.", assessment("overnight_travel_fit", "required trips", scope={"monthly_required": 3, "monthly_cap": 2}))]),
    (16, {
        "p1": [p("candidate", "station_attendance", "weekly cap", modality="preference_constraint", time={"phase": "onboarding"}, measure=m("count", "day", None, 2, "week")),
                p("candidate", "remote_work", "after onboarding", modality="preference_constraint", scope={"condition": "client data clearance granted"}, time={"phase": "after_onboarding"})],
        "e1": [p("role", "station_attendance", "weekly requirement", modality="requirement", time={"phase": "onboarding"}, measure=m("count", "day", 2, 2, "week")),
                p("role", "remote_work", "after onboarding", modality="permission", scope={"condition": "client data clearance granted"}, time={"phase": "after_onboarding"})]}, [
        c("c1", "Two required station days during onboarding", p("role", "station_attendance", "weekly requirement", modality="requirement", time={"phase": "onboarding"}, measure=m("count", "day", 2, 2, "week"))),
        c("c2", "fit my cap.", assessment("station_attendance_fit", "onboarding cap", time={"phase": "onboarding"}, scope={"required_days": 2, "cap_days": 2})),
        c("c3", "After onboarding, remote work is permitted on the clearance condition I accept.",
          p("role", "remote_work", "after onboarding", modality="permission", scope={"condition": "client data clearance granted"}, time={"phase": "after_onboarding"}),
          p("candidate", "remote_work", "after onboarding", modality="preference_constraint", scope={"condition": "client data clearance granted"}, time={"phase": "after_onboarding"}))]),
    (17, {
        "p1": [p("candidate", "station_attendance", "weekly cap", modality="preference_constraint", time={"phase": "after_onboarding"}, measure=m("count", "day", None, 3, "week"))],
        "e1": [p("role", "station_attendance", "older weekly requirement", modality="requirement", time={"phase": "after_onboarding"}, measure=m("count", "day", 3, 3, "week"))],
        "e2": [p("employer update", "supersedes", "older office-days term", modality="observation"),
                p("role", "station_attendance", "current weekly requirement", modality="requirement", time={"phase": "after_onboarding"}, measure=m("count", "day", 4, 4, "week"))]}, [
        c("c1", "The older three-day term has been superseded.", p("employer update", "supersedes", "older office-days term", modality="observation")),
        c("c2", "The current four-day requirement", p("role", "station_attendance", "current weekly requirement", modality="requirement", time={"phase": "after_onboarding"}, measure=m("count", "day", 4, 4, "week"))),
        c("c3", "still fits my three-day weekly cap.", assessment("station_attendance_fit", "current weekly requirement", time={"phase": "after_onboarding"}, scope={"required_days": 4, "cap_days": 3}))]),
    (18, {
        "p1": [p("candidate", "demo_presentation", "mandatory public demo", polarity="negative", modality="preference_constraint", scope={"audience": "public"}),
                p("candidate", "demo_presentation", "internal team demo", modality="permission", scope={"audience": "internal team"})],
        "e1": [p("role", "demo_presentation", "internal team demo", modality="requirement", scope={"audience": "internal team"}, measure=m("frequency", "demo", 1, 1, "calendar_month")),
                p("role", "demo_presentation", "mandatory public demo", polarity="negative", modality="requirement", scope={"audience": "public"})]}, [
        c("c1", "The monthly internal team demo", p("role", "demo_presentation", "internal team demo", modality="requirement", scope={"audience": "internal team"}, measure=m("frequency", "demo", 1, 1, "calendar_month"))),
        c("c2", "is acceptable to me.", assessment("demo_presentation_fit", "internal team demo", scope={"audience": "internal team", "frequency": "monthly"})),
        c("c3", "The role has no mandatory public demo.", p("role", "demo_presentation", "mandatory public demo", polarity="negative", modality="requirement", scope={"audience": "public"}))]),
    (19, {
        "p1": [p("candidate", "on_call", "weekend support", polarity="negative", modality="preference_constraint", time={"weekday": "Saturday"}),
                p("candidate", "on_call", "weekend support", polarity="negative", modality="preference_constraint", time={"weekday": "Sunday"})],
        "e1": [p("role", "on_call", "weekday support rota", modality="requirement", scope={"zone": "role_local", "only": True}, time={"weekday": "weekday", "start_minute": 540, "end_minute": 1020}),
                p("role", "on_call", "weekend shifts", polarity="negative", modality="requirement", time={"weekday": "Saturday"}),
                p("role", "on_call", "weekend shifts", polarity="negative", modality="requirement", time={"weekday": "Sunday"})]}, [
        c("c1", "The required support rota is weekdays only.", p("role", "on_call", "weekday support rota", modality="requirement", scope={"zone": "role_local", "only": True}, time={"weekday": "weekday", "start_minute": 540, "end_minute": 1020})),
        c("c2", "It leaves both weekend days free of on-call duty.",
          p("role", "on_call", "weekend shifts", polarity="negative", modality="requirement", time={"weekday": "Saturday"}),
          p("role", "on_call", "weekend shifts", polarity="negative", modality="requirement", time={"weekday": "Sunday"}),
          assessment("on_call_fit", "Saturday prohibition", scope={"only": True}, time={"weekday": "Saturday"}),
          assessment("on_call_fit", "Sunday prohibition", scope={"only": True}, time={"weekday": "Sunday"}))]),
    (20, {
        "p1": [p("candidate", "remote_work", "Portugal", modality="preference_constraint", scope={"location": "Portugal"}, time={"phase": "after_onboarding"})],
        "e1": [p("role", "remote_work", "approved EU locations", modality="permission", scope={"location_set": "approved EU locations", "approved_country_list": "unspecified"}, time={"phase": "after_onboarding"})]}, [
        c("c1", "Portugal might be an approved remote-work location after onboarding", assessment("remote_work_location_possibility", "Portugal", modality="possibility", scope={"location": "Portugal", "approval": "unknown"}, time={"phase": "after_onboarding"}), stance="conditional"),
        c("c2", "that needs confirmation from the employer.", assessment("confirmation_needed", "Portugal approval", modality="evaluation_instruction", scope={"location": "Portugal", "approval": "unknown"}), stance="advice")]),
]

G = [
    (1, "pass", "Five required station days occupy the stated induction week, and the after-induction remote permission preserves the clearance condition.", []),
    (2, "fail", "The offered EUR 1,200 annual allowance is accurately stated, but it is EUR 600 below the candidate's EUR 1,800 annual minimum.", ["c2"]),
    (3, "pass", "The exhaustive Saturday-only rota does not intersect the candidate's Monday–Friday prohibition.", []),
    (4, "pass", "The active update explicitly removes mandatory attendance after onboarding and allows voluntary visits.", []),
    (5, "pass", "The one-day role description would meet the candidate's limit, and the answer explicitly says the conflicting later two-day note leaves the current rule unresolved. It makes no unqualified current-fit claim.", []),
    (6, "fail", "The CHF 120 draft is real historical evidence, but it is withdrawn and the current offer has no transport stipend. The fit conclusion is false.", ["c2"]),
    (7, "pass", "The only required Tuesday demo ends exactly at the 16:00 cutoff in the same local time zone.", []),
    (8, "pass", "EUR 2,400 per year equals EUR 200 per calendar month as a budget equivalent; the answer does not assert a payment schedule.", []),
    (9, "fail", "Pending procurement and no activation promise cannot support a first-day guarantee; the pending status itself is accurately stated.", ["c2"]),
    (10, "pass", "The first-quarter travel restriction matches the no-travel term, while later travel is only described as possible.", []),
    (11, "fail", "The active role requires two weekly station days, not one. Both the reported term and its claimed fit are false.", ["c1", "c2"]),
    (12, "pass", "The written offer specifies Monday through Thursday working days and Friday free, exactly matching the expressed preference.", []),
    (13, "fail", "The team may approve Wednesday remote work case by case, and no approval decision has been made. The answer's feasibility judgment is tentative, but it asserts that a manager decides. The complete source inventory gives no support for that concrete decision-maker attribution.", ["c1"]),
    (14, "pass", "The written first-month CHF 100 monthly transport stipend exceeds the candidate's CHF 80 monthly floor.", []),
    (15, "fail", "Three required overnight trips each month exceed the candidate's two-trip cap; the role requirement itself is correctly quoted.", ["c2"]),
    (16, "pass", "Two required onboarding station days meet the two-day cap, and both the remote preference and permission retain the same clearance condition after onboarding.", []),
    (17, "fail", "The newer update expressly supersedes the three-day term; four current required days exceed the candidate's three-day cap. The supersession and current-day premises are true.", ["c3"]),
    (18, "pass", "Only the internal team demo is required, which the candidate accepts; the role explicitly has no mandatory public demo.", []),
    (19, "pass", "The required rota is exhaustive Monday–Friday and the source explicitly excludes weekend on-call shifts.", []),
    (20, "pass", "The employer allows approved EU locations but has not listed approved countries. The answer preserves Portugal as a possibility and asks for confirmation, without claiming approval.", []),
]


def ref(source_id, fact_index):
    return {"source_id": source_id, "fact_index": fact_index}


def check(op, offer, preference, remote=None):
    result = {"op": op, "offer": ref(*offer), "preference": ref(*preference)}
    if remote is not None:
        result["remote"] = ref(*remote)
    return result


# These replace only derived fit readings in the initial manual transcription.
# The untouched first version is preserved in preference-fit-initial-normalized.json.
TYPED = {
    (2, "c2"): (assessment("constraint_satisfied", "learning_allowance", scope={"currency": "EUR", "period": "calendar_year", "offered": 1200, "minimum": 1800}), check("constraint", ("e1", 0), ("p1", 0))),
    (3, "c2"): (assessment("constraint_satisfied", "on_call", scope={"only": True, "zone": "role_local"}, time={"weekday": "Saturday", "start_minute": 600, "end_minute": 840}), check("constraint", ("e1", 0), ("p1", 0))),
    (6, "c2"): (assessment("constraint_satisfied", "stipend", scope={"status": "current", "category": "transport", "currency": "CHF", "minimum_monthly": 90}), check("constraint", ("e2", 0), ("p1", 0))),
    (7, "c2"): (assessment("constraint_satisfied", "training_demo", scope={"only": True, "zone": "role_local"}, time={"weekday": "Tuesday", "end_minute": 960, "cutoff_minute": 960}), check("schedule_before", ("e1", 0), ("p1", 0))),
    (8, "c2"): (assessment("constraint_satisfied", "learning_allowance", scope={"currency": "EUR", "annual_budget": 2400, "monthly_floor": 200, "annual_acceptable": True}), check("constraint", ("e1", 0), ("p1", 0))),
    (10, "c2"): (assessment("constraint_satisfied", "business_travel", time={"phase": "first_calendar_quarter"}), check("constraint", ("e1", 0), ("p1", 0))),
    (11, "c2"): (assessment("constraint_satisfied", "station_attendance", time={"phase": "after_onboarding"}, scope={"required_days": 1, "cap_days": 1}), check("constraint", ("e1", 0), ("p1", 0))),
    (14, "c2"): (assessment("constraint_satisfied", "stipend", scope={"category": "transport", "currency": "CHF", "monthly_offer": 100, "monthly_floor": 80}, time={"phase": "first_month"}), check("constraint", ("e1", 0), ("p1", 0))),
    (15, "c2"): (assessment("constraint_satisfied", "overnight_travel", scope={"monthly_required": 3, "monthly_cap": 2}), check("constraint", ("e1", 0), ("p1", 0))),
    (16, "c2"): (assessment("constraint_satisfied", "station_attendance", time={"phase": "onboarding"}, scope={"required_days": 2, "cap_days": 2}), check("constraint", ("e1", 0), ("p1", 0))),
    (17, "c3"): (assessment("constraint_satisfied", "station_attendance", time={"phase": "after_onboarding"}, scope={"required_days": 4, "cap_days": 3}), check("constraint", ("e2", 1), ("p1", 0))),
}


def write_json(relative, value):
    path = BASE / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raw = json.loads((BASE / "raw/preference-fit.json").read_text(encoding="utf-8"))
    assert len(N) == len(G) == len(raw["rows"]) == 20
    by_id = {r["case_id"]: r for r in raw["rows"]}
    normal_rows = []
    for num, source_facts, claims in N:
        case_id = f"PF6H-{num:02d}"
        raw_row = by_id[case_id]
        assert set(source_facts) == {s["id"] for s in raw_row["sources"]}
        answer = raw_row["answer"]["text"]
        for claim in claims:
            assert answer.count(claim["quote"]) == 1, (case_id, claim["quote"])
            if (num, claim["id"]) in TYPED:
                reading, typed_check = TYPED[(num, claim["id"])]
                claim["readings"] = [reading]
                claim["check"] = typed_check
        normal_rows.append({"case_id": case_id,
                            "sources": [{"id": sid, "facts": facts} for sid, facts in source_facts.items()],
                            "claims": claims})
    exposure = {"checker_code_seen": False, "previous_cases_seen": False,
                "predictions_seen": False}
    write_json("normalized/preference-fit.json", {"schema": "maguire-v6-new-normalized",
               "family": "preference-fit", "human_approved": False,
               "exposure": exposure, "rows": normal_rows})
    write_json("gold/preference-fit.json", {"schema": "maguire-v6-new-gold",
               "family": "preference-fit", "human_approved": False,
               "exposure": exposure,
               "rows": [{"case_id": f"PF6H-{num:02d}", "verdict": verdict,
                         "reason": reason, "error_claim_ids": errors}
                        for num, verdict, reason, errors in G]})
