"""Small, typed temporal entailments for manually normalized career facts.

This is deliberately limited to dated events and current certificate status. It
does not infer general interval semantics from arbitrary ``time`` dictionaries.
"""

from datetime import date
import re

import v3_core as base


_MONTH = re.compile(r"^[0-9]{4}-(0[1-9]|1[0-2])$")
_DATE = re.compile(r"^[0-9]{4}-(0[1-9]|1[0-2])-([0-2][0-9]|3[01])$")
_DATED_EVENTS = frozenset({"certification_exam", "course_completion"})


def _date(value):
    if not isinstance(value, str) or not _DATE.fullmatch(value):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError:
        return None


def _month(value):
    if not isinstance(value, str) or not _MONTH.fullmatch(value):
        return None
    try:
        return date(int(value[:4]), int(value[5:]), 1)
    except ValueError:
        return None


def _usable(source, packet, at):
    if source["kind"] != "candidate_fact" or not base._eligible(source, at):
        return False
    # A positive replacement marker makes the old evidence unsafe even when the
    # replacement's substantive fact is not one of the shapes below.
    for other in packet["sources"]:
        if not base._eligible(other, at):
            continue
        if any(f["predicate"] == "supersedes" and f["object"] == source["id"] and
               f["polarity"] == "positive" for f in other["facts"]):
            return False
    return True


def _same(reading, fact):
    return (all(reading[k] == fact[k] for k in
                ("subject", "predicate", "object", "epistemic_scope", "scope")) and
            base._measure_supports(reading, fact) and
            base._modality_supports(fact["modality"], reading["modality"]))


def _result(claim, verdict, rule, explanation, support=(), counter=(), limited=()):
    return base._result(
        claim, {"pass": "supported", "fail": "contradicted"}.get(verdict, "conflicting"),
        verdict, rule, explanation, support=support, counter=counter, limited=limited,
        axes=["time"] if verdict != "pass" else (),
    )


def _resolve(claim, reading, direct, positive, negative, unresolved=()):
    """Merge dated implications with exact evidence already found by v3."""
    positive = list(dict.fromkeys(positive))
    negative = list(dict.fromkeys(negative))
    for sid in direct["support_evidence_ids"]:
        (positive if reading["polarity"] == "positive" else negative).append(sid)
    for sid in direct["counter_evidence_ids"]:
        (negative if reading["polarity"] == "positive" else positive).append(sid)
    positive = list(dict.fromkeys(positive))
    negative = list(dict.fromkeys(negative))
    unresolved = list(dict.fromkeys(unresolved))
    if positive and negative:
        return _result(claim, "needs_review", "temporal_conflict",
                       "Eligible evidence gives competing status or event implications.",
                       support=positive if reading["polarity"] == "positive" else negative,
                       counter=negative if reading["polarity"] == "positive" else positive,
                       limited=unresolved)
    if unresolved:
        return _result(claim, "needs_review", "temporal_boundary_unresolved",
                       "The available date structure or competing renewal record leaves status unresolved.",
                       support=positive if reading["polarity"] == "positive" else negative,
                       counter=negative if reading["polarity"] == "positive" else positive,
                       limited=unresolved)
    matching = positive if reading["polarity"] == "positive" else negative
    opposing = negative if reading["polarity"] == "positive" else positive
    if matching:
        return _result(claim, "pass", "bounded_temporal_entailment",
                       "The typed dates support this narrower assertion.", support=matching,
                       limited=unresolved)
    if opposing:
        return _result(claim, "fail", "bounded_temporal_contradiction",
                       "The typed dates establish the opposite current certificate status.",
                       counter=opposing, limited=unresolved)
    return None


def _event_year(claim, packet, at, direct, reading):
    wanted = reading["time"].get("year")
    if (reading["predicate"] not in _DATED_EVENTS or
            set(reading["time"]) != {"year"} or type(wanted) is not int or
            not 1 <= wanted <= 9999 or reading["epistemic_scope"] != "world"):
        return None
    positive_by_month, negative_by_month = {}, {}
    for source in packet["sources"]:
        if not _usable(source, packet, at):
            continue
        for fact in source["facts"]:
            if not _same(reading, fact) or set(fact["time"]) != {"month"}:
                continue
            month = _month(fact["time"]["month"])
            # An event in March proves one occurred that year. A denial limited
            # to March cannot prove no event occurred in the rest of the year.
            if month is not None and month.year == wanted:
                if (month > at.date().replace(day=1) or
                        source["observed_at"] is not None and month >
                        base._timestamp(source["observed_at"], "observed_at").date().replace(day=1)):
                    continue
                bucket = (positive_by_month if fact["polarity"] == "positive" else
                          negative_by_month)
                bucket.setdefault(month, []).append(source["id"])
    positive = [sid for ids in positive_by_month.values() for sid in ids]
    if not positive:
        return None
    conflicted = set(positive_by_month) & set(negative_by_month)
    if conflicted:
        return _result(claim, "needs_review", "temporal_conflict",
                       "Eligible sources disagree about whether the dated event occurred.",
                       support=[sid for month in conflicted for sid in positive_by_month[month]],
                       counter=[sid for month in conflicted for sid in negative_by_month[month]])
    return _resolve(claim, reading, direct, positive, [])


def _certificate_status(claim, packet, at, direct, reading):
    when = _date(reading["time"].get("at"))
    if (reading["predicate"] != "certificate_status" or
            reading["scope"] != {"status": "active"} or
            set(reading["time"]) != {"at"} or when is None or
            when != at.date() or reading["epistemic_scope"] != "world" or
            reading["measure"] is not None):
        return None

    positive, expiry, nonrenewal, unresolved = [], [], [], []
    for source in packet["sources"]:
        if not _usable(source, packet, at):
            continue
        # A source observed after the queried day cannot establish a past state.
        if source["observed_at"] is not None and base._timestamp(
                source["observed_at"], "observed_at").date() > when:
            continue
        for fact in source["facts"]:
            if (fact["subject"] != reading["subject"] or
                    fact["object"] != reading["object"] or
                    fact["epistemic_scope"] != reading["epistemic_scope"] or
                    not base._modality_supports(fact["modality"], reading["modality"]) or
                    fact["measure"] is not None):
                continue
            if (fact["predicate"] == "certificate_status" and
                    fact["scope"] == {"status": "active"} and
                    fact["polarity"] == "positive" and set(fact["time"]) == {"until"}):
                end_month = _month(fact["time"]["until"])
                if end_month is None or end_month.year == when.year and end_month.month == when.month:
                    unresolved.append(source["id"])
                elif end_month > when.replace(day=1):
                    positive.append(source["id"])
                else:
                    unresolved.append(source["id"])
            elif (fact["predicate"] == "certificate_expiry" and
                  fact["scope"] == {} and fact["polarity"] == "positive" and
                  set(fact["time"]) == {"date"}):
                expired = _date(fact["time"]["date"])
                if expired is None or expired >= when:
                    unresolved.append(source["id"])
                else:
                    expiry.append((source, expired))
            elif fact["predicate"] == "certificate_renewal" and fact["scope"] == {}:
                if fact["polarity"] == "negative" and fact["time"] == {}:
                    nonrenewal.append(source)
                elif fact["polarity"] == "positive":
                    # A dated renewal on or before the queried day challenges
                    # an unqualified no-renewal assertion. Future renewals do
                    # not change the status at this decision date.
                    renewed = (_date(fact["time"].get("date")) if
                               set(fact["time"]) == {"date"} else None)
                    if fact["time"] == {} or renewed is None or renewed <= when:
                        unresolved.append(source["id"])
                else:
                    unresolved.append(source["id"])
    negative = []
    for exp_source, expired in expiry:
        linked = [source for source in nonrenewal if
                  source["observed_at"] is None or
                  base._timestamp(source["observed_at"], "observed_at").date() >= expired]
        if linked:
            negative.extend((exp_source["id"], *(source["id"] for source in linked)))
        else:
            unresolved.append(exp_source["id"])
    if nonrenewal and not expiry:
        unresolved.extend(source["id"] for source in nonrenewal)
    if not positive and not negative and not unresolved:
        return None
    return _resolve(claim, reading, direct, positive, negative, unresolved)


def check(claim, packet, at, direct):
    """Return a bounded temporal result, or ``None`` to retain direct checking."""
    if (len(claim["readings"]) != 1 or claim["stance"] in base.NONASSERTIVE or
            claim["stance"] == "conditional" or direct["parse_status"] != "valid"):
        return None
    reading = claim["readings"][0]
    if reading["subject"] != "candidate":
        return None
    if reading["predicate"] in _DATED_EVENTS:
        return _event_year(claim, packet, at, direct, reading)
    if reading["predicate"] == "certificate_status":
        return _certificate_status(claim, packet, at, direct, reading)
    return None
