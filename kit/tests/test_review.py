"""Synthetic end-to-end checks for the manual two-rubric review bundle."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


CLI = Path(__file__).resolve().parents[1] / "graders/review.py"


class ReviewBundleTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="maguire-review-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.answer = self.root / "RESULT.md"
        self.cv = self.root / "CV.txt"
        self.jd = self.root / "JD.txt"
        self.answer.write_text("Candidate built a prototype. Role terms are unknown.\n")
        self.cv.write_text("Candidate built a prototype. Prefers remote work.\n")
        self.jd.write_text("Build production services. Work arrangement unspecified.\n")
        self.bundle = self.root / "reviews/agent-001"

    def call(self, *args):
        return subprocess.run([sys.executable, str(CLI), *map(str, args)],
                              capture_output=True, text=True)

    def start(self):
        result = self.call("init", "--assessment", self.answer, "--cv", self.cv,
                           "--jd", self.jd, "--output", self.bundle)
        self.assertEqual(result.returncode, 0, result.stderr)

    def draft(self, mode):
        path = self.bundle / (mode + ".draft.json")
        return path, json.loads(path.read_text())

    def fill(self, mode, status="reviewed", empty=False):
        path, review = self.draft(mode)
        review.update({"reviewer": "Example reviewer", "method": "agent",
                       "status": status, "summary": "Evidence is limited.",
                       "needs_review_reason": "Preferences were not provided." if status == "needs_review" else "",
                       "score": ({"status": "scored", "value": 2.5,
                                  "range": {"low": 2, "high": 3},
                                  "rationale": "The cited evidence covers part of this axis.",
                                  "missing_input": ""} if status == "reviewed" else
                                 {"status": "needs_review", "value": None, "range": None,
                                  "rationale": "No approved candidate goal is supplied.",
                                  "missing_input": "Candidate goal or preference text"})})
        if not empty:
            if mode == "jd-fit":
                evidence = [{"source": "jd", "quote": "Build production services.",
                             "locator": "line 1"},
                            {"source": "cv", "quote": "Candidate built a prototype.",
                             "locator": "line 1"}]
                verdict = "partial"
            else:
                evidence = [{"source": "cv", "quote": "Prefers remote work.",
                             "locator": "line 1"}]
                verdict = "unknown"
            review["coverage"] = ["item-1"]
            review["findings"] = [{"id": "item-1", "verdict": verdict,
                                   "rationale": "The available texts leave a material gap.",
                                   "evidence": evidence,
                                   "answer_quote": "Role terms are unknown."}]
        path.write_text(json.dumps(review))
        return path

    def test_two_reviews_and_revised_answer_preserve_original(self):
        self.start()
        original = (self.bundle / "assessment.original").read_bytes()
        self.fill("jd-fit")
        self.fill("employer-fit")
        self.answer.write_text("A revised answer.\n")
        result = self.call("finalize", "--bundle", self.bundle, "--revised", self.answer)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.bundle / "assessment.original").read_bytes(), original)
        self.assertEqual((self.bundle / "assessment.revised").read_text(), "A revised answer.\n")
        receipt = json.loads((self.bundle / "receipt.json").read_text())
        self.assertEqual(receipt["bindings"]["assessment_sha256"],
                         hashlib.sha256(original).hexdigest())
        self.assertEqual(set(receipt["reviews"]), {"jd-fit", "employer-fit"})
        for mode in ("jd-fit", "employer-fit"):
            path = self.bundle / (mode + ".review.json")
            self.assertEqual(receipt["reviews"][mode]["sha256"],
                             hashlib.sha256(path.read_bytes()).hexdigest())
        repeated = self.call("finalize", "--bundle", self.bundle)
        self.assertNotEqual(repeated.returncode, 0)
        self.assertIn("already exists", repeated.stderr)

    def test_pending_or_omitted_review_creates_no_final_results(self):
        self.start()
        self.fill("jd-fit")
        pending = self.call("finalize", "--bundle", self.bundle)
        self.assertNotEqual(pending.returncode, 0)
        self.assertIn("pending", pending.stderr)
        (self.bundle / "employer-fit.draft.json").unlink()
        omitted = self.call("finalize", "--bundle", self.bundle)
        self.assertNotEqual(omitted.returncode, 0)
        self.assertFalse((self.bundle / "receipt.json").exists())
        self.assertFalse((self.bundle / "jd-fit.review.json").exists())

    def test_forged_binding_and_rubric_id_fail(self):
        self.start()
        self.fill("jd-fit")
        path = self.fill("employer-fit")
        review = json.loads(path.read_text())
        review["bindings"]["assessment_sha256"] = "0" * 64
        path.write_text(json.dumps(review))
        result = self.call("finalize", "--bundle", self.bundle)
        self.assertIn("bindings do not match", result.stderr)
        review["bindings"] = json.loads((self.bundle / "manifest.json").read_text())["bindings"]
        review["rubric_id"] = "maguire-jd-fit.1"
        path.write_text(json.dumps(review))
        result = self.call("finalize", "--bundle", self.bundle)
        self.assertIn("wrong schema or rubric ID", result.stderr)
        self.assertFalse((self.bundle / "receipt.json").exists())

    def test_snapshot_drift_fails_even_with_completed_drafts(self):
        self.start()
        self.fill("jd-fit")
        self.fill("employer-fit")
        (self.bundle / "cv.source").write_bytes(b"changed")
        result = self.call("finalize", "--bundle", self.bundle)
        self.assertIn("cv snapshot hash mismatch", result.stderr)
        self.assertFalse((self.bundle / "receipt.json").exists())

    def test_original_snapshot_drift_fails(self):
        self.start()
        self.fill("jd-fit")
        self.fill("employer-fit")
        (self.bundle / "assessment.original").write_text("changed answer\n")
        result = self.call("finalize", "--bundle", self.bundle)
        self.assertIn("assessment snapshot hash mismatch", result.stderr)
        self.assertFalse((self.bundle / "receipt.json").exists())

    def test_preexisting_result_is_preserved_without_receipt(self):
        self.start()
        self.fill("jd-fit")
        self.fill("employer-fit")
        existing = self.bundle / "jd-fit.review.json"
        existing.write_text("existing result")
        result = self.call("finalize", "--bundle", self.bundle)
        self.assertIn("already exists", result.stderr)
        self.assertEqual(existing.read_text(), "existing result")
        self.assertFalse((self.bundle / "employer-fit.review.json").exists())
        self.assertFalse((self.bundle / "receipt.json").exists())

    def test_missing_preferences_may_remain_needs_review(self):
        self.cv.write_text("Candidate built a prototype.\n")
        self.start()
        self.fill("jd-fit")
        self.fill("employer-fit", status="needs_review", empty=True)
        result = self.call("finalize", "--bundle", self.bundle)
        self.assertEqual(result.returncode, 0, result.stderr)
        employer = json.loads((self.bundle / "employer-fit.review.json").read_text())
        self.assertEqual(employer["status"], "needs_review")
        self.assertEqual(employer["coverage"], [])
        self.assertTrue(employer["needs_review_reason"])

    def test_score_contract_rejects_invalid_values_and_ranges(self):
        self.start()
        path = self.fill("jd-fit")
        self.fill("employer-fit")
        base = json.loads(path.read_text())
        cases = [
            ("missing", lambda row: row.pop("score"), "invalid fields"),
            ("boolean", lambda row: row["score"].update(value=True), "half-point"),
            ("off-step", lambda row: row["score"].update(value=2.6), "half-point"),
            ("too-large", lambda row: row["score"].update(value=5.5), "half-point"),
            ("nonfinite", lambda row: row["score"].update(value=float("nan")), "half-point"),
            ("inverted", lambda row: row["score"].update(range={"low": 3, "high": 2}), "range"),
            ("outside", lambda row: row["score"].update(range={"low": 0, "high": 2}), "range"),
            ("range-bool", lambda row: row["score"].update(range={"low": False, "high": 3}), "range"),
        ]
        for name, mutate, error in cases:
            with self.subTest(name=name):
                review = json.loads(json.dumps(base))
                mutate(review)
                path.write_text(json.dumps(review))
                result = self.call("finalize", "--bundle", self.bundle)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(error, result.stderr)
                self.assertFalse((self.bundle / "receipt.json").exists())

    def test_unscored_requires_missing_input_and_review_status(self):
        self.cv.write_text("Candidate built a prototype.\n")
        self.start()
        self.fill("jd-fit")
        path = self.fill("employer-fit", status="needs_review", empty=True)
        base = json.loads(path.read_text())
        for name, change in (
            ("no missing input", {"missing_input": ""}),
            ("made up midpoint", {"value": 2.5}),
            ("fake range", {"range": {"low": 2, "high": 3}}),
        ):
            with self.subTest(name=name):
                review = json.loads(json.dumps(base))
                review["score"].update(change)
                path.write_text(json.dumps(review))
                result = self.call("finalize", "--bundle", self.bundle)
                self.assertNotEqual(result.returncode, 0)
        review = json.loads(json.dumps(base))
        review["status"] = "reviewed"
        review["needs_review_reason"] = ""
        path.write_text(json.dumps(review))
        result = self.call("finalize", "--bundle", self.bundle)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unscored result", result.stderr)
        self.assertFalse((self.bundle / "receipt.json").exists())

    def test_jd_cannot_be_unscored_when_candidate_source_is_present(self):
        self.start()
        path = self.fill("jd-fit", status="needs_review", empty=True)
        self.fill("employer-fit")
        review = json.loads(path.read_text())
        review["needs_review_reason"] = "Candidate source is allegedly missing."
        review["score"]["missing_input"] = "Candidate CV"
        path.write_text(json.dumps(review))
        result = self.call("finalize", "--bundle", self.bundle)
        self.assertIn("requires absent candidate source", result.stderr)
        self.assertFalse((self.bundle / "receipt.json").exists())

    def test_absent_candidate_source_can_be_unscored(self):
        result = self.call("init", "--assessment", self.answer, "--jd", self.jd,
                           "--output", self.bundle)
        self.assertEqual(result.returncode, 0, result.stderr)
        jd_path = self.fill("jd-fit", status="needs_review", empty=True)
        jd = json.loads(jd_path.read_text())
        jd["needs_review_reason"] = "No candidate source was supplied."
        jd["score"]["rationale"] = "The JD is available but no candidate evidence was supplied."
        jd["score"]["missing_input"] = "Candidate CV or career bank"
        jd_path.write_text(json.dumps(jd))
        self.fill("employer-fit", status="needs_review", empty=True)
        result = self.call("finalize", "--bundle", self.bundle)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIsNone(json.loads((self.bundle / "manifest.json").read_text())["bindings"]["cv_sha256"])

    def test_legacy_manifest_cannot_finalize_under_new_contract(self):
        self.start()
        manifest_path = self.bundle / "manifest.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["schema"] = "maguire-fit-review.1"
        manifest_path.write_text(json.dumps(manifest))
        result = self.call("finalize", "--bundle", self.bundle)
        self.assertIn("legacy .1 bundle is read-only", result.stderr)
        self.assertFalse((self.bundle / "receipt.json").exists())

    def test_template_or_invalid_method_cannot_be_finalized(self):
        self.start()
        self.fill("jd-fit")
        path = self.fill("employer-fit")
        review = json.loads(path.read_text())
        review["method"] = "automatic_pass"
        path.write_text(json.dumps(review))
        result = self.call("finalize", "--bundle", self.bundle)
        self.assertIn("invalid review method", result.stderr)
        self.assertFalse((self.bundle / "receipt.json").exists())

    def test_source_quote_must_match_text_snapshot(self):
        self.start()
        path = self.fill("jd-fit")
        self.fill("employer-fit")
        review = json.loads(path.read_text())
        review["findings"][0]["evidence"][0]["quote"] = "A requirement not in the JD."
        path.write_text(json.dumps(review))
        result = self.call("finalize", "--bundle", self.bundle)
        self.assertIn("source quote is absent from snapshot", result.stderr)
        self.assertFalse((self.bundle / "receipt.json").exists())

    def test_jd_non_unknown_findings_reject_one_sided_evidence(self):
        self.start()
        path = self.fill("jd-fit")
        self.fill("employer-fit")
        base = json.loads(path.read_text())
        for verdict in ("supported", "partial", "contradicted"):
            for evidence in ([base["findings"][0]["evidence"][0]],
                             [base["findings"][0]["evidence"][1]]):
                with self.subTest(verdict=verdict, source=evidence[0]["source"]):
                    review = json.loads(json.dumps(base))
                    review["findings"][0]["verdict"] = verdict
                    review["findings"][0]["evidence"] = evidence
                    path.write_text(json.dumps(review))
                    result = self.call("finalize", "--bundle", self.bundle)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("needs both JD and CV/bank evidence", result.stderr)
                    self.assertFalse((self.bundle / "receipt.json").exists())

    def test_employer_alignment_or_conflict_rejects_one_sided_evidence(self):
        self.start()
        self.fill("jd-fit")
        path = self.fill("employer-fit")
        base = json.loads(path.read_text())
        for verdict in ("aligned", "conflict"):
            for evidence in ([{"source": "jd", "quote": "Work arrangement unspecified."}],
                             [{"source": "cv", "quote": "Prefers remote work."}]):
                with self.subTest(verdict=verdict, source=evidence[0]["source"]):
                    review = json.loads(json.dumps(base))
                    review["findings"][0]["verdict"] = verdict
                    review["findings"][0]["evidence"] = evidence
                    path.write_text(json.dumps(review))
                    result = self.call("finalize", "--bundle", self.bundle)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("needs JD and candidate preference evidence", result.stderr)
                    self.assertFalse((self.bundle / "receipt.json").exists())

    def test_unknown_findings_accept_available_side_only(self):
        self.cv.write_text("Candidate built a prototype.\n")
        self.start()
        jd_path = self.fill("jd-fit")
        employer_path = self.fill("employer-fit")
        jd = json.loads(jd_path.read_text())
        jd["findings"][0]["verdict"] = "unknown"
        jd["findings"][0]["rationale"] = "The CV fact alone does not establish the JD requirement."
        jd["findings"][0]["evidence"] = [jd["findings"][0]["evidence"][1]]
        jd_path.write_text(json.dumps(jd))
        employer = json.loads(employer_path.read_text())
        employer["findings"][0]["rationale"] = "No approved preference was supplied for this JD term."
        employer["findings"][0]["evidence"] = [
            {"source": "jd", "quote": "Work arrangement unspecified."}]
        employer_path.write_text(json.dumps(employer))
        result = self.call("finalize", "--bundle", self.bundle)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_bank_can_supply_candidate_evidence_and_goals(self):
        bank = self.root / "bank.md"
        bank.write_text("I built a prototype. I prefer remote work.\n")
        self.cv.write_text("Candidate profile.\n")
        result = self.call("init", "--assessment", self.answer, "--cv", self.cv,
                           "--jd", self.jd, "--bank", bank, "--output", self.bundle)
        self.assertEqual(result.returncode, 0, result.stderr)
        jd_path = self.fill("jd-fit")
        employer_path = self.fill("employer-fit")
        jd = json.loads(jd_path.read_text())
        jd["findings"][0]["evidence"][1] = {"source": "bank", "quote": "I built a prototype."}
        jd_path.write_text(json.dumps(jd))
        employer = json.loads(employer_path.read_text())
        employer["findings"][0]["evidence"] = [
            {"source": "jd", "quote": "Work arrangement unspecified."},
            {"source": "bank", "quote": "I prefer remote work."}]
        employer_path.write_text(json.dumps(employer))
        result = self.call("finalize", "--bundle", self.bundle)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.bundle / "bank.source").read_text(), bank.read_text())


if __name__ == "__main__":
    unittest.main()
