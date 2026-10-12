"""Outcome-blind boundary checks for the pure offline grader API.

All packets here are invented for this module. No authored answer or annotation
from the development dataset is imported.
"""

import copy
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from graders import grade


def candidate_packet():
    return {
        "grader": "candidate_fit",
        "input": {
            "decision_at": "2026-10-12T00:00:00Z",
            "task": "Assess the candidate against the role using only supplied sources.",
            "jd": {
                "title": "Prototype Engineer",
                "sources": [
                    {
                        "id": "jd_prototype",
                        "text": "Build a Python prototype for internal review.",
                        "observed_at": "2026-10-01T00:00:00Z",
                        "authority": "job_description",
                        "supersedes": [],
                    }
                ],
            },
            "candidate": {
                "facts": [
                    {
                        "id": "fact_prototype",
                        "text": "I built a Python prototype for an internal review.",
                        "evidence_type": "self_report",
                        "observed_at": "2026-09-01T00:00:00Z",
                        "status": "active",
                        "supersedes": [],
                    },
                    {
                        "id": "fact_irrelevant",
                        "text": "I organized the office library.",
                        "evidence_type": "self_report",
                        "observed_at": "2026-09-01T00:00:00Z",
                        "status": "active",
                        "supersedes": [],
                    },
                ],
                "preferences": [],
            },
        },
        "gold": {
            "units": [
                {
                    "target_id": "jd_prototype",
                    "kind": "duty",
                    "allowed_labels": ["supported"],
                    "acceptable_evidence_sets": [["fact_prototype"]],
                    "rationale": "The self-report supports prototype work, with no production claim.",
                    "required_points": ["Prototype work is supported by a self-report."],
                    "forbidden_inferences": ["Production deployment is proven."],
                }
            ],
            "forbidden_assessment_targets": [],
            "acceptable_actions": ["pursue", "show_existing_evidence"],
        },
        "answer": {
            "assessments": [
                {
                    "target_id": "jd_prototype",
                    "label": "supported",
                    "evidence": [
                        {
                            "source_id": "fact_prototype",
                            "quote": "I built a Python prototype for an internal review.",
                        }
                    ],
                    "rationale": "The self-report describes the requested prototype work; deployment is unproven.",
                }
            ],
            "conclusion": {
                "action": "pursue",
                "text": "The described prototype work supports pursuing this role.",
                "next_step": "Show the existing prototype and explain its limits.",
            },
            "limitations": ["This is a self-report, not independent verification."],
        },
    }


def preference_packet():
    return {
        "grader": "preference_fit",
        "input": {
            "decision_at": "2026-10-12T00:00:00Z",
            "task": "Assess the role against the person's stated conditions.",
            "jd": {
                "title": "Hybrid Analyst",
                "sources": [
                    {
                        "id": "jd_office",
                        "text": "This role requires three office days each week.",
                        "observed_at": "2026-10-01T00:00:00Z",
                        "authority": "job_description",
                        "supersedes": [],
                    }
                ],
            },
            "candidate": {
                "facts": [],
                "preferences": [
                    {
                        "id": "pref_remote",
                        "text": "I cannot accept mandatory office days.",
                        "priority": "must_have",
                        "allowed_exceptions": ["I may ask whether the office rule can be waived."],
                        "confirmed_at": "2026-10-02T00:00:00Z",
                    }
                ],
            },
        },
        "gold": {
            "units": [
                {
                    "target_id": "pref_remote",
                    "kind": "expectation",
                    "allowed_labels": ["conflict"],
                    "acceptable_evidence_sets": [["jd_office", "pref_remote"]],
                    "rationale": "The mandatory office requirement conflicts with zero mandatory office days.",
                    "required_points": ["Three required office days conflict with this must-have."],
                    "forbidden_inferences": ["A waiver has already been granted."],
                }
            ],
            "forbidden_assessment_targets": [],
            "acceptable_actions": ["pass", "clarify"],
        },
        "answer": {
            "assessments": [
                {
                    "target_id": "pref_remote",
                    "label": "conflict",
                    "evidence": [
                        {"source_id": "jd_office", "quote": "requires three office days each week"},
                        {"source_id": "pref_remote", "quote": "cannot accept mandatory office days"},
                    ],
                    "rationale": "The published three-day rule conflicts with the stated must-have; a waiver is unknown.",
                }
            ],
            "conclusion": {
                "action": "clarify",
                "text": "Ask about a waiver before deciding whether to apply.",
                "next_step": "Ask whether all mandatory office days can be waived; pass if not.",
            },
            "limitations": ["No granted waiver is supplied."],
        },
    }


def failures(result):
    return [f for f in result["findings"] if f["severity"] in ("major", "critical")]


def normalized(result, id_map=None):
    id_map = id_map or {}
    return (
        result["verdict"],
        sorted(
            (f["criterion_id"], f["severity"], id_map.get(f["target_id"], f["target_id"]), f["code"])
            for f in failures(result)
        ),
    )


class GraderBoundaryTests(unittest.TestCase):
    def test_baseline_and_assurance(self):
        for packet in (candidate_packet(), preference_packet()):
            with self.subTest(grader=packet["grader"]):
                result = grade(packet)
                self.assertEqual("pass", result["verdict"], result)
                self.assertEqual("rule_checks_only", result["assurance"])
                self.assertEqual([], failures(result), result)

    def test_leaky_packet_is_invalid(self):
        for field, value in (
            ("case_id", "CF-01"),
            ("answer_id", "answer_01"),
            ("expected_verdict", "pass"),
            ("annotations", {"expected_verdict": "pass"}),
        ):
            packet = candidate_packet()
            packet[field] = value
            with self.subTest(field=field):
                self.assertEqual("invalid", grade(packet)["verdict"])

        for section, field, value in (
            ("input", "case_id", "CF-01"),
            ("gold", "critical_errors", []),
            ("answer", "answer_id", "answer_01"),
        ):
            packet = candidate_packet()
            packet[section][field] = value
            with self.subTest(section=section, field=field):
                self.assertEqual("invalid", grade(packet)["verdict"])

    def test_malformed_packet_is_invalid(self):
        malformed = [None, {}, {"grader": "candidate_fit"}, candidate_packet()]
        malformed[-1]["answer"]["assessments"] = "not a list"
        for packet in malformed:
            with self.subTest(packet=packet):
                self.assertEqual("invalid", grade(packet)["verdict"])

    def test_omitted_material_assessment_is_failure_not_invalid(self):
        packet = candidate_packet()
        packet["answer"]["assessments"] = []
        result = grade(packet)
        self.assertEqual("fail", result["verdict"], result)
        self.assertTrue(any(f["criterion_id"] == "CF-COVERAGE" and f["target_id"] == "jd_prototype" for f in failures(result)), result)

    def test_quote_must_be_literal_and_citation_relevant(self):
        invented = candidate_packet()
        invented["answer"]["assessments"][0]["evidence"][0]["quote"] = "I deployed this to production."
        result = grade(invented)
        self.assertEqual("fail", result["verdict"], result)
        self.assertTrue(any(f["criterion_id"] == "CF-EVIDENCE" for f in failures(result)), result)

        irrelevant = candidate_packet()
        irrelevant["answer"]["assessments"][0]["evidence"] = [
            {"source_id": "fact_irrelevant", "quote": "I organized the office library."}
        ]
        result = grade(irrelevant)
        self.assertEqual("fail", result["verdict"], result)
        self.assertTrue(any(f["target_id"] == "jd_prototype" for f in failures(result)), result)

    def test_job_requirement_cannot_prove_candidate_experience(self):
        packet = candidate_packet()
        packet["input"]["candidate"]["facts"] = []
        # Gold is a proposed annotation. Even an erroneously permissive source
        # set cannot turn an employer's request into candidate experience.
        packet["gold"]["units"][0]["acceptable_evidence_sets"] = [["jd_prototype"]]
        packet["answer"]["assessments"][0]["evidence"] = [
            {"source_id": "jd_prototype", "quote": "Build a Python prototype for internal review."}
        ]
        packet["answer"]["assessments"][0]["rationale"] = "The candidate has built the requested Python prototype."
        result = grade(packet)
        self.assertEqual("fail", result["verdict"], result)
        self.assertTrue(any(f["criterion_id"] == "CF-EVIDENCE" and f["target_id"] == "jd_prototype" for f in failures(result)), result)

    def test_source_id_renumbering_does_not_change_decision(self):
        for irrelevant_citation in (False, True):
            original = candidate_packet()
            if irrelevant_citation:
                original["answer"]["assessments"][0]["evidence"] = [
                    {"source_id": "fact_irrelevant", "quote": "I organized the office library."}
                ]
            renamed = copy.deepcopy(original)
            mapping = {"jd_prototype": "jd_731", "fact_prototype": "fact_908", "fact_irrelevant": "fact_219"}
            for source in renamed["input"]["jd"]["sources"]:
                source["id"] = mapping[source["id"]]
            for source in renamed["input"]["candidate"]["facts"]:
                source["id"] = mapping[source["id"]]
            for unit in renamed["gold"]["units"]:
                unit["target_id"] = mapping[unit["target_id"]]
                unit["acceptable_evidence_sets"] = [[mapping[s] for s in row] for row in unit["acceptable_evidence_sets"]]
            for assessment in renamed["answer"]["assessments"]:
                assessment["target_id"] = mapping[assessment["target_id"]]
                for citation in assessment["evidence"]:
                    citation["source_id"] = mapping[citation["source_id"]]
            inverse = {new: old for old, new in mapping.items()}
            with self.subTest(irrelevant_citation=irrelevant_citation):
                self.assertEqual(normalized(grade(original)), normalized(grade(renamed), inverse))

    def test_source_and_assessment_order_does_not_change_decision(self):
        packet = candidate_packet()
        second = copy.deepcopy(packet["input"]["jd"]["sources"][0])
        second["id"] = "jd_library"
        second["text"] = "Maintain an office library."
        packet["input"]["jd"]["sources"].append(second)
        packet["gold"]["units"].append({
            "target_id": "jd_library", "kind": "duty", "allowed_labels": ["supported"],
            "acceptable_evidence_sets": [["fact_irrelevant"]], "rationale": "The fact describes the task.",
            "required_points": ["Library work is reported."], "forbidden_inferences": [],
        })
        packet["answer"]["assessments"].append({
            "target_id": "jd_library", "label": "supported",
            "evidence": [{"source_id": "fact_irrelevant", "quote": "I organized the office library."}],
            "rationale": "The self-report describes library work.",
        })
        reordered = copy.deepcopy(packet)
        reordered["input"]["jd"]["sources"].reverse()
        reordered["input"]["candidate"]["facts"].reverse()
        reordered["gold"]["units"].reverse()
        reordered["answer"]["assessments"].reverse()
        self.assertEqual(normalized(grade(packet)), normalized(grade(reordered)))

    def test_allowed_action_and_label_alternatives(self):
        packet = preference_packet()
        first = grade(packet)
        self.assertEqual("pass", first["verdict"], first)
        packet["answer"]["conclusion"] = {
            "action": "pass", "text": "The stated office rule conflicts with the must-have.",
            "next_step": "Pass on the published conditions; reconsider only if a waiver is explicitly granted.",
        }
        second = grade(packet)
        self.assertEqual("pass", second["verdict"], second)

        cf = candidate_packet()
        cf["gold"]["units"][0]["allowed_labels"] = ["partial", "supported"]
        cf["answer"]["assessments"][0]["label"] = "partial"
        cf["answer"]["assessments"][0]["rationale"] = "The self-report supports a relevant prototype, but exact depth is uncertain."
        self.assertNotEqual("invalid", grade(cf)["verdict"])

    def test_unknown_does_not_mean_inability(self):
        packet = candidate_packet()
        packet["input"]["candidate"]["facts"] = []
        packet["gold"]["units"][0]["allowed_labels"] = ["unknown"]
        packet["gold"]["units"][0]["acceptable_evidence_sets"] = [[]]
        assessment = packet["answer"]["assessments"][0]
        assessment["label"] = "unknown"
        assessment["evidence"] = []
        assessment["rationale"] = "No supplied fact establishes whether the candidate has built a Python prototype."
        packet["answer"]["conclusion"] = {
            "action": "clarify", "text": "The experience is unknown from the supplied facts.",
            "next_step": "Ask for an existing example and its scope.",
        }
        packet["gold"]["acceptable_actions"] = ["clarify"]
        good = grade(packet)
        self.assertEqual("pass", good["verdict"], good)
        packet["answer"]["assessments"][0]["rationale"] = "The candidate cannot build a Python prototype."
        packet["answer"]["conclusion"]["text"] = "The candidate is unable to do this work."
        bad = grade(packet)
        self.assertEqual("fail", bad["verdict"], bad)
        self.assertTrue(any(f["criterion_id"] in ("CF-LABEL", "CF-EVIDENCE", "CF-UNCERTAINTY") for f in failures(bad)), bad)

    def test_negated_number_and_next_step_are_not_achievements(self):
        packet = candidate_packet()
        packet["input"]["jd"]["sources"][0]["text"] = "Have led three production launches."
        packet["input"]["candidate"]["facts"] = [{
            "id": "fact_prototype", "text": "I have not led three production launches.",
            "evidence_type": "self_report", "observed_at": "2026-09-01T00:00:00Z",
            "status": "active", "supersedes": [],
        }]
        packet["gold"]["units"][0].update({
            "allowed_labels": ["contradicted"],
            "rationale": "The candidate reports no such launches.",
            "required_points": ["The self-report explicitly denies three production launches."],
            "forbidden_inferences": ["Three launches were achieved."],
        })
        assessment = packet["answer"]["assessments"][0]
        assessment["label"] = "contradicted"
        assessment["evidence"] = [{"source_id": "fact_prototype", "quote": "I have not led three production launches."}]
        assessment["rationale"] = "I have not led three production launches, so I lack this required history."
        packet["gold"]["acceptable_actions"] = ["pass", "clarify"]
        packet["answer"]["conclusion"] = {
            "action": "pass", "text": "The explicit history does not meet the requirement.",
            "next_step": "Look for roles without the three-launch minimum.",
        }
        result = grade(packet)
        self.assertEqual("pass", result["verdict"], result)
        self.assertFalse(any(f["criterion_id"] == "CF-EVIDENCE" for f in failures(result)), result)

    def test_affirmative_overclaim_is_distinct_from_negated_source(self):
        packet = candidate_packet()
        packet["input"]["jd"]["sources"][0]["text"] = "Operate production systems."
        packet["input"]["candidate"]["facts"][0]["text"] = "I have not operated production systems."
        packet["gold"]["units"][0].update({
            "allowed_labels": ["unknown"],
            "acceptable_evidence_sets": [["fact_prototype"]],
            "rationale": "No past operations does not prove future inability.",
            "required_points": ["Past production operations are absent; future ability is unknown."],
            "forbidden_inferences": ["Production operation was achieved."],
        })
        assessment = packet["answer"]["assessments"][0]
        assessment["label"] = "supported"
        assessment["evidence"] = [{"source_id": "fact_prototype", "quote": "I have not operated production systems."}]
        assessment["rationale"] = "The candidate has operated production systems."
        packet["answer"]["conclusion"]["text"] = "The candidate has production operations experience."
        result = grade(packet)
        self.assertEqual("fail", result["verdict"], result)
        self.assertTrue(any(f["target_id"] == "jd_prototype" for f in failures(result)), result)

    def test_negated_or_planned_metric_is_not_an_achieved_outcome(self):
        for extra in (
            "I did not improve throughput by 30%.",
            "My next step is to improve throughput by 30%.",
        ):
            packet = candidate_packet()
            fact = packet["input"]["candidate"]["facts"][0]
            fact["text"] += " " + extra
            packet["answer"]["assessments"][0]["evidence"][0]["quote"] = fact["text"]
            packet["answer"]["assessments"][0]["rationale"] = "I built the prototype and improved throughput by 30%."
            with self.subTest(source=extra):
                result = grade(packet)
                self.assertEqual("fail", result["verdict"], result)
                self.assertTrue(any(f["criterion_id"] == "CF-EVIDENCE" and f["target_id"] == "jd_prototype" for f in failures(result)), result)

    def test_unknown_is_not_conclusion_level_inability(self):
        packet = candidate_packet()
        packet["input"]["candidate"]["facts"] = []
        packet["gold"]["units"][0]["allowed_labels"] = ["unknown"]
        packet["gold"]["units"][0]["acceptable_evidence_sets"] = [[]]
        packet["gold"]["acceptable_actions"] = ["clarify"]
        packet["answer"]["assessments"][0].update({
            "label": "unknown", "evidence": [],
            "rationale": "No supplied fact establishes whether the candidate can build a Python prototype.",
        })
        packet["answer"]["conclusion"] = {
            "action": "clarify", "text": "The candidate cannot build a Python prototype.",
            "next_step": "Ask for an existing example and its scope.",
        }
        result = grade(packet)
        self.assertEqual("fail", result["verdict"], result)
        self.assertTrue(any(f["criterion_id"] == "CF-UNCERTAINTY" for f in failures(result)), result)

    def test_correct_conflict_label_does_not_excuse_invented_waiver(self):
        packet = preference_packet()
        packet["answer"]["assessments"][0]["rationale"] = (
            "An employer waiver has been granted, so mandatory office days do not apply."
        )
        result = grade(packet)
        self.assertEqual("fail", result["verdict"], result)
        self.assertTrue(any(f["criterion_id"] in ("PF-EVIDENCE", "PF-UNKNOWN", "PF-INTERPRETATION")
                            and f["target_id"] == "pref_remote" for f in failures(result)), result)

    def test_hard_conflict_cannot_be_overridden_by_pay(self):
        packet = preference_packet()
        # A permissive proposed action list cannot authorize advice that
        # explicitly cancels a must-have using a soft advantage.
        packet["gold"]["acceptable_actions"].append("pursue")
        packet["answer"]["conclusion"] = {
            "action": "pursue",
            "text": "The high pay makes up for the mandatory office days; pursue this role.",
            "next_step": "Apply without asking about the office rule.",
        }
        result = grade(packet)
        self.assertEqual("fail", result["verdict"], result)
        self.assertTrue(any(f["criterion_id"] == "PF-PRIORITY" for f in failures(result)), result)


if __name__ == "__main__":
    unittest.main()
