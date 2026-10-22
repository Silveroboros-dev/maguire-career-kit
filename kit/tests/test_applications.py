"""Application register behavior using synthetic records in temporary folders."""

import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools/applications.py"
SPEC = importlib.util.spec_from_file_location("applications_tool", TOOL)
APPLICATIONS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(APPLICATIONS)


class ApplicationToolTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.register = self.root / "applications.md"

    def cli(self, *arguments, ok=True):
        result = subprocess.run(
            [sys.executable, str(TOOL), "--register", str(self.register), *arguments],
            text=True, capture_output=True,
        )
        if ok:
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        return result

    def init(self):
        return self.cli("init")

    def add(self, identifier="APP-001", *extra):
        return self.cli("add", "--id", identifier, "--role", "Fictional Co / Analyst",
                        "--date", "2026-10-21", "--provenance", "Candidate decision in test", *extra)

    def test_init_creates_one_empty_register_without_overwriting(self):
        self.assertTrue(self.init()["changed"])
        original = self.register.read_bytes()
        self.cli("init", ok=False)
        self.assertEqual(self.register.read_bytes(), original)
        self.assertEqual(self.cli("list")["records"], [])

    def test_adopts_exact_blank_template_and_preserves_prose(self):
        original = (ROOT / "templates/data/applications.md").read_bytes()
        self.register.write_bytes(original)
        added = self.add()["record"]
        self.assertEqual(added["id"], "APP-001")
        current = self.register.read_bytes()
        self.assertNotIn(b"`<APP-001>`", current)
        self.assertIn(original.split(b"\n\n")[-1], current)
        self.assertEqual(len(self.cli("list")["records"]), 1)

    def test_add_duplicate_fails_without_changing_bytes(self):
        self.init()
        self.add()
        before = self.register.read_bytes()
        self.cli("add", "--id", "APP-001", "--role", "Other",
                 "--date", "2026-10-22", "--provenance", "test", ok=False)
        self.assertEqual(self.register.read_bytes(), before)

    def test_update_by_id_preserves_other_row_and_all_existing_history(self):
        self.init()
        self.add()
        self.add("APP-002")
        before = self.register.read_text()
        untouched = next(line for line in before.splitlines(keepends=True) if line.startswith("| APP-002 |"))
        old_history = before[before.index(APPLICATIONS.HISTORY):]
        result = self.cli("update", "--id", "APP-001", "--status", "draft", "--next-action", "Candidate review",
                          "--date", "2026-10-22", "--provenance", "Draft prepared")
        current = self.register.read_text()
        self.assertEqual(result["record"]["status"], "draft")
        self.assertIn(untouched, current)
        self.assertIn(old_history, current)
        self.assertIn('"before": {', current)
        self.assertEqual(len(self.cli("list")["records"]), 2)

    def test_unknown_id_and_custom_schema_leave_bytes_unchanged(self):
        self.init()
        before = self.register.read_bytes()
        self.cli("update", "--id", "MISSING", "--status", "draft", "--date", "2026-10-21", "--provenance", "test", ok=False)
        self.assertEqual(self.register.read_bytes(), before)
        custom = b"# Existing private register\n\n| Role | State |\n| --- | --- |\n| Fictional | draft |\n"
        self.register.write_bytes(custom)
        self.cli("list", ok=False)
        self.cli("add", "--id", "APP-1", "--role", "Synthetic", "--date", "2026-10-21", "--provenance", "test", ok=False)
        self.assertEqual(self.register.read_bytes(), custom)

    def test_submitted_needs_explicit_confirmation_or_evidence(self):
        self.init()
        self.add()
        before = self.register.read_bytes()
        self.cli("update", "--id", "APP-001", "--status", "submitted", "--date", "2026-10-21", "--provenance", "Draft requested", ok=False)
        self.assertEqual(self.register.read_bytes(), before)
        result = self.cli("update", "--id", "APP-001", "--status", "submitted", "--date", "2026-10-21", "--provenance", "Candidate confirmed send in test", "--confirmed-send")
        self.assertEqual(result["record"]["status"], "submitted")
        self.assertIn('"confirmed_send": true', self.register.read_text())
        self.add("APP-002", "--status", "submitted", "--submission-evidence", "synthetic-confirmation.txt")
        self.assertIn('"submission_evidence": "synthetic-confirmation.txt"', self.register.read_text())

    def test_send_flags_cannot_mark_a_draft_as_sent(self):
        self.init()
        before = self.register.read_bytes()
        self.cli("add", "--id", "APP-001", "--role", "Synthetic", "--date", "2026-10-21", "--provenance", "Draft", "--confirmed-send", ok=False)
        self.assertEqual(self.register.read_bytes(), before)

    def test_existing_submitted_record_can_receive_a_followup_without_a_new_send(self):
        self.init()
        self.add("APP-001", "--status", "submitted", "--confirmed-send")
        result = self.cli("update", "--id", "APP-001", "--next-action", "Await response", "--date", "2026-10-22", "--provenance", "Candidate follow-up decision")
        self.assertEqual(result["record"]["status"], "submitted")
        self.assertEqual(result["record"]["next_action"], "Await response")

    def test_pipes_backslashes_and_unicode_roundtrip_without_new_columns(self):
        self.init()
        role = "Компания | Analyst \\ Research"
        event = "A `quoted` note | literal \\"
        self.add("APP-001", "--role", role, "--event", event)
        record = self.cli("find", "--id", "APP-001")["records"][0]
        self.assertEqual(record["role"], role)
        self.assertIn("\\u0060quoted\\u0060", self.register.read_text())
        self.assertEqual(len(self.cli("list")["records"]), 1)

    def test_invalid_input_never_mutates_register(self):
        self.init()
        before = self.register.read_bytes()
        cases = [
            ["--id", "../APP-001"], ["--role", "Line\nInjected"],
            ["--role", "Line\u2028Injected"], ["--date", "2026-02-30"],
            ["--provenance", ""], ["--status", "sent"],
            ["--next-action", "x" * 2001],
        ]
        for extra in cases:
            with self.subTest(extra=extra):
                self.cli("add", "--id", "APP-001", "--role", "Synthetic", "--date", "2026-10-21", "--provenance", "test", *extra, ok=False)
                self.assertEqual(self.register.read_bytes(), before)

    def test_list_filters_paginates_and_enforces_bounds(self):
        self.init()
        # Prepare many synthetic records directly to avoid testing subprocess
        # startup 25 times; tool parsing/filtering still exercises real CLI.
        register = APPLICATIONS.initial_register().decode()
        marker = "| --- | --- | --- | --- | --- | --- | --- |\n"
        rows = "".join(APPLICATIONS.row_line(dict(zip(APPLICATIONS.FIELDS, (
            f"APP-{index:03}", "Synthetic Analyst", "Unknown", "draft" if index % 2 else "considering",
            "2026-10-21 — synthetic fixture", f"applications/APP-{index:03}/", "Review",
        ))), "\n") for index in range(25))
        self.register.write_text(register.replace(marker, marker + rows))
        first = self.cli("list")
        self.assertEqual(len(first["records"]), 20)
        self.assertEqual(first["matched"], 25)
        self.assertTrue(first["has_more"])
        last = self.cli("list", "--offset", "20")
        self.assertEqual(len(last["records"]), 5)
        self.assertFalse(last["has_more"])
        self.assertEqual(self.cli("list", "--status", "draft")["matched"], 12)
        self.assertEqual(self.cli("find", "--query", "ANALYST", "--limit", "3")["matched"], 25)
        self.assertEqual(len(self.cli("find", "--query", "ANALYST", "--limit", "3")["records"]), 3)
        for bounds in (("--limit", "0"), ("--limit", "101"), ("--offset", "-1")):
            self.cli("list", *bounds, ok=False)

    def test_lock_conflict_leaves_register_and_existing_lock_untouched(self):
        self.init()
        before = self.register.read_bytes()
        lock = self.register.with_name(self.register.name + ".lock")
        lock.write_text("synthetic other writer\n")
        self.cli("add", "--id", "APP-001", "--role", "Synthetic", "--date", "2026-10-21", "--provenance", "test", ok=False)
        self.assertEqual(self.register.read_bytes(), before)
        self.assertEqual(lock.read_text(), "synthetic other writer\n")

    def test_symlink_register_and_parent_are_never_mutated(self):
        self.init()
        original = self.register.read_bytes()
        link = self.root / "link.md"
        link.symlink_to(self.register)
        self.register = link
        self.cli("add", "--id", "APP-001", "--role", "Synthetic", "--date", "2026-10-21", "--provenance", "test", ok=False)
        self.assertEqual(link.resolve().read_bytes(), original)
        parent = self.root / "linked-directory"
        parent.symlink_to(self.root, target_is_directory=True)
        self.register = parent / "new.md"
        self.cli("init", ok=False)
        self.assertFalse((self.root / "new.md").exists())

    def test_noncooperating_change_detected_before_atomic_replace(self):
        self.init()
        before = self.register.read_bytes()
        self.register.write_bytes(before + b"\nManual concurrent edit\n")
        with self.assertRaises(APPLICATIONS.RegisterError):
            APPLICATIONS.write_atomic(self.register, before, before + b"\nTool edit\n")
        self.assertTrue(self.register.read_bytes().endswith(b"Manual concurrent edit\n"))
        self.assertFalse(list(self.root.glob(".applications-*")))

    def test_init_cannot_overwrite_a_noncooperating_new_file(self):
        self.register.write_text("Another writer's data\n")
        with self.assertRaises(FileExistsError):
            APPLICATIONS.write_atomic(self.register, None, APPLICATIONS.initial_register())
        self.assertEqual(self.register.read_text(), "Another writer's data\n")

    def test_crlf_and_untouched_surrounding_prose_are_preserved(self):
        original = APPLICATIONS.initial_register().replace(b"\n", b"\r\n") + b"\r\nOwner prose stays here.\r\n"
        self.register.write_bytes(original)
        self.add()
        current = self.register.read_bytes()
        self.assertIn(b"Owner prose stays here.\r\n", current)
        self.assertNotIn(b"\n", current.replace(b"\r\n", b""))

    def test_malformed_rows_duplicate_ids_and_multiple_tables_fail_closed(self):
        initial = APPLICATIONS.initial_register().decode()
        malformed = initial.replace("| --- |", "| -- |", 1)
        for body in (malformed, initial + initial):
            with self.subTest(body=body):
                self.register.write_text(body)
                self.cli("list", ok=False)
                self.assertEqual(self.register.read_text(), body)
        self.register.write_text(initial)
        self.add()
        body = self.register.read_text()
        row = next(line for line in body.splitlines(keepends=True) if line.startswith("| APP-001 |"))
        malformed = body.replace(row, row + row)
        self.register.write_text(malformed)
        self.cli("list", ok=False)
        self.assertEqual(self.register.read_text(), malformed)

    def test_fenced_examples_and_malformed_adjacent_rows_are_not_live_records(self):
        initial = APPLICATIONS.initial_register().decode()
        for body in ("```markdown\n" + initial + "```\n", "~~~markdown\n" + initial + "~~~\n"):
            self.register.write_text(body)
            self.cli("list", ok=False)
            self.assertEqual(self.register.read_text(), body)
        malformed = initial.replace("| --- | --- | --- | --- | --- | --- | --- |\n",
            "| --- | --- | --- | --- | --- | --- | --- |\n"
            "APP-002 | Synthetic | Unknown | draft | Unknown | applications/APP-002/ | Review |\n")
        self.register.write_text(malformed)
        self.cli("add", "--id", "APP-002", "--role", "Synthetic", "--date", "2026-10-21", "--provenance", "test", ok=False)
        self.assertEqual(self.register.read_text(), malformed)

    def test_adjacent_owner_prose_with_a_literal_pipe_is_preserved(self):
        body = APPLICATIONS.initial_register().decode().replace(
            "| --- | --- | --- | --- | --- | --- | --- |\n\n",
            "| --- | --- | --- | --- | --- | --- | --- |\nOwner prefers A | B.\n\n")
        self.register.write_text(body)
        self.add()
        self.assertIn("Owner prefers A | B.\n", self.register.read_text())

    def test_distribution_templates_cannot_be_used_as_live_mutation_targets(self):
        path = self.root / ".maguire/kit/templates/data/applications.md"
        path.parent.mkdir(parents=True)
        path.write_bytes(APPLICATIONS.initial_register())
        self.register = path
        original = path.read_bytes()
        self.cli("add", "--id", "APP-001", "--role", "Synthetic", "--date", "2026-10-21", "--provenance", "test", ok=False)
        self.assertEqual(path.read_bytes(), original)
        with self.assertRaises(APPLICATIONS.RegisterError):
            APPLICATIONS.check_candidate_target(ROOT / "templates/data/applications.md")

    def test_new_cell_whitespace_is_normalized_consistently(self):
        self.init()
        result = self.add("APP-001", "--role", "  Synthetic role  ", "--provenance", "  Synthetic decision  ")
        saved = self.cli("find", "--id", "APP-001")["records"][0]
        self.assertEqual(result["record"], saved)
        self.assertEqual(saved["role"], "Synthetic role")

    def test_identical_update_is_noop_and_permission_bits_survive(self):
        self.init()
        self.add("APP-001", "--status", "draft")
        self.register.chmod(0o640)
        before = self.register.read_bytes()
        result = self.cli("update", "--id", "APP-001", "--status", "draft", "--date", "2026-10-21", "--provenance", "Candidate decision in test")
        self.assertFalse(result["changed"])
        self.assertEqual(self.register.read_bytes(), before)
        self.cli("update", "--id", "APP-001", "--status", "reviewed", "--date", "2026-10-22", "--provenance", "Candidate reviewed synthetic draft")
        self.assertEqual(self.register.stat().st_mode & 0o777, 0o640)


if __name__ == "__main__":
    unittest.main()
