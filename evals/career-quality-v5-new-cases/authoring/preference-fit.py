"""Hand-authored preference-fit cases. No grader or prior corpus imports."""
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
FAMILY = "preference-fit"
DECISION = "2026-10-12T12:00:00Z"
OBSERVED = "2026-10-11T12:00:00Z"


def m(kind, unit, lower, upper, per):
    return dict(kind=kind, unit=unit, lower=lower, upper=upper, per=per)


def p(subject, predicate, object, *, polarity="positive", modality="observation",
      epistemic_scope="world", scope=None, time=None, measure=None):
    return dict(subject=subject, predicate=predicate, object=object,
                polarity=polarity, modality=modality,
                epistemic_scope=epistemic_scope, scope=scope or {},
                time=time or {}, measure=measure)


def src(id, text, kind, facts, *, status="active", observed_at=OBSERVED):
    return dict(id=id, text=text, kind=kind, status=status,
                observed_at=observed_at, facts=facts)


def claim(quote, reading, *, stance="asserted", check=None):
    return dict(quote=quote, stance=stance, readings=[reading], check=check)


def assess(predicate, object, *, scope=None, time=None, modality="record_assessment"):
    return p("candidate", predicate, object, modality=modality,
             epistemic_scope="packet", scope=scope, time=time)


CASES = []


def add(n, title, sources, claims, verdict, reason, errors=(), answer_text=None):
    CASES.append(dict(case_id=f"PF5H-{n:02d}", title=title,
                      sources=sources, claims=claims, verdict=verdict,
                      reason=reason, errors=list(errors), answer_text=answer_text))


# 01: an exact annual/monthly budget equivalence, limited to course fees.
add(1, "Course-fee budget across periods", [
    src("s1", "The role provides CHF 1,800 per calendar year for course fees.",
        "job_description", [p("role", "learning_allowance", "course_fees",
                              modality="commitment", scope={"category": "course_fees"},
                              measure=m("amount", "CHF", 1800, 1800, "calendar_year"))]),
    src("s2", "I need at least CHF 120 per calendar month for course fees.",
        "preference", [p("candidate", "learning_allowance", "course_fees",
                         modality="preference_constraint", scope={"category": "course_fees"},
                         measure=m("amount", "CHF", 120, None, "calendar_month"))]),
], [claim("The course-fee allowance meets my CHF 120 monthly minimum on an annual-budget basis.",
          assess("constraint_satisfied", "course_fees", scope={"category": "course_fees"}),
          check={"op": "constraint", "offer": {"source_id": "s1", "fact_index": 0},
                 "preference": {"source_id": "s2", "fact_index": 0}})],
    "pass", "CHF 1,800 per year exceeds the CHF 1,440 annual equivalent of the course-fee minimum; the answer limits the comparison to annual budget equivalence.")

# 02: a larger figure in a different, expressly excluded category.
add(2, "Travel money is not tuition money", [
    src("s1", "The CHF 2,400 annual allowance covers conference travel only; it cannot pay course fees.",
        "job_description", [p("role", "learning_allowance", "conference_travel", modality="commitment",
                              scope={"category": "conference_travel"},
                              measure=m("amount", "CHF", 2400, 2400, "calendar_year")),
                            p("role", "learning_allowance", "course_fees", polarity="negative",
                              scope={"category": "course_fees"})]),
    src("s2", "My minimum is CHF 1,200 a year for course fees.", "preference",
        [p("candidate", "learning_allowance", "course_fees", modality="preference_constraint",
           scope={"category": "course_fees"}, measure=m("amount", "CHF", 1200, None, "calendar_year"))]),
], [claim("The annual allowance can cover my course-fee minimum.",
          p("role", "learning_allowance", "course_fees", modality="ability",
            scope={"category": "course_fees"}))],
    "fail", "The only allowance is restricted to conference travel and the JD explicitly excludes course fees; the answer changes the eligible category.", ["c1"])

# 03: conditional post-onboarding remote permission is preserved.
add(3, "Station onboarding followed by conditional remote work", [
    src("s1", "New hires must attend the station for two days during onboarding.",
        "job_description", [p("role", "station_attendance", "onboarding", modality="requirement",
                              time={"phase": "onboarding"}, measure=m("count", "day", 2, 2, None))]),
    src("s2", "After onboarding, remote work is permitted with manager approval.",
        "job_description", [p("role", "remote_work", "work_location", modality="permission",
                              scope={"condition": "manager_approval"}, time={"phase": "after_onboarding"})]),
    src("s3", "I can attend at most three onboarding days and need remote work afterward; manager approval is acceptable.",
        "preference", [p("candidate", "station_attendance", "onboarding", modality="preference_constraint",
                         scope={"requires_remote_after": True}, time={"phase": "onboarding"},
                         measure=m("count", "day", 0, 3, None)),
                       p("candidate", "remote_work", "work_location", modality="preference_constraint",
                         scope={"condition": "manager_approval"}, time={"phase": "after_onboarding"})]),
], [claim("The two required station days fit my three-day onboarding cap, with remote work permitted afterward subject to manager approval.",
          assess("constraint_satisfied", "onboarding",
                 scope={"requires_remote_after": True, "condition": "manager_approval"},
                 time={"phase": "onboarding"}),
          check={"op": "onboarding", "offer": {"source_id": "s1", "fact_index": 0},
                 "remote": {"source_id": "s2", "fact_index": 0},
                 "preference": {"source_id": "s3", "fact_index": 0}})],
    "pass", "Two required days are within three, and the separate post-onboarding remote permission exists. The answer retains its manager-approval condition and does not promise a schedule.")

# 04: approval is merely possible, leaving the necessary post-onboarding condition open.
add(4, "Remote approval remains discretionary", [
    src("s1", "Onboarding requires two station days.", "job_description",
        [p("role", "station_attendance", "onboarding", modality="requirement",
           time={"phase": "onboarding"}, measure=m("count", "day", 2, 2, None))]),
    src("s2", "After onboarding, remote work may be approved following a team review; no approval has been issued.",
        "employer_update", [p("role", "remote_work", "work_location", modality="possibility",
                              scope={"condition": "team_review", "status": "unapproved"},
                              time={"phase": "after_onboarding"})]),
    src("s3", "I can do up to three station days if remote work is available after onboarding.",
        "preference", [p("candidate", "station_attendance", "onboarding", modality="preference_constraint",
                         scope={"requires_remote_after": True}, time={"phase": "onboarding"},
                         measure=m("count", "day", 0, 3, None))]),
], [claim("The onboarding arrangement may meet my preference if remote approval follows the team review.",
          assess("constraint_satisfied", "onboarding", scope={"requires_remote_after": True,
                                                             "condition": "remote_approval_after_team_review"},
                 time={"phase": "onboarding"}),
          stance="conditional",
          check={"op": "onboarding", "offer": {"source_id": "s1", "fact_index": 0},
                 "remote": {"source_id": "s2", "fact_index": 0},
                 "preference": {"source_id": "s3", "fact_index": 0}})],
    "pass", "The day count fits. The answer says the arrangement may meet the preference only if remote approval follows team review; it does not claim that approval has already been granted.")

# 05: weekday windows are explicitly finite and aligned.
add(5, "Saturday support window", [
    src("s1", "The only on-call shift is Saturday 11:00–13:00, role-local time.",
        "job_description", [p("role", "on_call", "support_shift", modality="requirement",
                              scope={"only": True, "weekday": "Saturday", "window_start_minute": 660,
                                     "window_end_minute": 780}, time={"zone": "role_local"})]),
    src("s2", "I accept Saturday on-call work from 10:00–14:00 role-local time, but no weekday on-call work.",
        "preference", [p("candidate", "on_call", "support_shift", modality="preference_constraint",
                         scope={"weekday": "Saturday", "window_start_minute": 600,
                                "window_end_minute": 840}, time={"zone": "role_local"}),
                       p("candidate", "on_call", "support_shift", polarity="negative",
                         modality="preference_constraint", scope={"weekday_set": "Monday-Friday"},
                         time={"zone": "role_local"})]),
], [claim("The Saturday 11:00–13:00 on-call shift is inside my Saturday window and adds no weekday duty.",
          assess("constraint_satisfied", "support_shift", scope={"weekday": "Saturday",
                                                           "window_start_minute": 660,
                                                           "window_end_minute": 780},
                 time={"zone": "role_local"}),
          check={"op": "constraint", "offer": {"source_id": "s1", "fact_index": 0},
                 "preference": {"source_id": "s2", "fact_index": 0}})],
    "pass", "The sole mandatory window is contained in the accepted Saturday window, and the exhaustive term adds no prohibited weekday duty.")

# 06: the same duty falls on a prohibited day.
add(6, "Sunday duty against a Sunday prohibition", [
    src("s1", "The role requires on-call coverage every Sunday 11:00–13:00 local time.",
        "job_description", [p("role", "on_call", "support_shift", modality="requirement",
                              scope={"weekday": "Sunday", "window_start_minute": 660,
                                     "window_end_minute": 780}, time={"zone": "role_local"},
                              measure=m("frequency", "day", 1, 1, "week"))]),
    src("s2", "I cannot take Sunday on-call duty at any hour.", "preference",
        [p("candidate", "on_call", "support_shift", polarity="negative",
           modality="preference_constraint", scope={"weekday": "Sunday"},
           time={"zone": "role_local"})]),
], [claim("The mandatory Sunday shift fits my no-Sunday rule.",
          assess("constraint_satisfied", "support_shift", scope={"weekday": "Sunday"},
                 time={"zone": "role_local"}),
          check={"op": "constraint", "offer": {"source_id": "s1", "fact_index": 0},
                 "preference": {"source_id": "s2", "fact_index": 0}})],
    "fail", "A required Sunday shift directly violates the candidate's Sunday prohibition.", ["c1"])

# 07: request is allowed by a limit, without an approval guarantee.
add(7, "Remote request under a conditional cap", [
    src("s1", "Employees may request up to four remote days per calendar month with manager approval.",
        "job_description", [p("role", "remote_work", "work_location", modality="permission",
                              scope={"condition": "manager_approval"},
                              measure=m("count", "day", 0, 4, "calendar_month"))]),
    src("s2", "I would request two remote days per calendar month, subject to manager approval.",
        "preference", [p("candidate", "remote_work", "work_location", modality="preference_constraint",
                         scope={"condition": "manager_approval"},
                         measure=m("count", "day", 2, 2, "calendar_month"))]),
], [claim("A request for two remote days a month is within the stated four-day limit, subject to manager approval.",
          assess("request_within_limit", "work_location", scope={"condition": "manager_approval"}),
          check={"op": "permission_limit", "offer": {"source_id": "s1", "fact_index": 0},
                 "preference": {"source_id": "s2", "fact_index": 0}})],
    "pass", "Two days is within the four-day request cap, and the answer keeps the approval condition without saying approval is assured.")

# 08: the desired request exceeds the stated envelope.
add(8, "Remote request above the cap", [
    src("s1", "Staff may request up to three remote days per calendar month after probation, with manager approval.",
        "job_description", [p("role", "remote_work", "work_location", modality="permission",
                              scope={"condition": "manager_approval", "phase": "after_probation"},
                              measure=m("count", "day", 0, 3, "calendar_month"))]),
    src("s2", "After probation I need to request five remote days each calendar month, subject to approval.",
        "preference", [p("candidate", "remote_work", "work_location", modality="preference_constraint",
                         scope={"condition": "manager_approval", "phase": "after_probation"},
                         measure=m("count", "day", 5, 5, "calendar_month"))]),
], [claim("My five-day monthly request is within the post-probation limit.",
          assess("request_within_limit", "work_location",
                 scope={"condition": "manager_approval", "phase": "after_probation"}),
          check={"op": "permission_limit", "offer": {"source_id": "s1", "fact_index": 0},
                 "preference": {"source_id": "s2", "fact_index": 0}})],
    "fail", "The permission envelope ends at three days per month; a five-day request is outside it even after probation.", ["c1"])

# 09: source is explicitly pending and answer gives a bounded next step.
add(9, "Pending learning allowance", [
    src("s1", "The course-fee allowance for this role is still undecided; no amount has been approved.",
        "employer_update", [p("role", "learning_allowance", "course_fees", modality="possibility",
                              scope={"status": "pending", "category": "course_fees"}),
                            p("role", "allowance_amount_approved", "course_fees",
                              polarity="negative", scope={"category": "course_fees"})]),
    src("s2", "I need at least EUR 900 per calendar year for course fees.", "preference",
        [p("candidate", "learning_allowance", "course_fees", modality="preference_constraint",
           scope={"category": "course_fees"},
           measure=m("amount", "EUR", 900, None, "calendar_year"))]),
], [claim("Confirm the pending course-fee allowance before treating this budget preference as met.",
          assess("confirmation_needed", "course_fees", modality="evaluation_instruction",
                 scope={"status": "pending", "category": "course_fees"}), stance="advice",
          check={"op": "pending", "offer": {"source_id": "s1", "fact_index": 0},
                 "preference": {"source_id": "s2", "fact_index": 0}})],
    "pass", "The allowance is explicitly undecided, so a request to confirm it before claiming fit is supported.")

# 10: two eligible employer terms conflict without supersession.
add(10, "Unresolved onboarding revisions", [
    src("s1", "The role sheet requires three station days during onboarding.", "job_description",
        [p("role", "station_attendance", "onboarding", modality="requirement",
           time={"phase": "onboarding"}, measure=m("count", "day", 3, 3, None))]),
    src("s2", "The recruiter sheet requires five station days during onboarding; it does not state that it replaces the role sheet.",
        "employer_update", [p("role", "station_attendance", "onboarding", modality="requirement",
                              time={"phase": "onboarding"}, measure=m("count", "day", 5, 5, None))]),
    src("s3", "I can attend at most four station days in onboarding.", "preference",
        [p("candidate", "station_attendance", "onboarding", modality="preference_constraint",
           time={"phase": "onboarding"}, measure=m("count", "day", 0, 4, None))]),
], [claim("The station-attendance requirement fits my four-day cap.",
          assess("constraint_satisfied", "onboarding", time={"phase": "onboarding"}),
          check={"op": "constraint", "offer": {"source_id": "s1", "fact_index": 0},
                 "preference": {"source_id": "s3", "fact_index": 0}})],
    "needs_review", "One active employer term is within the cap and another is outside it. Neither explicitly supersedes the other, so the applicable requirement is unresolved.")

# 11: role-wide travel maximum versus a candidate's role-scoped preference.
add(11, "Travel cadence scoped to the role", [
    src("s1", "This role requires one client-site day each calendar month in Basel, and no other travel.",
        "job_description", [p("role", "station_attendance", "client_site", modality="requirement",
                              scope={"location": "Basel", "only": True, "role_scope": "this_role"},
                              measure=m("frequency", "day", 1, 1, "calendar_month"))]),
    src("s2", "For this role I accept up to two Basel client-site days per calendar month.",
        "preference", [p("candidate", "station_attendance", "client_site", modality="preference_constraint",
                         scope={"location": "Basel", "role_scope": "this_role"},
                         measure=m("frequency", "day", 0, 2, "calendar_month"))]),
], [claim("This role's one Basel client-site day per month stays within my two-day monthly cap for this role.",
          assess("constraint_satisfied", "client_site",
                 scope={"location": "Basel", "role_scope": "this_role"}),
          check={"op": "constraint", "offer": {"source_id": "s1", "fact_index": 0},
                 "preference": {"source_id": "s2", "fact_index": 0}})],
    "pass", "The sole role requirement is one Basel client-site day per month, inside the candidate's role-scoped two-day maximum.")

# 12: paid learning time is the same category and period as a personal minimum.
add(12, "Paid leadership learning time after probation", [
    src("s1", "After the three-month probation period, the role provides four paid learning hours per calendar month for leadership courses.",
        "job_description", [p("role", "learning_time", "leadership_courses", modality="commitment",
                              scope={"category": "leadership_courses", "paid": True},
                              time={"phase": "after_probation"},
                              measure=m("count", "hour", 4, 4, "calendar_month")),
                            p("role", "probation_duration", "probation_period",
                              measure=m("count", "month", 3, 3, None))]),
    src("s2", "After probation, I need at least three paid learning hours per calendar month for leadership courses.",
        "preference", [p("candidate", "learning_time", "leadership_courses",
                         modality="preference_constraint",
                         scope={"category": "leadership_courses", "paid": True},
                         time={"phase": "after_probation"},
                         measure=m("count", "hour", 3, None, "calendar_month"))]),
], [claim("After probation, the four paid leadership-learning hours per month meet my three-hour minimum.",
          assess("constraint_satisfied", "leadership_courses",
                 scope={"category": "leadership_courses", "paid": True},
                 time={"phase": "after_probation"}),
          check={"op": "constraint", "offer": {"source_id": "s1", "fact_index": 0},
                 "preference": {"source_id": "s2", "fact_index": 0}})],
    "pass", "The role commits four paid leadership-course hours per calendar month after probation, exceeding the candidate's three-hour minimum in the same phase and category.")

# 13: explicit supersession chooses the lower current duty.
add(13, "One-day revision supersedes three-day onboarding", [
    src("s1", "The earlier role sheet required three station days during onboarding.",
        "job_description", [p("role", "station_attendance", "onboarding", modality="requirement",
                              time={"phase": "onboarding"}, measure=m("count", "day", 3, 3, None))]),
    src("s2", "This signed update replaces the earlier role sheet's onboarding rule: one station day is required.",
        "employer_update", [p("role", "station_attendance", "onboarding", modality="requirement",
                              time={"phase": "onboarding"}, measure=m("count", "day", 1, 1, None)),
                            p("s2", "supersedes", "s1")]),
    src("s3", "I can do no more than two station days during onboarding.", "preference",
        [p("candidate", "station_attendance", "onboarding", modality="preference_constraint",
           time={"phase": "onboarding"}, measure=m("count", "day", 0, 2, None))]),
], [claim("The signed one-day onboarding rule fits my two-day cap.",
          assess("constraint_satisfied", "onboarding", time={"phase": "onboarding"}),
          check={"op": "constraint", "offer": {"source_id": "s2", "fact_index": 0},
                 "preference": {"source_id": "s3", "fact_index": 0}})],
    "pass", "The update expressly supersedes the three-day rule; the remaining required one day is within the two-day cap.")

# 14: the old rule is wrongly presented as still governing.
add(14, "Superseded rule described as current", [
    src("s1", "The original role sheet required four onboarding station days.",
        "job_description", [p("role", "station_attendance", "onboarding", modality="requirement",
                              time={"phase": "onboarding"}, measure=m("count", "day", 4, 4, None))]),
    src("s2", "This update replaces the original onboarding rule: two station days are now required.",
        "employer_update", [p("role", "station_attendance", "onboarding", modality="requirement",
                              time={"phase": "onboarding"}, measure=m("count", "day", 2, 2, None)),
                            p("s2", "supersedes", "s1")]),
], [claim("Four station days remain mandatory in the current onboarding rule.",
          p("role", "station_attendance", "onboarding", modality="requirement",
            scope={"status": "current"}, time={"phase": "onboarding"},
            measure=m("count", "day", 4, 4, None)))],
    "fail", "The original four-day term was explicitly replaced by a two-day rule, so the stated current requirement is false.", ["c1"])

# 15: committed stipend fits an exact monthly threshold.
add(15, "Committed on-call stipend", [
    src("s1", "For required evening on-call duty, the employer will pay a USD 400 stipend each calendar month.",
        "job_description", [p("role", "stipend", "on_call_compensation", modality="commitment",
                              scope={"category": "evening_on_call"},
                              measure=m("amount", "USD", 400, 400, "calendar_month")),
                            p("role", "on_call", "evening_duty", modality="requirement")]),
    src("s2", "For evening on-call duty I require at least USD 400 per calendar month.",
        "preference", [p("candidate", "stipend", "on_call_compensation", modality="preference_constraint",
                         scope={"category": "evening_on_call"},
                         measure=m("amount", "USD", 400, None, "calendar_month"))]),
], [claim("The committed USD 400 monthly evening on-call stipend meets my USD 400 monthly minimum.",
          assess("constraint_satisfied", "on_call_compensation",
                 scope={"category": "evening_on_call"}),
          check={"op": "constraint", "offer": {"source_id": "s1", "fact_index": 0},
                 "preference": {"source_id": "s2", "fact_index": 0}})],
    "pass", "The employer commitment is for the same duty, currency and month as the minimum, at exactly the required amount.")

# 16: a contingent maximum is not a guarantee.
add(16, "Possible stipend presented as guaranteed", [
    src("s1", "A project-funded stipend may pay up to USD 600 per calendar month for on-call work; funding has not been approved.",
        "job_description", [p("role", "stipend", "on_call_compensation", modality="possibility",
                              scope={"category": "on_call", "condition": "project_funding",
                                     "status": "unapproved"},
                              measure=m("amount", "USD", None, 600, "calendar_month"))]),
], [claim("The role guarantees a USD 600 monthly on-call stipend.",
          p("role", "stipend", "on_call_compensation", modality="guarantee",
            scope={"category": "on_call"}, measure=m("amount", "USD", 600, 600, "calendar_month")))],
    "fail", "A possible, unfunded maximum of USD 600 is neither an approved payment nor a guaranteed exact amount.", ["c1"])

# 17: exhaustive training-demo windows all end before the candidate cutoff.
add(17, "Training demo before daily cutoff", [
    src("s1", "The only required training demo is on Wednesday 09:00–12:30 role-local time.",
        "job_description", [p("role", "training_demo", "demo_session", modality="requirement",
                              scope={"only": True, "weekday": "Wednesday"},
                              time={"start_minute": 540, "end_minute": 750, "zone": "role_local"})]),
    src("s2", "I cannot attend training demos after 13:00 on Wednesdays, role-local time.",
        "preference", [p("candidate", "training_demo", "demo_session", polarity="negative",
                         modality="preference_constraint", scope={"weekday": "Wednesday"},
                         time={"after_minute": 780, "zone": "role_local"})]),
], [claim("The only required Wednesday demo finishes before my 13:00 cutoff.",
          assess("constraint_satisfied", "demo_session", scope={"weekday": "Wednesday"},
                 time={"zone": "role_local"}),
          check={"op": "schedule_before", "offer": {"source_id": "s1", "fact_index": 0},
                 "preference": {"source_id": "s2", "fact_index": 0}})],
    "pass", "The exhaustive required demo ends at 12:30, before the candidate's 13:00 Wednesday cutoff in the same time zone.")

# 18: required demo continues past the cutoff.
add(18, "Training demo crosses cutoff", [
    src("s1", "The only required training demo is Tuesday 13:00–15:00 role-local time.",
        "job_description", [p("role", "training_demo", "demo_session", modality="requirement",
                              scope={"only": True, "weekday": "Tuesday"},
                              time={"start_minute": 780, "end_minute": 900, "zone": "role_local"})]),
    src("s2", "I cannot attend Tuesday training demos after 14:00 role-local time.",
        "preference", [p("candidate", "training_demo", "demo_session", polarity="negative",
                         modality="preference_constraint", scope={"weekday": "Tuesday"},
                         time={"after_minute": 840, "zone": "role_local"})]),
], [claim("The required Tuesday demo ends before my 14:00 cutoff.",
          assess("constraint_satisfied", "demo_session", scope={"weekday": "Tuesday"},
                 time={"zone": "role_local"}),
          check={"op": "schedule_before", "offer": {"source_id": "s1", "fact_index": 0},
                 "preference": {"source_id": "s2", "fact_index": 0}})],
    "fail", "The required Tuesday demo ends at 15:00, an hour after the candidate's cutoff.", ["c1"])

# 19: a withdrawn notice cannot defeat a current, explicitly conditional permission.
add(19, "Withdrawn remote restriction", [
    src("s1", "Remote work is prohibited for this role.", "employer_update",
        [p("role", "remote_work", "work_location", polarity="negative", modality="requirement")],
        status="withdrawn", observed_at="2026-09-30T09:00:00Z"),
    src("s2", "The active role terms permit remote work on Fridays with supervisor approval.",
        "employer_update", [p("role", "remote_work", "work_location", modality="permission",
                              scope={"weekday": "Friday", "condition": "supervisor_approval"})]),
], [claim("The active terms permit Friday remote work with supervisor approval.",
          p("role", "remote_work", "work_location", modality="permission",
            scope={"weekday": "Friday", "condition": "supervisor_approval"}))],
    "pass", "The active term expressly permits conditional Friday remote work. The older contrary notice is withdrawn and does not govern at decision time.")

# 20: current-status unavailability coexists with procurement pending; no zero amount is invented.
add(20, "Captions unavailable now, procurement pending", [
    src("s1", "Live captions are not available now; procurement is pending, with no activation date promised.",
        "employer_update", [p("role", "live_captions", "meeting_accessibility",
                              polarity="negative", scope={"status": "available_now"}),
                            p("role", "live_captions", "meeting_accessibility",
                              modality="possibility", scope={"status": "pending"}),
                            p("role", "activation_date_promised", "live_captions",
                              polarity="negative")]),
    src("s2", "I need live captions in work meetings from my first day.", "preference",
        [p("candidate", "live_captions", "meeting_accessibility",
           modality="preference_constraint", time={"phase": "first_day"})]),
], [claim("Live captions are unavailable now",
          p("role", "live_captions", "meeting_accessibility", polarity="negative",
            scope={"status": "available_now"})),
    claim("procurement is pending",
          p("role", "live_captions", "meeting_accessibility", modality="possibility",
            scope={"status": "pending"})),
    claim("without a promised activation date",
          p("role", "activation_date_promised", "live_captions", polarity="negative")),
    claim("Confirm availability before assuming my first-day caption requirement is met.",
          assess("confirmation_needed", "meeting_accessibility",
                 modality="evaluation_instruction", scope={"status": "pending"},
                 time={"phase": "first_day"}), stance="advice",
          check={"op": "pending", "offer": {"source_id": "s1", "fact_index": 1},
                 "preference": {"source_id": "s2", "fact_index": 0}})],
    "pass", "The answer preserves current unavailability, pending procurement, and the absence of a promised activation date, then asks for confirmation before treating a first-day requirement as met.",
    answer_text="Live captions are unavailable now, while procurement is pending without a promised activation date. Confirm availability before assuming my first-day caption requirement is met.")


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    assert len(CASES) == 20
    assert {v: sum(c["verdict"] == v for c in CASES) for v in ("pass", "fail", "needs_review")} == {
        "pass": 13, "fail": 6, "needs_review": 1}
    exposure = {"checker_code_seen": False, "previous_cases_seen": False,
                "predictions_seen": False}
    raw = dict(schema="maguire-v5-new-raw", family=FAMILY,
               human_approved=False, exposure=exposure, rows=[])
    norm = dict(schema="maguire-v5-new-normalized", family=FAMILY,
                human_approved=False, exposure=exposure, rows=[])
    gold = dict(schema="maguire-v5-new-gold", family=FAMILY,
                human_approved=False, exposure=exposure, rows=[])
    for case in CASES:
        case_id = case["case_id"]
        answer = case["answer_text"] or " ".join(c["quote"] for c in case["claims"])
        raw["rows"].append(dict(case_id=case_id, title=case["title"], decision_at=DECISION,
                                sources=[{k: s[k] for k in ("id", "text", "kind", "status", "observed_at")}
                                         for s in case["sources"]], answer={"text": answer}))
        norm["rows"].append(dict(case_id=case_id,
                                 sources=[dict(id=s["id"], facts=s["facts"]) for s in case["sources"]],
                                 claims=[dict(id=f"c{i}", **c) for i, c in enumerate(case["claims"], 1)]))
        gold["rows"].append(dict(case_id=case_id, verdict=case["verdict"],
                                 reason=case["reason"], error_claim_ids=case["errors"]))
        for c in case["claims"]:
            assert answer.count(c["quote"]) == 1, case_id
    files = [(BASE / "raw" / f"{FAMILY}.json", raw),
             (BASE / "normalized" / f"{FAMILY}.json", norm),
             (BASE / "gold" / f"{FAMILY}.json", gold)]
    for path, obj in files:
        write_json(path, obj)
    attest_path = BASE / "authoring" / f"{FAMILY}-attestation.json"
    authored = []
    history_dir = BASE / "authoring" / "preference-history"
    history_files = sorted(path for path in history_dir.iterdir() if path.is_file()) if history_dir.exists() else []
    for path in [Path(__file__), *[x[0] for x in files], *history_files]:
        data = path.read_bytes()
        authored.append(dict(path=str(path.relative_to(BASE)), bytes=len(data),
                             sha256=hashlib.sha256(data).hexdigest()))
    attest = dict(schema="maguire-v5-new-author-attestation", family=FAMILY,
                  author="Codex subagent /root/v5h_preference_author (GPT-6 family; exact variant not exposed)",
                  human_approved=False, checker_code_seen=False,
                  previous_cases_seen=False, predictions_seen=False,
                  allowed_files_read=["AGENTS.md", "README.md", "CREDITS.md",
                                      "evals/career-quality-v5-new-cases/AUTHORING.md",
                                      "evals/career-quality-v5-new-cases/FROZEN_SCHEMA.md",
                                      *["evals/career-quality-v5-new-cases/" + str(path.relative_to(BASE))
                                        for path in [Path(__file__), *[x[0] for x in files], *history_files]],
                                      "evals/career-quality-v5-new-cases/authoring/preference-fit-attestation.json"],
                  files_authored=authored,
                  composition_notes="Twenty hand-authored fictional cases: 13 pass, 6 fail, 1 review after blind semantic review corrected PF04. Cases combine budgets and category, onboarding and approval, duty windows, permission caps, pending decisions, conflicting terms, role scope, supersession, stipend modality, schedules, source status, and accessibility timing.",
                  review_corrections=[
                      "PF04: blind raw-only reviewer found conditional possibility supported; changed gold needs_review to pass and preserved conditional stance/approval contingency in normalization without changing raw.",
                      "PF09: added an explicit negative fact for no approved allowance amount.",
                      "PF12: pre-freeze family-scope correction replaced candidate qualification with a paid learning-time preference comparison; previous raw, normalized, gold, and attestation bytes are preserved, and blind raw-only review judged the replacement pass before new normalization/gold.",
                      "PF16: changed unknown stipend lower bound from zero to null.",
                      "PF20: aligned preference predicate with live_captions; split current unavailability, pending procurement, and absence of promised date into separate claims/facts; raw answer unchanged.",
                      "PF06, PF11, PF15: retained every-Sunday frequency, role-only scope, and required evening duty in source normalization.",
                  ],
                  limitations="The prescribed 12/6/2 mix becomes 13/6/1 because PF04 is semantically pass; no raw text or gold truth was altered merely to meet a quota. PF12 raw changed only for pre-freeze family scope, before grader execution. No checker, predecessor cases, predictions, API, or network used. Attestation cannot hash itself without recursion.")
    write_json(attest_path, attest)


if __name__ == "__main__":
    main()
