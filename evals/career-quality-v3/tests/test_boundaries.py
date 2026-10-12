"""Reviewer-authored counterfactuals for v3 inference boundaries."""

import copy
import os
import sys
import unittest


sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from checker import check_claim, digest, grade_fragment  # noqa: E402


DECISION = "2026-10-12T10:00:00Z"


def anchor(text):
    return {"sha256": "a" * 64, "pointer": "/synthetic", "start": 0,
            "end": len(text), "quote": text}


def proposition(predicate, subject, object_, **changes):
    result = {"subject": subject, "predicate": predicate, "object": object_,
              "polarity": "positive", "modality": "observation",
              "epistemic_scope": "world", "scope": {}, "time": {}, "measure": None}
    result.update(changes)
    return result


def source(id_, kind, fact, observed_at="2026-10-11T10:00:00Z"):
    return {"id": id_, "kind": kind, "status": "active", "observed_at": observed_at,
            "anchor": anchor(id_), "facts": [fact]}


def claim(id_, reading, stance="asserted"):
    return {"id": id_, "anchor": anchor(id_), "stance": stance,
            "readings": [reading]}


def grade(sources, claims, **coverage_changes):
    coverage = {"scope": "fragment", "source_sha256": digest(sources),
                "claims_sha256": digest(claims), "status": "agent_reviewed",
                "source_inventory_complete": True, "fragment_complete": True}
    coverage.update(coverage_changes)
    return grade_fragment({"schema": "maguire-claim-packet-v3",
                           "grader": "preference_fit", "decision_at": DECISION,
                           "sources": sources, "claims": claims, "coverage": coverage})


class ReviewerBoundaries(unittest.TestCase):
    def test_unrestricted_hard_ban_applies_to_recurring_duty(self):
        duty = proposition("on_call", "role", "overnight_duty",
                           modality="requirement", time={"recurrence": "every_fourth_week"})
        ban = proposition("on_call", "candidate", "overnight_duty",
                          polarity="negative", modality="preference_constraint",
                          scope={"priority": "must_have", "exceptions": False,
                                 "quantifier": "all"})
        decision = proposition("compatible", "candidate", "overnight_duty",
                               modality="record_assessment")
        result = grade([source("jd", "job_description", duty),
                        source("preference", "preference", ban)], [claim("fit", decision)])
        self.assertEqual(result["claims"][0]["evidence_relation"], "contradicted")
        self.assertEqual(result["claims"][0]["rule"], "hard_preference_conflict")

    def test_same_object_unrelated_predicates_do_not_establish_fit(self):
        unrelated_preference = proposition("training_demo", "candidate", "overnight_duty",
                                           modality="preference_constraint")
        duty = proposition("on_call", "role", "overnight_duty", modality="requirement")
        decision = proposition("compatible", "candidate", "overnight_duty",
                               modality="record_assessment")
        result = grade([source("pref", "preference", unrelated_preference),
                        source("jd", "job_description", duty)], [claim("fit", decision)])
        self.assertNotEqual(result["verdict"], "pass")
        self.assertNotEqual(result["claims"][0]["evidence_relation"], "supported")

    def test_matching_object_cannot_hide_incompatible_frequency(self):
        ceiling = {"kind": "frequency", "unit": "weekday", "lower": 0,
                   "upper": 2, "per": "calendar_month"}
        weekly = {"kind": "frequency", "unit": "weekday", "lower": 2,
                  "upper": 2, "per": "week"}
        preference = proposition("station_attendance", "candidate", "field_station",
                                 modality="preference_constraint", measure=ceiling,
                                 scope={"priority": "must_have", "exceptions": False},
                                 time={"recurring": True})
        role = proposition("station_attendance", "role", "field_station",
                           modality="requirement", measure=weekly,
                           time={"recurring": True})
        decision = proposition("compatible", "candidate", "field_station",
                               modality="record_assessment", time={"recurring": True})
        result = grade([source("pref", "preference", preference),
                        source("jd", "job_description", role)], [claim("fit", decision)])
        self.assertNotEqual(result["verdict"], "pass")
        self.assertNotEqual(result["claims"][0]["evidence_relation"], "supported")

    def test_universal_ban_does_not_import_another_roles_requirement(self):
        ban = proposition("on_call", "candidate", "overnight_duty",
                          polarity="negative", modality="preference_constraint",
                          scope={"priority": "must_have", "exceptions": False,
                                 "quantifier": "all"})
        other_role = proposition("on_call", "role", "overnight_duty",
                                 modality="requirement", scope={"role": "B"})
        decision = proposition("compatible", "candidate", "overnight_duty",
                               modality="record_assessment", scope={"role": "A"})
        result = grade([source("pref", "preference", ban),
                        source("jd", "job_description", other_role)],
                       [claim("role_A_fit", decision)])
        self.assertNotEqual(result["claims"][0]["evidence_relation"], "contradicted")

    def test_universal_ban_does_not_import_another_schedule(self):
        ban = proposition("on_call", "candidate", "overnight_duty",
                          polarity="negative", modality="preference_constraint",
                          scope={"priority": "must_have", "exceptions": False,
                                 "quantifier": "all"})
        tuesday_duty = proposition("on_call", "role", "overnight_duty",
                                   modality="requirement", time={"event": "Tuesday"})
        monday_fit = proposition("compatible", "candidate", "overnight_duty",
                                 modality="record_assessment", time={"event": "Monday"})
        result = grade([source("pref", "preference", ban),
                        source("jd", "job_description", tuesday_duty)],
                       [claim("Monday_fit", monday_fit)])
        self.assertNotEqual(result["claims"][0]["evidence_relation"], "contradicted")

    def test_observation_order_does_not_make_a_rule_govern(self):
        older = source("old", "job_description",
                       proposition("remote_work", "editor_role", "work_location",
                                   modality="permission"), "2026-02-01T12:00:00Z")
        newer = source("new", "employer_update",
                       proposition("location_flexibility", "editor_role", "work_location"),
                       "2026-09-15T12:00:00Z")
        governing = proposition("governs", "new", "role_attendance",
                                modality="record_assessment")
        unsupported = grade([older, newer], [claim("authority", governing)])
        self.assertEqual(unsupported["claims"][0]["evidence_relation"], "not_established")
        explicit = copy.deepcopy(newer)
        explicit["facts"].append(copy.deepcopy(governing))
        supported = grade([older, explicit], [claim("authority", governing)])
        self.assertEqual(supported["claims"][0]["evidence_relation"], "supported")

    def test_one_supported_atom_does_not_mask_unsupported_promotion(self):
        report = proposition("console_use", "candidate", "signal_console",
                             modality="self_report", time={"last_use_year": 2021})
        premise = proposition("console_use", "candidate", "signal_console",
                              time={"last_use_year": 2021})
        conclusion = proposition("alert_escalation", "candidate", "signal_anomalies",
                                 polarity="negative", modality="ability",
                                 time={"event": "future_shift"})
        result = grade([source("career_fact", "candidate_fact", report)],
                       [claim("premise", premise), claim("projection", conclusion)])
        self.assertEqual(result["verdict"], "fail")
        self.assertEqual(result["claims"][0]["evidence_relation"], "supported")
        self.assertIn("self-report", result["claims"][0]["explanation"])
        self.assertEqual(result["claims"][1]["evidence_relation"], "not_established")
        self.assertEqual([item["claim_id"] for item in result["findings"]], ["projection"])

    def test_no_claims_and_unreviewed_inventory_cannot_pass(self):
        evidence = [source("record", "candidate_fact",
                           proposition("console_use", "candidate", "console"))]
        self.assertNotEqual(grade(evidence, [])["verdict"], "pass")
        assertion = claim("claim", proposition("console_use", "candidate", "console"))
        self.assertEqual(grade(evidence, [assertion], status="unreviewed")["verdict"],
                         "needs_review")

    def test_direct_claim_call_rejects_stale_content_binding(self):
        evidence = [source("record", "candidate_fact",
                           proposition("console_use", "candidate", "console"))]
        assertion = claim("claim", proposition("console_use", "candidate", "console"))
        coverage = {"scope": "fragment", "source_sha256": digest(evidence),
                    "claims_sha256": digest([assertion]), "status": "agent_reviewed",
                    "source_inventory_complete": True, "fragment_complete": True}
        changed = copy.deepcopy(evidence)
        changed[0]["facts"][0]["object"] = "another_console"
        result = check_claim(assertion, changed,
                             {"grader": "candidate_fit", "decision_at": DECISION,
                              "coverage": coverage})
        self.assertNotEqual(result["evidence_relation"], "supported")
        self.assertEqual(result["rule"], "invalid_input")

    def test_editorial_command_is_not_authority_even_in_candidate_record(self):
        command = proposition("evaluation_authority", "editorial_command", "ignore_evidence",
                              modality="evaluation_instruction")
        promoted = proposition("evaluation_authority", "editorial_command", "ignore_evidence",
                               modality="permission")
        result = grade([source("source", "candidate_fact", command)],
                       [claim("claim", promoted)])
        self.assertNotEqual(result["verdict"], "pass")
        self.assertIn("source_role", result["claims"][0]["axes"])


if __name__ == "__main__":
    unittest.main()
