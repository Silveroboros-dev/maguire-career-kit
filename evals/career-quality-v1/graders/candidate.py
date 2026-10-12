"""Candidate-to-JD checks whose grounds are explicit in the projected packet."""

from __future__ import annotations

import re

from .shared import _has_positive_claim, finding


_INABILITY = r"\b(?:candidate|applicant|person|they|he|she)\s+(?:is\s+)?(?:unable\s+to|cannot|can't|incapable\s+of)\s+(?!establish|determine|tell|verify|confirm|assess|infer)"
_INDEPENDENT = r"\b(?:independently\s+(?:verified|confirmed|proven)|verified\s+(?:independently|by\s+(?:an?\s+)?independent\b)|proven\s+workplace\s+experience)\b"
_PRODUCTION = r"\b(?:candidate|applicant|person|they|he|she|I)\s+(?:has|have|had|demonstrated|proved|shows?|built|owned|led|operated|deployed)\b[^.;:!?]{0,55}\b(?:production|deployed|live\s+service)\b"
_OUTCOME = r"\b(?:reduced|increased|improved|cut|grew|saved|boosted)\b[^.;:!?]{0,60}?\b(?:\d+(?:\.\d+)?\s*%|CHF\s*[\d,]+)"


def _affirmative_metric_fact(metric: str, text: str) -> bool:
    """A number in a denial or future intention is not an achieved outcome."""
    normalized = metric.replace(" ", "").lower()
    for match in re.finditer(r"\d+(?:\.\d+)?\s*%|CHF\s*[\d,]+", text, re.I):
        if match.group().replace(" ", "").lower() != normalized:
            continue
        clause = re.split(r"[.;:!?]", text[max(0, match.start() - 100):match.start()])[-1].lower()
        denied = re.search(r"\b(?:did|do|does|have|has|had|was|were|is|are)\s+not\b|\b(?:never|didn't|doesn't|haven't|hasn't|cannot|can't)\b", clause)
        planned = re.search(r"\b(?:plan(?:ned)?|aim|intend|hope|want|expect|next\s+step|would\s+like|will|going\s+to)\b", clause)
        if not denied and not planned:
            return True
    return False


def _asserted_outcome(text: str):
    """Return an achieved numerical claim, excluding explicit doubt or plans."""
    for match in re.finditer(_OUTCOME, text, re.I):
        context = re.split(r"[.!?]", text[max(0, match.start() - 120):match.start()])[-1].lower()
        speculative = re.search(
            r"\b(?:not|never|no|cannot|can't|without|unproven|unknown|uncertain|"
            r"whether|if|may|might|could|would|should|can|will|plan|aim|test|"
            r"verify|measure|evaluate)\b|next\s+step", context)
        if not speculative:
            return match
    return None


def candidate_checks(inp: dict, gold: dict, answer: dict, sources: dict, units: dict) -> list[dict]:
    results = []
    facts = {row["id"]: row for row in inp["candidate"]["facts"]}
    superseded_facts = {old for row in facts.values() if row["status"] == "active" for old in row["supersedes"]}
    for i, row in enumerate(answer["assessments"]):
        target = row["target_id"]
        if target not in units:
            continue
        p = f"/answer/assessments/{i}"
        citations = row["evidence"]
        cited_facts = [facts[c["source_id"]] for c in citations if c["source_id"] in facts]
        if row["label"] in {"supported", "partial"} and not cited_facts:
            results.append(finding("CF-EVIDENCE", "major", target, "role_term_as_candidate_experience",
                                   f"{p}/evidence", "The assessment asserts candidate experience but cites no candidate fact; a job requirement alone cannot establish personal experience."))
        for j, citation in enumerate(citations):
            ident = citation["source_id"]
            if ident in facts and (facts[ident]["status"] == "withdrawn" or ident in superseded_facts):
                results.append(finding("CF-UNCERTAINTY", "major", target, "withdrawn_fact",
                                       f"{p}/evidence/{j}/source_id",
                                       "The cited candidate fact is withdrawn or superseded by an active correction and cannot support the current assessment."))
        if row["label"] == "unknown" and _has_positive_claim(row["rationale"], _INABILITY):
            results.append(finding("CF-UNCERTAINTY", "major", target, "unknown_as_inability",
                                   f"{p}/rationale", "The answer states that the candidate cannot do the work although this target is marked unknown from the supplied evidence."))
        # A bare self-report is evidence of a report, not independent corroboration.
        if cited_facts and all(f["evidence_type"] == "self_report" for f in cited_facts):
            if _has_positive_claim(row["rationale"], _INDEPENDENT):
                results.append(finding("CF-UNCERTAINTY", "major", target, "self_report_promoted",
                                       f"{p}/rationale", "Only self-reported candidate facts are cited, but the rationale asserts independent verification."))
        limited = cited_facts and all(re.search(r"\b(?:prototype|fictional|exercise|local\s+test|never\s+deployed|not\s+deployed)\b", f["text"], re.I) for f in cited_facts)
        if limited and _has_positive_claim(row["rationale"], _PRODUCTION):
            results.append(finding("CF-EVIDENCE", "major", target, "prototype_as_production",
                                   f"{p}/rationale", "The cited facts describe only a prototype, exercise, or explicit lack of deployment, while the rationale asserts production work."))
        match = _asserted_outcome(row["rationale"])
        if match:
            metric = re.search(r"\d+(?:\.\d+)?\s*%|CHF\s*[\d,]+", match.group(), re.I)
            if metric and not any(_affirmative_metric_fact(metric.group(), f["text"]) for f in cited_facts):
                results.append(finding("CF-EVIDENCE", "major", target, "unsupported_outcome_metric",
                                       f"{p}/rationale", f"The rationale asserts an achieved quantified outcome ({metric.group()}); the cited candidate facts either omit it or mention it only as a denial or plan."))
    unknown_targets = [r["target_id"] for r in answer["assessments"] if r["target_id"] in units and r["label"] == "unknown"]
    has_contradicted = any(r["label"] == "contradicted" for r in answer["assessments"])
    if unknown_targets and not has_contradicted:
        for field in ("text", "next_step"):
            if _has_positive_claim(answer["conclusion"][field], _INABILITY):
                target = unknown_targets[0] if len(unknown_targets) == 1 else None
                results.append(finding("CF-UNCERTAINTY", "major", target, "unknown_as_inability_in_conclusion",
                                       f"/answer/conclusion/{field}",
                                       "The conclusion asserts candidate inability while the relevant assessment records an unknown capability and no explicit counterfact."))
    return results
