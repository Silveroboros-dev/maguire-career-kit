"""Reviewer-authored, invented pairs for the narrow v5 corrections.

These packets are outside the frozen 40-case cohort. Values and wording are
intentionally different from the exposed cases; assertions test the contract
boundary and include the useful positive path alongside each refusal.
"""

import unittest

from test_review_probes import assessment, constraint, fact, measure, packet, source
import checker


class V5ReviewProbes(unittest.TestCase):
    def test_stipend_direct_fact_and_changed_amount(self):
        employer = source("OFFER", "job_description", fact(
            "employer", "stipend", "desk equipment", "observation",
            measure=measure(720, 720, kind="amount", unit="USD", per="calendar_year")))
        matching = fact("employer", "stipend", "desk equipment", "observation",
                        measure=measure(720, 720, kind="amount", unit="USD", per="calendar_year"))
        changed = fact("employer", "stipend", "desk equipment", "observation",
                       measure=measure(980, 980, kind="amount", unit="USD", per="calendar_year"))
        self.assertEqual(checker.grade_fragment(packet([employer], matching))["verdict"], "pass")
        self.assertNotEqual(checker.grade_fragment(packet([employer], changed))["verdict"], "pass")

    def test_onboarding_canonical_day_unit_pass_and_exceed(self):
        def run(required_days):
            offer = source("OFFER", "job_description",
                           fact("role", "station_attendance", "onboarding", "requirement",
                                time={"phase": "onboarding"},
                                measure=measure(required_days, required_days,
                                                kind="count", unit="day", per=None)),
                           fact("role", "remote_work", "work_location", "permission",
                                time={"phase": "after_onboarding"}))
            pref = source("PREF", "preference", fact(
                "candidate", "station_attendance", "onboarding", "preference_constraint",
                scope={"priority": "must_have", "requires_remote_after": True},
                time={"phase": "onboarding"},
                measure=measure(None, 28, kind="count", unit="day", per=None)))
            check = {"op": "onboarding", "offer": {"source_id": "OFFER", "fact_index": 0},
                     "remote": {"source_id": "OFFER", "fact_index": 1},
                     "preference": {"source_id": "PREF", "fact_index": 0}}
            reading = assessment("onboarding", scope={"requires_remote_after": True},
                                 time={"phase": "onboarding"})
            return checker.grade_fragment(packet([offer, pref], reading, check))["verdict"]

        self.assertEqual(run(27), "pass")
        self.assertEqual(run(29), "fail")

    def test_pending_and_current_unavailability_are_distinct(self):
        pref = source("PREF", "preference", fact(
            "candidate", "accessibility_service", "captioning", "preference_constraint",
            scope={"priority": "must_have"}))
        check = {"op": "pending", "offer": {"source_id": "OFFER", "fact_index": 0},
                 "preference": {"source_id": "PREF", "fact_index": 0}}
        reading = assessment("captioning", predicate="constraint_unresolved",
                             scope={"status": "pending"})

        def run(negative_scope):
            offer = source("OFFER", "job_description",
                           fact("role", "accessibility_service", "captioning", "observation",
                                scope={"status": "pending"}),
                           fact("role", "accessibility_service", "captioning", "observation",
                                polarity="negative", scope=negative_scope))
            return checker.grade_fragment(packet([offer, pref], reading, check))["verdict"]

        self.assertEqual(run({"status": "available_now"}), "pass")
        self.assertNotEqual(run({}), "pass")

    def test_explicit_denial_of_replacement_keeps_old_limit(self):
        old = source("OLD", "job_description", fact(
            "role", "station_attendance", "office", "requirement",
            measure=measure(3, 3)))
        pref = source("PREF", "preference", fact(
            "candidate", "station_attendance", "office", "preference_constraint",
            scope={"priority": "must_have"}, measure=measure(None, 2)))
        check = constraint("OLD", "PREF")
        reading = assessment("office")

        def run(*markers):
            note = source("NOTE", "employer_update", *markers)
            return checker.grade_fragment(packet([old, note, pref], reading, check))

        denial = fact("NOTE", "supersedes", "OLD", "observation", polarity="negative")
        result = run(denial)
        self.assertEqual(result["verdict"], "fail")
        self.assertEqual(result["claims"][0]["rule"], "constraint_interval")

        uncertain_markers = (
            fact("NOTE", "supersedes", "OLD", "observation", polarity="negative",
                 scope={"condition": "if policy changes"}),
            fact("NOTE", "supersedes", "OLD", "observation",
                 scope={"condition": "if manager approves"}),
            fact("NOTE", "supersedes", "OLD", "possibility"),
        )
        for marker in uncertain_markers:
            with self.subTest(marker=marker):
                self.assertEqual(run(marker)["verdict"], "needs_review")

        packet_denial = {**denial, "epistemic_scope": "packet"}
        self.assertEqual(run(packet_denial)["verdict"], "needs_review")

        conflicting = fact("NOTE", "supersedes", "OLD", "observation")
        self.assertEqual(run(denial, conflicting)["verdict"], "needs_review")

    def test_one_successor_denial_does_not_cancel_another_successor_update(self):
        old = source("OLD", "job_description", fact(
            "role", "station_attendance", "office", "requirement",
            measure=measure(3, 3)))
        denial = source("NO", "employer_update", fact(
            "NO", "supersedes", "OLD", "observation", polarity="negative"))
        replacement = source("YES", "employer_update", fact(
            "YES", "supersedes", "OLD", "observation"))
        pref = source("PREF", "preference", fact(
            "candidate", "station_attendance", "office", "preference_constraint",
            scope={"priority": "must_have"}, measure=measure(None, 2)))
        result = checker.grade_fragment(packet(
            [old, denial, replacement, pref], assessment("office"),
            constraint("OLD", "PREF")))
        self.assertEqual(result["verdict"], "needs_review")
        self.assertEqual(result["claims"][0]["rule"], "superseded_operand")


if __name__ == "__main__":
    unittest.main()
