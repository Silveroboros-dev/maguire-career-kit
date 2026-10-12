"""Projection validation and checks common to both career-quality graders."""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Any


LABELS = {
    "candidate_fit": {"supported", "partial", "unknown", "contradicted"},
    "preference_fit": {"aligned", "conflict", "unknown"},
}
ACTIONS = {"pursue", "clarify", "pass", "show_existing_evidence", "verify_skill"}
UNIT_KEYS = {"target_id", "kind", "allowed_labels", "acceptable_evidence_sets", "rationale", "required_points", "forbidden_inferences"}
SOURCE_KEYS = {"id", "text", "observed_at", "authority", "supersedes"}
FACT_KEYS = {"id", "text", "evidence_type", "observed_at", "status", "supersedes"}
PREF_KEYS = {"id", "text", "priority", "allowed_exceptions", "confirmed_at"}
ASSESSMENT_KEYS = {"target_id", "label", "evidence", "rationale"}


def finding(criterion: str, severity: str, target: str | None, code: str, path: str, explanation: str) -> dict:
    return {"criterion_id": criterion, "severity": severity, "target_id": target,
            "code": code, "path": path, "explanation": explanation}


def _invalid(path: str, reason: str) -> dict:
    return {"verdict": "invalid", "assurance": "rule_checks_only",
            "findings": [finding("PACKET", "error", None, "malformed_packet", path, reason)]}


def _keys(value: Any, names: set[str], path: str, exact: bool = True) -> None:
    if not isinstance(value, dict):
        raise ValueError((path, "Expected an object."))
    missing = names - value.keys()
    extra = value.keys() - names
    if missing or (exact and extra):
        raise ValueError((path, f"Unexpected object fields: missing {sorted(missing)}, extra {sorted(extra)}."))


def _string(value: Any, path: str, nonempty: bool = True) -> None:
    if not isinstance(value, str) or (nonempty and not value.strip()):
        raise ValueError((path, "Expected a nonempty string." if nonempty else "Expected a string."))


def _list(value: Any, path: str, nonempty: bool = False) -> None:
    if not isinstance(value, list) or (nonempty and not value):
        raise ValueError((path, "Expected a nonempty list." if nonempty else "Expected a list."))


def _strings(value: Any, path: str, nonempty: bool = False) -> None:
    _list(value, path, nonempty)
    for i, item in enumerate(value):
        _string(item, f"{path}/{i}")


def _unique_ids(rows: list, path: str) -> dict[str, dict]:
    result = {}
    for i, row in enumerate(rows):
        ident = row["id"]
        if ident in result:
            raise ValueError((f"{path}/{i}/id", "Duplicate source ID."))
        result[ident] = row
    return result


def _utc_snapshot(value: Any, path: str, decision: datetime | None = None) -> datetime:
    _string(value, path)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError((path, "Expected an ISO UTC timestamp.")) from None
    if parsed.utcoffset() != timedelta(0):
        raise ValueError((path, "Expected a UTC timestamp."))
    if decision is not None and parsed > decision:
        raise ValueError((path, "Source timestamp is after the decision snapshot."))
    return parsed


def _validate(packet: Any) -> tuple[str, dict, dict, dict, dict, dict]:
    _keys(packet, {"grader", "input", "gold", "answer"}, "")
    grader = packet["grader"]
    if grader not in LABELS:
        raise ValueError(("/grader", "Unknown grader."))
    inp, gold, answer = packet["input"], packet["gold"], packet["answer"]
    _keys(inp, {"decision_at", "task", "jd", "candidate"}, "/input")
    decision = _utc_snapshot(inp["decision_at"], "/input/decision_at")
    _string(inp["task"], "/input/task")
    _keys(inp["jd"], {"title", "sources"}, "/input/jd")
    _string(inp["jd"]["title"], "/input/jd/title")
    _list(inp["jd"]["sources"], "/input/jd/sources")
    for i, row in enumerate(inp["jd"]["sources"]):
        p = f"/input/jd/sources/{i}"
        _keys(row, SOURCE_KEYS, p)
        for key in ("id", "text", "observed_at"):
            _string(row[key], f"{p}/{key}")
        _utc_snapshot(row["observed_at"], f"{p}/observed_at", decision)
        if row["authority"] not in {"job_description", "employer_update"}:
            raise ValueError((f"{p}/authority", "Unknown JD authority."))
        _strings(row["supersedes"], f"{p}/supersedes")
    _keys(inp["candidate"], {"facts", "preferences"}, "/input/candidate")
    _list(inp["candidate"]["facts"], "/input/candidate/facts")
    _list(inp["candidate"]["preferences"], "/input/candidate/preferences")
    for i, row in enumerate(inp["candidate"]["facts"]):
        p = f"/input/candidate/facts/{i}"
        _keys(row, FACT_KEYS, p)
        for key in ("id", "text", "observed_at"):
            _string(row[key], f"{p}/{key}")
        _utc_snapshot(row["observed_at"], f"{p}/observed_at", decision)
        if row["evidence_type"] not in {"self_report", "supplied_artifact_excerpt"}:
            raise ValueError((f"{p}/evidence_type", "Unknown evidence type."))
        if row["status"] not in {"active", "withdrawn"}:
            raise ValueError((f"{p}/status", "Unknown fact status."))
        _strings(row["supersedes"], f"{p}/supersedes")
    for i, row in enumerate(inp["candidate"]["preferences"]):
        p = f"/input/candidate/preferences/{i}"
        _keys(row, PREF_KEYS, p)
        for key in ("id", "text", "confirmed_at"):
            _string(row[key], f"{p}/{key}")
        _utc_snapshot(row["confirmed_at"], f"{p}/confirmed_at", decision)
        if row["priority"] not in {"must_have", "nice_to_have"}:
            raise ValueError((f"{p}/priority", "Unknown preference priority."))
        _strings(row["allowed_exceptions"], f"{p}/allowed_exceptions")

    jd = _unique_ids(inp["jd"]["sources"], "/input/jd/sources")
    facts = _unique_ids(inp["candidate"]["facts"], "/input/candidate/facts")
    prefs = _unique_ids(inp["candidate"]["preferences"], "/input/candidate/preferences")
    if len(jd) + len(facts) + len(prefs) != len(set(jd) | set(facts) | set(prefs)):
        raise ValueError(("/input", "Source IDs must be unique across input collections."))
    sources = {**jd, **facts, **prefs}
    for kind, rows in (("jd", jd), ("facts", facts)):
        for ident, row in rows.items():
            if any(s not in rows or s == ident for s in row["supersedes"]):
                raise ValueError((f"/input/{kind}", "Supersedes must reference another source of the same type."))

    _keys(gold, {"units", "forbidden_assessment_targets", "acceptable_actions"}, "/gold")
    _list(gold["units"], "/gold/units", True)
    _strings(gold["forbidden_assessment_targets"], "/gold/forbidden_assessment_targets")
    _strings(gold["acceptable_actions"], "/gold/acceptable_actions", True)
    if len(gold["acceptable_actions"]) != len(set(gold["acceptable_actions"])) or not set(gold["acceptable_actions"]) <= ACTIONS:
        raise ValueError(("/gold/acceptable_actions", "Gold contains duplicate or unknown actions."))
    target_sources = jd if grader == "candidate_fit" else prefs
    units = {}
    for i, row in enumerate(gold["units"]):
        p = f"/gold/units/{i}"
        _keys(row, UNIT_KEYS, p)
        for key in ("target_id", "kind", "rationale"):
            _string(row[key], f"{p}/{key}")
        _strings(row["allowed_labels"], f"{p}/allowed_labels", True)
        _strings(row["required_points"], f"{p}/required_points")
        _strings(row["forbidden_inferences"], f"{p}/forbidden_inferences")
        if not set(row["allowed_labels"]) <= LABELS[grader]:
            raise ValueError((f"{p}/allowed_labels", "Gold label outside grader vocabulary."))
        _list(row["acceptable_evidence_sets"], f"{p}/acceptable_evidence_sets", True)
        for j, evidence_set in enumerate(row["acceptable_evidence_sets"]):
            _strings(evidence_set, f"{p}/acceptable_evidence_sets/{j}")
            if len(evidence_set) != len(set(evidence_set)) or not set(evidence_set) <= sources.keys():
                raise ValueError((f"{p}/acceptable_evidence_sets/{j}", "Gold evidence set has duplicate or unknown source."))
        target = row["target_id"]
        if target not in target_sources or target in units:
            raise ValueError((f"{p}/target_id", "Gold target is missing, from wrong collection, or duplicated."))
        units[target] = row
    if set(gold["forbidden_assessment_targets"]) & units.keys() or not set(gold["forbidden_assessment_targets"]) <= sources.keys():
        raise ValueError(("/gold/forbidden_assessment_targets", "Gold forbidden targets are unknown or overlap assessed targets."))

    _keys(answer, {"assessments", "conclusion", "limitations"}, "/answer")
    _list(answer["assessments"], "/answer/assessments")
    for i, row in enumerate(answer["assessments"]):
        p = f"/answer/assessments/{i}"
        _keys(row, ASSESSMENT_KEYS, p)
        for key in ("target_id", "label", "rationale"):
            _string(row[key], f"{p}/{key}")
        if row["label"] not in LABELS[grader]:
            raise ValueError((f"{p}/label", "Unknown answer label."))
        _list(row["evidence"], f"{p}/evidence")
        for j, citation in enumerate(row["evidence"]):
            ep = f"{p}/evidence/{j}"
            _keys(citation, {"source_id", "quote"}, ep)
            _string(citation["source_id"], f"{ep}/source_id")
            _string(citation["quote"], f"{ep}/quote")
    _keys(answer["conclusion"], {"action", "text", "next_step"}, "/answer/conclusion")
    for key in ("action", "text", "next_step"):
        _string(answer["conclusion"][key], f"/answer/conclusion/{key}")
    if answer["conclusion"]["action"] not in ACTIONS:
        raise ValueError(("/answer/conclusion/action", "Unknown answer action."))
    _strings(answer["limitations"], "/answer/limitations", True)
    return grader, inp, gold, answer, sources, units


def _has_positive_claim(text: str, pattern: str) -> bool:
    """Find an explicit assertion without treating nearby negation as an assertion."""
    for match in re.finditer(pattern, text, re.IGNORECASE):
        before = text[max(0, match.start() - 45):match.start()].lower()
        before = re.split(r"[.;:!?]", before)[-1]
        if not re.search(r"\b(?:not|never|no|cannot|can't|without|unverified|unproven|doesn't|do not)\b", before):
            return True
    return False


def _global_semantics(answer: dict, sources: dict, prefix: str) -> list[dict]:
    results = []
    conclusion = answer["conclusion"]
    for field in ("text", "next_step"):
        text = conclusion[field]
        if _has_positive_claim(text, r"\b(?:guarantee(?:d|s)?|certain(?:ly)?)\s+(?:an?\s+)?(?:interview|offer|job|hire|employment)\b"):
            results.append(finding(prefix + "-ACTION", "major", None, "unsupported_guarantee",
                                   f"/answer/conclusion/{field}", "The conclusion claims a guaranteed hiring outcome; the supplied snapshots cannot establish one."))
    return results


def grade(packet: Any) -> dict:
    """Grade one anonymous projected answer using bounded deterministic checks."""
    try:
        grader, inp, gold, answer, sources, units = _validate(packet)
    except (ValueError, TypeError, KeyError) as exc:
        if isinstance(exc, ValueError) and exc.args and isinstance(exc.args[0], tuple):
            path, reason = exc.args[0]
        else:
            path, reason = "", "Malformed packet field."
        return _invalid(path, reason)

    prefix = "CF" if grader == "candidate_fit" else "PF"
    findings = []
    target_rows = {}
    for i, row in enumerate(answer["assessments"]):
        target = row["target_id"]
        p = f"/answer/assessments/{i}"
        if target in target_rows:
            findings.append(finding(prefix + "-COVERAGE", "major", target, "duplicate_target", f"{p}/target_id",
                                    "A duplicate assessment does not provide a separate assessment of a material target."))
        else:
            target_rows[target] = i
        if target in gold["forbidden_assessment_targets"]:
            criterion = "CF-SCOPE" if prefix == "CF" else "PF-INTERPRETATION"
            findings.append(finding(criterion, "major", target, "forbidden_target", f"{p}/target_id",
                                    "This source is explicitly excluded as an assessment target by the proposed rubric."))
        elif target not in units:
            findings.append(finding(prefix + "-COVERAGE", "major", target if target in sources else None,
                                    "unmapped_target", f"{p}/target_id", "This assessment does not correspond to a material gold target."))
        if target in units:
            unit = units[target]
            if row["label"] not in unit["allowed_labels"]:
                criterion = "CF-LABEL" if prefix == "CF" else "PF-INTERPRETATION"
                findings.append(finding(criterion, "major", target, "disallowed_label", f"{p}/label",
                                        f"The proposed rubric allows {unit['allowed_labels']} for this target; the answer uses {row['label']!r}."))
            cited = {citation["source_id"] for citation in row["evidence"]}
            if not any(set(group) <= cited for group in unit["acceptable_evidence_sets"]):
                criterion = prefix + "-EVIDENCE"
                findings.append(finding(criterion, "major", target, "insufficient_source_set", f"{p}/evidence",
                                        "The cited source IDs do not contain any complete sufficient evidence set in the proposed rubric."))
        for j, citation in enumerate(row["evidence"]):
            ep = f"{p}/evidence/{j}"
            source = sources.get(citation["source_id"])
            if source is None:
                findings.append(finding(prefix + "-EVIDENCE", "major", target if target in sources else None,
                                        "unknown_source", f"{ep}/source_id", "The citation names no supplied input source."))
            elif citation["quote"] not in source["text"]:
                findings.append(finding(prefix + "-EVIDENCE", "major", target if target in sources else None,
                                        "nonliteral_quote", f"{ep}/quote", "The quoted text is not a literal substring of the named source."))
    for target in units:
        if target not in target_rows:
            findings.append(finding(prefix + "-COVERAGE", "major", target, "missing_target", "/answer/assessments",
                                    "A material gold target has no assessment row."))
    action = answer["conclusion"]["action"]
    if action not in gold["acceptable_actions"]:
        findings.append(finding(prefix + "-ACTION", "major", None, "disallowed_action", "/answer/conclusion/action",
                                f"The proposed rubric permits {gold['acceptable_actions']}; the answer chooses {action!r}."))
    findings.extend(_global_semantics(answer, sources, prefix))
    if grader == "candidate_fit":
        findings.extend(candidate_checks(inp, gold, answer, sources, units))
    else:
        findings.extend(preference_checks(inp, gold, answer, sources, units))
    return {"verdict": "fail" if findings else "pass", "findings": findings,
            "assurance": "rule_checks_only"}


# Load both family implementations while importing the package. grade() itself
# must perform no import, file access, process call, network request, or clock read.
from .candidate import candidate_checks  # noqa: E402
from .preference import preference_checks  # noqa: E402
