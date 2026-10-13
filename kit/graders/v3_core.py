"""Offline, bounded comparison of manually normalized career claims.

This module deliberately does not read source files or interpret anchor quotes.
The caller binds anchors to originals and authenticates the coverage review.
"""

from datetime import datetime, timezone
import hashlib
import json
import math
import re


SCHEMA = "maguire-claim-packet-v3"
PREDICATES = frozenset(
    "distance_saving console_use alert_escalation archive_processing sample_size ocr_method "
    "training_certification evaluation_authority personal_stipend published_stipend "
    "on_call learning_allowance compatible station_attendance remote_work "
    "location_flexibility supersedes governs resolves live_captions caption_refusal "
    "caption_requirement meeting_platform written_offer ledger_maintenance "
    "training_demo observed_after".split()
)
ABSENCE_PREDICATES = frozenset({"resolves", "governs", "supersedes", "written_offer"})
MODALITIES = frozenset(
    "observation self_report requirement permission possibility prediction commitment "
    "guarantee ability evaluation_instruction preference_constraint record_assessment".split()
)
STANCES = frozenset(
    {"asserted", "recommended_as_fact", "quoted", "rejected", "question", "conditional"}
)
NONASSERTIVE = frozenset({"quoted", "rejected", "question"})
MEASURE_KINDS = frozenset({"count", "difference", "rate", "amount", "frequency"})
DENOMINATORS = frozenset({"day", "week", "calendar_month", "calendar_quarter"})
_HEX = re.compile(r"^[0-9a-fA-F]{64}$")


class InvalidPacket(ValueError):
    """A packet violates the declared structural or integrity contract."""


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                      allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def _fields(value, names, path):
    if not isinstance(value, dict) or set(value) != set(names):
        raise InvalidPacket("%s must have exactly: %s" % (path, ", ".join(sorted(names))))


def _string(value, path, allow_empty=False):
    if not isinstance(value, str) or (not allow_empty and not value):
        raise InvalidPacket("%s must be a string%s" % (path, "" if allow_empty else " with content"))


def _timestamp(value, path):
    _string(value, path)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise InvalidPacket("%s must be an ISO timestamp" % path) from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise InvalidPacket("%s must include a timezone" % path)
    return parsed.astimezone(timezone.utc)


def _anchor(value, path):
    _fields(value, {"sha256", "pointer", "start", "end", "quote"}, path)
    if not isinstance(value["sha256"], str) or not _HEX.fullmatch(value["sha256"]):
        raise InvalidPacket("%s.sha256 must be a SHA-256 hex digest" % path)
    _string(value["pointer"], path + ".pointer", allow_empty=True)
    if any(type(value[k]) is not int or value[k] < 0 for k in ("start", "end")):
        raise InvalidPacket("%s offsets must be nonnegative integers" % path)
    if value["end"] < value["start"]:
        raise InvalidPacket("%s has reversed offsets" % path)
    _string(value["quote"], path + ".quote", allow_empty=True)
    if value["end"] - value["start"] != len(value["quote"]):
        raise InvalidPacket("%s quote length differs from code point offsets" % path)


def _dimensions(value, path):
    if not isinstance(value, dict):
        raise InvalidPacket("%s must be a dimension object" % path)
    for key, scalar in value.items():
        _string(key, path + " key")
        if scalar is not None and type(scalar) not in (str, int, float, bool):
            raise InvalidPacket("%s.%s must be scalar" % (path, key))
        if type(scalar) is float and not math.isfinite(scalar):
            raise InvalidPacket("%s.%s must be finite" % (path, key))


def _measure(value, path):
    if value is None:
        return
    _fields(value, {"kind", "unit", "lower", "upper", "per"}, path)
    if value["kind"] not in MEASURE_KINDS:
        raise InvalidPacket("%s.kind is invalid" % path)
    _string(value["unit"], path + ".unit")
    if value["per"] is not None and value["per"] not in DENOMINATORS:
        raise InvalidPacket("%s.per is invalid" % path)
    for key in ("lower", "upper"):
        number = value[key]
        if number is not None and (type(number) not in (int, float) or not math.isfinite(number)):
            raise InvalidPacket("%s.%s must be a finite number or null" % (path, key))
    if value["lower"] is not None and value["upper"] is not None:
        if value["lower"] > value["upper"]:
            raise InvalidPacket("%s has a reversed interval" % path)


def _proposition(value, path):
    _fields(value, {"subject", "predicate", "object", "polarity", "modality",
                    "epistemic_scope", "scope", "time", "measure"}, path)
    for key in ("subject", "predicate", "object"):
        _string(value[key], path + "." + key)
    if value["polarity"] not in ("positive", "negative"):
        raise InvalidPacket("%s.polarity is invalid" % path)
    if value["modality"] not in MODALITIES:
        raise InvalidPacket("%s.modality is invalid" % path)
    if value["epistemic_scope"] not in ("world", "packet"):
        raise InvalidPacket("%s.epistemic_scope is invalid" % path)
    _dimensions(value["scope"], path + ".scope")
    _dimensions(value["time"], path + ".time")
    _measure(value["measure"], path + ".measure")


def _source(value, path):
    _fields(value, {"id", "kind", "status", "observed_at", "anchor", "facts"}, path)
    _string(value["id"], path + ".id")
    if value["kind"] not in ("candidate_fact", "job_description", "employer_update", "preference"):
        raise InvalidPacket("%s.kind is invalid" % path)
    if value["status"] not in ("active", "withdrawn"):
        raise InvalidPacket("%s.status is invalid" % path)
    if value["observed_at"] is not None:
        _timestamp(value["observed_at"], path + ".observed_at")
    _anchor(value["anchor"], path + ".anchor")
    if not isinstance(value["facts"], list):
        raise InvalidPacket("%s.facts must be an array" % path)
    for index, fact in enumerate(value["facts"]):
        _proposition(fact, "%s.facts[%d]" % (path, index))


def _claim(value, path):
    _fields(value, {"id", "anchor", "stance", "readings"}, path)
    _string(value["id"], path + ".id")
    _anchor(value["anchor"], path + ".anchor")
    if value["stance"] not in STANCES:
        raise InvalidPacket("%s.stance is invalid" % path)
    if not isinstance(value["readings"], list) or not value["readings"]:
        raise InvalidPacket("%s.readings must be a nonempty array" % path)
    for index, reading in enumerate(value["readings"]):
        _proposition(reading, "%s.readings[%d]" % (path, index))


def _coverage(value):
    _fields(value, {"scope", "source_sha256", "claims_sha256", "status",
                    "source_inventory_complete", "fragment_complete"}, "coverage")
    if value["scope"] != "fragment":
        raise InvalidPacket("coverage.scope must be fragment")
    for key in ("source_sha256", "claims_sha256"):
        if not isinstance(value[key], str) or not _HEX.fullmatch(value[key]):
            raise InvalidPacket("coverage.%s must be a SHA-256 hex digest" % key)
    if value["status"] not in ("agent_reviewed", "unreviewed"):
        raise InvalidPacket("coverage.status is invalid")
    for key in ("source_inventory_complete", "fragment_complete"):
        if type(value[key]) is not bool:
            raise InvalidPacket("coverage.%s must be boolean" % key)


def _validate_sources_claims(sources, claims):
    if not isinstance(sources, list) or not isinstance(claims, list):
        raise InvalidPacket("sources and claims must be arrays")
    ids = set()
    for kind, values, validator in (("sources", sources, _source), ("claims", claims, _claim)):
        for index, value in enumerate(values):
            validator(value, "%s[%d]" % (kind, index))
            if value["id"] in ids:
                raise InvalidPacket("duplicate ID: %s" % value["id"])
            ids.add(value["id"])


def _eligible(source, decision_at):
    return source["status"] == "active" and (source["observed_at"] is None or
           _timestamp(source["observed_at"], "observed_at") <= decision_at)


def _modality_supports(evidence, claim):
    if evidence == claim:
        return True
    return (evidence, claim) in {("self_report", "observation"),
                                 ("observation", "possibility")}


def _contains_interval(outer, inner):
    """Whether every value permitted by inner lies inside outer."""
    return ((outer["lower"] is None or
             (inner["lower"] is not None and outer["lower"] <= inner["lower"])) and
            (outer["upper"] is None or
             (inner["upper"] is not None and outer["upper"] >= inner["upper"])))


def _measure_supports(claim, fact):
    wanted, observed = claim["measure"], fact["measure"]
    if wanted == observed:
        return True
    if wanted is None or observed is None:
        return False
    if any(wanted[key] != observed[key] for key in ("kind", "unit", "per")):
        return False
    if fact["modality"] == "observation" and claim["modality"] == "possibility":
        return _contains_interval(observed, wanted)
    if fact["modality"] == claim["modality"]:
        return _contains_interval(wanted, observed)
    return False


def _compare_axes(claim, fact):
    axes = []
    for key in ("subject", "predicate", "object", "epistemic_scope", "scope", "time"):
        if claim[key] != fact[key]:
            axes.append(key)
    if not _measure_supports(claim, fact):
        axes.append("measure")
    if not _modality_supports(fact["modality"], claim["modality"]):
        axes.append("modality")
    return axes


def _result(claim, relation=None, verdict="needs_review", rule="unresolved",
            explanation="Reasoning is unresolved.", support=(), counter=(), limited=(), axes=(),
            parse_status="valid"):
    support, counter, limited = (list(dict.fromkeys(values)) for values in (support, counter, limited))
    return {"id": claim["id"], "anchor": claim["anchor"], "parse_status": parse_status,
            "reasoning_status": "resolved" if verdict != "needs_review" else "unresolved",
            "evidence_relation": relation, "verdict": verdict, "rule": rule,
            "explanation": explanation, "support_evidence_ids": support,
            "counter_evidence_ids": counter, "limited_evidence_ids": limited,
            "evidence_ids": list(dict.fromkeys(support + counter + limited)),
            "inspected_source_ids": [],
            "axes": list(dict.fromkeys(axes))}


def _frequency_factor(claim_per, ceiling_per):
    if claim_per == ceiling_per:
        return 1
    factors = {("week", "calendar_month"): 3,
               ("calendar_month", "calendar_quarter"): 3,
               ("week", "calendar_quarter"): 9}
    return factors.get((claim_per, ceiling_per))


def _frequency_limit(reading, eligible):
    """Return a certain ceiling violation or an unresolved related ceiling."""
    measure = reading["measure"]
    if (reading["modality"] != "permission" or reading["time"].get("recurring") is not True or
            measure is None or measure["kind"] != "frequency"):
        return None
    related = []
    for source in eligible:
        if source["kind"] != "preference":
            continue
        for fact in source["facts"]:
            ceiling = fact["measure"]
            preference_scope = {key: value for key, value in fact["scope"].items()
                                if key not in ("priority", "exceptions")}
            if (fact["modality"] == "preference_constraint" and
                    fact["predicate"] == reading["predicate"] and
                    fact["subject"] == reading["subject"] and
                    fact["object"] == reading["object"] and
                    preference_scope == reading["scope"] and fact["time"] == reading["time"] and
                    ceiling is not None and
                    ceiling["kind"] == "frequency" and ceiling["unit"] == measure["unit"]):
                related.append((source["id"], fact))
    if not related:
        return None
    for source_id, fact in related:
        ceiling = fact["measure"]
        factor = _frequency_factor(measure["per"], ceiling["per"])
        if (reading["time"].get("recurring") is True and
                fact["time"].get("recurring") is True and
                measure["per"] is not None and ceiling["per"] is not None and
                factor is not None and measure["lower"] is not None and
                ceiling["upper"] is not None and
                measure["lower"] * factor > ceiling["upper"]):
            return ("violation", [source_id])
    return ("ambiguous", [source_id for source_id, _ in related])


def _compatibility(reading, eligible, complete):
    if reading["predicate"] != "compatible" or reading["polarity"] != "positive":
        return None
    preference, requirement = [], []
    for source in eligible:
        for fact in source["facts"]:
            if fact["object"] != reading["object"]:
                continue
            if (source["kind"] == "preference" and fact["modality"] == "preference_constraint" and
                    fact["subject"] == reading["subject"]):
                preference.append((source["id"], fact))
            if (source["kind"] in ("job_description", "employer_update") and
                    fact["modality"] == "requirement" and fact["polarity"] == "positive"):
                requirement.append((source["id"], fact))
    related = [sid for sid, _ in preference + requirement]
    ambiguous = False
    for preference_id, pref in preference:
        pref_scope = {key: value for key, value in pref["scope"].items()
                      if key not in ("priority", "exceptions", "quantifier")}
        universal = pref["scope"].get("quantifier") == "all" and not pref["time"]
        for requirement_id, req in requirement:
            if pref["predicate"] != req["predicate"]:
                continue
            if universal:
                scope_matches = all(req["scope"].get(key) == value for key, value in pref_scope.items())
                scope_matches &= all(reading["scope"].get(key) == value for key, value in pref_scope.items())
                scope_matches &= req["scope"] == reading["scope"]
                if reading["time"]:
                    scope_matches &= req["time"] == reading["time"]
            else:
                scope_matches = pref_scope == req["scope"] == reading["scope"]
            if not scope_matches:
                ambiguous = True
                continue
            hard = (pref["polarity"] == "negative" and
                    pref["scope"].get("priority") == "must_have" and
                    pref["scope"].get("exceptions") is False)
            if hard and (universal or pref["time"] == req["time"] == reading["time"]):
                # A universal prohibition covers narrower scheduling; a narrow ban
                # needs the same explicit time on preference, role, and claim.
                if pref["measure"] is None or req["measure"] == pref["measure"]:
                    return ("contradicted", [preference_id, requirement_id],
                            "hard_preference_conflict", ["preference_constraint", "requirement"])
                ambiguous = True
                continue
            if (pref["polarity"] == "positive" and
                    pref["time"] == req["time"] == reading["time"] and
                    pref["measure"] is None and req["measure"] is None):
                return ("supported", [preference_id, requirement_id],
                        "preference_requirement_match", [])
            ambiguous = True
    if ambiguous:
        return (None, related, "compatibility_conditions_unresolved", ["scope", "time", "measure"])
    return ("not_established" if complete else None, related, "compatibility_gap",
            ["preference", "requirement"])


def _evaluate_valid_claim(claim, sources, context):
    if len(claim["readings"]) != 1:
        return _result(claim, rule="alternative_readings", explanation="Multiple plausible readings require review.",
                       parse_status="ambiguous")
    reading = claim["readings"][0]
    if reading["predicate"] not in PREDICATES:
        return _result(claim, rule="unknown_predicate", explanation="Predicate has no registered comparison rule.",
                       axes=["predicate"])
    if claim["stance"] in NONASSERTIVE:
        return _result(claim, verdict="pass", rule="nonassertive_stance",
                       explanation="Quoted, rejected, or questioned text does not assert world truth.")
    if claim["stance"] == "conditional":
        return _result(claim, rule="conditional_semantics", explanation="Conditional reasoning is outside this slice.",
                       axes=["stance"])

    decision_at = _timestamp(context["decision_at"], "context.decision_at")
    coverage = context["coverage"]
    complete = coverage["status"] == "agent_reviewed" and coverage["source_inventory_complete"]
    eligible = [source for source in sources if _eligible(source, decision_at)]

    if reading["predicate"] == "observed_after":
        if (reading["modality"] != "record_assessment" or
                reading["epistemic_scope"] != "packet" or reading["scope"] or
                reading["time"] or reading["measure"] is not None):
            return _result(claim, rule="observed_after_shape",
                           explanation="Observed-after requires a packet record assessment without dimensions.",
                           axes=["modality", "epistemic_scope", "scope", "time", "measure"])
        by_id = {source["id"]: source for source in eligible}
        pair = [by_id.get(reading["subject"]), by_id.get(reading["object"])]
        if any(source is None or source["observed_at"] is None for source in pair):
            return _result(claim, rule="observed_after_unknown",
                           explanation="Both active source observation times are needed for this comparison.",
                           limited=[source["id"] for source in pair if source is not None],
                           axes=["observed_at"])
        later = _timestamp(pair[0]["observed_at"], "observed_at") > _timestamp(pair[1]["observed_at"], "observed_at")
        agrees = later == (reading["polarity"] == "positive")
        return _result(claim, "supported" if agrees else "contradicted",
                       "pass" if agrees else "fail", "observed_after_comparison",
                       "Source observation timestamps establish only their recorded order.",
                       support=[reading["subject"], reading["object"]] if agrees else (),
                       counter=[reading["subject"], reading["object"]] if not agrees else (),
                       axes=[] if agrees else ["observed_at"])

    if reading["predicate"] in ABSENCE_PREDICATES and reading["polarity"] == "negative" and reading["epistemic_scope"] == "packet":
        recorded = [source["id"] for source in eligible for fact in source["facts"]
                    if all(fact[k] == reading[k] for k in ("subject", "predicate", "object", "scope", "time"))
                    and fact["polarity"] == "positive" and
                    fact["modality"] in ("observation", "self_report", "commitment", "guarantee", "record_assessment")]
        if recorded:
            return _result(claim, "contradicted", "fail", "packet_positive_recorded",
                           "The reviewed packet contains a matching positive assertion.", counter=recorded,
                           axes=["polarity", "epistemic_scope"])
        if complete:
            return _result(claim, "supported", "pass", "complete_packet_absence",
                           "No matching positive assertion appears in the complete reviewed source inventory.")
        return _result(claim, rule="incomplete_packet_absence",
                       explanation="Packet absence requires a complete reviewed source inventory.",
                       axes=["coverage"])

    special = _compatibility(reading, eligible, complete)
    if special:
        relation, evidence, rule, special_axes = special
        if relation == "contradicted":
            return _result(claim, relation, "fail", rule,
                           "A must-have candidate constraint conflicts with a matching role requirement.",
                           counter=evidence, axes=special_axes)
        if relation == "supported":
            return _result(claim, relation, "pass", rule,
                           "An active candidate preference and role requirement support compatibility.",
                           support=evidence)
        if relation is None:
            return _result(claim, rule=rule, explanation="Compatibility needs reviewed preference and role coverage.",
                           limited=evidence, axes=special_axes + (["coverage"] if not complete else []))
        return _result(claim, relation, "fail", rule,
                       "A matching candidate preference and role requirement do not jointly establish compatibility.",
                       limited=evidence, axes=special_axes)

    freq = _frequency_limit(reading, eligible)
    if freq:
        status, evidence = freq
        if status == "violation":
            return _result(claim, "contradicted", "fail", "frequency_ceiling",
                           "The recurring permission necessarily exceeds an active candidate ceiling.",
                           counter=evidence, axes=["measure", "modality"])

    support, counter, limited, axes = [], [], [], []
    authority_limited = False
    self_report = False
    for source in sources:
        usable = _eligible(source, decision_at)
        for fact in source["facts"]:
            if fact["predicate"] != reading["predicate"]:
                continue
            if fact["subject"] != reading["subject"] and fact["object"] != reading["object"]:
                continue
            mismatches = _compare_axes(reading, fact)
            if not usable:
                limited.append(source["id"])
                axes.append("source_status" if source["status"] == "withdrawn" else "observed_at")
                continue
            if (reading["predicate"] == "evaluation_authority" and
                    fact["modality"] == "evaluation_instruction"):
                authority_limited = True
                limited.append(source["id"])
                axes.append("source_role")
                continue
            if not mismatches:
                if fact["polarity"] == reading["polarity"]:
                    support.append(source["id"])
                    self_report |= fact["modality"] == "self_report" and reading["modality"] == "observation"
                else:
                    counter.append(source["id"])
                continue
            # Polarity does not affect the ordinary dimension comparison.
            limited.append(source["id"])
            axes.extend(mismatches)
    if support and counter:
        return _result(claim, "conflicting", "needs_review", "conflicting_evidence",
                       "Matching support and opposite-polarity evidence remain in the packet.",
                       support=support, counter=counter, limited=limited, axes=axes + ["polarity"])
    if counter:
        return _result(claim, "contradicted", "fail", "opposite_polarity",
                       "Applicable evidence states the opposite polarity.", counter=counter,
                       limited=limited, axes=axes + ["polarity"])
    if support:
        return _result(claim, "supported", "pass", "direct_support",
                       "Direct support found" + (" at self-report evidence level." if self_report else "."),
                       support=support, limited=limited, axes=axes)
    if freq and freq[0] == "ambiguous":
        return _result(claim, rule="frequency_ambiguous",
                       explanation="A related ceiling exists, but the available bounds do not prove a violation.",
                       limited=limited + freq[1], axes=axes + ["measure", "time"])
    if not complete:
        return _result(claim, rule="incomplete_source_inventory",
                       explanation="The reviewed inventory is incomplete; an evidence gap is unresolved.",
                       limited=limited, axes=axes + ["coverage"])
    if not limited:
        axes.append("supporting_proposition")
    requested = "%s / %s / %s" % (reading["subject"], reading["predicate"], reading["object"])
    return _result(claim, "not_established", "fail", "source_role_boundary" if authority_limited else "evidence_gap",
                   "Available evidence does not establish the asserted proposition: %s." % requested,
                   limited=limited, axes=axes)


def _check_valid_claim(claim, sources, context):
    result = _evaluate_valid_claim(claim, sources, context)
    decision_at = _timestamp(context["decision_at"], "context.decision_at")
    result["inspected_source_ids"] = [source["id"] for source in sources if _eligible(source, decision_at)]
    return result


def check_claim(claim, sources, context):
    """Check one claim, binding all sources; claims hash binds only full fragments."""
    try:
        _claim(claim, "claim")
        _validate_sources_claims(sources, [claim])
        _fields(context, {"grader", "decision_at", "coverage"}, "context")
        if context["grader"] not in ("candidate_fit", "preference_fit"):
            raise InvalidPacket("context.grader is invalid")
        _timestamp(context["decision_at"], "context.decision_at")
        _coverage(context["coverage"])
        if context["coverage"]["source_sha256"].lower() != digest(sources):
            raise InvalidPacket("coverage.source_sha256 does not bind sources")
    except (InvalidPacket, KeyError, TypeError, ValueError) as exc:
        safe_claim = claim if isinstance(claim, dict) and "id" in claim and "anchor" in claim else {"id": None, "anchor": None}
        return _result(safe_claim, rule="invalid_input", explanation=str(exc), parse_status="invalid")
    return _check_valid_claim(claim, sources, context)


def grade_fragment(packet):
    """Grade only the selected fragment; always return an auditable envelope."""
    base = {"schema": SCHEMA, "scope": "fragment",
            "assurance": "manual_normalization_agent_reviewed", "verdict": "invalid",
            "claims": [], "findings": [], "review_reasons": [], "whole_answer_verdict": None}
    try:
        _fields(packet, {"schema", "grader", "decision_at", "sources", "claims", "coverage"}, "packet")
        if packet["schema"] != SCHEMA:
            raise InvalidPacket("packet.schema is invalid")
        if packet["grader"] not in ("candidate_fit", "preference_fit"):
            raise InvalidPacket("packet.grader is invalid")
        _timestamp(packet["decision_at"], "packet.decision_at")
        _validate_sources_claims(packet["sources"], packet["claims"])
        if not packet["claims"]:
            raise InvalidPacket("claims must be nonempty")
        _coverage(packet["coverage"])
        if packet["coverage"]["source_sha256"].lower() != digest(packet["sources"]):
            raise InvalidPacket("coverage.source_sha256 does not bind sources")
        if packet["coverage"]["claims_sha256"].lower() != digest(packet["claims"]):
            raise InvalidPacket("coverage.claims_sha256 does not bind claims")
    except (InvalidPacket, KeyError, TypeError, ValueError, OverflowError) as exc:
        base["review_reasons"] = ["invalid_packet: " + str(exc)]
        return base
    context = {"grader": packet["grader"], "decision_at": packet["decision_at"],
               "coverage": packet["coverage"]}
    results = [_check_valid_claim(claim, packet["sources"], context) for claim in packet["claims"]]
    findings = [{"claim_id": result["id"], "anchor": result["anchor"],
                 "evidence_relation": result["evidence_relation"], "rule": result["rule"],
                 "explanation": result["explanation"], "axes": result["axes"],
                 "evidence_ids": result["evidence_ids"]}
                for result in results if result["verdict"] == "fail"]
    reasons = ["claim_needs_review: " + str(result["id"]) for result in results
               if result["verdict"] == "needs_review"]
    if packet["coverage"]["status"] != "agent_reviewed":
        reasons.append("coverage_unreviewed")
    if not packet["coverage"]["source_inventory_complete"]:
        reasons.append("source_inventory_incomplete")
    if not packet["coverage"]["fragment_complete"]:
        reasons.append("fragment_incomplete")
    base.update(claims=results, findings=findings, review_reasons=reasons,
                verdict="fail" if findings else "needs_review" if reasons else "pass")
    return base
