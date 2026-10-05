#!/usr/bin/env python3
"""Build a deterministic kit ZIP and detached provenance from a committed tag.

Reads Git objects only. Outputs outside the source repository; no Site code,
candidate files, working-tree edits or generated manifest go into the ZIP.
"""

import argparse
from datetime import date
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import zipfile


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "https://github.com/Silveroboros-dev/maguire-career-kit"


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("version", help="Committed tag, for example v0.1.1")
    parser.add_argument("output", type=Path)
    parser.add_argument("--release-date", required=True, type=date.fromisoformat)
    args = parser.parse_args()
    if not re.fullmatch(r"v\d+\.\d+\.\d+", args.version):
        parser.error("Expected a vMAJOR.MINOR.PATCH tag")
    output = args.output.expanduser().resolve()
    if output == ROOT or ROOT in output.parents:
        parser.error("Release output must be outside the source repository")
    if git("status", "--porcelain").strip():
        parser.error("Commit source changes before building a release")
    try:
        commit = git("rev-parse", "--verify", f"refs/tags/{args.version}^{{commit}}").decode().strip()
    except subprocess.CalledProcessError:
        parser.error("The release tag must exist locally")
    if git("rev-parse", "HEAD").decode().strip() != commit:
        parser.error("Check out the tagged commit before building")
    # Also bind the executed builder to the release source it describes.
    if Path(__file__).read_bytes() != git("show", f"{commit}:scripts/build_release.py"):
        parser.error("Builder differs from the tagged source")

    payload = {}
    for record in git("ls-tree", "-r", "-z", commit).split(b"\0"):
        if not record:
            continue
        metadata, encoded_path = record.split(b"\t", 1)
        mode, kind, _ = metadata.decode().split()
        source_path = encoded_path.decode()
        if source_path.startswith("kit/"):
            path = source_path[4:]
        elif source_path in ("LICENSE", "CREDITS.md"):
            path = source_path
        else:
            continue
        if kind != "blob" or mode not in ("100644", "100755"):
            parser.error(f"Release source must be a regular file: {source_path}")
        if path in payload:
            parser.error(f"Two source files map to the same release path: {path}")
        payload[path] = (source_path, git("show", f"{commit}:{source_path}"))
    for required in ("install.py", "README.md", "AGENTS.md", "LICENSE", "CREDITS.md"):
        if required not in payload:
            parser.error(f"Missing release file: {required}")
    if not any(path.startswith("templates/") for path in payload):
        parser.error("Release has no templates")

    name = f"maguire-career-kit-{args.version}"
    buffer = io.BytesIO()
    files = []
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path, (source_path, data) in sorted(payload.items()):
            info = zipfile.ZipInfo(f"{name}/{path}", (2026, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
            files.append({"path": path, "source_path": source_path,
                          "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})
    data = buffer.getvalue()
    archive_hash = hashlib.sha256(data).hexdigest()
    manifest = {
        "version": args.version,
        "release_date": args.release_date.isoformat(),
        "source_repository": REPOSITORY,
        "source_commit": commit,
        "source_tag": args.version,
        "source": f"{REPOSITORY}/tree/{commit}/kit",
        "relationship": "Generated release; the GitHub repository owns the kit source.",
        "github_release": f"{REPOSITORY}/releases/tag/{args.version}",
        "archive": f"/kit/releases/{name}.zip",
        "archive_sha256": archive_hash,
        "files": files,
    }
    artifacts = {
        f"{name}.zip": data,
        f"{name}.zip.sha256": f"{archive_hash}  {name}.zip\n".encode(),
        f"{name}.manifest.json": (json.dumps(manifest, indent=2) + "\n").encode(),
    }
    for filename in artifacts:
        if (output / filename).exists():
            parser.error(f"Refusing to overwrite existing artifact: {output / filename}")
    output.mkdir(parents=True, exist_ok=True)
    for filename, contents in artifacts.items():
        (output / filename).write_bytes(contents)
    print(json.dumps({"source_commit": commit, "version": args.version,
                      "archive_sha256": archive_hash, "file_count": len(files),
                      "artifacts": [str(output / filename) for filename in artifacts]}))


if __name__ == "__main__":
    main()
