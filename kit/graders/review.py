#!/usr/bin/env python3
"""Save two manual fit reviews against immutable local input snapshots.

This records reviewer judgments; it does not run or replace either rubric.
"""

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys


SCHEMA = "maguire-fit-review.1"
RUBRICS = {"jd-fit": "maguire-jd-fit.1",
           "employer-fit": "maguire-employer-fit.1"}
SNAPSHOTS = {"assessment": "assessment.original", "cv": "cv.source",
             "jd": "jd.source", "preferences": "preferences.source"}
VERDICTS = {"jd-fit": {"supported", "partial", "unknown", "contradicted"},
            "employer-fit": {"aligned", "conflict", "unknown"}}


class ReviewError(ValueError):
    pass


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def read_bytes(path):
    try:
        return path.read_bytes()
    except OSError as error:
        raise ReviewError("cannot read {}: {}".format(path, error)) from error


def read_json(path):
    try:
        return json.loads(read_bytes(path).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ReviewError("invalid JSON in {}: {}".format(path, error)) from error


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2,
                       allow_nan=False) + "\n").encode("utf-8")


def create_file(path, data):
    # O_EXCL is also used after existence preflight: an unexpected file is never replaced.
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(data)
            output.flush()
            os.fsync(output.fileno())
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def initial_draft(mode, bindings):
    return {"schema": SCHEMA, "rubric_id": RUBRICS[mode],
            "bindings": bindings, "reviewer": "", "method": "",
            "status": "pending", "summary": "", "coverage": [], "findings": [],
            "needs_review_reason": ""}


def init(args):
    output = Path(args.output)
    inputs = {"assessment": Path(args.assessment), "cv": Path(args.cv),
              "jd": Path(args.jd)}
    if args.preferences:
        inputs["preferences"] = Path(args.preferences)
    data = {name: read_bytes(path) for name, path in inputs.items()}
    if not data["assessment"]:
        raise ReviewError("assessment is empty")
    if not data["jd"]:
        raise ReviewError("JD is empty")
    bindings = {name + "_sha256": sha256(data[name]) if name in data else None
                for name in SNAPSHOTS}
    manifest = {"schema": SCHEMA, "bindings": bindings,
                "snapshots": {name: SNAPSHOTS[name] if name in data else None
                              for name in SNAPSHOTS}}
    try:
        output.mkdir(parents=True, exist_ok=False)
    except OSError as error:
        raise ReviewError("cannot create bundle {}: {}".format(output, error)) from error
    try:
        for name, content in data.items():
            create_file(output / SNAPSHOTS[name], content)
        create_file(output / "manifest.json", json_bytes(manifest))
        for mode in RUBRICS:
            create_file(output / (mode + ".draft.json"),
                        json_bytes(initial_draft(mode, bindings)))
    except BaseException:
        # No completed init should leave an apparently usable partial bundle.
        for path in output.iterdir():
            if path.is_file():
                path.unlink()
        output.rmdir()
        raise
    print(output)


def require_text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ReviewError("{} must be nonempty text".format(field))
    if value.strip().lower() in {"todo", "tbd", "pending", "replace", "template", "..."}:
        raise ReviewError("{} is still a placeholder".format(field))


def verify_manifest(bundle):
    manifest = read_json(bundle / "manifest.json")
    if not isinstance(manifest, dict) or manifest.get("schema") != SCHEMA:
        raise ReviewError("invalid bundle manifest schema")
    bindings = manifest.get("bindings")
    snapshots = manifest.get("snapshots")
    if not isinstance(bindings, dict) or not isinstance(snapshots, dict):
        raise ReviewError("invalid bundle manifest")
    if set(bindings) != {name + "_sha256" for name in SNAPSHOTS}:
        raise ReviewError("invalid bundle bindings")
    if set(snapshots) != set(SNAPSHOTS):
        raise ReviewError("invalid snapshot inventory")
    contents = {}
    for name, filename in snapshots.items():
        expected = SNAPSHOTS[name] if filename is not None else None
        if filename != expected or (name != "preferences" and expected is None):
            raise ReviewError("invalid {} snapshot name".format(name))
        digest = bindings[name + "_sha256"]
        path = bundle / SNAPSHOTS[name]
        if filename is None:
            if digest is not None or path.exists():
                raise ReviewError("unexpected {} snapshot".format(name))
        else:
            content = read_bytes(path)
            if not isinstance(digest, str) or sha256(content) != digest:
                raise ReviewError("{} snapshot hash mismatch".format(name))
            contents[name] = content
    return manifest, contents


def verify_finding(finding, mode, coverage, contents, index):
    label = "{} finding {}".format(mode, index)
    if not isinstance(finding, dict):
        raise ReviewError("{} must be an object".format(label))
    if set(finding) != {"id", "verdict", "rationale", "evidence", "answer_quote"}:
        raise ReviewError("{} has invalid fields".format(label))
    require_text(finding["id"], label + " id")
    if finding["id"] not in coverage:
        raise ReviewError("{} id is outside coverage".format(label))
    if not isinstance(finding["verdict"], str) or finding["verdict"] not in VERDICTS[mode]:
        raise ReviewError("{} has invalid verdict".format(label))
    require_text(finding["rationale"], label + " rationale")
    quote = finding["answer_quote"]
    if not isinstance(quote, str):
        raise ReviewError("{} answer_quote must be text".format(label))
    if quote and quote not in contents["assessment"].decode("utf-8"):
        raise ReviewError("{} answer quote is absent from original".format(label))
    evidence = finding["evidence"]
    if not isinstance(evidence, list):
        raise ReviewError("{} evidence must be a list".format(label))
    for item in evidence:
        if not isinstance(item, dict) or not {"source", "quote"} <= set(item) or \
                set(item) - {"source", "quote", "locator"}:
            raise ReviewError("{} has invalid evidence".format(label))
        if not isinstance(item["source"], str) or item["source"] not in contents:
            raise ReviewError("{} references an absent source".format(label))
        require_text(item["quote"], label + " evidence quote")
        if "locator" in item and not isinstance(item["locator"], str):
            raise ReviewError("{} evidence locator must be text".format(label))
        try:
            source_text = contents[item["source"]].decode("utf-8")
        except UnicodeDecodeError:
            if not item.get("locator", "").strip():
                raise ReviewError("{} binary source evidence needs a locator".format(label))
        else:
            if item["quote"] not in source_text:
                raise ReviewError("{} source quote is absent from snapshot".format(label))
    if not evidence:
        raise ReviewError("{} needs source evidence".format(label))
    source_ids = {item["source"] for item in evidence}
    allowed_sources = {"jd", "cv"} if mode == "jd-fit" else {"jd", "cv", "preferences"}
    if not source_ids <= allowed_sources:
        raise ReviewError("{} has evidence outside rubric sources".format(label))
    if finding["verdict"] != "unknown":
        if mode == "jd-fit" and not {"jd", "cv"} <= source_ids:
            raise ReviewError("{} needs both JD and CV evidence".format(label))
        if mode == "employer-fit" and ("jd" not in source_ids or
                                       not source_ids.intersection({"cv", "preferences"})):
            raise ReviewError("{} needs JD and candidate preference evidence".format(label))


def verify_review(review, mode, bindings, contents):
    if not isinstance(review, dict) or set(review) != {
            "schema", "rubric_id", "bindings", "reviewer", "method", "status",
            "summary", "coverage", "findings", "needs_review_reason"}:
        raise ReviewError("{} draft has invalid fields".format(mode))
    if review["schema"] != SCHEMA or review["rubric_id"] != RUBRICS[mode]:
        raise ReviewError("{} draft has wrong schema or rubric ID".format(mode))
    if review["bindings"] != bindings:
        raise ReviewError("{} draft bindings do not match bundle".format(mode))
    if not isinstance(review["status"], str) or review["status"] not in {"reviewed", "needs_review"}:
        raise ReviewError("{} is pending or has invalid status".format(mode))
    require_text(review["reviewer"], mode + " reviewer")
    if not isinstance(review["method"], str) or review["method"] not in {"human", "agent", "human_and_agent"}:
        raise ReviewError("{} has invalid review method".format(mode))
    require_text(review["summary"], mode + " summary")
    reason = review["needs_review_reason"]
    if not isinstance(reason, str):
        raise ReviewError("{} needs_review_reason must be text".format(mode))
    if review["status"] == "needs_review":
        require_text(reason, mode + " needs_review_reason")
    elif reason.strip():
        raise ReviewError("{} reviewed status cannot retain needs_review_reason".format(mode))
    coverage = review["coverage"]
    findings = review["findings"]
    if not isinstance(coverage, list) or not isinstance(findings, list):
        raise ReviewError("{} coverage and findings must be lists".format(mode))
    if any(not isinstance(item, str) or not item.strip() for item in coverage) or \
            len(coverage) != len(set(coverage)):
        raise ReviewError("{} coverage needs unique nonempty IDs".format(mode))
    if review["status"] == "reviewed" and not coverage:
        raise ReviewError("{} reviewed status needs coverage".format(mode))
    for index, finding in enumerate(findings):
        verify_finding(finding, mode, coverage, contents, index)
    ids = [finding["id"] for finding in findings]
    if len(ids) != len(set(ids)):
        raise ReviewError("{} has duplicate finding IDs".format(mode))
    if review["status"] == "reviewed" and set(ids) != set(coverage):
        raise ReviewError("{} reviewed status needs a finding for each coverage ID".format(mode))


def finalize(args):
    bundle = Path(args.bundle)
    manifest, contents = verify_manifest(bundle)
    bindings = manifest["bindings"]
    reviews = {mode: read_json(bundle / (mode + ".draft.json")) for mode in RUBRICS}
    try:
        contents["assessment"].decode("utf-8")
    except UnicodeDecodeError as error:
        raise ReviewError("original assessment must be UTF-8 text") from error
    for mode, review in reviews.items():
        verify_review(review, mode, bindings, contents)
    revised = read_bytes(Path(args.revised)) if args.revised else None
    targets = [bundle / (mode + ".review.json") for mode in RUBRICS]
    targets.append(bundle / "assessment.revised")
    targets.append(bundle / "receipt.json")
    if any(path.exists() for path in targets):
        raise ReviewError("final result already exists; create a new bundle for another review")
    encoded = {mode: json_bytes(review) for mode, review in reviews.items()}
    receipt = {"schema": SCHEMA, "bindings": bindings,
               "reviews": {mode: {"file": mode + ".review.json",
                                  "sha256": sha256(encoded[mode])} for mode in RUBRICS},
               "revised": {"file": "assessment.revised", "sha256": sha256(revised)}
               if revised is not None else None}
    created = []
    try:
        for mode in RUBRICS:
            path = bundle / (mode + ".review.json")
            create_file(path, encoded[mode])
            created.append(path)
        if revised is not None:
            path = bundle / "assessment.revised"
            create_file(path, revised)
            created.append(path)
        path = bundle / "receipt.json"
        create_file(path, json_bytes(receipt))
        created.append(path)
    except BaseException:
        for path in created:
            path.unlink(missing_ok=True)
        raise
    print(bundle / "receipt.json")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    start = commands.add_parser("init", help="snapshot inputs and create two pending review drafts")
    for flag in ("assessment", "cv", "jd", "output"):
        start.add_argument("--" + flag, required=True)
    start.add_argument("--preferences", help="candidate-approved preference source, if available")
    finish = commands.add_parser("finalize", help="validate both drafts and save separate reviews")
    finish.add_argument("--bundle", required=True)
    finish.add_argument("--revised", help="optional revised answer to preserve beside original")
    args = parser.parse_args(argv)
    try:
        if args.command == "init":
            init(args)
        else:
            finalize(args)
    except (ReviewError, OSError) as error:
        parser.exit(1, "review: {}\n".format(error))


if __name__ == "__main__":
    main()
