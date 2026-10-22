"""Synthetic local Git preservation, scope and review checks."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
HELPER = ROOT / "kit/tools/workspace_git.py"


@unittest.skipUnless(shutil.which("git"), "Git is required")
class WorkspaceGitTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.workspace = self.root / "Career archive"
        self.workspace.mkdir()
        self.environment = os.environ.copy()
        self.environment.update({
            "GIT_CONFIG_GLOBAL": str(self.root / "empty-global-config"),
            "GIT_CONFIG_SYSTEM": os.devnull,
            "GIT_CONFIG_NOSYSTEM": "1",
        })
        for field in ("GIT_AUTHOR_NAME", "GIT_AUTHOR_EMAIL", "GIT_COMMITTER_NAME", "GIT_COMMITTER_EMAIL", "EMAIL"):
            self.environment.pop(field, None)

    def run_helper(self, *args, success=True, workspace=None, environment=None):
        command = [sys.executable, str(HELPER), "--workspace", str(workspace or self.workspace), *args]
        result = subprocess.run(command, env=environment or self.environment, capture_output=True, text=True)
        if success:
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        return json.loads(result.stderr)

    def git(self, *args, workspace=None):
        return subprocess.check_output(["git", "-c", "init.defaultBranch=main", "-C", str(workspace or self.workspace), *args], env=self.environment)

    def identity(self):
        self.git("config", "--local", "user.name", "Synthetic Candidate")
        self.git("config", "--local", "user.email", "candidate@example.invalid")

    def initialize(self):
        self.run_helper("init")
        self.identity()

    def test_init_is_local_preserves_files_and_rerun_preserves_repository(self):
        original = {"CV.md": b"Synthetic career facts\n", ".gitignore": b"private-notes/\n", "AGENTS.md": b"Candidate project rules\n"}
        for name, data in original.items():
            (self.workspace / name).write_bytes(data)
        self.assertTrue(self.run_helper("init")["created"])
        self.assertEqual(self.git("remote"), b"")
        self.assertFalse((self.workspace / ".git/HEAD").read_text().strip().endswith("0000"))
        exclude = self.workspace / ".git/info/exclude"
        before = exclude.read_bytes()
        self.assertIn(b"/.maguire/kit/", before)
        (self.workspace / ".git/config").write_text((self.workspace / ".git/config").read_text() + "\n[custom]\n\tnote = preserve\n")
        self.assertFalse(self.run_helper("init")["created"])
        self.assertEqual(exclude.read_bytes(), before)
        self.assertIn(b"preserve", (self.workspace / ".git/config").read_bytes())
        for name, data in original.items():
            self.assertEqual((self.workspace / name).read_bytes(), data)

    def test_existing_repo_exclude_is_not_edited(self):
        self.git("init", "--template=")
        exclude = self.workspace / ".git/info/exclude"
        exclude.parent.mkdir(exist_ok=True)
        exclude.write_bytes(b"owner-specific-pattern\n")
        self.run_helper("init")
        self.assertEqual(exclude.read_bytes(), b"owner-specific-pattern\n")

    def test_parent_repository_refused_without_nested_git_creation(self):
        self.git("init", "--template=", workspace=self.root)
        result = self.run_helper("init", success=False)
        self.assertIn("parent repository", result["error"])
        self.assertFalse((self.workspace / ".git").exists())

    def test_bare_repository_and_broken_parent_config_are_not_reinitialized(self):
        bare = self.root / "bare"
        bare.mkdir()
        self.git("init", "--bare", "--template=", workspace=bare)
        original = (bare / "config").read_bytes()
        self.assertIn("bare repository", self.run_helper("init", workspace=bare, success=False)["error"])
        self.assertFalse((bare / ".git").exists())
        self.assertEqual((bare / "config").read_bytes(), original)
        self.git("init", "--template=", workspace=self.root)
        (self.root / ".git/config").write_bytes(b"invalid config line [\n")
        result = self.run_helper("init", success=False)
        self.assertIn("config", result["error"])
        self.assertFalse((self.workspace / ".git").exists())

    def test_source_repository_and_payload_rejected(self):
        for path in (ROOT, ROOT / "kit", ROOT / "kit/templates"):
            result = self.run_helper("init", workspace=path, success=False)
            self.assertIn("outside", result["error"])

    def test_checkpoint_commits_only_explicit_paths(self):
        self.initialize()
        (self.workspace / "CV with spaces.md").write_text("# Synthetic CV\n")
        (self.workspace / "private.md").write_text("Unselected private material\n")
        result = self.run_helper("checkpoint", "--path", "CV with spaces.md", "--message", "Save reviewed CV draft")
        self.assertTrue(result["committed"])
        self.assertEqual(self.git("ls-tree", "--name-only", "HEAD"), b"CV with spaces.md\n")
        self.assertEqual((self.workspace / "private.md").read_text(), "Unselected private material\n")
        self.assertEqual(self.git("diff", "--cached", "--name-only"), b"")
        self.assertFalse(self.run_helper("checkpoint", "--path", "CV with spaces.md", "--message", "No change")["committed"])

    def test_identity_required_before_staging(self):
        self.run_helper("init")
        (self.workspace / "CV.md").write_text("Synthetic CV\n")
        result = self.run_helper("checkpoint", "--path", "CV.md", "--message", "Initial", success=False)
        self.assertIn("identity", result["error"])
        self.assertEqual(self.git("diff", "--cached", "--name-only"), b"")
        self.assertFalse((self.workspace / ".git/index").exists())

    def test_unrelated_staged_file_prevents_checkpoint_and_preserves_index(self):
        self.initialize()
        (self.workspace / "CV.md").write_text("Synthetic CV\n")
        (self.workspace / "other.md").write_text("Separate task\n")
        self.git("add", "--", "other.md")
        index = self.workspace / ".git/index"
        original = index.read_bytes()
        result = self.run_helper("checkpoint", "--path", "CV.md", "--message", "CV only", success=False)
        self.assertIn("already staged", result["error"])
        self.assertEqual(index.read_bytes(), original)
        self.assertEqual(self.git("diff", "--cached", "--name-only"), b"other.md\n")

    def test_preexisting_selected_staging_and_tracked_deletion_are_supported(self):
        self.initialize()
        target = self.workspace / "CV.md"
        target.write_text("Synthetic CV\n")
        self.git("add", "--", "CV.md")
        self.run_helper("checkpoint", "--path", "CV.md", "--message", "Initial")
        target.unlink()
        self.run_helper("checkpoint", "--path", "CV.md", "--message", "Retire obsolete synthetic variant")
        self.assertEqual(self.git("ls-tree", "--name-only", "HEAD"), b"")

    def test_path_escape_directory_symlink_payload_and_literal_pathspec(self):
        self.initialize()
        (self.workspace / "CV.md").write_text("Synthetic CV\n")
        (self.workspace / "archive").mkdir()
        outside = self.root / "outside.md"
        outside.write_text("Outside\n")
        (self.workspace / "linked.md").symlink_to(outside)
        for name in ("../outside.md", str(outside), ".", "archive", "linked.md", ".git/config", ".maguire/kit/README.md", ":(glob)*"):
            with self.subTest(name=name):
                self.run_helper("checkpoint", "--path", name, "--message", "Must fail", success=False)
                self.assertEqual(self.git("diff", "--cached", "--name-only"), b"")
        self.assertEqual(outside.read_text(), "Outside\n")

    def test_ignored_file_is_not_force_added(self):
        self.initialize()
        (self.workspace / ".gitignore").write_text("secret.md\n")
        (self.workspace / "secret.md").write_text("Synthetic ignored content\n")
        result = self.run_helper("checkpoint", "--path", "secret.md", "--message", "Must fail", success=False)
        self.assertIn("ignored", result["error"])
        self.assertEqual(self.git("diff", "--cached", "--name-only"), b"")

    def test_status_and_diff_are_bounded_and_new_file_can_be_reviewed(self):
        self.initialize()
        (self.workspace / "CV.md").write_text("\n".join("Synthetic line " + str(i) for i in range(30)) + "\n")
        result = self.run_helper("diff", "--path", "CV.md", "--max-lines", "5")
        self.assertTrue(result["untracked"]["truncated"])
        self.assertLessEqual(len(result["untracked"]["lines"]), 5)
        self.assertIn("CV.md", "\n".join(result["untracked"]["lines"]))
        status = self.run_helper("status", "--max-lines", "1")
        self.assertTrue(status["truncated"])
        self.run_helper("status", "--max-lines", "1001", success=False)

    def test_workspace_symlink_refused(self):
        alias = self.root / "alias"
        alias.symlink_to(self.workspace, target_is_directory=True)
        self.assertIn("symlink", self.run_helper("init", workspace=alias, success=False)["error"])
        self.assertFalse((self.workspace / ".git").exists())

    def test_caller_git_directory_does_not_redirect_commands(self):
        other = self.root / "other"
        other.mkdir()
        self.git("init", "--template=", workspace=other)
        environment = self.environment.copy()
        environment["GIT_DIR"] = str(other / ".git")
        environment["GIT_WORK_TREE"] = str(other)
        self.run_helper("init", environment=environment)
        self.assertTrue((self.workspace / ".git").is_dir())
        self.assertEqual(self.git("remote", workspace=other), b"")

    def test_checkpoint_lock_prevents_parallel_helper(self):
        self.initialize()
        (self.workspace / "CV.md").write_text("Synthetic CV\n")
        lock = self.workspace / ".git/maguire-checkpoint.lock"
        lock.write_text("Synthetic active lock")
        result = self.run_helper("checkpoint", "--path", "CV.md", "--message", "Locked", success=False)
        self.assertIn("lock", result["error"])
        self.assertEqual(lock.read_text(), "Synthetic active lock")
        self.assertEqual(self.git("diff", "--cached", "--name-only"), b"")

    def test_failed_hook_restores_helper_staging(self):
        if os.name == "nt":
            self.skipTest("Shell hook fixture is POSIX-only")
        self.initialize()
        (self.workspace / "CV.md").write_text("Synthetic CV\n")
        hooks = self.workspace / ".git/hooks"
        hooks.mkdir(exist_ok=True)
        hook = hooks / "pre-commit"
        hook.write_text("#!/bin/sh\nprintf ran > .git/hook-ran\nexit 1\n")
        hook.chmod(0o700)
        self.run_helper("checkpoint", "--path", "CV.md", "--message", "Rejected by owner hook", success=False)
        self.assertTrue((self.workspace / ".git/hook-ran").exists())
        self.assertEqual(self.git("diff", "--cached", "--name-only"), b"")
        self.assertEqual((self.workspace / "CV.md").read_text(), "Synthetic CV\n")


if __name__ == "__main__":
    unittest.main()
