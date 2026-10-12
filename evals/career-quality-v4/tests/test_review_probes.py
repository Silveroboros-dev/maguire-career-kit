"""Independent, synthetic probes for the v4 normalization/checker boundary."""

import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import checker  # noqa: E402


ANCHOR = {"sha256": "0" * 64, "pointer": "", "start": 0, "end": 1, "quote": "x"}


def fact(subject, predicate, obj, modality, *, scope=None, time=None,
         measure=None, polarity="positive"):
    return {"subject": subject, "predicate": predicate, "object": obj,
            "modality": modality, "polarity": polarity, "epistemic_scope": "world",
            "scope": {} if scope is None else scope,
            "time": {} if time is None else time, "measure": measure}


def source(source_id, kind, *facts, status="active", observed_at="2026-01-01T00:00:00Z"):
    return {"id": source_id, "kind": kind, "status": status,
            "observed_at": observed_at, "anchor": ANCHOR, "facts": list(facts)}


def measure(lower, upper, *, kind="frequency", unit="day", per="week"):
    return {"kind": kind, "unit": unit, "lower": lower, "upper": upper, "per": per}


def assessment(obj, *, predicate="constraint_satisfied", scope=None, time=None):
    return {"subject": "candidate", "predicate": predicate, "object": obj,
            "modality": "record_assessment", "polarity": "positive",
            "epistemic_scope": "packet", "scope": {} if scope is None else scope,
            "time": {} if time is None else time, "measure": None}


def packet(sources, reading, check=None):
    claims = [{"id": "C", "anchor": ANCHOR, "stance": "asserted",
               "readings": [reading], "check": check}]
    return {"schema": "maguire-claim-packet-v4", "grader": "preference_fit",
            "decision_at": "2026-02-01T00:00:00Z", "sources": sources,
            "claims": claims,
            "coverage": {"scope": "fragment", "status": "agent_reviewed",
                         "source_inventory_complete": True, "fragment_complete": True,
                         "source_sha256": checker.digest(sources),
                         "claims_sha256": checker.digest(claims)}}


def constraint(offer_id="J", pref_id="P"):
    return {"op": "constraint", "offer": {"source_id": offer_id, "fact_index": 0},
            "preference": {"source_id": pref_id, "fact_index": 0}}


class ReviewerProbes(unittest.TestCase):
    def test_foreign_reference_is_invalid(self):
        job = source("J", "job_description", fact("role", "station_attendance", "station",
                     "requirement", measure=measure(1, 1)))
        pref = source("P", "preference", fact("candidate", "station_attendance", "station",
                      "preference_constraint", measure=measure(None, 2),
                      scope={"priority": "must_have"}))
        result = checker.grade_fragment(packet([job, pref], assessment("station"),
                                               constraint(offer_id="OTHER")))
        self.assertEqual(result["verdict"], "invalid")

    def test_property_mismatch_cannot_pass(self):
        job = source("J", "job_description", fact("role", "stipend", "equipment",
                     "observation", measure=measure(600, 600, kind="amount", unit="USD", per="calendar_year")))
        pref = source("P", "preference", fact("candidate", "stipend", "internet",
                      "preference_constraint", scope={"priority": "must_have"},
                      measure=measure(500, None, kind="amount", unit="USD", per="calendar_year")))
        result = checker.grade_fragment(packet([job, pref], assessment("equipment"), constraint()))
        self.assertEqual(result["verdict"], "needs_review")

    def test_material_condition_cannot_disappear_from_claim(self):
        job = source("J", "job_description", fact("role", "station_attendance", "station",
                     "requirement", scope={"condition": "manager_approval"}, measure=measure(1, 1)))
        pref = source("P", "preference", fact("candidate", "station_attendance", "station",
                      "preference_constraint", scope={"priority": "must_have", "condition": "manager_approval"},
                      measure=measure(None, 2)))
        result = checker.grade_fragment(packet([job, pref], assessment("station"), constraint()))
        self.assertEqual(result["verdict"], "needs_review")

    def test_preference_exception_cannot_be_ignored(self):
        job = source("J", "job_description", fact("role", "station_attendance", "station",
                     "requirement", measure=measure(1, 1)))
        pref = source("P", "preference", fact("candidate", "station_attendance", "station",
                      "preference_constraint", scope={"priority": "must_have", "exceptions": True},
                      measure=measure(None, 2)))
        result = checker.grade_fragment(packet([job, pref], assessment("station"), constraint()))
        self.assertEqual(result["verdict"], "needs_review")

    def test_annual_amount_does_not_meet_monthly_floor(self):
        job = source("J", "job_description", fact("employer", "stipend", "internet",
                     "observation", measure=measure(900, 900, kind="amount", unit="USD", per="calendar_year")))
        pref = source("P", "preference", fact("candidate", "stipend", "internet",
                      "preference_constraint", scope={"priority": "must_have"},
                      measure=measure(200, None, kind="amount", unit="USD", per="calendar_month")))
        result = checker.grade_fragment(packet([job, pref], assessment("internet"), constraint()))
        self.assertEqual(result["verdict"], "fail")
        self.assertEqual(result["claims"][0]["rule"], "constraint_interval")
        self.assertEqual(set(result["claims"][0]["counter_evidence_ids"]), {"J", "P"})

    def test_permission_cannot_establish_guarantee(self):
        job = source("J", "job_description", fact("role", "remote_work", "remote days",
                     "permission", scope={"condition": "manager_approval"},
                     measure=measure(None, 4)))
        asserted = fact("role", "remote_work", "remote days", "guarantee",
                        measure=measure(3, 3))
        result = checker.grade_fragment(packet([job], asserted))
        self.assertEqual(result["verdict"], "fail")
        self.assertNotEqual(result["claims"][0]["rule"], "direct_support")

    def test_unknown_qualitative_rule_abstains(self):
        job = source("J", "job_description", fact("role", "training_demo", "equipment",
                     "requirement"))
        reading = {**assessment("equipment", predicate="fit_relevance"),
                   "subject": "candidate history"}
        result = checker.grade_fragment(packet([job], reading))
        self.assertEqual(result["verdict"], "needs_review")
        self.assertEqual(result["claims"][0]["rule"], "unknown_predicate")

    def test_positive_count_does_not_hide_explicit_negative_record(self):
        positive = source("S1", "candidate_fact", fact("candidate", "training_demo", "equipment",
                          "observation", measure=measure(4, 4, kind="count", unit="demos", per=None)))
        negative = source("S2", "candidate_fact", fact("candidate", "training_demo", "equipment",
                          "observation", polarity="negative"))
        reading = fact("candidate", "training_demo", "equipment", "observation")
        result = checker.grade_fragment(packet([positive, negative], reading))
        self.assertNotEqual(result["verdict"], "pass")

    def test_negative_pending_status_cannot_prove_unresolved_constraint(self):
        job = source("J", "job_description", fact("employer", "learning_allowance", "allowance",
                     "observation", polarity="negative", scope={"status": "pending"}))
        pref = source("P", "preference", fact("candidate", "learning_allowance", "allowance",
                      "preference_constraint", scope={"priority": "must_have"},
                      measure=measure(1000, None, kind="amount", unit="USD", per="calendar_year")))
        check = {"op": "pending", "offer": {"source_id": "J", "fact_index": 0},
                 "preference": {"source_id": "P", "fact_index": 0}}
        result = checker.grade_fragment(packet([job, pref],
                                               assessment("allowance", predicate="constraint_unresolved",
                                                          scope={"status": "pending"}), check))
        self.assertNotEqual(result["verdict"], "pass")

    def test_superseded_permission_cannot_support_request_limit(self):
        old = source("J", "job_description", fact("role", "remote_work", "remote schedule",
                     "permission", measure=measure(None, 4)))
        update = source("U", "employer_update",
                        fact("U", "supersedes", "J", "observation"),
                        fact("role", "remote_work", "remote schedule", "permission",
                             measure=measure(None, 1)))
        pref = source("P", "preference", fact("candidate", "remote_work", "remote schedule",
                      "preference_constraint", scope={"priority": "nice_to_have"},
                      measure=measure(2, 2)))
        check = {"op": "permission_limit", "offer": {"source_id": "J", "fact_index": 0},
                 "preference": {"source_id": "P", "fact_index": 0}}
        result = checker.grade_fragment(packet([old, update, pref],
                                               assessment("remote schedule", predicate="request_within_limit"),
                                               check))
        self.assertNotEqual(result["verdict"], "pass")

    def test_negative_onboarding_requirement_cannot_pass(self):
        job = source("J", "job_description",
                     fact("role", "station_attendance", "onboarding", "requirement",
                          polarity="negative", time={"phase": "onboarding"},
                          measure=measure(30, 30, kind="count", unit="day", per=None)),
                     fact("role", "remote_work", "work_location", "permission",
                          time={"phase": "after_onboarding"}))
        pref = source("P", "preference", fact("candidate", "station_attendance", "onboarding",
                      "preference_constraint", scope={"priority": "must_have", "requires_remote_after": True},
                      time={"phase": "onboarding"},
                      measure=measure(None, 30, kind="count", unit="day", per=None)))
        check = {"op": "onboarding", "offer": {"source_id": "J", "fact_index": 0},
                 "remote": {"source_id": "J", "fact_index": 1},
                 "preference": {"source_id": "P", "fact_index": 0}}
        result = checker.grade_fragment(packet([job, pref],
                                               assessment("onboarding", scope={"requires_remote_after": True},
                                                          time={"phase": "onboarding"}), check))
        self.assertNotEqual(result["verdict"], "pass")

    def test_planned_item_with_undecided_amount_is_still_pending(self):
        job = source("J", "job_description",
                     fact("employer", "learning_allowance", "allowance", "observation",
                          scope={"status": "planned"}),
                     fact("employer", "learning_allowance", "allowance", "observation",
                          scope={"status": "undecided"}))
        pref = source("P", "preference", fact("candidate", "learning_allowance", "allowance",
                      "preference_constraint", scope={"priority": "must_have"},
                      measure=measure(1000, None, kind="amount", unit="USD", per="calendar_year")))
        check = {"op": "pending", "offer": {"source_id": "J", "fact_index": 1},
                 "preference": {"source_id": "P", "fact_index": 0}}
        result = checker.grade_fragment(packet([job, pref],
                                               assessment("allowance", predicate="constraint_unresolved",
                                                          scope={"status": "undecided"}), check))
        self.assertEqual(result["verdict"], "pass")

    def test_current_unavailability_can_coexist_with_pending_procurement(self):
        job = source("J", "job_description",
                     fact("role", "live_captions", "team captions", "observation",
                          polarity="negative", scope={"status": "available_now"}),
                     fact("role", "live_captions", "team captions", "observation",
                          scope={"status": "pending", "reason": "procurement"}))
        pref = source("P", "preference", fact("candidate", "live_captions", "team captions",
                      "preference_constraint", scope={"priority": "must_have"}))
        check = {"op": "pending", "offer": {"source_id": "J", "fact_index": 1},
                 "preference": {"source_id": "P", "fact_index": 0}}
        result = checker.grade_fragment(packet([job, pref],
                                               assessment("team captions", predicate="constraint_unresolved",
                                                          scope={"status": "pending", "reason": "procurement"}), check))
        self.assertEqual(result["verdict"], "pass")

    def test_explicit_denial_of_pending_status_blocks_pending_pass(self):
        job = source("J", "job_description",
                     fact("employer", "learning_allowance", "allowance", "observation",
                          scope={"status": "pending"}),
                     fact("employer", "learning_allowance", "allowance", "observation",
                          polarity="negative", scope={"status": "pending"}))
        pref = source("P", "preference", fact("candidate", "learning_allowance", "allowance",
                      "preference_constraint", scope={"priority": "must_have"},
                      measure=measure(1000, None, kind="amount", unit="USD", per="calendar_year")))
        check = {"op": "pending", "offer": {"source_id": "J", "fact_index": 0},
                 "preference": {"source_id": "P", "fact_index": 0}}
        result = checker.grade_fragment(packet([job, pref],
                                               assessment("allowance", predicate="constraint_unresolved",
                                                          scope={"status": "pending"}), check))
        self.assertNotEqual(result["verdict"], "pass")

    def test_unscoped_denial_of_property_blocks_pending_pass(self):
        job = source("J", "job_description",
                     fact("employer", "learning_allowance", "allowance", "observation",
                          scope={"status": "pending"}),
                     fact("employer", "learning_allowance", "allowance", "observation",
                          polarity="negative"))
        pref = source("P", "preference", fact("candidate", "learning_allowance", "allowance",
                      "preference_constraint", scope={"priority": "must_have"},
                      measure=measure(1000, None, kind="amount", unit="USD", per="calendar_year")))
        check = {"op": "pending", "offer": {"source_id": "J", "fact_index": 0},
                 "preference": {"source_id": "P", "fact_index": 0}}
        result = checker.grade_fragment(packet([job, pref],
                                               assessment("allowance", predicate="constraint_unresolved",
                                                          scope={"status": "pending"}), check))
        self.assertNotEqual(result["verdict"], "pass")


if __name__ == "__main__":
    unittest.main()
