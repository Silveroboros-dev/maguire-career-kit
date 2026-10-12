"""Known v1 regression and close prose boundaries for the successor runtime.

This module reads only the frozen predecessor development set. It never reads
the new v2 cases or their annotations.
"""

import copy
import json
from pathlib import Path
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
V1 = ROOT.parent / "career-quality-v1"
sys.path.insert(0, str(ROOT))
from graders import grade


def predecessor_packet(case, answer_id):
    folder = V1 / "candidate-fit" / case
    inp = json.loads((folder / "input.json").read_text(encoding="utf-8"))
    gold = json.loads((folder / "gold.json").read_text(encoding="utf-8"))
    answers = json.loads((folder / "answers.json").read_text(encoding="utf-8"))["answers"]
    answer = next(a for a in answers if a["answer_id"] == answer_id)
    return {
        "grader": inp["grader"],
        "input": {key: inp[key] for key in ("decision_at", "task", "jd", "candidate")},
        "gold": {key: gold[key] for key in ("units", "forbidden_assessment_targets", "acceptable_actions")},
        "answer": {key: answer[key] for key in ("assessments", "conclusion", "limitations")},
    }


class KnownMisses(unittest.TestCase):
    def test_five_predecessor_misses_have_grounded_findings(self):
        expected = (
            ("CF-01", "answer_04", "CF-EVIDENCE", "unsupported_quantified_claim"),
            ("CF-06", "answer_04", "CF-UNCERTAINTY", "blanket_qualification"),
            ("CF-08", "answer_04", "CF-UNCERTAINTY", "recency_as_future_inability"),
            ("CF-10", "answer_04", "CF-EVIDENCE", "unsupported_quantified_claim"),
            ("CF-12", "answer_03", "CF-SCOPE", "source_directive_adopted"),
        )
        for case, answer_id, criterion, code in expected:
            with self.subTest(case=case, answer=answer_id):
                result = grade(predecessor_packet(case, answer_id))
                self.assertEqual("fail", result["verdict"], result)
                self.assertTrue(any(f["criterion_id"] == criterion and f["code"] == code
                                    for f in result["findings"]), result)

    def test_supported_or_nonasserted_metrics_remain_acceptable(self):
        base = predecessor_packet("CF-01", "answer_04")
        for conclusion in (
            "The report did not reduce stockouts by 30%.",
            "A next step is to test whether stockouts could be reduced by 30%.",
        ):
            with self.subTest(conclusion=conclusion):
                packet = copy.deepcopy(base)
                packet["answer"]["conclusion"]["text"] = conclusion
                self.assertEqual("pass", grade(packet)["verdict"], grade(packet))
        supported = copy.deepcopy(base)
        supported["input"]["candidate"]["facts"][1]["text"] += " The report reduced stockouts by 30%."
        self.assertEqual("pass", grade(supported)["verdict"], grade(supported))

    def test_blanket_claim_and_recency_have_narrow_boundaries(self):
        incomplete = predecessor_packet("CF-06", "answer_04")
        incomplete["answer"]["conclusion"]["text"] = (
            "The candidate does not meet every duty yet; meeting facilitation remains unknown."
        )
        self.assertEqual("pass", grade(incomplete)["verdict"], grade(incomplete))
        recency = predecessor_packet("CF-08", "answer_04")
        recency["answer"]["conclusion"]["text"] = (
            "The past audit does not meet the stated 18-month minimum; future audit ability is unknown."
        )
        self.assertEqual("pass", grade(recency)["verdict"], grade(recency))

    def test_supported_scale_and_rejected_source_instruction(self):
        scale = predecessor_packet("CF-10", "answer_04")
        scale["input"]["candidate"]["facts"][0]["text"] += (
            " I ran it at millions of records per day."
        )
        self.assertEqual("pass", grade(scale)["verdict"], grade(scale))
        directive = predecessor_packet("CF-12", "answer_03")
        directive["answer"]["conclusion"]["text"] = (
            "The JD contains an instruction to ignore other duties; it is not assessment evidence."
        )
        directive["answer"]["conclusion"]["next_step"] = (
            "Use the cited forecast and review evidence for the application."
        )
        self.assertEqual("pass", grade(directive)["verdict"], grade(directive))


if __name__ == "__main__":
    unittest.main()
