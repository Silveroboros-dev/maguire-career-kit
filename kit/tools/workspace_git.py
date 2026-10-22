#!/usr/bin/env python3
"""Keep local, explicit Git checkpoints in a candidate-owned career workspace."""
from __future__ import annotations

import argparse
import difflib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


KIT = Path(__file__).resolve().parents[1]
EXCLUDED = (".maguire/kit/", ".maguire/download/", ".agents/skills/")
EXCLUDE_BLOCK = "\n# Maguire: installed distribution (career records stay visible)\n" + "\n".join("/" + path for path in EXCLUDED) + "\n"


class GitError(ValueError):
    pass


def git_env() -> dict[str, str]:
    env = os.environ.copy()
    # Do not let the caller's unrelated repository/index redirect this command.
    for name in (
        "GIT_DIR", "GIT_WORK_TREE", "GIT_INDEX_FILE", "GIT_COMMON_DIR",
        "GIT_OBJECT_DIRECTORY", "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_CEILING_DIRECTORIES", "GIT_NAMESPACE", "GIT_LITERAL_PATHSPECS",
        "GIT_GLOB_PATHSPECS", "GIT_NOGLOB_PATHSPECS", "GIT_ICASE_PATHSPECS",
    ):
        env.pop(name, None)
    env["LC_ALL"] = "C"
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["GIT_OPTIONAL_LOCKS"] = "0"
    return env


def git(workspace: Path, *args: str, allowed: tuple[int, ...] = (0,)) -> subprocess.CompletedProcess:
    literal = [] if args[0] == "check-ignore" else ["--literal-pathspecs"]
    command = ["git", "--no-pager", *literal, "-c", "core.fsmonitor=false", "-C", str(workspace), *args]
    result = subprocess.run(command, env=git_env(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if result.returncode not in allowed:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise GitError(detail or f"Git failed with exit code {result.returncode}")
    return result


def candidate_workspace(value: Path) -> Path:
    path = value.expanduser().absolute()
    for parent in (path, *path.parents):
        if parent.is_symlink():
            raise GitError(f"Use a real workspace path, not a symlink: {parent}")
    workspace = path.resolve()
    if not workspace.is_dir():
        raise GitError("Workspace must be an existing candidate-owned directory")
    if workspace == KIT or KIT in workspace.parents:
        raise GitError("Choose a candidate workspace outside the kit payload")
    source_repo = KIT.parent if KIT.name == "kit" and (KIT.parent / ".git").exists() else None
    if source_repo and (workspace == source_repo or source_repo in workspace.parents):
        raise GitError("Candidate workspace must be outside the kit source repository")
    return workspace


def repository_root(workspace: Path, required: bool = True) -> Path | None:
    discovery = git(workspace, "rev-parse", "--is-bare-repository", allowed=(0, 128))
    if discovery.returncode:
        detail = discovery.stderr.decode("utf-8", errors="replace").strip()
        # An absent repository is acceptable for init. Invalid configuration,
        # ownership errors or a damaged .git must never become nested init.
        absent = detail.startswith("fatal: not a git repository")
        if not absent or (workspace / ".git").exists() or (workspace / ".git").is_symlink():
            raise GitError(detail)
        if required:
            raise GitError("No local repository; run init for this career workspace first")
        return None
    if discovery.stdout.strip() == b"true":
        raise GitError("A bare repository is not a candidate career working folder; choose a separate workspace")
    found = git(workspace, "rev-parse", "--show-toplevel")
    root = Path(os.fsdecode(found.stdout.rstrip(b"\n"))).resolve()
    if root != workspace:
        raise GitError(f"Workspace belongs to parent repository {root}; choose that root explicitly or a separate career folder")
    return root


def initialize(workspace: Path) -> dict:
    root = repository_root(workspace, required=False)
    if root:
        return {"workspace": str(workspace), "created": False, "message": "Existing local repository preserved"}
    # Ignore global init templates: the helper neither installs nor runs hooks.
    git(workspace, "init", "--template=")
    exclude = workspace / ".git/info/exclude"
    exclude.parent.mkdir(parents=True, exist_ok=True)
    with exclude.open("a", encoding="utf-8") as stream:
        stream.write(EXCLUDE_BLOCK)
    return {"workspace": str(workspace), "created": True, "message": "Local repository initialized; no remote, commit or identity was created"}


def bounded(text: str, maximum: int) -> dict:
    lines = text.splitlines()
    # Bound a single exceptionally long line as well as the number of lines.
    selected = lines[:maximum]
    shortened = [line if len(line) <= 2000 else line[:2000] + "…" for line in selected]
    return {"lines": shortened, "truncated": len(lines) > maximum or shortened != selected}


def selected_paths(workspace: Path, values: list[str], require_existing: bool = False) -> list[str]:
    result = []
    for value in values:
        relative = Path(value)
        if relative.is_absolute() or not relative.parts or ".." in relative.parts or ".git" in relative.parts:
            raise GitError(f"Use an explicit relative file path inside the workspace: {value}")
        normalized = relative.as_posix()
        if any(normalized == prefix.rstrip("/") or normalized.startswith(prefix) for prefix in EXCLUDED):
            raise GitError(f"Installed kit material is excluded from career checkpoints: {value}")
        path = workspace
        for part in relative.parts:
            path = path / part
            if path.is_symlink():
                raise GitError(f"Refusing a symlink in checkpoint path: {value}")
        if path.exists() and not path.is_file():
            raise GitError(f"List individual files, not directories: {value}")
        if not path.exists():
            known = git(workspace, "ls-files", "--error-unmatch", "--", normalized, allowed=(0, 1))
            if require_existing or known.returncode:
                raise GitError(f"File does not exist and is not a tracked deletion: {value}")
        if normalized not in result:
            result.append(normalized)
    return result


def show_status(workspace: Path, maximum: int) -> dict:
    repository_root(workspace)
    output = git(workspace, "status", "--short", "--branch", "--untracked-files=all").stdout.decode("utf-8", errors="replace")
    return {"workspace": str(workspace), **bounded(output, maximum)}


def show_diff(workspace: Path, values: list[str], maximum: int) -> dict:
    repository_root(workspace)
    paths = selected_paths(workspace, values)
    arguments = ["--", *paths] if paths else []
    working = git(workspace, "diff", "--no-ext-diff", "--no-textconv", *arguments).stdout.decode("utf-8", errors="replace")
    staged = git(workspace, "diff", "--cached", "--no-ext-diff", "--no-textconv", *arguments).stdout.decode("utf-8", errors="replace")
    untracked = git(workspace, "ls-files", "--others", "--exclude-standard", "-z", *arguments).stdout.split(b"\0")
    chunks = []
    for item in untracked:
        if not item:
            continue
        path = os.fsdecode(item)
        target = workspace / path
        if target.is_symlink():
            chunks.append(f"Untracked symlink (not read): {path}\n")
            continue
        with target.open("rb") as stream:
            data = stream.read(65537)
        if b"\0" in data or len(data) > 65536:
            chunks.append(f"Untracked file (binary or larger than 64 KiB; inspect separately): {path}\n")
        else:
            lines = data.decode("utf-8", errors="replace").splitlines(keepends=True)
            chunks.extend(difflib.unified_diff([], lines, fromfile="/dev/null", tofile=path))
        if len("".join(chunks).splitlines()) >= maximum:
            chunks.append("Further untracked preview omitted.\n")
            break
    return {"workspace": str(workspace), "working": bounded(working, maximum), "staged": bounded(staged, maximum), "untracked": bounded("".join(chunks), maximum)}


def index_path(workspace: Path) -> Path:
    output = git(workspace, "rev-parse", "--git-path", "index").stdout
    path = Path(os.fsdecode(output.rstrip(b"\n")))
    return path if path.is_absolute() else workspace / path


def checkpoint(workspace: Path, values: list[str], message: str) -> dict:
    repository_root(workspace)
    paths = selected_paths(workspace, values)
    if not paths:
        raise GitError("At least one explicit --path file is required")
    if not message.strip() or "\0" in message:
        raise GitError("Provide a nonempty checkpoint message")
    for field in ("user.name", "user.email"):
        value = git(workspace, "config", "--get", field, allowed=(0, 1)).stdout.strip()
        if not value:
            raise GitError("Git identity is missing. Set your own user.name and user.email with git -C WORKSPACE config --local; no identity was invented and nothing was staged")
    staged = {os.fsdecode(path) for path in git(workspace, "diff", "--cached", "--name-only", "--no-renames", "-z").stdout.split(b"\0") if path}
    if staged - set(paths):
        raise GitError("Unrelated files are already staged; preserve/review that staging before a checkpoint: " + ", ".join(sorted(staged - set(paths))))
    for path in paths:
        ignored = git(workspace, "check-ignore", "--quiet", "--", path, allowed=(0, 1))
        if ignored.returncode == 0:
            raise GitError(f"File is ignored; the helper does not force-add it: {path}")
    index = index_path(workspace)
    if index.is_symlink():
        raise GitError("Refusing a symlinked Git index")
    lock = index.with_name("maguire-checkpoint.lock")
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise GitError(f"Another helper checkpoint may be active; inspect lock before retrying: {lock}") from None
    original = None
    staged_bytes = None
    try:
        os.close(descriptor)
        original = index.read_bytes() if index.exists() else None
        # Recheck after acquiring our lock. Git itself also uses index.lock.
        current_staged = {os.fsdecode(path) for path in git(workspace, "diff", "--cached", "--name-only", "--no-renames", "-z").stdout.split(b"\0") if path}
        if current_staged - set(paths):
            raise GitError("Staging changed; unrelated files must be reviewed before checkpointing")
        git(workspace, "add", "--", *paths)
        staged_bytes = index.read_bytes()
        changed = git(workspace, "diff", "--cached", "--quiet", "--", *paths, allowed=(0, 1))
        if changed.returncode == 0:
            return {"workspace": str(workspace), "committed": False, "paths": paths, "message": "Selected files have no changes"}
        # --only guarantees this commit cannot sweep in an unrelated staged file.
        git(workspace, "commit", "--only", "--message", message, "--", *paths)
        revision = git(workspace, "rev-parse", "HEAD").stdout.decode().strip()
        return {"workspace": str(workspace), "committed": True, "commit": revision, "paths": paths}
    except (OSError, GitError):
        # Restore our staging only if nobody (including a failing owner hook)
        # changed it after git add. Never overwrite someone else's newer index.
        if staged_bytes is not None and index.exists() and index.read_bytes() == staged_bytes:
            if original is None:
                index.unlink()
            else:
                with tempfile.NamedTemporaryFile(dir=index.parent, delete=False) as stream:
                    temporary = Path(stream.name)
                    stream.write(original)
                os.replace(temporary, index)
        raise
    finally:
        lock.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init", help="Initialize local Git; preserve an existing repository")
    for command in ("status", "diff"):
        child = commands.add_parser(command)
        child.add_argument("--max-lines", type=int, default=200)
        if command == "diff":
            child.add_argument("--path", action="append", default=[])
    child = commands.add_parser("checkpoint")
    child.add_argument("--path", action="append", required=True)
    child.add_argument("--message", required=True)
    args = parser.parse_args()
    try:
        if not shutil.which("git"):
            raise GitError("Git is not installed; install it locally before using this helper")
        workspace = candidate_workspace(args.workspace)
        if args.command in ("status", "diff") and not 1 <= args.max_lines <= 1000:
            raise GitError("--max-lines must be between 1 and 1000")
        if args.command == "init":
            result = initialize(workspace)
        elif args.command == "status":
            result = show_status(workspace, args.max_lines)
        elif args.command == "diff":
            result = show_diff(workspace, args.path, args.max_lines)
        else:
            result = checkpoint(workspace, args.path, args.message)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (OSError, GitError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
