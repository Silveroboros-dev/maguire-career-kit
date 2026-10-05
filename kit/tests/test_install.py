"""Behavioral checks for safe local installation and update."""

import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


KIT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class InstallTest(unittest.TestCase):
    def test_update_preserves_candidate_files_and_local_changes(self):
        with tempfile.TemporaryDirectory(prefix="maguire-kit-test-") as root:
            root = Path(root)
            source = root / "source"
            workspace = root / "candidate"
            shutil.copytree(KIT, source, ignore=shutil.ignore_patterns(".DS_Store", "__pycache__"))
            (workspace / "incoming").mkdir(parents=True)
            cv = workspace / "incoming/CV-master.md"
            cv.write_text("Synthetic master, candidate-owned\n", encoding="utf-8")
            data = workspace / "data/experience.md"
            data.parent.mkdir()
            data.write_text("Candidate bank edit\n", encoding="utf-8")
            original_cv = sha(cv)
            original_data = sha(data)
            existing_agents = workspace / "AGENTS.md"
            existing_agents.write_text("My own project rules\n", encoding="utf-8")

            def install():
                return subprocess.run(
                    [sys.executable, str(source / "install.py"), str(workspace)],
                    check=True, capture_output=True, text=True,
                ).stdout

            first = install()
            self.assertIn("PRESERVED AGENTS.md", first)
            self.assertEqual(existing_agents.read_text(), "My own project rules\n")
            self.assertTrue((workspace / ".maguire/kit/README.md").is_file())
            self.assertTrue((workspace / ".agents/skills/maguire-career-pilot/SKILL.md").is_file())
            self.assertFalse((workspace / ".maguire/kit/examples").exists())

            # New kit instructions update when the installed copy is untouched.
            (source / "README.md").write_text(
                (source / "README.md").read_text() + "\nTest kit revision.\n", encoding="utf-8"
            )
            skill = workspace / ".agents/skills/maguire-career-pilot/SKILL.md"
            skill.write_text(skill.read_text() + "\nMy local customization.\n", encoding="utf-8")
            second = install()
            self.assertIn("UPDATED .maguire/kit/README.md", second)
            self.assertIn("PRESERVED .agents/skills/maguire-career-pilot/SKILL.md", second)
            self.assertIn("Test kit revision.", (workspace / ".maguire/kit/README.md").read_text())
            self.assertIn("My local customization.", skill.read_text())
            incoming = list(skill.parent.glob("SKILL.md.maguire-incoming-*"))
            self.assertEqual(len(incoming), 1)

            install()  # Idempotent rerun does not duplicate incoming files.
            self.assertEqual(len(list(skill.parent.glob("SKILL.md.maguire-incoming-*"))), 1)
            self.assertEqual(sha(cv), original_cv)
            self.assertEqual(sha(data), original_data)
            self.assertEqual(existing_agents.read_text(), "My own project rules\n")

    def test_preexisting_matching_agents_remains_candidate_owned(self):
        with tempfile.TemporaryDirectory(prefix="maguire-kit-test-") as root:
            root = Path(root)
            source = root / "source"
            workspace = root / "candidate"
            workspace.mkdir()
            shutil.copytree(KIT, source, ignore=shutil.ignore_patterns(".DS_Store", "__pycache__"))
            agents = workspace / "AGENTS.md"
            agents.write_bytes((source / "AGENTS.md").read_bytes())
            first_hash = sha(agents)

            subprocess.run([sys.executable, str(source / "install.py"), str(workspace)], check=True, capture_output=True)
            (source / "AGENTS.md").write_text((source / "AGENTS.md").read_text() + "\nNew rule.\n")
            subprocess.run([sys.executable, str(source / "install.py"), str(workspace)], check=True, capture_output=True)
            self.assertEqual(sha(agents), first_hash)
            self.assertEqual(len(list(workspace.glob("AGENTS.md.maguire-incoming-*"))), 1)

    def test_nonfile_agents_stops_before_installation(self):
        with tempfile.TemporaryDirectory(prefix="maguire-kit-test-") as root:
            workspace = Path(root) / "candidate"
            (workspace / "AGENTS.md").mkdir(parents=True)
            result = subprocess.run(
                [sys.executable, str(KIT / "install.py"), str(workspace)],
                capture_output=True, text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Managed path is not a file", result.stderr)
            self.assertFalse((workspace / ".maguire").exists())

    def test_rejects_symlink_in_managed_path(self):
        with tempfile.TemporaryDirectory(prefix="maguire-kit-test-") as root:
            root = Path(root)
            workspace = root / "candidate"
            workspace.mkdir()
            (workspace / ".maguire").symlink_to(root / "elsewhere")
            result = subprocess.run(
                [sys.executable, str(KIT / "install.py"), str(workspace)],
                capture_output=True, text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Refusing symlink", result.stderr)
            self.assertFalse((workspace / "AGENTS.md").exists())


if __name__ == "__main__":
    unittest.main()
