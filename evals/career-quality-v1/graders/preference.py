"""Role-to-preference checks that preserve person-owned exceptions and source scope."""

from __future__ import annotations

import re

from .shared import _has_positive_claim, finding


_GRANTED_EXCEPTION = r"\b(?:waiver|exception|flexibility|exemption)\s+(?:has\s+been|was|is)\s+(?:granted|approved|confirmed|offered)\b"
_NO_EXCEPTION = r"\b(?:no|never|cannot|can't)\s+(?:waiver|exception|flexibility|exemption)\s+(?:is|will\s+be|can\s+be)?\s*(?:available|possible|granted|approved)\b"
_DEFINITE_OFFER = r"\b(?:will\s+(?:receive|earn|be\s+paid)|has\s+an?\s+offer\s+of)\s+CHF\s*[\d,]+\b"
_SOFT_OFFSETS_HARD = r"\b(?:pay|salary|benefits?|prestige|perks?)\b[^.;:!?]{0,60}?\b(?:makes?\s+up\s+for|offsets?|outweighs?|compensates?\s+for)\b"


def preference_checks(inp: dict, gold: dict, answer: dict, sources: dict, units: dict) -> list[dict]:
    results = []
    jd = {row["id"]: row for row in inp["jd"]["sources"]}
    superseded = {old for row in jd.values() for old in row["supersedes"]}
    prefs = {row["id"]: row for row in inp["candidate"]["preferences"]}
    for i, row in enumerate(answer["assessments"]):
        target = row["target_id"]
        if target not in units:
            continue
        p = f"/answer/assessments/{i}"
        for j, citation in enumerate(row["evidence"]):
            if citation["source_id"] in superseded:
                results.append(finding("PF-EVIDENCE", "major", target, "superseded_role_term",
                                       f"{p}/evidence/{j}/source_id",
                                       "The cited role term was explicitly superseded by a later authoritative source."))
        if _has_positive_claim(row["rationale"], _GRANTED_EXCEPTION):
            employer_text = " ".join(jd[c["source_id"]]["text"] for c in row["evidence"] if c["source_id"] in jd)
            if not re.search(_GRANTED_EXCEPTION, employer_text, re.I):
                results.append(finding("PF-UNKNOWN", "major", target, "invented_exception",
                                       f"{p}/rationale", "The answer says an employer exception was granted, but no cited role source grants one."))
        if row["label"] == "conflict" and prefs[target]["allowed_exceptions"] and _has_positive_claim(row["rationale"], _NO_EXCEPTION):
            results.append(finding("PF-INTERPRETATION", "major", target, "exception_ruled_out",
                                   f"{p}/rationale", "The answer categorically rules out an exception although the candidate explicitly permits an inquiry."))
        if _has_positive_claim(row["rationale"], _DEFINITE_OFFER):
            cited_text = " ".join(sources[c["source_id"]]["text"] for c in row["evidence"] if c["source_id"] in sources)
            if not re.search(r"\b(?:offer|contract|will\s+pay)\b", cited_text, re.I):
                results.append(finding("PF-EVIDENCE", "major", target, "invented_pay_offer",
                                       f"{p}/rationale", "The rationale states a definite personal pay offer; cited sources only describe role terms or a range."))
    hard_conflicts = [r["target_id"] for r in answer["assessments"]
                      if r["target_id"] in prefs and prefs[r["target_id"]]["priority"] == "must_have" and r["label"] == "conflict"]
    if hard_conflicts:
        for field in ("text", "next_step"):
            conclusion = answer["conclusion"][field]
            for match in re.finditer(_SOFT_OFFSETS_HARD, conclusion, re.I):
                if not re.search(r"\b(?:not|never|no|cannot|can't|doesn't|isn't)\b", match.group(), re.I):
                    results.append(finding("PF-PRIORITY", "major", hard_conflicts[0] if len(hard_conflicts) == 1 else None,
                                           "soft_overrides_hard", f"/answer/conclusion/{field}",
                                           "The conclusion explicitly treats pay or another soft advantage as compensation for a stated must-have conflict."))
                    break
    return results
