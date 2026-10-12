"""Invented, outcome-blind fixtures for the offline grader rules."""

import copy
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from graders import grade


def candidate_packet():
    return {
        "grader": "candidate_fit",
        "input": {
            "decision_at": "2026-01-10T00:00:00Z", "task": "Assess the stated duty.",
            "jd": {"title": "Field Analyst", "sources": [
                {"id": "requirement", "text": "Prepare a sample map for the field team.",
                 "observed_at": "2026-01-01T00:00:00Z", "authority": "job_description", "supersedes": []}]},
            "candidate": {"facts": [
                {"id": "report", "text": "I prepared a sample map in a local exercise.",
                 "evidence_type": "self_report", "observed_at": "2026-01-02T00:00:00Z",
                 "status": "active", "supersedes": []}], "preferences": []}},
        "gold": {"units": [
            {"target_id": "requirement", "kind": "duty", "allowed_labels": ["supported"],
             "acceptable_evidence_sets": [["requirement", "report"]],
             "rationale": "The exercise is reported, not independently verified.",
             "required_points": ["A local map was prepared."],
             "forbidden_inferences": ["No production result is shown."]}],
            "forbidden_assessment_targets": [], "acceptable_actions": ["pursue", "show_existing_evidence"]},
        "answer": {"assessments": [
            {"target_id": "requirement", "label": "supported", "evidence": [
                {"source_id": "requirement", "quote": "Prepare a sample map"},
                {"source_id": "report", "quote": "I prepared a sample map"}],
             "rationale": "The candidate reports making a sample map in an exercise."}],
            "conclusion": {"action": "pursue", "text": "The work is relevant.",
                           "next_step": "Show the existing map and explain its limited scope."},
            "limitations": ["The experience is self-reported."]}}


def preference_packet():
    packet = candidate_packet()
    packet["grader"] = "preference_fit"
    packet["input"]["candidate"]["facts"] = []
    packet["input"]["candidate"]["preferences"] = [
        {"id": "hours", "text": "I require a 30-hour week.", "priority": "must_have",
         "allowed_exceptions": [], "confirmed_at": "2026-01-02T00:00:00Z"}]
    packet["input"]["jd"]["sources"][0]["text"] = "This is a 30-hour role."
    packet["gold"]["units"][0].update({
        "target_id": "hours", "kind": "hours", "allowed_labels": ["aligned"],
        "acceptable_evidence_sets": [["requirement"]],
    })
    packet["answer"]["assessments"] = [
        {"target_id": "hours", "label": "aligned", "evidence": [
            {"source_id": "requirement", "quote": "30-hour role"}],
         "rationale": "The stated hours match the preference."}]
    packet["answer"]["limitations"] = ["The terms are supplied snapshots."]
    return packet


def codes(result):
    return {f["code"] for f in result["findings"]}


class GraderTests(unittest.TestCase):
    def test_clean_packets_and_permitted_alternatives(self):
        for packet in (candidate_packet(), preference_packet()):
            with self.subTest(grader=packet["grader"]):
                self.assertEqual("pass", grade(packet)["verdict"])
                self.assertEqual("rule_checks_only", grade(packet)["assurance"])
        packet = candidate_packet()
        packet["gold"]["units"][0]["allowed_labels"].append("partial")
        packet["answer"]["assessments"][0]["label"] = "partial"
        packet["answer"]["conclusion"]["action"] = "show_existing_evidence"
        self.assertEqual("pass", grade(packet)["verdict"])

    def test_coverage_and_duplicate_are_answer_failures(self):
        packet = candidate_packet()
        packet["answer"]["assessments"] = []
        result = grade(packet)
        self.assertEqual("fail", result["verdict"])
        self.assertIn("missing_target", codes(result))
        packet = candidate_packet()
        packet["answer"]["assessments"].append(copy.deepcopy(packet["answer"]["assessments"][0]))
        self.assertIn("duplicate_target", codes(grade(packet)))

    def test_label_action_and_evidence_set(self):
        packet = candidate_packet()
        packet["answer"]["assessments"][0]["label"] = "contradicted"
        packet["answer"]["assessments"][0]["evidence"].pop()
        packet["answer"]["conclusion"]["action"] = "pass"
        self.assertTrue({"disallowed_label", "insufficient_source_set", "disallowed_action"} <= codes(grade(packet)))

    def test_unknown_source_and_nonliteral_quote_are_answer_failures(self):
        packet = candidate_packet()
        packet["answer"]["assessments"][0]["evidence"][1]["source_id"] = "missing"
        self.assertIn("unknown_source", codes(grade(packet)))
        packet = candidate_packet()
        packet["answer"]["assessments"][0]["evidence"][1]["quote"] = "I delivered a company-wide map"
        self.assertIn("nonliteral_quote", codes(grade(packet)))

    def test_withdrawn_fact_and_self_report_inflation(self):
        packet = candidate_packet()
        packet["input"]["candidate"]["facts"][0]["status"] = "withdrawn"
        self.assertIn("withdrawn_fact", codes(grade(packet)))
        packet = candidate_packet()
        packet["answer"]["assessments"][0]["rationale"] = "This was independently verified by a third party."
        self.assertIn("self_report_promoted", codes(grade(packet)))
        packet["answer"]["assessments"][0]["rationale"] = "This was not independently verified by a third party."
        self.assertNotIn("self_report_promoted", codes(grade(packet)))

    def test_unknown_cannot_be_stated_as_inability(self):
        packet = candidate_packet()
        packet["gold"]["units"][0]["allowed_labels"] = ["unknown"]
        packet["answer"]["assessments"][0]["label"] = "unknown"
        packet["answer"]["assessments"][0]["rationale"] = "The candidate cannot prepare a map."
        self.assertIn("unknown_as_inability", codes(grade(packet)))

    def test_corrected_role_term_is_not_current_evidence(self):
        packet = preference_packet()
        packet["input"]["jd"]["sources"].append({
            "id": "correction", "text": "Correction: the role now has 35 hours.",
            "observed_at": "2026-01-03T00:00:00Z", "authority": "employer_update",
            "supersedes": ["requirement"]})
        self.assertIn("superseded_role_term", codes(grade(packet)))

    def test_projection_leakage_and_bad_gold_are_invalid(self):
        packet = candidate_packet()
        packet["answer"]["answer_id"] = "answer_1"
        self.assertEqual("invalid", grade(packet)["verdict"])
        packet = candidate_packet()
        packet["gold"]["units"][0]["acceptable_evidence_sets"] = [["missing"]]
        self.assertEqual("invalid", grade(packet)["verdict"])

    def test_source_id_spelling_does_not_affect_verdict(self):
        packet = candidate_packet()
        changed = copy.deepcopy(packet)
        changed["input"]["jd"]["sources"][0]["id"] = "weird"
        changed["input"]["candidate"]["facts"][0]["id"] = "opaque"
        changed["gold"]["units"][0]["target_id"] = "weird"
        changed["gold"]["units"][0]["acceptable_evidence_sets"] = [["weird", "opaque"]]
        changed["answer"]["assessments"][0]["target_id"] = "weird"
        for citation, ident in zip(changed["answer"]["assessments"][0]["evidence"], ("weird", "opaque")):
            citation["source_id"] = ident
        self.assertEqual(grade(packet)["verdict"], grade(changed)["verdict"])

    def test_denied_or_planned_number_is_not_achieved_outcome(self):
        for extra in ("I did not improve completion by 30%.",
                      "My plan is to improve completion by 30%."):
            with self.subTest(extra=extra):
                packet = candidate_packet()
                packet["input"]["candidate"]["facts"][0]["text"] += " " + extra
                packet["answer"]["assessments"][0]["evidence"][1]["quote"] = extra
                packet["answer"]["assessments"][0]["rationale"] = "I improved completion by 30%."
                self.assertIn("unsupported_outcome_metric", codes(grade(packet)))

    def test_rationale_can_deny_or_propose_metric_without_claiming_it(self):
        for rationale in (
            "The source does not establish that the candidate improved completion by 30%.",
            "Next step: test whether completion can be improved by 30%.",
        ):
            with self.subTest(rationale=rationale):
                packet = candidate_packet()
                packet["answer"]["assessments"][0]["rationale"] = rationale
                self.assertNotIn("unsupported_outcome_metric", codes(grade(packet)))
        packet = candidate_packet()
        packet["answer"]["assessments"][0]["rationale"] = "The candidate improved completion by 30%."
        self.assertIn("unsupported_outcome_metric", codes(grade(packet)))

    def test_job_requirement_is_not_candidate_experience(self):
        packet = candidate_packet()
        packet["gold"]["units"][0]["acceptable_evidence_sets"] = [["requirement"]]
        packet["answer"]["assessments"][0]["evidence"] = [
            {"source_id": "requirement", "quote": "Prepare a sample map"}]
        self.assertIn("role_term_as_candidate_experience", codes(grade(packet)))

    def test_invented_employer_waiver_is_a_failure_even_with_correct_label(self):
        packet = preference_packet()
        packet["gold"]["units"][0]["allowed_labels"] = ["conflict"]
        packet["answer"]["assessments"][0]["label"] = "conflict"
        packet["answer"]["assessments"][0]["rationale"] = "An employer waiver has been granted."
        self.assertIn("invented_exception", codes(grade(packet)))

    def test_soft_advantage_cannot_offset_explicit_hard_conflict(self):
        packet = preference_packet()
        packet["gold"]["units"][0]["allowed_labels"] = ["conflict"]
        packet["answer"]["assessments"][0]["label"] = "conflict"
        packet["answer"]["conclusion"]["text"] = "High pay makes up for the must-have conflict."
        self.assertIn("soft_overrides_hard", codes(grade(packet)))


if __name__ == "__main__":
    unittest.main()
