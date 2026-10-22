#!/usr/bin/env python3
"""Query and update one candidate-owned Markdown application register.

Python 3.9+, standard library only. No network, database, or submission actions.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import date
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile


HEADERS = (
    "Application ID", "Employer / role", "JD source and capture date", "Status",
    "Last event date and provenance", "Package path", "Next action / due date",
)
FIELDS = ("id", "role", "jd_source", "status", "last_event", "package", "next_action")
STATUSES = ("considering", "draft", "reviewed", "submitted", "response", "interview", "outcome", "withdrawn")
HISTORY = "<!-- maguire-applications-history-v1 -->"
ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}\Z")
PLACEHOLDER = (
    "`<APP-001>`", "", "",
    "`considering / draft / reviewed / submitted / response / interview / outcome / withdrawn`",
    "", "`applications/<id>/`", "",
)


class RegisterError(ValueError):
    pass


def checked_text(value: str, name: str, *, required: bool = False) -> str:
    if not isinstance(value, str) or any(ord(ch) < 32 or ord(ch) == 127 or ch in "\u0085\u2028\u2029" for ch in value):
        raise RegisterError(f"{name} must be one line without control characters")
    if len(value) > 2000:
        raise RegisterError(f"{name} must be at most 2000 characters")
    if required and not value.strip():
        raise RegisterError(f"{name} is required")
    return value


def checked_id(value: str) -> str:
    if not ID_PATTERN.fullmatch(value):
        raise RegisterError("Application ID must be 1–80 letters, digits, dots, underscores or hyphens, starting with a letter or digit")
    return value


def checked_date(value: str) -> str:
    try:
        if date.fromisoformat(value).isoformat() != value:
            raise ValueError()
    except ValueError:
        raise RegisterError("--date must be an ISO date: YYYY-MM-DD") from None
    return value


def plain(value: str) -> str:
    return value[1:-1] if value.startswith("`") and value.endswith("`") else value


def cells(line: str) -> list[str]:
    """Split only unescaped table pipes, retaining Markdown text in each cell."""
    text = line.rstrip("\r\n").strip()
    if not text.startswith("|") or not text.endswith("|"):
        raise RegisterError("Unsupported register: every table row needs leading and trailing pipes")
    result, current, escaped = [], [], False
    for char in text[1:-1]:
        if escaped:
            if char in ("|", "\\"):
                current.append(char)
            else:
                current.extend(("\\", char))
            escaped = False
        elif char == "\\":
            escaped = True
        elif char == "|":
            result.append("".join(current).strip())
            current = []
        else:
            current.append(char)
    if escaped:
        current.append("\\")
    result.append("".join(current).strip())
    return result


def encode_cell(value: str) -> str:
    # Backslashes must be escaped before pipes so a literal backslash cannot
    # accidentally unescape a pipe and create a new column on the next read.
    return value.replace("\\", "\\\\").replace("|", "\\|")


def row_line(record: dict[str, str], newline: str) -> str:
    return "| " + " | ".join(encode_cell(record[field]) for field in FIELDS) + " |" + newline


class Register:
    def __init__(self, data: bytes):
        try:
            self.text = data.decode("utf-8")
        except UnicodeDecodeError:
            raise RegisterError("Register must be UTF-8; no files changed") from None
        self.lines = self.text.splitlines(keepends=True)
        self.newline = "\r\n" if "\r\n" in self.text else "\n"
        headers = []
        fence = None
        for index, line in enumerate(self.lines):
            marker = re.match(r"^ {0,3}(`{3,}|~{3,})", line)
            if marker:
                token = marker.group(1)
                if fence is None:
                    fence = token
                elif token[0] == fence[0] and len(token) >= len(fence):
                    fence = None
                continue
            if fence is not None or line.startswith(("    ", "\t")):
                continue
            if line.lstrip().startswith("|"):
                try:
                    if tuple(cells(line)) == HEADERS:
                        headers.append(index)
                except RegisterError:
                    continue
        if len(headers) != 1:
            raise RegisterError("Unsupported register: expected exactly one table with the kit's seven application columns; existing file is unchanged")
        self.header = headers[0]
        if self.header + 1 >= len(self.lines):
            raise RegisterError("Unsupported register: missing table separator")
        separators = cells(self.lines[self.header + 1])
        if len(separators) != len(HEADERS) or not all(re.fullmatch(r":?-{3,}:?", value) for value in separators):
            raise RegisterError("Unsupported register: malformed table separator")
        self.records = []
        self.positions = {}
        self.placeholder_positions = []
        end = self.header + 2
        while end < len(self.lines) and self.lines[end].lstrip().startswith("|"):
            values = cells(self.lines[end])
            if len(values) != len(FIELDS):
                raise RegisterError(f"Malformed application row at line {end + 1}; no files changed")
            if tuple(values) == PLACEHOLDER:
                self.placeholder_positions.append(end)
                end += 1
                continue
            record = dict(zip(FIELDS, values))
            record["id"] = checked_id(plain(record["id"]))
            record["status"] = plain(record["status"]).lower()
            if record["status"] not in STATUSES:
                raise RegisterError(f"Unsupported status in {record['id']}: {record['status']}")
            for field, value in record.items():
                checked_text(value, field)
            if record["id"] in self.positions:
                raise RegisterError(f"Duplicate application ID in register: {record['id']}")
            self.positions[record["id"]] = end
            self.records.append(record)
            end += 1
        self.end = end
        if end < len(self.lines) and self.lines[end].strip() and self.lines[end].count("|") >= len(FIELDS) - 1:
            raise RegisterError(f"Unsupported table-like row at line {end + 1}; expected leading and trailing pipes")
        if len(self.placeholder_positions) > 1:
            raise RegisterError("Unsupported register: repeated template placeholders")

    def change(self, before: dict[str, str] | None, after: dict[str, str], event: dict) -> bytes:
        lines = self.lines[:]
        if before is None:
            # Remove only the exact blank shipped placeholder, never a filled row.
            if self.placeholder_positions:
                position = self.placeholder_positions[0]
                lines[position] = row_line(after, self.newline)
            else:
                if self.end and not lines[self.end - 1].endswith(("\n", "\r")):
                    lines[self.end - 1] += self.newline
                lines.insert(self.end, row_line(after, self.newline))
        else:
            lines[self.positions[before["id"]]] = row_line(after, self.newline)
        body = "".join(lines)
        if body and not body.endswith(("\n", "\r")):
            body += self.newline
        if HISTORY not in body:
            body += self.newline + "## Application tool history" + self.newline * 2 + HISTORY + self.newline
        # JSON stores the complete prior/new row and caller-supplied provenance.
        # Escape backticks so user text cannot break the inline-code audit entry.
        payload = json.dumps(event, ensure_ascii=False, sort_keys=True).replace("`", "\\u0060")
        body += self.newline + "- `" + payload + "`" + self.newline
        return body.encode("utf-8")


def safe_path(path: Path) -> Path:
    path = Path(os.path.abspath(path.expanduser()))
    for component in (*reversed(path.parents), path):
        if component.is_symlink():
            raise RegisterError(f"Refusing symlink in register path: {component}")
    if path.exists() and not path.is_file():
        raise RegisterError(f"Register path is not a regular file: {path}")
    return path


@contextmanager
def locked(path: Path):
    lock = path.with_name(path.name + ".lock")
    try:
        descriptor = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError:
        raise RegisterError(f"Register is locked: {lock}. Retry after the other writer finishes; inspect stale locks manually") from None
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            stream.write(str(os.getpid()) + "\n")
        yield
    finally:
        lock.unlink(missing_ok=True)


def write_atomic(path: Path, original: bytes | None, data: bytes):
    safe_path(path)
    mode = stat.S_IMODE(path.stat().st_mode) if original is not None else 0o600
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".applications-", delete=False) as stream:
            temporary = Path(stream.name)
            os.fchmod(stream.fileno(), mode)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        safe_path(path)
        if original is None:
            # A hard-link creates the final name atomically and cannot overwrite
            # a non-cooperating writer's newly created file.
            os.link(temporary, path)
        else:
            if not path.exists() or path.read_bytes() != original:
                raise RegisterError("Register changed during update; no files replaced. Retry from current data")
            os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def initial_register() -> bytes:
    return ("# Application register\n\n"
            "This is the one authoritative application register for this workspace.\n\n"
            "| " + " | ".join(HEADERS) + " |\n"
            "| " + " | ".join("---" for _ in HEADERS) + " |\n\n"
            "Draft and reviewed are not submission. Submitted requires a candidate-confirmed send or actual submission evidence.\n"
            "Dated changes made by the tool are retained below; keep any existing role notes as well.\n").encode("utf-8")


def check_candidate_target(path: Path):
    # The source kit and installed/downloaded reference copies are distribution
    # material, never a candidate's authoritative live application register.
    parts = path.parts
    for first, second in zip(parts, parts[1:]):
        if (first, second) in ((".maguire", "kit"), (".maguire", "download"), (".agents", "skills")):
            raise RegisterError("Choose the candidate-owned register, outside managed kit/download/skill files")
    kit = Path(__file__).resolve().parents[1]
    if path == kit or kit in path.parents:
        raise RegisterError("Choose a candidate register outside the kit payload and its reference templates")
    if kit.name == "kit" and (kit.parent / ".git").exists():
        source = kit.parent
        if path == source or source in path.parents:
            raise RegisterError("Choose a candidate register outside the kit source repository")


def emit(value: dict):
    print(json.dumps(value, ensure_ascii=False, sort_keys=True))


def pagination(parser):
    parser.add_argument("--status", choices=STATUSES)
    parser.add_argument("--limit", type=int, default=20, help="Maximum records returned, 1–100 (default 20)")
    parser.add_argument("--offset", type=int, default=0)


def mutation_options(parser, *, adding: bool):
    parser.add_argument("--id", required=True)
    parser.add_argument("--role", required=adding)
    parser.add_argument("--jd-source")
    parser.add_argument("--status", choices=STATUSES, default="considering" if adding else None)
    parser.add_argument("--package")
    parser.add_argument("--next-action")
    parser.add_argument("--date", required=True, help="Actual event date, YYYY-MM-DD")
    parser.add_argument("--provenance", required=True, help="Source of this event/decision")
    parser.add_argument("--event", help="Optional description, retained in append-only history")
    parser.add_argument("--confirmed-send", action="store_true", help="Caller records explicit candidate confirmation of sending")
    parser.add_argument("--submission-evidence", help="Actual submission evidence reference; the helper does not authenticate it")


def parser_for_cli():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--register", type=Path, required=True, help="The ONE existing authoritative register, or chosen new path for init")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("init", help="Create a new empty register; never overwrite an existing file")
    adding = commands.add_parser("add", help="Add one new stable application ID")
    mutation_options(adding, adding=True)
    update = commands.add_parser("update", help="Update by stable ID and append the previous/new state to history")
    mutation_options(update, adding=False)
    listing = commands.add_parser("list", help="Return a bounded page of records")
    pagination(listing)
    finding = commands.add_parser("find", help="Find an exact ID or a case-insensitive text query")
    query = finding.add_mutually_exclusive_group(required=True)
    query.add_argument("--id")
    query.add_argument("--query")
    pagination(finding)
    return parser


def run(args):
    path = safe_path(args.register)
    if args.command in ("init", "add", "update"):
        check_candidate_target(path)
    if args.command == "init":
        if not path.parent.is_dir():
            raise RegisterError("Create the chosen register's parent directory before init")
        with locked(path):
            if path.exists():
                raise RegisterError("Register already exists; use it instead of creating a second ledger")
            write_atomic(path, None, initial_register())
        emit({"register": str(path), "changed": True, "records": []})
        return
    if args.command in ("list", "find"):
        if not 1 <= args.limit <= 100 or args.offset < 0:
            raise RegisterError("--limit must be 1–100 and --offset must be nonnegative")
        register = Register(path.read_bytes())
        records = register.records
        if args.status:
            records = [record for record in records if record["status"] == args.status]
        if args.command == "find":
            if args.id:
                checked_id(args.id)
                records = [record for record in records if record["id"] == args.id]
            else:
                query = checked_text(args.query, "query", required=True).casefold()
                records = [record for record in records if query in " ".join(record.values()).casefold()]
        emit({"register": str(path), "records": records[args.offset:args.offset + args.limit],
              "matched": len(records), "offset": args.offset, "limit": args.limit,
              "has_more": len(records) > args.offset + args.limit})
        return
    checked_id(args.id)
    checked_date(args.date)
    args.provenance = checked_text(args.provenance, "provenance", required=True).strip()
    for name in ("role", "jd_source", "package", "next_action", "event", "submission_evidence"):
        value = getattr(args, name)
        if value is not None:
            setattr(args, name, checked_text(value, name, required=True).strip())
    if args.command == "update" and not any(getattr(args, name) is not None for name in ("role", "jd_source", "status", "package", "next_action", "event")):
        raise RegisterError("update needs at least one changed field or --event")
    with locked(path):
        original = path.read_bytes()
        register = Register(original)
        before = next((record for record in register.records if record["id"] == args.id), None)
        if args.command == "add" and before is not None:
            raise RegisterError(f"Application ID already exists: {args.id}; use update")
        if args.command == "update" and before is None:
            raise RegisterError(f"Application ID not found: {args.id}")
        after = dict(before) if before else dict(zip(FIELDS, (args.id, args.role, "Unknown", "considering", "", f"applications/{args.id}/", "Unknown")))
        for name in ("role", "jd_source", "status", "package", "next_action"):
            if getattr(args, name) is not None:
                after[name] = getattr(args, name)
        after["last_event"] = args.date + " — " + args.provenance
        for field, value in after.items():
            checked_text(value, field)
        is_send = after["status"] == "submitted" and (before is None or before["status"] != "submitted")
        if is_send and not (args.confirmed_send or args.submission_evidence):
            raise RegisterError("submitted requires --confirmed-send or --submission-evidence, plus actual --date and --provenance; preparing a draft is not sending")
        if (args.confirmed_send or args.submission_evidence) and after["status"] != "submitted":
            raise RegisterError("Send confirmation/evidence is valid only with status submitted")
        event = {"date": args.date, "id": args.id, "operation": args.command,
                 "provenance": args.provenance, "description": args.event,
                 "confirmed_send": args.confirmed_send, "submission_evidence": args.submission_evidence,
                 "before": before, "after": after}
        changed = before != after or args.event is not None or args.confirmed_send or args.submission_evidence is not None
        if changed:
            data = register.change(before, after, event)
            Register(data)  # Refuse changes that cannot be read back using this schema.
            write_atomic(path, original, data)
    emit({"register": str(path), "changed": changed, "record": after})


def main() -> int:
    parser = parser_for_cli()
    args = parser.parse_args()
    try:
        run(args)
    except (OSError, RegisterError) as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
