"""Installed grader bundle executes both named v8 modes on invented fragments."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


KIT = Path(__file__).resolve().parents[1]


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def packet(grader):
    anchor = {"sha256": "a" * 64, "pointer": "", "start": 0, "end": 1, "quote": "x"}
    reading = {"subject": "candidate", "predicate": "invented_unregistered_predicate",
               "object": "example", "polarity": "positive", "modality": "observation",
               "epistemic_scope": "world", "scope": {}, "time": {}, "measure": None}
    sources = [{"id": "source", "kind": "candidate_fact" if grader == "candidate_fit" else "preference",
                "status": "active", "observed_at": "2026-01-01T00:00:00Z",
                "anchor": anchor, "facts": [reading]}]
    claims = [{"id": "claim", "anchor": anchor, "stance": "asserted",
               "readings": [reading], "check": None}]
    return {"schema": "maguire-claim-packet-v8", "grader": grader,
            "decision_at": "2026-02-01T00:00:00Z", "sources": sources, "claims": claims,
            "coverage": {"scope": "fragment", "status": "agent_reviewed",
                         "source_inventory_complete": True, "fragment_complete": True,
                         "source_sha256": digest(sources), "claims_sha256": digest(claims)}}


class InstalledGradersTest(unittest.TestCase):
    def test_both_modes_preserve_identity_and_unknown_predicate(self):
        with tempfile.TemporaryDirectory(prefix="maguire-graders-") as temporary:
            workspace = Path(temporary) / "candidate"
            subprocess.run([sys.executable, str(KIT / "install.py"), str(workspace)],
                           check=True, capture_output=True, text=True)
            cli = workspace / ".maguire/kit/graders/grade.py"
            for mode, grader in (("jd-fit", "candidate_fit"),
                                 ("employer-fit", "preference_fit")):
                with self.subTest(mode=mode):
                    value = packet(grader)
                    identity = digest(value)
                    input_path = workspace / (mode + ".jsonl")
                    output_path = workspace / (mode + ".out.jsonl")
                    input_path.write_text(json.dumps({"packet_sha256": identity, "packet": value}) + "\n")
                    result = subprocess.run([sys.executable, str(cli), "--mode", mode,
                                             "--packets", str(input_path), "--predictions", str(output_path)],
                                            capture_output=True, text=True)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    row = json.loads(output_path.read_text())
                    self.assertEqual(row["packet_sha256"], identity)
                    self.assertEqual(row["result"]["verdict"], "needs_review")
                    self.assertIsNone(row["result"]["whole_answer_verdict"])
                    self.assertIsNone(row["execution_error"])

    def test_wrong_mode_fails_before_output_creation(self):
        with tempfile.TemporaryDirectory(prefix="maguire-graders-") as temporary:
            workspace = Path(temporary) / "candidate"
            subprocess.run([sys.executable, str(KIT / "install.py"), str(workspace)],
                           check=True, capture_output=True)
            value = packet("candidate_fit")
            input_path = workspace / "packet.jsonl"
            output_path = workspace / "result.jsonl"
            input_path.write_text(json.dumps({"packet_sha256": digest(value), "packet": value}) + "\n")
            result = subprocess.run([sys.executable, str(workspace / ".maguire/kit/graders/grade.py"),
                                     "--mode", "employer-fit", "--packets", str(input_path),
                                     "--predictions", str(output_path)], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("does not match selected mode", result.stderr)
            self.assertFalse(output_path.exists())

    def test_source_manifest_matches_copied_runtime(self):
        bundle = KIT / "graders"
        manifest = json.loads((bundle / "source-manifest.json").read_text())
        self.assertEqual(manifest["runtime_version"], "maguire-claim-packet-v8")
        self.assertEqual(len(manifest["files"]), 7)
        for row in manifest["files"]:
            self.assertFalse(Path(row["source_relative_path"]).is_absolute())
            data = (bundle / row["bundled_path"]).read_bytes()
            self.assertEqual(len(data), row["bytes"])
            self.assertEqual(hashlib.sha256(data).hexdigest(), row["sha256"])


if __name__ == "__main__":
    unittest.main()
