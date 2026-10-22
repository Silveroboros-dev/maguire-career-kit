"""Behavioral checks for safe local installation and update."""

import hashlib
import json
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
    def test_installed_tools_work_without_installer_mutating_candidate_records(self):
        with tempfile.TemporaryDirectory(prefix="maguire-kit-test-") as root:
            workspace = Path(root) / "candidate"
            workspace.mkdir()
            original = workspace / "CV.md"
            original.write_text("Fictional candidate original, unchanged\n", encoding="utf-8")
            register = workspace / "data/applications.md"
            register.parent.mkdir()
            register.write_bytes((KIT / "templates/data/applications.md").read_bytes())
            before = {path: path.read_bytes() for path in (original, register)}
            install = [sys.executable, str(KIT / "install.py"), "--portable", str(workspace)]
            subprocess.run(install, check=True, capture_output=True)
            self.assertFalse((workspace / ".git").exists())
            self.assertFalse((workspace / ".agents").exists())
            self.assertEqual({path: path.read_bytes() for path in before}, before)
            tools = workspace / ".maguire/kit/tools"
            for filename in ("workspace_git.py", "GIT.md", "export.py", "EXPORT.md",
                             "applications.py", "APPLICATIONS.md"):
                self.assertEqual((tools / filename).read_bytes(), (KIT / "tools" / filename).read_bytes())
            command = [sys.executable, str(tools / "applications.py"), "--register", str(register)]
            empty = subprocess.run(command + ["list", "--limit", "1"],
                                   check=True, capture_output=True, text=True)
            self.assertEqual(json.loads(empty.stdout)["records"], [])
            subprocess.run(command + ["add", "--id", "APP-001", "--role", "Fictional role",
                                      "--date", "2026-10-21", "--provenance", "Synthetic fixture"],
                           check=True, capture_output=True)
            filled = register.read_bytes()
            subprocess.run(install, check=True, capture_output=True)
            self.assertEqual(register.read_bytes(), filled)
            self.assertEqual(original.read_bytes(), before[original])
            self.assertFalse((workspace / ".git").exists())

    def test_portable_nested_download_preserves_candidate_records_without_agents_access(self):
        with tempfile.TemporaryDirectory(prefix="maguire-kit-test-") as root:
            root = Path(root)
            workspace = root / "candidate"
            source = workspace / ".maguire/download/release"
            shutil.copytree(KIT, source, ignore=shutil.ignore_patterns(".DS_Store", "__pycache__"))
            # A candidate Git repository above a downloaded release is not the
            # kit's source repository.
            (workspace / ".git").mkdir()
            cv = workspace / "originals/CV.md"
            jd = workspace / "applications/role-1/job.md"
            cv.parent.mkdir()
            jd.parent.mkdir(parents=True)
            cv.write_text("Synthetic candidate CV\n", encoding="utf-8")
            jd.write_text("Synthetic job description\n", encoding="utf-8")
            agents = workspace / "AGENTS.md"
            agents.write_text("Candidate project rules\n", encoding="utf-8")
            protected = root / "protected-agents"
            protected.mkdir()
            marker = protected / "marker"
            marker.write_text("unchanged\n", encoding="utf-8")
            (workspace / ".agents").symlink_to(protected, target_is_directory=True)
            before = {path: sha(path) for path in (cv, jd, agents, marker)}

            command = [sys.executable, str(source / "install.py"), "--portable", str(workspace)]
            first = subprocess.run(command, check=True, capture_output=True, text=True)
            self.assertIn("PORTABLE: Ask your agent to read", first.stdout)
            self.assertIn(".maguire/kit/skills/maguire-career-pilot/SKILL.md", first.stdout)
            self.assertIn("PRESERVED AGENTS.md", first.stdout)
            self.assertTrue((workspace / ".maguire/kit/skills/maguire-career-pilot/SKILL.md").is_file())
            self.assertTrue((workspace / ".maguire/kit/graders/jd-fit.md").is_file())
            self.assertTrue((workspace / ".maguire/kit/graders/employer-fit.md").is_file())
            self.assertEqual(list(protected.iterdir()), [marker])
            self.assertEqual({path: sha(path) for path in before}, before)
            manifest = json.loads((workspace / ".maguire/kit/manifest.json").read_text())
            self.assertNotIn(".agents/skills/maguire-career-pilot/SKILL.md", manifest["files"])

            canonical = workspace / ".maguire/kit/skills/maguire-career-pilot/SKILL.md"
            canonical.write_text(canonical.read_text() + "\nLocal candidate instruction.\n")
            second = subprocess.run(command, check=True, capture_output=True, text=True)
            self.assertIn("PRESERVED .maguire/kit/skills/maguire-career-pilot/SKILL.md", second.stdout)
            self.assertIn("Local candidate instruction.", canonical.read_text())
            self.assertEqual(len(list(canonical.parent.glob("SKILL.md.maguire-incoming-*"))), 1)
            self.assertEqual({path: sha(path) for path in before}, before)
            self.assertEqual(list(protected.iterdir()), [marker])

    def test_normal_and_portable_reruns_share_canonical_skill(self):
        with tempfile.TemporaryDirectory(prefix="maguire-kit-test-") as root:
            root = Path(root)
            source = root / "source"
            workspace = root / "candidate"
            shutil.copytree(KIT, source, ignore=shutil.ignore_patterns(".DS_Store", "__pycache__"))

            def install(*options):
                return subprocess.run(
                    [sys.executable, str(source / "install.py"), *options, str(workspace)],
                    check=True, capture_output=True, text=True,
                ).stdout

            install("--portable")
            normal = install()
            self.assertIn("INSTALLED .agents/skills/maguire-career-pilot/SKILL.md", normal)
            canonical = workspace / ".maguire/kit/skills/maguire-career-pilot/SKILL.md"
            discoverable = workspace / ".agents/skills/maguire-career-pilot/SKILL.md"
            self.assertEqual(sha(canonical), sha(discoverable))
            self.assertIn("'installed': 0", install("--portable"))
            self.assertIn("'installed': 0", install())

    def test_rejects_workspace_in_source_repo_and_source_in_managed_destination(self):
        with tempfile.TemporaryDirectory(prefix="maguire-kit-test-") as root:
            root = Path(root)
            repo = root / "source-repo"
            source = repo / "kit"
            shutil.copytree(KIT, source, ignore=shutil.ignore_patterns(".DS_Store", "__pycache__"))
            (repo / ".git").mkdir()
            workspace = repo / "private-candidate"
            result = subprocess.run(
                [sys.executable, str(source / "install.py"), str(workspace)],
                capture_output=True, text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("source repository", result.stderr)
            self.assertFalse(workspace.exists())

            workspace = root / "candidate"
            overlapping = workspace / ".maguire/kit/download"
            shutil.copytree(KIT, overlapping, ignore=shutil.ignore_patterns(".DS_Store", "__pycache__"))
            result = subprocess.run(
                [sys.executable, str(overlapping / "install.py"), "--portable", str(workspace)],
                capture_output=True, text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("overlaps an installer-managed path", result.stderr)
            self.assertFalse((workspace / ".maguire/kit/manifest.json").exists())

    def test_incomplete_kit_never_creates_or_changes_a_workspace(self):
        # Entire directories, individual templates and core instructions must
        # all fail before any write, including when updating an existing install.
        for missing in ("templates", "templates/workspace-map.md", "README.md",
                        "AGENTS.md", "skills/maguire-career-pilot/SKILL.md",
                        "graders", "graders/jd-fit.md", "graders/employer-fit.md",
                        "graders/checker.py", "graders/grade.py", "graders/PACKET_FORMAT.md",
                        "graders/source-manifest.json", "tools", "tools/workspace_git.py",
                        "tools/applications.py", "tools/export.py", "tools/GIT.md",
                        "tools/EXPORT.md", "tools/APPLICATIONS.md"):
            for existing in (False, True):
                with self.subTest(missing=missing, existing=existing):
                    with tempfile.TemporaryDirectory(prefix="maguire-kit-test-") as root:
                        root = Path(root)
                        source = root / "source"
                        workspace = root / "candidate"
                        shutil.copytree(KIT, source, ignore=shutil.ignore_patterns(".DS_Store", "__pycache__"))
                        if existing:
                            subprocess.run([sys.executable, str(source / "install.py"), str(workspace)],
                                           check=True, capture_output=True)
                            (workspace / "data").mkdir()
                            (workspace / "data/experience.md").write_text("Candidate-owned bank\n")
                        before = {p.relative_to(workspace): p.read_bytes()
                                  for p in workspace.rglob("*") if p.is_file()}
                        before_paths = {p.relative_to(workspace) for p in workspace.rglob("*")}
                        removed = source / missing
                        if removed.is_dir():
                            shutil.rmtree(removed)
                        else:
                            removed.unlink()
                        result = subprocess.run([sys.executable, str(source / "install.py"), str(workspace)],
                                                capture_output=True, text=True)
                        self.assertNotEqual(result.returncode, 0)
                        self.assertIn("Incomplete kit", result.stderr)
                        self.assertIn(missing, result.stderr)
                        after = {p.relative_to(workspace): p.read_bytes()
                                 for p in workspace.rglob("*") if p.is_file()}
                        self.assertEqual(after, before)
                        self.assertEqual({p.relative_to(workspace) for p in workspace.rglob("*")}, before_paths)
                        self.assertEqual(workspace.exists(), existing)

    def test_empty_or_nonfile_last_template_fails_before_writes(self):
        for invalid in ("empty", "directory", "symlink"):
            with self.subTest(invalid=invalid):
                with tempfile.TemporaryDirectory(prefix="maguire-kit-test-") as root:
                    root = Path(root)
                    source = root / "source"
                    workspace = root / "candidate"
                    shutil.copytree(KIT, source, ignore=shutil.ignore_patterns(".DS_Store", "__pycache__"))
                    template = source / "templates/workspace-map.md"
                    template.unlink()
                    if invalid == "empty":
                        template.write_bytes(b"")
                    elif invalid == "directory":
                        template.mkdir()
                    else:
                        template.symlink_to(source / "README.md")
                    result = subprocess.run([sys.executable, str(source / "install.py"), str(workspace)],
                                            capture_output=True, text=True)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("Incomplete kit", result.stderr)
                    self.assertFalse(workspace.exists())

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
            self.assertTrue((workspace / ".maguire/kit/graders/jd-fit.md").is_file())
            self.assertTrue((workspace / ".maguire/kit/graders/employer-fit.md").is_file())
            self.assertFalse((workspace / ".maguire/kit/examples").exists())

            # New kit instructions update when the installed copy is untouched.
            (source / "README.md").write_text(
                (source / "README.md").read_text() + "\nTest kit revision.\n", encoding="utf-8"
            )
            skill = workspace / ".agents/skills/maguire-career-pilot/SKILL.md"
            skill.write_text(skill.read_text() + "\nMy local customization.\n", encoding="utf-8")
            grader = workspace / ".maguire/kit/graders/jd-fit.md"
            grader.write_text(grader.read_text() + "\nMy local review note.\n", encoding="utf-8")
            tool = workspace / ".maguire/kit/tools/applications.py"
            tool.write_text(tool.read_text() + "\n# My local customization.\n", encoding="utf-8")
            (source / "tools/applications.py").write_text(
                (source / "tools/applications.py").read_text() + "\n# New kit revision.\n",
                encoding="utf-8",
            )
            second = install()
            self.assertIn("UPDATED .maguire/kit/README.md", second)
            self.assertIn("PRESERVED .agents/skills/maguire-career-pilot/SKILL.md", second)
            self.assertIn("Test kit revision.", (workspace / ".maguire/kit/README.md").read_text())
            self.assertIn("My local customization.", skill.read_text())
            self.assertIn("PRESERVED .maguire/kit/graders/jd-fit.md", second)
            self.assertIn("My local review note.", grader.read_text())
            self.assertIn("PRESERVED .maguire/kit/tools/applications.py", second)
            self.assertIn("My local customization.", tool.read_text())
            self.assertNotIn("New kit revision.", tool.read_text())
            self.assertEqual(len(list(tool.parent.glob("applications.py.maguire-incoming-*"))), 1)
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
