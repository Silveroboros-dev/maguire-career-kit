"""Offline v8 claim checker. Operands are typed facts, never quote-text hints.

The local v3 copy supplies validation, direct comparison, and the result envelope.
These runtime-only overrides remove its approximate frequency conversion and admit
the v5 annual period; neither changes v3_core.py on disk.
"""

import re

import v3_core as base
import temporal


SCHEMA = "maguire-claim-packet-v8"
digest = base.digest
InvalidPacket = base.InvalidPacket
base.DENOMINATORS = base.DENOMINATORS | {"calendar_year"}
base.STANCES = base.STANCES | {"advice"}
base._frequency_limit = lambda reading, eligible: None
# Concrete source/answer actions only. Each remains subject to v3's exact
# subject, object, scope, time, polarity, modality and measure comparison.
# Qualitative fit/transferability are deliberately outside this registry.
DIRECT_ACTIONS = frozenset({
    "handoff_recording", "demo_presentation", "incident_review_facilitation",
    "follow_up_documentation", "vendor_cutover_coordination", "kubernetes_use",
    "plan_drafting", "plan_review", "guide_writing", "triage_time_reduction",
    "rollback_plan_writing", "rollback_plan_documentation", "course_completion",
    "certification_exam", "sql_query", "client_onboarding", "runbook_writing",
    "operator_training", "activation_date_promised",
    "incident_handling", "cutover_observation", "certificate_status",
    "checklist_documentation", "tool_building", "pilot_use",
    "guide_review", "business_travel", "overnight_travel",
    "work_pattern", "reimbursement_schedule", "remote_work_approval_authority",
    "plan_approval", "cutover_execution", "handoff_documentation",
    "Portuguese_proficiency", "audit_contact", "decision_log",
    "asynchronous_reading", "weekend_shift", "planning_work", "client_calls",
    "adjustable_desk", "core_hours_publication", "quiet_mornings",
    "induction_funding", "payment_method", "language_class_reimbursement",
    "individual_contributor", "direct_reports", "staff_supervision",
    "relocation_support", "relocation_amount", "relocation_approval",
    "role_consideration", "internal_briefs", "public_presentations",
    "meeting_transcript",
})
base.PREDICATES = base.PREDICATES | DIRECT_ACTIONS | {
    "constraint_satisfied", "request_within_limit", "constraint_unresolved",
    "confirmation_needed", "condition_required", "alert_triage", "stipend",
}

OPERANDS = {
    "constraint": ("offer", "preference"),
    "permission_limit": ("offer", "preference"),
    "pending": ("offer", "preference"),
    "condition": ("offer",),
    "onboarding": ("offer", "remote", "preference"),
    "schedule_before": ("offer", "preference"),
    "source_statement": ("source",),
    "confirm_unknown": ("unknown",),
}
PREDICATES = {
    "constraint": {"constraint_satisfied"},
    "permission_limit": {"request_within_limit"},
    "pending": {"constraint_unresolved", "confirmation_needed"},
    "condition": {"condition_required"},
    "onboarding": {"constraint_satisfied"},
    "schedule_before": {"constraint_satisfied"},
}
_MONTH = re.compile(r"^(\d{4})-(0[1-9]|1[0-2])$")
_DAYS = frozenset({"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"})


def _validate(packet):
    base._fields(packet, {"schema", "grader", "decision_at", "sources", "claims", "coverage"}, "packet")
    if packet["schema"] != SCHEMA or packet["grader"] not in ("candidate_fit", "preference_fit"):
        raise InvalidPacket("invalid schema or grader")
    base._timestamp(packet["decision_at"], "packet.decision_at")
    if not isinstance(packet["sources"], list) or not isinstance(packet["claims"], list) or not packet["claims"]:
        raise InvalidPacket("sources and nonempty claims must be arrays")
    ids = set()
    sources = {}
    for i, source in enumerate(packet["sources"]):
        base._source(source, "sources[%d]" % i)
        for j, proposition in enumerate(source["facts"]):
            _money_period(proposition, "sources[%d].facts[%d]" % (i, j))
            _time_fields(proposition, "sources[%d].facts[%d]" % (i, j))
        if source["id"] in ids:
            raise InvalidPacket("duplicate ID: " + source["id"])
        ids.add(source["id"])
        sources[source["id"]] = source
    for i, claim in enumerate(packet["claims"]):
        path = "claims[%d]" % i
        base._fields(claim, {"id", "anchor", "stance", "readings", "check"}, path)
        base._claim({k: claim[k] for k in ("id", "anchor", "stance", "readings")}, path)
        for j, proposition in enumerate(claim["readings"]):
            _money_period(proposition, path + ".readings[%d]" % j)
            _time_fields(proposition, path + ".readings[%d]" % j)
        if claim["id"] in ids:
            raise InvalidPacket("duplicate ID: " + claim["id"])
        ids.add(claim["id"])
        check = claim["check"]
        if check is None:
            continue
        if not isinstance(check, dict) or not isinstance(check.get("op"), str):
            raise InvalidPacket(path + ".check must be a typed operation")
        op = check["op"]
        if op not in OPERANDS:
            if set(check) != {"op"}:
                raise InvalidPacket(path + ".check unknown operation has extra fields")
            continue
        expected = {"op", *OPERANDS[op]}
        if op == "confirm_unknown":
            expected.add("field")
        base._fields(check, expected, path + ".check")
        if op == "confirm_unknown" and check["field"] != "approved_country_list":
            raise InvalidPacket(path + ".check.field is not a supported unknown field")
        for key in OPERANDS[op]:
            ref = check[key]
            base._fields(ref, {"source_id", "fact_index"}, path + ".check." + key)
            base._string(ref["source_id"], path + ".check." + key + ".source_id")
            index = ref["fact_index"]
            if type(index) is not int or index < 0 or ref["source_id"] not in sources or index >= len(sources[ref["source_id"]]["facts"]):
                raise InvalidPacket(path + ".check." + key + " references no fact in this packet")
        _supported_shape(claim, sources, path)
    base._coverage(packet["coverage"])
    if packet["coverage"]["source_sha256"].lower() != digest(packet["sources"]):
        raise InvalidPacket("coverage.source_sha256 does not bind sources")
    if packet["coverage"]["claims_sha256"].lower() != digest(packet["claims"]):
        raise InvalidPacket("coverage.claims_sha256 does not bind claims")


def _money_period(proposition, path):
    m = proposition["measure"]
    if m is not None and m["kind"] == "amount" and m["per"] is None:
        raise InvalidPacket(path + ".measure requires an explicit money period")


def _time_fields(proposition, path):
    time = proposition["time"]
    for key in ("start", "end"):
        if key in time and (not isinstance(time[key], str) or not _MONTH.fullmatch(time[key])):
            raise InvalidPacket(path + ".time." + key + " must be YYYY-MM")
    for key in ("start_minute", "end_minute", "after_minute"):
        if key in time and (type(time[key]) is not int or not 0 <= time[key] <= 1440):
            raise InvalidPacket(path + ".time." + key + " must be a minute in [0,1440]")


def _supported_shape(claim, sources, path):
    """Preflight the declared typed form, without deciding whether it is true."""
    op = claim["check"]["op"]
    if len(claim["readings"]) != 1:
        raise InvalidPacket(path + ".readings must contain one atom for a typed check")
    reading = claim["readings"][0]
    if op == "source_statement":
        sid = claim["check"]["source"]["source_id"]
        if (claim["stance"] not in ("asserted", "recommended_as_fact") or
                reading["subject"] != sid or reading["epistemic_scope"] != "packet"):
            raise InvalidPacket(path + " is not a canonical historical source statement")
        return
    if op == "confirm_unknown":
        if (claim["stance"] != "advice" or reading["subject"] != "candidate" or
                reading["predicate"] != "confirmation_needed" or
                reading["object"] != "country_approval" or
                reading["polarity"] != "positive" or
                reading["modality"] != "evaluation_instruction" or
                reading["epistemic_scope"] != "packet" or reading["measure"] is not None or
                set(reading["scope"]) != {"location", "approval"} or
                not isinstance(reading["scope"]["location"], str) or
                not reading["scope"]["location"] or
                reading["scope"]["approval"] != "unknown"):
            raise InvalidPacket(path + " is not canonical confirmation advice")
        return
    offer_ref = claim["check"]["offer"]
    offer = sources[offer_ref["source_id"]]["facts"][offer_ref["fact_index"]]
    comparison_keys = {"currency", "period", "offered", "minimum", "required_days",
                       "cap_days", "monthly_required", "monthly_cap", "minimum_monthly"}
    if (any(type(value) in (int, float) for value in reading["scope"].values()) or
            any(key in reading["scope"] for key in comparison_keys)):
        raise InvalidPacket(path + ".readings[0].scope contains comparison inputs instead of context")
    if (claim["stance"] not in ("asserted", "recommended_as_fact", "advice") or
            not _reading_shape(claim, op, offer)):
        raise InvalidPacket(path + " is not a canonical derived reading")
    if claim["stance"] == "advice" and not (op == "pending" and reading["predicate"] == "confirmation_needed"):
        raise InvalidPacket(path + " advice is unsupported for this operation")
    if claim["stance"] != "advice" and op == "pending" and reading["predicate"] != "constraint_unresolved":
        raise InvalidPacket(path + " must assert the unresolved constraint")
    if "preference" in claim["check"]:
        pref_ref = claim["check"]["preference"]
        pref = sources[pref_ref["source_id"]]["facts"][pref_ref["fact_index"]]
        if op != "onboarding" and (offer["predicate"], offer["object"]) != (pref["predicate"], pref["object"]):
            raise InvalidPacket(path + " operands do not name the same semantic property")
        if op == "onboarding" and offer["object"] != pref["object"]:
            raise InvalidPacket(path + " onboarding operands do not name the same property")


def validate_packet(packet):
    """Structural validation only. Raises InvalidPacket; never predicts claims."""
    try:
        _validate(packet)
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        if isinstance(exc, InvalidPacket):
            raise
        raise InvalidPacket(str(exc)) from exc
    return True


def _result(claim, status, rule, explanation, evidence=(), axes=(), other=()):
    relation = {"pass": "supported", "fail": "contradicted"}.get(status)
    buckets = {"support": (), "counter": (), "limited": ()}
    buckets[{"pass": "support", "fail": "counter"}.get(status, "limited")] = evidence
    result = base._result(claim, relation, status, rule, explanation,
                          support=buckets["support"], counter=buckets["counter"],
                          limited=buckets["limited"], axes=axes)
    result["evidence_ids"] = list(dict.fromkeys(result["evidence_ids"] + list(other)))
    return result


def _eligible(source, at):
    return base._eligible(source, at)


def _operand(packet, ref):
    source = next(s for s in packet["sources"] if s["id"] == ref["source_id"])
    return source, source["facts"][ref["fact_index"]]


def _context(scope):
    return {k: v for k, v in scope.items() if k != "priority"}


def _weekdays(value):
    if value == "weekday":
        return _DAYS - {"Saturday", "Sunday"}
    if value == "weekend":
        return {"Saturday", "Sunday"}
    return {value} if value in _DAYS else None


def _contexts_overlap(a, b):
    a, b = _context(a), _context(b)
    for key in set(a) & set(b):
        if a[key] == b[key]:
            continue
        if key == "weekday":
            left, right = _weekdays(a[key]), _weekdays(b[key])
            if left is not None and right is not None and not (left & right):
                return False
        else:
            return None
    return True


def _time_overlap(a, b):
    """Finite same-zone weekday/window overlap; other dimensions are unknown."""
    if a == b:
        return True
    allowed = {"weekday", "zone", "start_minute", "end_minute"}
    if not set(a) <= allowed or not set(b) <= allowed or a.get("zone") != b.get("zone") or not a.get("zone"):
        return None
    left, right = _weekdays(a.get("weekday")), _weekdays(b.get("weekday"))
    if left is None or right is None:
        return None
    if not left & right:
        return False
    for value in (a, b):
        if ("start_minute" in value) != ("end_minute" in value):
            return None
        if "start_minute" in value and not (type(value["start_minute"]) is int and
                type(value["end_minute"]) is int and 0 <= value["start_minute"] < value["end_minute"] <= 1440):
            return None
    start = max(a.get("start_minute", 0), b.get("start_minute", 0))
    end = min(a.get("end_minute", 1440), b.get("end_minute", 1440))
    return start < end


def _offer_scope_without_only(offer_scope, pref_scope):
    """Named offer-only provenance qualifiers do not alter candidate limits."""
    return ({k: v for k, v in offer_scope.items() if k not in ("only", "written_offer", "offer_inventory")} == _context(pref_scope)
            and ("only" not in offer_scope or offer_scope["only"] is True)
            and ("written_offer" not in offer_scope or offer_scope["written_offer"] is True)
            and ("offer_inventory" not in offer_scope or offer_scope["offer_inventory"] == "current"))


def _exhaustive_disjoint(offer, pref):
    """A complete offered duty set outside a whole-day ban is compatible."""
    if offer["scope"].get("only") is not True or not _offer_scope_without_only(offer["scope"], pref["scope"]):
        return False
    a, b = offer["time"], pref["time"]
    allowed = {"weekday", "zone", "start_minute", "end_minute"}
    if (not set(a) <= allowed or set(b) != {"weekday", "zone"} or
            a.get("zone") != b.get("zone") or a.get("zone") != "role_local"):
        return False
    if (("start_minute" in a) != ("end_minute" in a) or
            ("start_minute" in a and not (type(a["start_minute"]) is int and
             type(a["end_minute"]) is int and
             0 <= a["start_minute"] < a["end_minute"] <= 1440))):
        return False
    offered, banned = _weekdays(a.get("weekday")), _weekdays(b.get("weekday"))
    return offered is not None and banned is not None and not (offered & banned)


def _whole_day_ban_covers(offer, pref):
    if not _offer_scope_without_only(offer["scope"], pref["scope"]):
        return False
    allowed = {"weekday", "zone", "start_minute", "end_minute"}
    a, b = offer["time"], pref["time"]
    if (not set(a) <= allowed or set(b) != {"weekday", "zone"} or
            a.get("zone") != b.get("zone") or a.get("zone") != "role_local"):
        return False
    offered, banned = _weekdays(a.get("weekday")), _weekdays(b.get("weekday"))
    if offered is None or banned is None or not offered <= banned:
        return False
    return _time_overlap(a, b) is True


def _allowed_window_covers(offer, pref):
    if not _offer_scope_without_only(offer["scope"], pref["scope"]):
        return False
    a, b = offer["time"], pref["time"]
    required = {"weekday", "zone", "start_minute", "end_minute"}
    if set(a) != required or set(b) != required or a["zone"] != b["zone"] or a["zone"] != "role_local":
        return False
    offered, allowed = _weekdays(a["weekday"]), _weekdays(b["weekday"])
    return (offered is not None and allowed is not None and offered <= allowed and
            all(type(v) is int for v in (a["start_minute"], a["end_minute"], b["start_minute"], b["end_minute"])) and
            0 <= b["start_minute"] <= a["start_minute"] < a["end_minute"] <= b["end_minute"] <= 1440)


def _remote_preference(packet, remote, at):
    """A conditional permission needs explicit candidate acceptance of its term."""
    related = []
    for source in packet["sources"]:
        if source["kind"] != "preference" or not _eligible(source, at):
            continue
        for fact in source["facts"]:
            if (fact["subject"] == "candidate" and fact["predicate"] == "remote_work" and
                    fact["object"] == remote["object"] and
                    fact["modality"] == "preference_constraint" and fact["epistemic_scope"] == "world"):
                related.append((source["id"], fact))
    if remote["scope"].get("condition") is None and not related:
        return True, []
    if not related:
        return False, []
    accepted = False
    for _, fact in related:
        if (fact["polarity"] != "positive" or fact["scope"] != remote["scope"] or
                fact["time"] != remote["time"] or fact["measure"] is not None):
            return False, list(dict.fromkeys(sid for sid, _ in related))
        accepted = True
    return accepted, list(dict.fromkeys(sid for sid, _ in related))


def _same_property(offer, pref):
    return offer["predicate"] == pref["predicate"] and offer["object"] == pref["object"]


def _reading_shape(claim, op, offer):
    if len(claim["readings"]) != 1 or claim["stance"] == "conditional":
        return False
    r = claim["readings"][0]
    return (r["predicate"] in PREDICATES[op] and r["subject"] == "candidate" and
            r["object"] == offer["object"] and r["polarity"] == "positive" and
            r["modality"] == ("evaluation_instruction" if op == "pending" and claim["stance"] == "advice" else "record_assessment") and
            r["epistemic_scope"] == "packet" and r["measure"] is None)


def _interval(measure):
    return measure["lower"], measure["upper"]


def _numeric(offer, pref, mode):
    om, pm = offer["measure"], pref["measure"]
    if om is None or pm is None or om["kind"] != pm["kind"] or om["unit"] != pm["unit"]:
        return None, "measure"
    if om["per"] != pm["per"]:
        if (om["kind"] != "amount" or {om["per"], pm["per"]} != {"calendar_month", "calendar_year"}):
            return None, "period"
        factor = 12 if om["per"] == "calendar_month" else 1 / 12
        om = dict(om, lower=None if om["lower"] is None else om["lower"] * factor,
                  upper=None if om["upper"] is None else om["upper"] * factor)
    lo, hi = _interval(om)
    plo, phi = _interval(pm)
    if mode == "limit":
        if hi is None or plo is None or phi is None:
            return None, "measure"
        if (lo is None or lo <= plo) and hi >= phi:
            return "pass", "measure"
        return "fail", "measure"
    if plo is not None and lo is not None and lo < plo:
        return ("fail" if hi is not None and hi < plo else None), "measure"
    if phi is not None and hi is not None and hi > phi:
        return ("fail" if lo is not None and lo > phi else None), "measure"
    if (plo is None or lo is not None) and (phi is None or hi is not None):
        return "pass", "measure"
    return None, "measure"


def _supersession_evidence(packet, old_id, at):
    """Separate authorized replacement, observed denial, and unresolved markers."""
    positive, negative, uncertain = [], [], []
    for source in packet["sources"]:
        if source["kind"] != "employer_update" or not _eligible(source, at):
            continue
        for fact in source["facts"]:
            if (fact["predicate"] != "supersedes" or fact["subject"] != source["id"] or
                    fact["object"] != old_id):
                continue
            if fact["scope"] or fact["time"] or fact["measure"] is not None:
                uncertain.append(source["id"])
            elif fact["polarity"] == "positive" and fact["modality"] in ("observation", "commitment", "record_assessment"):
                positive.append(source["id"])
            elif (fact["polarity"] == "negative" and fact["modality"] == "observation" and
                  fact["epistemic_scope"] == "world"):
                negative.append(source["id"])
            else:
                uncertain.append(source["id"])
    # Two different updates can make different claims about the old term.
    # Only opposing signs from the same update contradict one another.
    uncertain.extend(sid for sid in positive if sid in negative)
    return (list(dict.fromkeys(positive)), list(dict.fromkeys(negative)),
            list(dict.fromkeys(uncertain)))


def _superseded(packet, old_id, at):
    positive, _, uncertain = _supersession_evidence(packet, old_id, at)
    return [] if uncertain else positive


def _uncertain_supersession(packet, old_id, at):
    return _supersession_evidence(packet, old_id, at)[2]


def _term_guard(packet, items, at, op):
    """Return a conservative conflict or trace for selected source terms."""
    trace = []
    for key in ("offer", "remote", "preference"):
        if key not in items:
            continue
        selected_source, selected_fact = items[key]
        if key != "preference":
            # A dated observation that an update does not amend this source
            # preserves the selected term and remains visible in the trace.
            trace.extend(_supersession_evidence(packet, selected_source["id"], at)[1])
            uncertain = _uncertain_supersession(packet, selected_source["id"], at)
            if uncertain:
                return ("supersession_unresolved", [selected_source["id"], *uncertain]), trace
            markers = _superseded(packet, selected_source["id"], at)
            if markers:
                return ("superseded_operand", [selected_source["id"], *markers]), trace
        for source in packet["sources"]:
            same_kind = (source["kind"] == selected_source["kind"] if key == "preference" else
                         source["kind"] in ("job_description", "employer_update"))
            if not _eligible(source, at) or not same_kind:
                continue
            markers = _superseded(packet, source["id"], at) if key != "preference" else []
            if markers and source is not selected_source:
                trace.extend([source["id"], *markers])
                continue
            for other in source["facts"]:
                if other is selected_fact or not _same_property(other, selected_fact) or other["subject"] != selected_fact["subject"]:
                    continue
                if op == "pending" and key == "offer":
                    # Planned, currently unavailable, and pending status facts can
                    # coexist. The pending rule below checks whether a firm term
                    # actually settles the same property.
                    continue
                same_scope = _contexts_overlap(other["scope"], selected_fact["scope"])
                if same_scope is False:
                    continue
                left_time, right_time = other["time"], selected_fact["time"]
                if op == "schedule_before" and key == "offer":
                    left_time = {k: v for k, v in left_time.items() if k not in ("start_minute", "end_minute")}
                    right_time = {k: v for k, v in right_time.items() if k not in ("start_minute", "end_minute")}
                if left_time != right_time and left_time and right_time:
                    continue
                if (same_scope is None or any(other[k] != selected_fact[k] for k in ("polarity", "modality", "measure", "scope", "time"))):
                    return ("competing_terms", [selected_source["id"], source["id"]]), trace
    return None, list(dict.fromkeys(trace))


def _competing(packet, selected, fact, at):
    competing = []
    for source in packet["sources"]:
        if source["id"] == selected["id"] or source["kind"] not in ("job_description", "employer_update") or not _eligible(source, at):
            continue
        if _superseded(packet, source["id"], at):
            continue
        for other in source["facts"]:
            if (_same_property(other, fact) and other["subject"] == fact["subject"] and
                    other["scope"] == fact["scope"] and other["time"] == fact["time"] and
                    any(other[k] != fact[k] for k in ("polarity", "modality", "measure"))):
                competing.append(source["id"])
    return list(dict.fromkeys(competing))


def _other_restrictions(packet, selected_offer, selected_pref_fact, fact, at):
    """Inspect all eligible same-property terms; one reference cannot hide a duty."""
    employers, preferences = [], []
    for source in packet["sources"]:
        if not _eligible(source, at) or _superseded(packet, source["id"], at):
            continue
        for other in source["facts"]:
            if not _same_property(other, fact):
                continue
            if source["kind"] in ("job_description", "employer_update"):
                # The role's lack of a duty is not undone by a different team
                # performing that duty. Conflicts still count for the same actor.
                if other["subject"] == fact["subject"]:
                    employers.append((source["id"], other))
            elif source["kind"] == "preference" and other["modality"] == "preference_constraint":
                preferences.append((source["id"], other))
    unknown = []
    for preference_id, preference in preferences:
        if preference is selected_pref_fact or preference["polarity"] != "positive":
            continue
        overlap = _contexts_overlap(preference["scope"], selected_pref_fact["scope"])
        if overlap is None or overlap:
            unknown.append(preference_id)
    for employer_id, employer in employers:
        for preference_id, preference in preferences:
            if preference["polarity"] != "negative" or employer["polarity"] != "positive" or employer["modality"] != "requirement":
                continue
            overlap = _contexts_overlap(employer["scope"], preference["scope"])
            time_overlap = _time_overlap(employer["time"], preference["time"])
            if overlap is None:
                unknown.extend((employer_id, preference_id))
            elif overlap and time_overlap is None:
                unknown.extend((employer_id, preference_id))
            elif overlap and time_overlap:
                positive_duty = (employer["measure"] is None or
                                 (employer["measure"]["lower"] is not None and employer["measure"]["lower"] > 0))
                if preference["measure"] is None and positive_duty and _whole_day_ban_covers(employer, preference):
                    return "fail", [employer_id, preference_id]
                unknown.extend((employer_id, preference_id))
    # Unknown additional terms on the same property cannot be silently ignored.
    for sid, other in employers:
        if sid != selected_offer["id"] and other["polarity"] == "positive" and other["modality"] == "requirement":
            if not any(_contexts_overlap(other["scope"], p["scope"]) is False for _, p in preferences):
                unknown.append(sid)
    for i, (sid, left) in enumerate(employers):
        for other_sid, right in employers[i + 1:]:
            if (left["scope"] == right["scope"] and left["time"] == right["time"] and
                    any(left[k] != right[k] for k in ("polarity", "modality", "measure"))):
                unknown.extend((sid, other_sid))
    return ("needs_review", list(dict.fromkeys(unknown))) if unknown else (None, [])


def _source_statement(claim, packet, at):
    ref = claim["check"]["source"]
    source, stated_fact = _operand(packet, ref)
    reading = claim["readings"][0]
    sid = source["id"]
    if source["observed_at"] is not None and base._timestamp(source["observed_at"], "observed_at") > at:
        return _result(claim, "needs_review", "future_source", "The named document was not observed by the decision time.", [sid], ["observed_at"])
    fields = ("predicate", "object", "polarity", "modality", "scope", "time", "measure")
    if (stated_fact["epistemic_scope"] == "world" and
            all(stated_fact[key] == reading[key] for key in fields)):
        return _result(claim, "pass", "historical_source_statement", "The named source contains this historical statement.", [sid])
    complete = packet["coverage"]["status"] == "agent_reviewed" and packet["coverage"]["source_inventory_complete"]
    if complete:
        return _result(claim, "fail", "historical_statement_mismatch", "The reviewed named source does not contain the asserted statement.", [sid], ["source_content"])
    return _result(claim, "needs_review", "historical_statement_unresolved", "The named source does not establish this statement in incomplete evidence.", [sid], ["source_content"])


def _confirm_unknown(claim, packet, at):
    ref = claim["check"]["unknown"]
    source, fact = _operand(packet, ref)
    sid = source["id"]
    reading = claim["readings"][0]
    if not _eligible(source, at):
        return _result(claim, "needs_review", "ineligible_unknown", "The unknown field is not in an active observed source.", [sid], ["source_status", "observed_at"])
    superseders = _superseded(packet, sid, at)
    if superseders:
        return _result(claim, "needs_review", "superseded_unknown", "The source with the unknown field was explicitly superseded.", [sid, *superseders], ["supersedes"])
    if (source["kind"] not in ("job_description", "employer_update") or
            fact["subject"] not in ("role", "employer") or
            fact["predicate"] != "remote_work" or fact["polarity"] != "positive" or
            fact["modality"] != "permission" or fact["epistemic_scope"] != "world" or
            fact["scope"].get("approved_country_list") != "unspecified" or
            reading["time"] != fact["time"]):
        return _result(claim, "needs_review", "unknown_not_established", "An active remote-work permission with an unspecified country list is required.", [sid], ["unknown_field", "time"])
    competing = []
    for other_source in packet["sources"]:
        if other_source["kind"] not in ("job_description", "employer_update") or not _eligible(other_source, at):
            continue
        if _superseded(packet, other_source["id"], at):
            continue
        for other in other_source["facts"]:
            if (other is fact or other["predicate"] != "remote_work" or
                    other["time"] != fact["time"] or other["epistemic_scope"] != "world"):
                continue
            if other["object"] == reading["scope"]["location"]:
                competing.append(other_source["id"])
                continue
            if other["object"] != fact["object"]:
                continue
            if (other["scope"].get("approved_country_list") not in (None, "unspecified") or
                    other["polarity"] != fact["polarity"] or other["modality"] != fact["modality"]):
                competing.append(other_source["id"])
    if competing:
        return _result(claim, "needs_review", "unknown_competing_term", "Another active term may settle or contradict the country list.", [sid, *competing], ["source_conflict"])
    return _result(claim, "pass", "confirm_explicit_unknown", "The named permission leaves the country list unspecified, so confirming it is advised.", [sid])


def _derived(claim, packet, at):
    check = claim["check"]
    op = check["op"]
    if op not in OPERANDS:
        return _result(claim, "needs_review", "unknown_operation", "This operation has no comparison rule.", axes=["check.op"])
    if op == "source_statement":
        return _source_statement(claim, packet, at)
    if op == "confirm_unknown":
        return _confirm_unknown(claim, packet, at)
    items = {key: _operand(packet, check[key]) for key in OPERANDS[op]}
    ids = list(dict.fromkeys(src["id"] for src, _ in items.values()))
    offer_source, offer = items["offer"]
    if len(claim["readings"]) != 1:
        return _result(claim, "needs_review", "alternative_readings", "Multiple readings require review.", ids, ["readings"])
    if claim["stance"] in base.NONASSERTIVE or claim["stance"] == "conditional":
        return _result(claim, "needs_review", "operation_stance", "The operation requires an asserted proposition or advice.", ids, ["stance"])
    if not _reading_shape(claim, op, offer):
        return _result(claim, "needs_review", "operation_shape", "The reading is not the canonical packet assessment for these operands.", ids, ["predicate", "subject", "object", "modality", "epistemic_scope", "measure"])
    if any(not _eligible(source, at) for source, _ in items.values()):
        return _result(claim, "needs_review", "ineligible_operand", "An operand is inactive or acquired after the decision.", ids, ["source_status", "observed_at"])
    if offer_source["kind"] not in ("job_description", "employer_update") or offer["subject"] not in ("employer", "role"):
        return _result(claim, "needs_review", "operand_role", "The offer must be an employer or role term.", ids, ["source_role", "subject"])
    if offer["epistemic_scope"] != "world":
        return _result(claim, "needs_review", "operand_scope", "The offer term must state a world-level fact.", ids, ["epistemic_scope"])
    if "preference" in items:
        ps, pref = items["preference"]
        if ps["kind"] != "preference" or pref["subject"] != "candidate" or pref["modality"] != "preference_constraint":
            return _result(claim, "needs_review", "operand_role", "The preference operand must be a candidate preference.", ids, ["source_role", "subject", "modality"])
        if pref["epistemic_scope"] != "world":
            return _result(claim, "needs_review", "operand_scope", "The candidate preference must state a world-level constraint.", ids, ["epistemic_scope"])
        if op != "onboarding" and not _same_property(offer, pref):
            return _result(claim, "needs_review", "property_mismatch", "The operands address different properties.", ids, ["predicate", "object"])
    r = claim["readings"][0]
    guarded, trace = _term_guard(packet, items, at, op)
    if guarded:
        rule, competing_ids = guarded
        return _result(claim, "needs_review", rule, "Another active term or explicit supersession changes the selected evidence.",
                       list(dict.fromkeys(ids + competing_ids + trace)), ["source_conflict"])
    ids = list(dict.fromkeys(ids + trace))
    if op == "permission_limit":
        if _context(pref["scope"]) != offer["scope"] or pref["time"] != offer["time"] or r["scope"] != offer["scope"] or r["time"] != offer["time"]:
            return _result(claim, "needs_review", "context_mismatch", "Property context or time is not retained across operands and claim.", ids, ["scope", "time"])
    if op == "constraint":
        if r["scope"] != offer["scope"] or r["time"] != offer["time"]:
            return _result(claim, "needs_review", "context_mismatch", "The claim must retain the offer's scope and time, including exhaustive windows.", ids, ["scope", "time"])
        if not _offer_scope_without_only(offer["scope"], pref["scope"]):
            return _result(claim, "needs_review", "context_mismatch", "The offer and preference have unmatched material scope dimensions.", ids, ["scope"])
        if pref["polarity"] == "negative":
            if not (pref["time"] == offer["time"] or _whole_day_ban_covers(offer, pref) or
                    _exhaustive_disjoint(offer, pref)):
                return _result(claim, "needs_review", "context_mismatch", "The prohibition does not demonstrably cover the offered window.", ids, ["time"])
        elif (pref["time"] != offer["time"] and pref["time"] != {} and
              not _allowed_window_covers(offer, pref)):
            return _result(claim, "needs_review", "context_mismatch", "The offered time is not inside an explicit allowed window.", ids, ["time"])
    if op == "pending":
        # A pending offer may add status/reason unavailable in a preference; the
        # reading must retain both, while all actual preference qualifiers remain.
        if (any(offer["scope"].get(k) != v for k, v in _context(pref["scope"]).items()) or
                (pref["time"] != offer["time"] and not (offer["time"] == {} and pref["time"] == {"phase": "first_day"})) or
                r["scope"] != offer["scope"] or r["time"] != pref["time"]):
            return _result(claim, "needs_review", "context_mismatch", "Pending context is not retained across operands and claim.", ids, ["scope", "time"])
    if op == "condition":
        condition = offer["scope"].get("condition")
        claimed_condition = r["scope"].get("condition")
        if claimed_condition is None or r["time"] != offer["time"] or {k:v for k,v in r["scope"].items() if k != "condition"} != {k:v for k,v in offer["scope"].items() if k != "condition"}:
            return _result(claim, "needs_review", "context_mismatch", "Claim context must retain the offer condition and time.", ids, ["scope", "time"])
        if condition is None or condition != claimed_condition:
            alternative = []
            for source in packet["sources"]:
                if source["kind"] not in ("job_description", "employer_update") or not _eligible(source, at):
                    continue
                for other in source["facts"]:
                    if (_same_property(other, offer) and other["subject"] == offer["subject"] and
                            other["scope"].get("condition") == claimed_condition and other["time"] == r["time"] and
                            other["polarity"] == "positive" and other["modality"] in ("permission", "requirement") and
                            {k:v for k,v in other["scope"].items() if k != "condition"} == {k:v for k,v in r["scope"].items() if k != "condition"}):
                        alternative.append(source["id"])
            if alternative:
                return _result(claim, "needs_review", "alternative_condition_source", "Another eligible term states the condition, but the referenced term does not.",
                               ids + alternative, ["source_reference", "scope.condition"])
            complete = packet["coverage"]["status"] == "agent_reviewed" and packet["coverage"]["source_inventory_complete"]
            if not complete:
                return _result(claim, "needs_review", "condition_gap", "The incomplete inventory cannot establish this asserted condition.", ids, ["scope.condition"])
            return base._result(claim, "not_established", "fail", "condition_gap",
                                "No eligible offer fact establishes this asserted condition.", limited=ids,
                                axes=["scope.condition"])
        if offer["modality"] not in ("permission", "requirement"):
            return _result(claim, "needs_review", "modality_mismatch", "Only explicit permissions or requirements establish this condition.", ids, ["modality"])
        return _result(claim, "pass", "explicit_condition", "The offer explicitly carries the stated condition.", ids)
    if op == "pending":
        if (offer["scope"].get("status") not in ("pending", "undecided") or offer["polarity"] != "positive" or
                offer["modality"] not in ("observation", "commitment")):
            return _result(claim, "needs_review", "status_unknown", "The offer is not explicitly pending.", ids, ["scope.status"])
        competing = _competing(packet, offer_source, offer, at)
        for source in packet["sources"]:
            if source["kind"] not in ("job_description", "employer_update") or not _eligible(source, at) or _superseded(packet, source["id"], at):
                continue
            for other in source["facts"]:
                if other is offer or not _same_property(other, offer):
                    continue
                same_time_and_entity = other["time"] == offer["time"] and other["subject"] == offer["subject"]
                planned = (same_time_and_entity and other["polarity"] == "positive" and
                           other["modality"] == "observation" and other["scope"] == {"status": "planned"} and
                           other["measure"] is None)
                unavailable_now = (same_time_and_entity and other["polarity"] == "negative" and
                                   other["modality"] == "observation" and other["scope"] == {"status": "available_now"} and
                                   other["measure"] is None)
                duplicate_pending = (same_time_and_entity and all(other[k] == offer[k] for k in
                                     ("polarity", "modality", "scope", "measure")))
                if not (planned or unavailable_now or duplicate_pending):
                    competing.append(source["id"])
        if competing:
            return _result(claim, "needs_review", "competing_terms", "A firm competing term prevents treating this property as unresolved.", ids + list(dict.fromkeys(competing)), ["source_conflict"])
        return _result(claim, "pass", "explicit_pending", "The source explicitly leaves this constraint unresolved.", ids)
    if op == "onboarding":
        remote_source, remote = items["remote"]
        if (offer["predicate"] != "station_attendance" or offer["object"] != "onboarding" or offer["modality"] != "requirement" or
                offer["polarity"] != "positive" or offer["epistemic_scope"] != "world" or
                pref["predicate"] != offer["predicate"] or pref["object"] != offer["object"] or
                pref["polarity"] != "positive" or pref["epistemic_scope"] != "world" or
                pref["scope"].get("requires_remote_after") is not True or
                remote_source["kind"] not in ("job_description", "employer_update") or remote["predicate"] != "remote_work" or
                remote["object"] != "work_location" or remote["modality"] != "permission" or remote["polarity"] != "positive" or
                remote["subject"] != offer["subject"] or remote["epistemic_scope"] != "world" or
                remote["time"] != {"phase": "after_onboarding"} or offer["time"] != {"phase": "onboarding"} or
                pref["time"] != offer["time"] or offer["measure"] is None or pref["measure"] is None or
                offer["measure"]["kind"] != "count" or pref["measure"]["kind"] != "count" or
                offer["measure"]["unit"] != "day" or pref["measure"]["unit"] != "day" or
                not set(remote["scope"]) <= {"condition"} or
                not isinstance(remote["scope"].get("condition", ""), str)):
            return _result(claim, "needs_review", "onboarding_operands", "Onboarding and later remote permission are not explicitly aligned.", ids, ["predicate", "object", "modality", "time", "scope"])
        expected_scope = dict(offer["scope"], requires_remote_after=True)
        if remote["scope"].get("condition"):
            expected_scope["remote_condition"] = remote["scope"]["condition"]
        if (r["scope"] != expected_scope or r["time"] != offer["time"] or
                _context({k:v for k,v in pref["scope"].items() if k != "requires_remote_after"}) != offer["scope"]):
            return _result(claim, "needs_review", "context_mismatch", "Onboarding context is not retained.", ids, ["scope", "time"])
        accepted, preference_ids = _remote_preference(packet, remote, at)
        ids = list(dict.fromkeys(ids + preference_ids))
        if not accepted:
            return _result(claim, "needs_review", "remote_preference_unresolved",
                           "The candidate's acceptance of the remote permission condition is not established.",
                           ids, ["preference_constraint", "scope.condition"])
        status, axis = _numeric(offer, pref, "constraint")
        return _result(claim, status or "needs_review", "onboarding_limit", "Onboarding duration compared with the preference and later remote permission.", ids, [] if status == "pass" else [axis])
    if op == "schedule_before":
        if (offer["predicate"] != "training_demo" or pref["predicate"] != "training_demo" or offer["object"] != pref["object"] or
                offer["modality"] != "requirement" or offer["polarity"] != "positive" or
                offer["measure"] is not None or pref["measure"] is not None or
                offer["scope"] != {"only": True} or pref["polarity"] != "negative" or
                r["scope"] != offer["scope"] or _context(pref["scope"]) != {} or
                offer["time"].get("zone") != "role_local" or pref["time"].get("zone") != "role_local" or
                offer["time"].get("weekday") not in _DAYS or pref["time"].get("weekday") not in _DAYS or
                (pref["time"].get("weekday") is not None and offer["time"].get("weekday") != pref["time"].get("weekday")) or
                set(offer["time"]) != {"weekday", "start_minute", "end_minute", "zone"} or
                set(pref["time"]) != {"weekday", "after_minute", "zone"}):
            return _result(claim, "needs_review", "schedule_context", "The schedule is not an exhaustive same-zone weekday requirement with matching prohibition.", ids, ["scope", "time", "modality"])
        start, end, cutoff = offer["time"].get("start_minute"), offer["time"].get("end_minute"), pref["time"].get("after_minute")
        reading_time = {k: offer["time"][k] for k in ("weekday", "zone")}
        if any(type(v) is not int or not 0 <= v <= 1440 for v in (start, end, cutoff)) or start >= end or r["time"] not in (reading_time, offer["time"]):
            return _result(claim, "needs_review", "schedule_unknown", "A same-day schedule and cutoff are required.", ids, ["time"])
        status = "pass" if end <= cutoff else "fail"
        return _result(claim, status, "schedule_cutoff", "The exhaustive schedule %s the prohibited cutoff." % ("ends by" if status == "pass" else "extends beyond"), ids, [] if status == "pass" else ["time"])
    if op == "permission_limit":
        if offer["modality"] != "permission" or pref["polarity"] != "positive" or offer["measure"] is None or offer["measure"]["upper"] is None:
            return _result(claim, "needs_review", "permission_semantics", "A stated permission ceiling and positive request are required.", ids, ["modality", "measure"])
        status, axis = _numeric(offer, pref, "limit")
        return _result(claim, status or "needs_review", "permission_envelope", "Requested interval compared with the explicit permission ceiling; grant is not inferred.", ids, [] if status == "pass" else [axis])
    if op == "constraint":
        competing = _competing(packet, offer_source, offer, at)
        superseders = _superseded(packet, offer_source["id"], at)
        if superseders:
            return _result(claim, "needs_review", "superseded_operand", "The selected offer term was explicitly superseded.", ids + superseders, ["supersedes"])
        if competing:
            return _result(claim, "needs_review", "competing_terms", "Active employer terms conflict without explicit supersession.", ids + competing, ["source_conflict"])
        extra_status, extra_ids = _other_restrictions(packet, offer_source, pref, offer, at)
        if extra_status:
            return _result(claim, extra_status, "additional_restriction", "Other active terms on this property change the constraint assessment.", ids + extra_ids, ["source_conflict", "preference_constraint"])
        if (pref["polarity"] == "negative" and pref["measure"] is None and
                offer["polarity"] == "negative" and offer["measure"] is None and
                offer["modality"] in ("requirement", "observation", "commitment")):
            return _result(claim, "pass", "explicit_absent_duty",
                           "The role explicitly excludes the same duty the candidate rules out.", ids)
        if (pref["polarity"] == "positive" and pref["measure"] is None and
                offer["polarity"] == "positive" and offer["measure"] is None and
                offer["modality"] in ("observation", "commitment", "requirement", "permission")):
            return _result(claim, "pass", "explicit_nonquantitative_fit",
                           "An active term explicitly provides or permits the matching nonquantitative preference.", ids)
        if (pref["polarity"] == "negative" and pref["measure"] is None and
                offer["polarity"] == "positive" and offer["modality"] == "requirement" and
                _exhaustive_disjoint(offer, pref)):
            return _result(claim, "pass", "exhaustive_disjoint_duty", "The complete offered duty schedule is disjoint from the whole-day prohibition.", ids)
        if (offer["polarity"] == "negative" and offer["modality"] == "observation" and
                offer["measure"] is None and pref["polarity"] == "positive" and
                pref["measure"] is not None and pref["measure"]["lower"] is not None and
                pref["measure"]["lower"] > 0 and _offer_scope_without_only(offer["scope"], pref["scope"]) and
                offer["time"] == pref["time"]):
            explanation = ("The current offer inventory explicitly lists no benefit needed above zero." if
                           offer["scope"].get("offer_inventory") == "current" else
                           "The active term explicitly denies a benefit needed above zero.")
            return _result(claim, "fail", "explicit_absent_quantity", explanation, ids, ["polarity", "measure"])
        if (pref["polarity"] == "negative" and offer["polarity"] == "positive" and offer["modality"] == "requirement" and
                pref["measure"] is None and (offer["measure"] is None or
                (offer["measure"]["lower"] is not None and offer["measure"]["lower"] > 0))):
            return _result(claim, "fail", "prohibited_duty", "A mandatory duty conflicts with the explicit no-duty preference.", ids, ["polarity"])
        if pref["polarity"] != "positive" or offer["polarity"] != "positive" or offer["modality"] not in ("observation", "commitment", "requirement", "permission"):
            return _result(claim, "needs_review", "constraint_modality", "The offer does not establish an affirmative committed or required quantity.", ids, ["modality", "polarity"])
        if offer["measure"] is None and pref["measure"] is None and offer["scope"].get("only") is True and _allowed_window_covers(offer, pref):
            return _result(claim, "pass", "exhaustive_window", "The exhaustive required window is inside the explicitly allowed window.", ids)
        status, axis = _numeric(offer, pref, "constraint")
        supersession_trace = []
        for source in packet["sources"]:
            if source["id"] == offer_source["id"] or not _eligible(source, at):
                continue
            if any(_same_property(f, offer) for f in source["facts"]):
                markers = _superseded(packet, source["id"], at)
                if markers:
                    supersession_trace.extend([source["id"], *markers])
        return _result(claim, status or "needs_review", "constraint_interval", "Entire offered interval compared with the candidate's allowed interval.", ids + supersession_trace, [] if status == "pass" else [axis])


def _strict_exceeds(claim, packet, at):
    """A unique explicit offer and candidate minimum establish a strict excess."""
    if len(claim["readings"]) != 1 or claim["stance"] in base.NONASSERTIVE or claim["stance"] == "conditional":
        return None
    r = claim["readings"][0]
    if r["predicate"] != "exceeds_minimum":
        return None
    if (r["subject"] != "candidate" or r["polarity"] != "positive" or
            r["modality"] != "record_assessment" or r["epistemic_scope"] != "packet" or
            r["measure"] is not None):
        return _result(claim, "needs_review", "minimum_shape", "A strict minimum comparison needs a canonical assessment.", axes=["subject", "modality", "epistemic_scope", "measure"])
    offers, preferences = [], []
    for source in packet["sources"]:
        if not _eligible(source, at):
            continue
        for fact in source["facts"]:
            if fact["object"] != r["object"] or fact["epistemic_scope"] != "world":
                continue
            if (source["kind"] in ("job_description", "employer_update") and
                    fact["subject"] in ("role", "employer")):
                offers.append((source, fact))
            elif (source["kind"] == "preference" and fact["subject"] == "candidate" and
                    fact["modality"] == "preference_constraint"):
                preferences.append((source, fact))
    related = list(dict.fromkeys(s["id"] for s, _ in offers + preferences))
    if len(offers) != 1 or len(preferences) != 1:
        return _result(claim, "needs_review", "minimum_operands", "A unique active offer term and candidate minimum are required.", related, ["source_role", "preference_constraint"])
    offer_source, offer = offers[0]
    pref_source, pref = preferences[0]
    items = {"offer": (offer_source, offer), "preference": (pref_source, pref)}
    guarded, trace = _term_guard(packet, items, at, "strict_exceeds")
    ids = list(dict.fromkeys(related + trace))
    if guarded:
        return _result(claim, "needs_review", guarded[0], "Another active term or supersession changes the comparison.",
                       ids + guarded[1], ["source_conflict"])
    if (offer["predicate"] != pref["predicate"] or
            offer["scope"] != r["scope"] or not _offer_scope_without_only(offer["scope"], pref["scope"]) or
            offer["time"] != r["time"] or pref["time"] not in (offer["time"], {}) or
            offer["polarity"] != "positive" or pref["polarity"] != "positive" or
            offer["modality"] not in ("permission", "commitment", "requirement", "observation")):
        return _result(claim, "needs_review", "minimum_context", "The offer and minimum are not the same affirmative property and context.", ids,
                       ["predicate", "scope", "time", "polarity", "modality"])
    om, pm = offer["measure"], pref["measure"]
    if (om is None or pm is None or om["kind"] != pm["kind"] or om["unit"] != pm["unit"] or
            om["per"] != pm["per"] or pm["lower"] is None or pm["upper"] is not None):
        return _result(claim, "needs_review", "minimum_measure", "A comparable explicit lower minimum is required.", ids, ["measure"])
    if om["lower"] is not None and om["lower"] > pm["lower"]:
        return _result(claim, "pass", "strict_minimum_exceeded", "The entire offered interval is strictly above the candidate minimum.", ids)
    if om["upper"] is not None and om["upper"] <= pm["lower"]:
        return _result(claim, "fail", "strict_minimum_not_exceeded", "The offer is at or below the candidate minimum.", ids, ["measure"])
    return _result(claim, "needs_review", "minimum_interval", "The offered interval crosses the strict minimum boundary.", ids, ["measure"])


def _direct(claim, packet, at):
    old = {k: claim[k] for k in ("id", "anchor", "stance", "readings")}
    context = {"grader": packet["grader"], "decision_at": packet["decision_at"], "coverage": packet["coverage"]}
    direct = base._check_valid_claim(old, packet["sources"], context)
    temporal_result = temporal.check(claim, packet, at, direct)
    if temporal_result is not None:
        return temporal_result
    exceeds = _strict_exceeds(claim, packet, at)
    if exceeds is not None:
        return exceeds
    reading = claim["readings"][0] if len(claim["readings"]) == 1 else None
    if (reading and reading["predicate"] == "plan_drafting" and reading["subject"] == "candidate" and
            reading["polarity"] == "positive" and claim["stance"] not in base.NONASSERTIVE and
            claim["stance"] != "conditional"):
        authored, denied = [], []
        for source in packet["sources"]:
            if not _eligible(source, at):
                continue
            for fact in source["facts"]:
                if (fact["subject"] == "candidate" and fact["predicate"] == "plan_drafting" and
                        fact["object"] == reading["object"] and fact["scope"] == reading["scope"] and
                        fact["time"] == reading["time"] and fact["epistemic_scope"] == reading["epistemic_scope"] and
                        fact["measure"] == reading["measure"] and
                        base._modality_supports(fact["modality"], reading["modality"])):
                    (authored if fact["polarity"] == "positive" else denied).append(source["id"])
        if authored and denied:
            return base._result(claim, "conflicting", "needs_review", "authorship_conflict",
                                "Eligible sources disagree about the candidate's authorship of this plan.",
                                support=authored, counter=denied, axes=["polarity", "contribution"])
    if (reading and reading["predicate"] in DIRECT_ACTIONS and reading["polarity"] == "positive" and
            reading["measure"] is not None and reading["measure"]["kind"] == "count" and
            reading["measure"]["lower"] is not None and reading["measure"]["lower"] > 0 and
            claim["stance"] not in base.NONASSERTIVE and claim["stance"] != "conditional"):
        denials = []
        for source in packet["sources"]:
            if not _eligible(source, at):
                continue
            for fact in source["facts"]:
                if (fact["polarity"] == "negative" and fact["measure"] is None and
                        fact["modality"] in ("observation", "self_report") and
                        base._modality_supports(fact["modality"], reading["modality"]) and
                        all(fact[k] == reading[k] for k in
                            ("subject", "predicate", "object", "epistemic_scope", "scope", "time"))):
                    denials.append(source["id"])
        if denials:
            support = direct["support_evidence_ids"]
            if support:
                return base._result(claim, "conflicting", "needs_review", "event_count_conflict",
                                    "A positive event count conflicts with an explicit denial of occurrence.",
                                    support=support, counter=denials, axes=["polarity", "measure"])
            return _result(claim, "fail", "event_nonoccurrence",
                           "An explicit denial of the event contradicts the asserted positive count.",
                           denials, ["polarity", "measure"])
    if (reading and reading["predicate"] in base.PREDICATES and reading["polarity"] == "positive" and
            claim["stance"] not in base.NONASSERTIVE and claim["stance"] != "conditional"):
        support, counter = [], []
        for source in packet["sources"]:
            if not _eligible(source, at):
                continue
            for fact in source["facts"]:
                same = all(reading[k] == fact[k] for k in ("subject", "predicate", "object", "epistemic_scope"))
                strong = fact["modality"] in ("observation", "self_report") and base._modality_supports(fact["modality"], reading["modality"])
                if not same or not strong:
                    continue
                if (reading["measure"] is None and fact["measure"] is not None and
                        fact["measure"]["kind"] == "count" and fact["polarity"] == "positive" and
                        reading["scope"] == fact["scope"] and reading["time"] == fact["time"]):
                    if fact["measure"]["lower"] is not None and fact["measure"]["lower"] > 0:
                        support.append(source["id"])
                    elif fact["measure"]["upper"] == 0:
                        counter.append(source["id"])
                duration = reading["scope"].get("duration_months_lower")
                start, end = fact["time"].get("start"), fact["time"].get("end")
                duration_context = (reading["scope"] == dict(fact["scope"], duration_months_lower=duration) and
                                    reading["time"] == fact["time"] and reading["measure"] == fact["measure"])
                if (fact["polarity"] == "positive" and type(duration) is int and duration >= 0 and
                        isinstance(start, str) and isinstance(end, str) and
                        _MONTH.fullmatch(start) and _MONTH.fullmatch(end) and
                        duration_context):
                    months = (int(end[:4]) - int(start[:4])) * 12 + int(end[5:]) - int(start[5:])
                    if months >= duration:
                        support.append(source["id"])
        if support:
            counter.extend(direct["counter_evidence_ids"])
            if counter:
                result = base._result(claim, "conflicting", "needs_review", "conflicting_evidence",
                                      "Positive event evidence conflicts with an eligible counter record.",
                                      support=support, counter=counter, axes=["polarity", "measure"])
                return result
            return _result(claim, "pass", "bounded_direct_entailment", "Actual positive count or explicit elapsed months support the narrower assertion.", support)
    return direct


def grade_fragment(packet):
    """Grade one validated selected fragment, retaining v3's audit envelope."""
    result = {"schema": SCHEMA, "scope": "fragment", "assurance": "manual_normalization_agent_reviewed",
              "verdict": "invalid", "claims": [], "findings": [], "review_reasons": [], "whole_answer_verdict": None}
    try:
        validate_packet(packet)
    except InvalidPacket as exc:
        result["review_reasons"] = ["invalid_packet: " + str(exc)]
        return result
    at = base._timestamp(packet["decision_at"], "packet.decision_at")
    claims = []
    for claim in packet["claims"]:
        checked = _direct(claim, packet, at) if claim["check"] is None else _derived(claim, packet, at)
        checked["inspected_source_ids"] = list(dict.fromkeys(
            [s["id"] for s in packet["sources"] if _eligible(s, at)] + checked["evidence_ids"]))
        claims.append(checked)
    findings = [{"claim_id": c["id"], "anchor": c["anchor"], "evidence_relation": c["evidence_relation"],
                 "rule": c["rule"], "explanation": c["explanation"], "axes": c["axes"],
                 "evidence_ids": c["evidence_ids"]} for c in claims if c["verdict"] == "fail"]
    reasons = ["claim_needs_review: " + c["id"] for c in claims if c["verdict"] == "needs_review"]
    coverage = packet["coverage"]
    if coverage["status"] != "agent_reviewed":
        reasons.append("coverage_unreviewed")
    if not coverage["source_inventory_complete"]:
        reasons.append("source_inventory_incomplete")
    if not coverage["fragment_complete"]:
        reasons.append("fragment_incomplete")
    result.update(claims=claims, findings=findings, review_reasons=reasons,
                  verdict="fail" if findings else "needs_review" if reasons else "pass")
    return result
