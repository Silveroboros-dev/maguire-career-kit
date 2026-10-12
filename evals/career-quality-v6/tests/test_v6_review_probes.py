"""Independent invented v6 safety probes; never grades the 40-case cohort."""

import sys
import unittest
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import checker  # noqa: E402


ANCHOR = {"sha256": "0" * 64, "pointer": "", "start": 0, "end": 1, "quote": "x"}
WHEN = "2026-02-01T00:00:00Z"


def fact(subject, predicate, obj, modality="observation", *, polarity="positive",
         scope=None, time=None, measure=None, epistemic_scope="world"):
    return {"subject": subject, "predicate": predicate, "object": obj,
            "polarity": polarity, "modality": modality,
            "epistemic_scope": epistemic_scope, "scope": scope or {},
            "time": time or {}, "measure": measure}


def source(sid, kind, *facts, status="active", observed_at="2026-01-01T00:00:00Z"):
    return {"id": sid, "kind": kind, "status": status,
            "observed_at": observed_at, "anchor": ANCHOR, "facts": list(facts)}


def measure(lower, upper, *, kind="count", unit="day", per=None):
    return {"kind": kind, "unit": unit, "lower": lower, "upper": upper, "per": per}


def assessment(obj, predicate="constraint_satisfied", *, scope=None, time=None,
               modality="record_assessment"):
    return fact("candidate", predicate, obj, modality,
                epistemic_scope="packet", scope=scope, time=time)


def packet(sources, reading, check=None, *, stance="asserted", grader="candidate_fit"):
    claims = [{"id": "invented-claim", "anchor": ANCHOR, "stance": stance,
               "readings": [reading], "check": check}]
    return {"schema": "maguire-claim-packet-v6", "grader": grader,
            "decision_at": WHEN, "sources": sources, "claims": claims,
            "coverage": {"scope": "fragment", "status": "agent_reviewed",
                         "source_inventory_complete": True, "fragment_complete": True,
                         "source_sha256": checker.digest(sources),
                         "claims_sha256": checker.digest(claims)}}


def ref(sid, index=0):
    return {"source_id": sid, "fact_index": index}


def verdict(sources, reading, check=None, *, stance="asserted", grader="candidate_fit"):
    return checker.grade_fragment(packet(sources, reading, check, stance=stance,
                                         grader=grader))["verdict"]


class V6ReviewerProbes(unittest.TestCase):
    def test_registered_concrete_action_has_positive_control(self):
        reading = fact("candidate", "handoff_recording", "release notes", "self_report",
                       scope={"team": "platform"})
        src = source("REC", "candidate_fact", reading)
        self.assertEqual(verdict([src], reading), "pass")

    def test_registered_action_does_not_choose_one_of_conflicting_records(self):
        reading = fact("candidate", "handoff_recording", "release notes", "self_report",
                       scope={"team": "platform"})
        positive = source("YES", "candidate_fact", reading)
        negative = source("NO", "candidate_fact", fact(
            "candidate", "handoff_recording", "release notes", "self_report",
            polarity="negative", scope={"team": "platform"}))
        self.assertEqual(verdict([positive, negative], reading), "needs_review")

    def test_unknown_qualitative_transfer_stays_review(self):
        src = source("REC", "candidate_fact", fact(
            "candidate", "caption_testing", "recorded lectures"))
        reading = fact("candidate", "live_session_transferability", "live lectures")
        self.assertEqual(verdict([src], reading), "needs_review")

    def test_expired_and_future_sources_do_not_prove_experience(self):
        reading = fact("candidate", "rollback_documentation", "release runbook")
        for src in (
            source("REC", "candidate_fact", reading, status="inactive"),
            source("REC", "candidate_fact", reading,
                   observed_at="2026-03-01T00:00:00Z"),
        ):
            with self.subTest(src=src):
                self.assertNotEqual(verdict([src], reading), "pass")

    def test_team_measure_does_not_become_personal_measure(self):
        src = source("REC", "candidate_fact", fact(
            "team", "latency_reduction", "queue service", "observation",
            measure=measure(38, 38, kind="amount", unit="percent", per="calendar_year")))
        reading = fact("candidate", "latency_reduction", "queue service", "observation",
                       measure=measure(38, 38, kind="amount", unit="percent", per="calendar_year"))
        self.assertNotEqual(verdict([src], reading), "pass")

    def test_sandbox_scope_cannot_prove_production_use(self):
        src = source("REC", "candidate_fact", fact(
            "candidate", "sql_use", "warehouse", "self_report",
            scope={"environment": "sandbox"}))
        reading = fact("candidate", "sql_use", "warehouse", "self_report",
                       scope={"environment": "production"})
        self.assertNotEqual(verdict([src], reading), "pass")

    def test_permission_does_not_prove_event_occurrence(self):
        src = source("REC", "candidate_fact", fact(
            "candidate", "customer_demo", "demo series", "permission",
            measure=measure(7, 7, unit="demo")))
        reading = fact("candidate", "customer_demo", "demo series", "observation")
        self.assertNotEqual(verdict([src], reading), "pass")

    def test_pending_status_does_not_prove_active_benefit(self):
        offer = source("OFFER", "job_description", fact(
            "employer", "learning_allowance", "lab fees", "observation",
            scope={"status": "pending"}))
        preference = source("PREF", "preference", fact(
            "candidate", "learning_allowance", "lab fees", "preference_constraint",
            scope={"priority": "must_have"},
            measure=measure(600, None, kind="amount", unit="USD", per="calendar_year")))
        check = {"op": "pending", "offer": ref("OFFER"), "preference": ref("PREF")}
        self.assertNotEqual(verdict([offer, preference], assessment(
            "lab fees", "constraint_satisfied", scope={"status": "active"}),
            check, grader="preference_fit"), "pass")
        self.assertEqual(verdict([offer, preference], assessment(
            "lab fees", "constraint_unresolved", scope={"status": "pending"}),
            check, grader="preference_fit"), "pass")

    def test_approval_condition_cannot_disappear_from_request(self):
        offer = source("OFFER", "job_description", fact(
            "role", "remote_work", "remote days", "permission",
            scope={"condition": "manager_approval"},
            measure=measure(None, 6, per="calendar_month")))
        preference = source("PREF", "preference", fact(
            "candidate", "remote_work", "remote days", "preference_constraint",
            scope={"priority": "nice_to_have"},
            measure=measure(3, 3, per="calendar_month")))
        check = {"op": "permission_limit", "offer": ref("OFFER"),
                 "preference": ref("PREF")}
        reading = assessment("remote days", "request_within_limit")
        self.assertNotEqual(verdict([offer, preference], reading, check,
                                    grader="preference_fit"), "pass")

    def test_condition_claim_requires_actual_source_condition(self):
        reading = assessment("remote days", "condition_required",
                             scope={"condition": "security_review"})
        check = {"op": "condition", "offer": ref("OFFER")}
        for scope, expected in (({"condition": "security_review"}, "pass"),
                                ({}, "fail")):
            with self.subTest(scope=scope):
                offer = source("OFFER", "job_description", fact(
                    "role", "remote_work", "remote days", "permission",
                    scope=scope))
                self.assertEqual(verdict([offer], reading, check,
                                         grader="preference_fit"), expected)

    def test_narrow_required_window_cannot_evade_whole_day_prohibition(self):
        offer = source("OFFER", "job_description", fact(
            "role", "on_call", "pager rotation", "requirement",
            scope={"weekday": "Sunday"},
            time={"start_minute": 240, "end_minute": 360, "zone": "role_local"}))
        preference = source("PREF", "preference", fact(
            "candidate", "on_call", "pager rotation", "preference_constraint",
            polarity="negative", scope={"weekday": "Sunday", "priority": "must_have"}))
        check = {"op": "constraint", "offer": ref("OFFER"),
                 "preference": ref("PREF")}
        reading = assessment("pager rotation", scope={"weekday": "Sunday"})
        self.assertNotEqual(verdict([offer, preference], reading, check,
                                    grader="preference_fit"), "pass")

    def test_exhaustive_demo_window_respects_end_boundary(self):
        preference = source("PREF", "preference", fact(
            "candidate", "training_demo", "lab tour", "preference_constraint",
            polarity="negative", time={"weekday": "Thursday",
                                       "after_minute": 720, "zone": "role_local"}))
        check = {"op": "schedule_before", "offer": ref("OFFER"),
                 "preference": ref("PREF")}
        reading = assessment("lab tour", scope={"only": True},
                             time={"weekday": "Thursday", "zone": "role_local"})
        for end_minute, expected in ((690, "pass"), (780, "fail")):
            with self.subTest(end_minute=end_minute):
                offer = source("OFFER", "job_description", fact(
                    "role", "training_demo", "lab tour", "requirement",
                    scope={"only": True},
                    time={"weekday": "Thursday", "start_minute": 540,
                          "end_minute": end_minute, "zone": "role_local"}))
                self.assertEqual(verdict([offer, preference], reading, check,
                                         grader="preference_fit"), expected)

    def test_unrecognized_weekday_cannot_pass_schedule(self):
        offer = source("OFFER", "job_description", fact(
            "role", "training_demo", "lab tour", "requirement",
            scope={"only": True}, time={"weekday": "Funday",
                                      "start_minute": 540, "end_minute": 690,
                                      "zone": "role_local"}))
        preference = source("PREF", "preference", fact(
            "candidate", "training_demo", "lab tour", "preference_constraint",
            polarity="negative", time={"weekday": "Funday",
                                       "after_minute": 720, "zone": "role_local"}))
        reading = assessment("lab tour", scope={"only": True},
                             time={"weekday": "Funday", "zone": "role_local"})
        check = {"op": "schedule_before", "offer": ref("OFFER"),
                 "preference": ref("PREF")}
        self.assertNotEqual(verdict([offer, preference], reading, check,
                                    grader="preference_fit"), "pass")

    def test_onboarding_cannot_hide_refused_remote_approval(self):
        offer = source("OFFER", "job_description",
                       fact("role", "station_attendance", "onboarding", "requirement",
                            time={"phase": "onboarding"}, measure=measure(2, 2)),
                       fact("role", "remote_work", "work_location", "permission",
                            scope={"condition": "manager_approval"},
                            time={"phase": "after_onboarding"}))
        reading = assessment("onboarding", scope={"requires_remote_after": True,
                                                   "remote_condition": "manager_approval"},
                             time={"phase": "onboarding"})
        check = {"op": "onboarding", "offer": ref("OFFER", 0),
                 "remote": ref("OFFER", 1), "preference": ref("PREF", 0)}
        for polarity, expected in (("positive", "pass"), ("negative", "needs_review")):
            with self.subTest(polarity=polarity):
                preference = source("PREF", "preference",
                                    fact("candidate", "station_attendance", "onboarding",
                                         "preference_constraint",
                                         scope={"priority": "must_have", "requires_remote_after": True},
                                         time={"phase": "onboarding"},
                                         measure=measure(None, 3)),
                                    fact("candidate", "remote_work", "work_location",
                                         "preference_constraint", polarity=polarity,
                                         scope={"condition": "manager_approval"},
                                         time={"phase": "after_onboarding"}))
                self.assertEqual(verdict([offer, preference], reading, check,
                                         grader="preference_fit"), expected)

    def test_onboarding_cannot_hide_generic_remote_ban(self):
        offer = source("OFFER", "job_description",
                       fact("role", "station_attendance", "onboarding", "requirement",
                            time={"phase": "onboarding"}, measure=measure(2, 2)),
                       fact("role", "remote_work", "work_location", "permission",
                            scope={"condition": "manager_approval"},
                            time={"phase": "after_onboarding"}))
        preference = source("PREF", "preference",
                            fact("candidate", "station_attendance", "onboarding",
                                 "preference_constraint",
                                 scope={"priority": "must_have", "requires_remote_after": True},
                                 time={"phase": "onboarding"},
                                 measure=measure(None, 3)),
                            fact("candidate", "remote_work", "work_location",
                                 "preference_constraint", polarity="positive",
                                 scope={"condition": "manager_approval"},
                                 time={"phase": "after_onboarding"}),
                            fact("candidate", "remote_work", "work_location",
                                 "preference_constraint", polarity="negative",
                                 time={}))
        reading = assessment("onboarding", scope={"requires_remote_after": True,
                                                   "remote_condition": "manager_approval"},
                             time={"phase": "onboarding"})
        check = {"op": "onboarding", "offer": ref("OFFER", 0),
                 "remote": ref("OFFER", 1), "preference": ref("PREF", 0)}
        self.assertNotEqual(verdict([offer, preference], reading, check,
                                    grader="preference_fit"), "pass")

    def test_malformed_foreign_reference_is_invalid(self):
        offer = source("OFFER", "job_description", fact(
            "role", "remote_work", "remote days", "permission",
            measure=measure(None, 2, per="calendar_month")))
        preference = source("PREF", "preference", fact(
            "candidate", "remote_work", "remote days", "preference_constraint",
            measure=measure(1, 1, per="calendar_month")))
        check = {"op": "permission_limit", "offer": ref("FOREIGN"),
                 "preference": ref("PREF")}
        self.assertEqual(verdict([offer, preference], assessment(
            "remote days", "request_within_limit"), check,
            grader="preference_fit"), "invalid")


if __name__ == "__main__":
    unittest.main()
