"""Role-to-preference checks that preserve person-owned exceptions and source scope."""

from __future__ import annotations

import re

from .shared import _has_positive_claim, finding


_GRANTED_EXCEPTION = r"\b(?:waiver|exception|flexibility|exemption)\s+(?:has\s+been|was|is)\s+(?:granted|approved|confirmed|offered)\b|\b(?:employer|company|role)\s+(?:has\s+)?(?:granted|approved|confirmed|offered)\s+(?:an?\s+)?(?:waiver|exception|exemption|flexibility|it)\b"
_NO_EXCEPTION = r"\b(?:no|never|cannot|can't)\s+(?:waiver|exception|flexibility|exemption)\s+(?:is|will\s+be|can\s+be)?\s*(?:available|possible|granted|approved)\b"
_DEFINITE_OFFER = r"\b(?:will\s+(?:receive|earn|be\s+paid|get)|has\s+(?:an?\s+)?(?:confirmed|guaranteed)?\s*offer\s+of|is\s+guaranteed\s+(?:an?\s+)?)\s*(?:CHF|USD|EUR|GBP|\$|€|£)\s*[\d,]+\b|\b(?:personal|candidate's|their)\s+(?:salary|offer|pay)\s+(?:is|has\s+been)\s+(?:guaranteed|confirmed|secured)\b"
_SOFT_OFFSETS_HARD = r"\b(?:pay|salary|benefits?|prestige|perks?)\b[^.;:!?]{0,60}?\b(?:makes?\s+up\s+for|offsets?|outweighs?|compensates?\s+for|cancels?\s+(?:out\s+)?[^.;:!?]{0,35}\b(?:condition|conflict|requirement))\b"
_CANDIDATE_WAIVES = r"\b(?:candidate|person|applicant|they|she|he)\s+(?:can|will|has\s+agreed\s+to|is\s+willing\s+to)\s+(?:waive|relax|drop|set\s+aside|accept\s+despite)\b|\b(?:candidate's|person's|applicant's)\s+exception\s+(?:makes?|means?)\s+(?:the\s+)?(?:requirement|condition|conflict)\s+(?:acceptable|resolved|irrelevant)\b"
_NEWER_DECIDES = r"\b(?:newer|latest|later|more\s+recent)\b[^.;:!?]{0,75}\b(?:supersedes?|overrides?|replaces?|settles?|resolves?|authoritative|controlling|definitive)\b|\b(?:supersedes?|overrides?|replaces?|settles?|resolves?)\b[^.;:!?]{0,75}\b(?:because|since)\s+(?:it\s+is\s+)?(?:newer|latest|later|more\s+recent)\b"
_SCOPE_EXPANSION = r"\b(?:personal|individual)\s+(?:contract|offer|guarantee|entitlement)\b|\b(?:candidate|applicant|person)\s+has\s+(?:a\s+)?(?:guaranteed|confirmed|binding)\b[^.;:!?]{0,45}\b(?:contract|offer|term|entitlement)\b|\b(?:company[- ]wide|globally|all\s+employees|everyone|every\s+team|all\s+roles)\b"
_UNKNOWN_CERTAINTY = r"\b(?:condition|requirement|preference|term|benefit|arrangement|fit|compatibility)\s+(?:is|has\s+been)\s+(?:definitely|clearly|fully\s+)?(?:met|satisfied|confirmed|guaranteed|established|known|secured)\b|\b(?:we|the\s+candidate|they)\s+(?:know|can\s+be\s+certain)\s+(?:that\s+)?(?:the\s+)?(?:condition|requirement|preference|term|benefit|arrangement|fit)\b"
_UNKNOWN_OFFER = r"\b(?:employer|company|role)\s+(?:definitely|certainly|clearly)?\s*(?:offers?|provides?|guarantees?)\s+(?:the\s+)?(?:candidate|applicant|person)\b"
_MEASURE = r"\b(?:\d+(?:\.\d+)?|one|two|three|four|five|six|seven|eight|nine|ten|zero)\s+(?:days?|hours?|weeks?|months?|years?)\s+(?:(?:per|a|each|every)\s+(?:day|week|month|year))?\b"


def _asserted(text: str, pattern: str) -> bool:
    """Conservative English assertion check: plans, questions and rejected quotes are excluded."""
    for match in re.finditer(pattern, text, re.I):
        prefix = re.split(r"[.!?;:]|,\s*(?:therefore|so|hence)\b", text[max(0, match.start() - 115):match.start()], flags=re.I)[-1]
        if re.search(r"\b(?:not|never|no|neither|nor|cannot|can't|without|unconfirmed|unknown|unverified|unproven|if|whether|may|might|could|would|should|ask|check|verify|clarify|hypothetical|claimed|claiming|claims|incorrectly|wrongly|falsely)\b", prefix, re.I):
            continue
        if '"' in prefix or '“' in prefix or '‘' in prefix:
            continue
        return True
    return False


def _unsupported_time_claim(text: str, cited_text: str) -> bool:
    """Check an asserted time unit against cited amounts and basis, allowing inflection."""
    units = {"day": r"days?", "week": r"weeks?", "month": r"months?", "year": r"years?"}
    for match in re.finditer(_MEASURE, text, re.I):
        phrase = match.group().lower()
        count = re.match(r"(\d+(?:\.\d+)?|one|two|three|four|five|six|seven|eight|nine|ten|zero)", phrase)
        unit = next((name for name, pat in units.items() if re.search(r"\b" + pat + r"\b", phrase)), None)
        if not count or not unit:
            continue
        source_pattern = rf"\b{re.escape(count.group())}\b(?:[\s\-–]+\w+){{0,3}}?[\s\-–]+{units[unit]}\b"
        if not re.search(source_pattern, cited_text, re.I) and _asserted(text[max(0, match.start()-60):match.end()], re.escape(match.group())):
            return True
    basis = {
        "day": r"\b(?:daily|each\s+day|every\s+day|per\s+day|a\s+day)\b",
        "week": r"\b(?:weekly|working\s+week|each\s+week|every\s+week|per\s+week|a\s+week)\b",
        "month": r"\b(?:monthly|each\s+month|every\s+month|per\s+month|a\s+month)\b",
        "year": r"\b(?:annually|annual|yearly|each\s+year|every\s+year|per\s+year|a\s+year)\b",
    }
    for name, pattern in basis.items():
        for match in re.finditer(pattern, text, re.I):
            if name == "year" and re.search(r"\b(?:quarterly|each\s+quarter|per\s+quarter)\b", text, re.I) and re.search(r"\b(?:quarterly|each\s+quarter|per\s+quarter)\b", cited_text, re.I):
                # An explicit quarterly-to-annual comparison can be legitimate.
                continue
            if not re.search(pattern, cited_text, re.I) and _asserted(text[max(0, match.start()-60):match.end()], re.escape(match.group())):
                return True
    return False


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
        employer_text = " ".join(jd[c["source_id"]]["text"] for c in row["evidence"] if c["source_id"] in jd)
        cited_text = " ".join(sources[c["source_id"]]["text"] for c in row["evidence"] if c["source_id"] in sources)
        if _asserted(row["rationale"], _GRANTED_EXCEPTION) and not re.search(_GRANTED_EXCEPTION, employer_text, re.I):
            results.append(finding("PF-UNKNOWN", "major", target, "invented_exception",
                                   f"{p}/rationale", "The answer says an employer exception was granted, but no cited employer source grants one."))
        if row["label"] == "conflict" and prefs[target]["allowed_exceptions"] and _has_positive_claim(row["rationale"], _NO_EXCEPTION):
            results.append(finding("PF-INTERPRETATION", "major", target, "exception_ruled_out",
                                   f"{p}/rationale", "The answer categorically rules out an exception although the candidate explicitly permits an inquiry."))
        if _asserted(row["rationale"], _DEFINITE_OFFER):
            if not re.search(r"\b(?:personal\s+offer|individual\s+contract|candidate\s+will\s+(?:receive|be\s+paid)|has\s+been\s+offered)\b", employer_text, re.I):
                results.append(finding("PF-EVIDENCE", "major", target, "invented_pay_offer",
                                       f"{p}/rationale", "The rationale states a definite personal pay offer; cited employer terms do not establish one."))
        if row["label"] == "conflict" and prefs[target]["allowed_exceptions"] and _asserted(row["rationale"], _CANDIDATE_WAIVES):
            allowed = " ".join(prefs[target]["allowed_exceptions"])
            if not re.search(r"\b(?:may|can|will)\s+(?:accept|waive|relax|drop|set\s+aside)\b", allowed, re.I):
                results.append(finding("PF-INTERPRETATION", "major", target, "exception_scope_expanded",
                                       f"{p}/rationale", "The candidate permits an inquiry but has not waived the hard condition."))
        if _asserted(row["rationale"], _NEWER_DECIDES):
            cited_jd = [jd[c["source_id"]] for c in row["evidence"] if c["source_id"] in jd]
            if len(cited_jd) > 1 and not any(s["supersedes"] for s in cited_jd):
                results.append(finding("PF-EVIDENCE", "major", target, "date_as_authority",
                                       f"{p}/rationale", "The cited employer snapshots do not establish supersession; a newer date alone cannot settle conflicting terms."))
        if _asserted(row["rationale"], _SCOPE_EXPANSION) and re.search(r"\b(?:team|local|pilot|trial|department)\b", employer_text, re.I):
            if not re.search(_SCOPE_EXPANSION, employer_text, re.I):
                results.append(finding("PF-INTERPRETATION", "major", target, "scope_expanded",
                                       f"{p}/rationale", "A team or local term is described as a personal contract or wider policy without supporting authority."))
        if row["label"] == "unknown" and _asserted(row["rationale"], _UNKNOWN_CERTAINTY):
            results.append(finding("PF-UNKNOWN", "major", target, "unknown_as_known",
                                   f"{p}/rationale", "The rationale calls the unresolved preference term settled or confirmed."))
        if row["label"] == "unknown" and _asserted(row["rationale"], _UNKNOWN_OFFER):
            results.append(finding("PF-UNKNOWN", "major", target, "unknown_as_known",
                                   f"{p}/rationale", "The rationale turns an unresolved individual term into a definite employer offer."))
        if _unsupported_time_claim(row["rationale"], cited_text):
            results.append(finding("PF-INTERPRETATION", "major", target, "unsupported_time_basis",
                                   f"{p}/rationale", "The rationale asserts a frequency or time amount absent from its cited source terms."))
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
    employer_all = " ".join(s["text"] for s in jd.values())
    unresolved = [r["target_id"] for r in answer["assessments"] if r["target_id"] in prefs and r["label"] == "unknown"]
    for field in ("text", "next_step"):
        text = answer["conclusion"][field]
        path = f"/answer/conclusion/{field}"
        target = unresolved[0] if len(unresolved) == 1 else None
        if unresolved and _asserted(text, _UNKNOWN_CERTAINTY):
            results.append(finding("PF-UNKNOWN", "major", target, "unknown_as_known", path,
                                   "The conclusion presents an unresolved preference term as established."))
        if unresolved and _asserted(text, _UNKNOWN_OFFER):
            results.append(finding("PF-UNKNOWN", "major", target, "unknown_as_known", path,
                                   "The conclusion turns an unresolved individual term into a definite employer offer."))
        if _asserted(text, _GRANTED_EXCEPTION) and not re.search(_GRANTED_EXCEPTION, employer_all, re.I):
            results.append(finding("PF-UNKNOWN", "major", None, "invented_exception", path,
                                   "The conclusion asserts a granted employer exception absent from the supplied employer terms."))
        if _asserted(text, _DEFINITE_OFFER) and not re.search(r"\b(?:personal\s+offer|individual\s+contract|candidate\s+will\s+(?:receive|be\s+paid)|has\s+been\s+offered)\b", employer_all, re.I):
            results.append(finding("PF-EVIDENCE", "major", None, "invented_pay_offer", path,
                                   "A published range or possibility does not establish a guaranteed personal offer."))
        if _asserted(text, _NEWER_DECIDES) and len(jd) > 1 and not any(s["supersedes"] for s in jd.values()):
            results.append(finding("PF-EVIDENCE", "major", None, "date_as_authority", path,
                                   "The sources do not establish supersession; date order alone cannot resolve them."))
        if _asserted(text, _SCOPE_EXPANSION) and re.search(r"\b(?:team|local|pilot|trial|department)\b", employer_all, re.I) and not re.search(_SCOPE_EXPANSION, employer_all, re.I):
            results.append(finding("PF-INTERPRETATION", "major", None, "scope_expanded", path,
                                   "A limited employer term is expanded to personal or global scope without support."))
        if hard_conflicts and _asserted(text, _CANDIDATE_WAIVES):
            targets = [t for t in hard_conflicts if prefs[t]["allowed_exceptions"] and not re.search(r"\b(?:may|can|will)\s+(?:accept|waive|relax|drop|set\s+aside)\b", " ".join(prefs[t]["allowed_exceptions"]), re.I)]
            if targets:
                results.append(finding("PF-INTERPRETATION", "major", targets[0] if len(targets) == 1 else None,
                                       "exception_scope_expanded", path, "Permission to ask about an exception is not consent to waive a must-have."))
    return results
