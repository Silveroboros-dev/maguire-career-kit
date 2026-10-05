#!/usr/bin/env python3
"""Install or update the file-based Maguire kit without replacing user data.

Python standard library only. The kit owns only the paths listed in managed_files().
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile


KIT = Path(__file__).resolve().parent
MANIFEST = Path(".maguire/kit/manifest.json")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def managed_files() -> dict[Path, Path]:
    files = {
        Path("AGENTS.md"): KIT / "AGENTS.md",
        Path(".maguire/kit/AGENTS.md"): KIT / "AGENTS.md",
        Path(".maguire/kit/README.md"): KIT / "README.md",
        Path(".agents/skills/maguire-career-pilot/SKILL.md"):
            KIT / "skills/maguire-career-pilot/SKILL.md",
    }
    for source in sorted((KIT / "templates").rglob("*.md")):
        files[Path(".maguire/kit/templates") / source.relative_to(KIT / "templates")] = source
    return files


def safe_path(workspace: Path, relative: Path) -> Path:
    path = workspace
    for part in relative.parts:
        path = path / part
        if path.is_symlink():
            raise ValueError(f"Refusing symlink in managed path: {path}")
    return path


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
        temporary = Path(stream.name)
        try:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
    try:
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path, help="Candidate-owned folder")
    args = parser.parse_args()
    workspace = args.workspace.expanduser().resolve()
    if workspace == KIT or KIT in workspace.parents or workspace in KIT.parents:
        parser.error("Choose a separate candidate-owned workspace, outside the kit source")
    source_repo = next((parent for parent in KIT.parents if (parent / ".git").exists()), None)
    if source_repo and (workspace == source_repo or source_repo in workspace.parents):
        parser.error("Candidate workspace must be outside the kit's source repository")
    if workspace.exists() and not workspace.is_dir():
        parser.error("Workspace path is not a directory")
    workspace.mkdir(parents=True, exist_ok=True)

    try:
        manifest_path = safe_path(workspace, MANIFEST)
    except ValueError as error:
        parser.error(str(error))
    if manifest_path.exists():
        try:
            previous = json.loads(manifest_path.read_text(encoding="utf-8"))
            if previous.get("format") != 1 or not isinstance(previous.get("files"), dict):
                raise ValueError("unsupported manifest format")
            old_hashes = previous["files"]
        except (OSError, ValueError) as error:
            parser.error(f"Cannot read existing manifest; no files updated: {error}")
    else:
        old_hashes = {}

    sources = managed_files()
    # Validate all managed paths before the first write.
    try:
        for relative in sources:
            target = safe_path(workspace, relative)
            if target.exists() and not target.is_file():
                raise ValueError(f"Managed path is not a file: {target}")
    except ValueError as error:
        parser.error(str(error))

    new_hashes = dict(old_hashes)
    counts = {"installed": 0, "updated": 0, "unchanged": 0, "preserved": 0}
    for relative, source in sources.items():
        target = workspace / relative
        data = source.read_bytes()
        wanted = digest(data)
        key = relative.as_posix()
        if not target.exists():
            atomic_write(target, data)
            new_hashes[key] = wanted
            counts["installed"] += 1
            print(f"INSTALLED {key}")
            continue
        current = digest(target.read_bytes())
        # A root AGENTS.md that existed before installation belongs to the
        # candidate, even if it happens to match this version byte-for-byte.
        if key == "AGENTS.md" and key not in old_hashes and current == wanted:
            print("PRESERVED AGENTS.md: pre-existing project instructions")
            counts["preserved"] += 1
            continue
        if current == wanted:
            new_hashes[key] = wanted
            counts["unchanged"] += 1
            continue
        if current == old_hashes.get(key):
            atomic_write(target, data)
            new_hashes[key] = wanted
            counts["updated"] += 1
            print(f"UPDATED {key}")
            continue
        # Never overwrite a pre-existing or locally edited file. Keep one stable
        # incoming copy of this source version so reruns do not create duplicates.
        incoming_relative = relative.with_name(relative.name + f".maguire-incoming-{wanted[:12]}")
        incoming = safe_path(workspace, incoming_relative)
        if not incoming.exists():
            incoming.parent.mkdir(parents=True, exist_ok=True)
            with incoming.open("xb") as stream:
                stream.write(data)
        elif not incoming.is_file() or digest(incoming.read_bytes()) != wanted:
            print(f"PRESERVED {key}: incoming path also conflicts; inspect manually")
            counts["preserved"] += 1
            continue
        print(f"PRESERVED {key}; review {incoming_relative.as_posix()}")
        counts["preserved"] += 1

    manifest = {"format": 1, "files": new_hashes}
    atomic_write(manifest_path, (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode())
    print(f"Result: {counts}")
    if (workspace / "AGENTS.md").read_bytes() != (KIT / "AGENTS.md").read_bytes():
        print("Root AGENTS.md differs. Add a reference to .maguire/kit/README.md manually.")
    print("User CVs, bank, preferences, applications, and submitted records were not visited.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
