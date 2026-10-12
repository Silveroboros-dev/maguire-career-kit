"""Synthetic adversarial controls; no case-corpus predictions."""

import copy
import hashlib
import os
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from checker import digest, grade_fragment, validate_packet, InvalidPacket  # noqa: E402

T0 = "2026-10-12T10:00:00+00:00"
T1 = "2026-10-11T10:00:00+00:00"


def anchor(text="x"):
    return {"sha256": hashlib.sha256(text.encode()).hexdigest(), "pointer": "",
            "start": 0, "end": len(text), "quote": text}


def measure(n, kind="count", unit="day", per=None, upper=None):
    return {"kind": kind, "unit": unit, "lower": n, "upper": n if upper is None else upper, "per": per}


def fact(predicate="on_call", object_="night_duty", subject="role", **kw):
    value = {"subject": subject, "predicate": predicate, "object": object_,
             "polarity": "positive", "modality": "requirement", "epistemic_scope": "world",
             "scope": {}, "time": {}, "measure": None}
    value.update(kw)
    return value


def source(id_, item, kind="job_description", **kw):
    value = {"id": id_, "kind": kind, "status": "active", "observed_at": T1,
             "anchor": anchor(id_), "facts": [item]}
    value.update(kw)
    return value


def ref(id_, index=0):
    return {"source_id": id_, "fact_index": index}


def claim(op=None, predicate="constraint_satisfied", object_="night_duty", **kw):
    reading = fact(predicate, object_, "candidate", modality="record_assessment",
                   epistemic_scope="packet")
    reading.update(kw)
    return {"id": "c", "anchor": anchor("c"), "stance": "asserted",
            "readings": [reading], "check": op}


def packet(sources, claims):
    coverage = {"scope": "fragment", "source_sha256": digest(sources),
                "claims_sha256": digest(claims), "status": "agent_reviewed",
                "source_inventory_complete": True, "fragment_complete": True}
    return {"schema": "maguire-claim-packet-v4", "grader": "preference_fit",
            "decision_at": T0, "sources": sources, "claims": claims, "coverage": coverage}


def grade(sources, item):
    return grade_fragment(packet(sources, [item]))["claims"][0]


class CheckerTests(unittest.TestCase):
    def setUp(self):
        self.offer = fact("learning_allowance", "training_budget",
                          measure=measure(1200, "amount", "CHF", "calendar_year"))
        self.pref = fact("learning_allowance", "training_budget", "candidate",
                         modality="preference_constraint",
                         measure=measure(100, "amount", "CHF", "calendar_month"))
        self.sources = [source("offer", self.offer), source("pref", self.pref, "preference")]
        self.claim = claim({"op": "constraint", "offer": ref("offer"), "preference": ref("pref")},
                           object_="training_budget")

    def test_money_conversion_and_number_flip(self):
        self.assertEqual(grade(self.sources, self.claim)["verdict"], "pass")
        altered = copy.deepcopy(self.sources)
        altered[0]["facts"][0]["measure"] = measure(2400, "amount", "CHF", "calendar_year")
        self.assertEqual(grade(altered, self.claim)["verdict"], "fail")
        altered[0]["facts"][0]["measure"] = measure(1800, "amount", "CHF", "calendar_year", upper=2400)
        self.assertEqual(grade(altered, self.claim)["verdict"], "fail")

    def test_category_currency_period_and_modality(self):
        for change in ({"object": "salary"}, {"measure": measure(1200, "amount", "EUR", "calendar_year")},
                       {"measure": measure(1200, "amount", "CHF", "week")},
                       {"modality": "permission"}, {"modality": "possibility"}):
            altered = copy.deepcopy(self.sources)
            altered[0]["facts"][0].update(change)
            self.assertEqual(grade(altered, self.claim)["verdict"], "needs_review", change)

    def test_context_condition_and_eligibility(self):
        altered = copy.deepcopy(self.sources)
        altered[0]["facts"][0]["scope"] = {"condition": "manager_approval"}
        self.assertEqual(grade(altered, self.claim)["verdict"], "needs_review")
        for change in ({"status": "withdrawn"}, {"observed_at": "2026-10-13T00:00:00+00:00"}):
            altered = copy.deepcopy(self.sources)
            altered[0].update(change)
            self.assertEqual(grade(altered, self.claim)["verdict"], "needs_review")

    def test_supersession_and_hidden_conflict(self):
        other = source("other", fact("learning_allowance", "training_budget",
                                     measure=measure(500, "amount", "CHF", "calendar_year")),
                       kind="employer_update")
        sources = self.sources + [other]
        self.assertEqual(grade(sources, self.claim)["verdict"], "needs_review")
        other["observed_at"] = T0  # Later acquisition alone has no authority.
        self.assertEqual(grade(sources, self.claim)["verdict"], "needs_review")
        other["facts"].append(fact("supersedes", "offer", "other", modality="record_assessment"))
        self.assertEqual(grade(sources, self.claim)["verdict"], "needs_review")
        self.assertIn("other", grade(sources, self.claim)["evidence_ids"])
        other["facts"][0]["measure"] = measure(1200, "amount", "CHF", "calendar_year")
        selected_new = copy.deepcopy(self.claim)
        selected_new["check"]["offer"] = ref("other")
        self.assertEqual(grade(sources, selected_new)["verdict"], "pass")
        self.assertIn("offer", grade(sources, selected_new)["evidence_ids"])

    def test_permission_limit_is_not_guarantee(self):
        offer = fact("remote_work", "work_location", modality="permission",
                     scope={"condition": "manager_approval"}, measure=measure(0, "count", "day", upper=2))
        pref = fact("remote_work", "work_location", "candidate", modality="preference_constraint",
                    scope={"condition": "manager_approval"}, measure=measure(1, "count", "day"))
        checked = claim({"op": "permission_limit", "offer": ref("o"), "preference": ref("p")},
                        predicate="request_within_limit", object_="work_location",
                        scope={"condition": "manager_approval"})
        self.assertEqual(grade([source("o", offer), source("p", pref, "preference")], checked)["verdict"], "pass")
        checked["readings"][0]["modality"] = "guarantee"
        self.assertEqual(grade([source("o", offer), source("p", pref, "preference")], checked)["verdict"], "needs_review")
        checked["readings"][0]["modality"] = "record_assessment"
        checked["readings"][0]["scope"] = {}
        self.assertEqual(grade([source("o", offer), source("p", pref, "preference")], checked)["verdict"], "needs_review")

    def test_pending_and_condition(self):
        offer = fact("remote_work", "work_location", scope={"status": "pending"}, modality="observation")
        pref = fact("remote_work", "work_location", "candidate", modality="preference_constraint",
                    scope={"status": "pending"})
        item = claim({"op": "pending", "offer": ref("o"), "preference": ref("p")},
                     predicate="constraint_unresolved", object_="work_location", scope={"status": "pending"})
        sources = [source("o", offer), source("p", pref, "preference")]
        self.assertEqual(grade(sources, item)["verdict"], "pass")
        item["stance"] = "advice"
        item["readings"][0]["modality"] = "evaluation_instruction"
        item["readings"][0]["predicate"] = "confirmation_needed"
        self.assertEqual(grade(sources, item)["verdict"], "pass")
        offer["scope"] = {"condition": "manager_approval"}
        item = claim({"op": "condition", "offer": ref("o")}, predicate="condition_required",
                     object_="work_location", scope={"condition": "manager_approval"})
        sources = [source("o", offer)]
        self.assertEqual(grade(sources, item)["verdict"], "needs_review")  # possibility cannot require
        sources[0]["facts"][0]["modality"] = "permission"
        self.assertEqual(grade(sources, item)["verdict"], "pass")
        sources[0]["facts"][0]["scope"] = {}
        self.assertEqual(grade(sources, item)["verdict"], "fail")

    def test_pending_extra_status_and_reason(self):
        offer = fact("remote_work", "work_location", modality="observation",
                     scope={"status": "pending", "reason": "procurement"})
        pref = fact("remote_work", "work_location", "candidate", modality="preference_constraint",
                    scope={"priority": "must_have"})
        item = claim({"op": "pending", "offer": ref("o"), "preference": ref("p")},
                     predicate="confirmation_needed", object_="work_location",
                     scope={"status": "pending", "reason": "procurement"})
        item["stance"] = "advice"
        item["readings"][0]["modality"] = "evaluation_instruction"
        self.assertEqual(grade([source("o", offer), source("p", pref, "preference")], item)["verdict"], "pass")
        firm = source("firm", fact("remote_work", "work_location", modality="commitment"), "employer_update")
        self.assertEqual(grade([source("o", offer), source("p", pref, "preference"), firm], item)["verdict"], "needs_review")
        item["readings"][0]["scope"].pop("reason")
        self.assertEqual(grade([source("o", offer), source("p", pref, "preference")], item)["verdict"], "needs_review")

    def test_hidden_weekday_duty(self):
        offer = fact("on_call", "shift", scope={"weekday": "Saturday"},
                     measure=measure(1, "frequency", "shift", "calendar_month"))
        no_weekday = fact("on_call", "shift", scope={"weekday": "weekday"},
                          polarity="negative", modality="observation")
        pref = fact("on_call", "shift", "candidate", modality="preference_constraint",
                    scope={"priority": "must_have", "weekday": "Saturday"},
                    measure=measure(1, "frequency", "shift", "calendar_month"))
        ban = fact("on_call", "shift", "candidate", polarity="negative",
                   modality="preference_constraint", scope={"priority": "must_have", "weekday": "weekday"})
        item = claim({"op": "constraint", "offer": ref("o"), "preference": ref("p")},
                     object_="shift", scope={"weekday": "Saturday"})
        employers = source("o", offer)
        employers["facts"].append(no_weekday)
        prefs = source("p", pref, "preference")
        prefs["facts"].append(ban)
        self.assertEqual(grade([employers, prefs], item)["verdict"], "pass")
        employers["facts"][1] = fact("on_call", "shift", scope={"weekday": "Wednesday"})
        self.assertEqual(grade([employers, prefs], item)["verdict"], "fail")

    def test_onboarding_and_exhaustive_schedule(self):
        onboarding = fact("station_attendance", "onboarding", measure=measure(30, "count", "day"),
                          time={"phase": "onboarding"})
        remote = fact("remote_work", "work_location", modality="permission",
                      time={"phase": "after_onboarding"})
        pref = fact("station_attendance", "onboarding", "candidate", modality="preference_constraint",
                    scope={"requires_remote_after": True}, measure=measure(0, "count", "day", upper=30),
                    time={"phase": "onboarding"})
        item = claim({"op": "onboarding", "offer": ref("o"), "remote": ref("r"), "preference": ref("p")},
                     predicate="constraint_satisfied", object_="onboarding",
                     scope={"requires_remote_after": True}, time={"phase": "onboarding"})
        sources = [source("o", onboarding), source("r", remote), source("p", pref, "preference")]
        self.assertEqual(grade(sources, item)["verdict"], "pass")
        sources[1]["facts"][0]["modality"] = "possibility"
        self.assertEqual(grade(sources, item)["verdict"], "needs_review")

        offer = fact("training_demo", "demo", scope={"only": True},
                     time={"weekday": "Wednesday", "start_minute": 900, "end_minute": 960, "zone": "role_local"})
        restriction = fact("training_demo", "demo", "candidate", polarity="negative",
                           modality="preference_constraint", time={"after_minute": 1080, "zone": "role_local"})
        item = claim({"op": "schedule_before", "offer": ref("o"), "preference": ref("p")},
                     object_="demo", scope={"only": True}, time={"weekday": "Wednesday", "zone": "role_local"})
        sources = [source("o", offer), source("p", restriction, "preference")]
        self.assertEqual(grade(sources, item)["verdict"], "pass")
        sources[0]["facts"][0]["time"]["end_minute"] = 1200
        self.assertEqual(grade(sources, item)["verdict"], "fail")

    def test_direct_event_count_and_duration(self):
        observed = fact("ledger_maintenance", "issue_log", "candidate", modality="self_report",
                        measure=measure(3, "count", "event"))
        direct = claim(None, predicate="ledger_maintenance", object_="issue_log",
                       modality="observation", epistemic_scope="world")
        self.assertEqual(grade([source("s", observed, "candidate_fact")], direct)["verdict"], "pass")
        observed["measure"]["lower"] = observed["measure"]["upper"] = 0
        self.assertNotEqual(grade([source("s", observed, "candidate_fact")], direct)["verdict"], "pass")
        observed["measure"] = None
        observed["time"] = {"start": "2025-01", "end": "2026-01"}
        direct["readings"][0]["time"] = observed["time"].copy()
        direct["readings"][0]["scope"] = {"duration_months_lower": 12}
        self.assertEqual(grade([source("s", observed, "candidate_fact")], direct)["verdict"], "pass")
        direct["readings"][0]["scope"] = {"duration_months_lower": 13}
        self.assertNotEqual(grade([source("s", observed, "candidate_fact")], direct)["verdict"], "pass")

    def test_structure_and_unknown_operation(self):
        valid = packet(self.sources, [self.claim])
        self.assertTrue(validate_packet(valid))
        for mutation in (lambda p: p["claims"][0]["check"]["offer"].update(source_id="foreign"),
                         lambda p: p["claims"][0]["check"]["offer"].update(fact_index=True),
                         lambda p: p["coverage"].update(claims_sha256="0" * 64),
                         lambda p: p["claims"][0]["anchor"].update(sha256="x")):
            changed = copy.deepcopy(valid)
            mutation(changed)
            self.assertEqual(grade_fragment(changed)["verdict"], "invalid")
        unknown = claim({"op": "unrecognized"}, object_="training_budget")
        self.assertEqual(grade([*self.sources], unknown)["verdict"], "needs_review")
        renumbered = copy.deepcopy(valid)
        renumbered["sources"][0]["id"] = "x90"
        renumbered["claims"][0]["check"]["offer"]["source_id"] = "x90"
        renumbered["coverage"]["source_sha256"] = digest(renumbered["sources"])
        renumbered["coverage"]["claims_sha256"] = digest(renumbered["claims"])
        self.assertEqual(grade_fragment(renumbered)["verdict"], "pass")

    def test_no_io(self):
        p = packet(self.sources, [self.claim])
        with patch("builtins.open", side_effect=AssertionError("file I/O")), \
             patch("socket.socket", side_effect=AssertionError("network")), \
             patch("subprocess.Popen", side_effect=AssertionError("process")):
            self.assertEqual(grade_fragment(p)["verdict"], "pass")

    def test_direct_does_not_weaken_polarity_strength_or_time(self):
        positive = fact("ledger_maintenance", "issue_log", "candidate", modality="observation",
                        measure=measure(4, "count", "event"))
        reading = claim(None, predicate="ledger_maintenance", object_="issue_log",
                        modality="observation", epistemic_scope="world")
        self.assertEqual(grade([source("s", positive, "candidate_fact")], reading)["verdict"], "pass")
        negative = copy.deepcopy(positive)
        negative["polarity"] = "negative"
        self.assertNotEqual(grade([source("s", negative, "candidate_fact")], reading)["verdict"], "pass")
        reading["readings"][0]["modality"] = "self_report"
        self.assertNotEqual(grade([source("s", positive, "candidate_fact")], reading)["verdict"], "pass")
        reading["readings"][0]["modality"] = "observation"
        positive["time"] = {"year": 2025}
        self.assertNotEqual(grade([source("s", positive, "candidate_fact")], reading)["verdict"], "pass")
        positive["time"] = {}
        denial = fact("ledger_maintenance", "issue_log", "candidate", polarity="negative",
                      modality="observation")
        s = source("s", positive, "candidate_fact")
        s["facts"].append(denial)
        result = grade([s], reading)
        self.assertEqual(result["verdict"], "needs_review")
        self.assertEqual(result["evidence_relation"], "conflicting")

    def test_pending_requires_affirmative_status_and_scans_same_source(self):
        pending = fact("remote_work", "work_location", modality="observation",
                       scope={"status": "pending"})
        pref = fact("remote_work", "work_location", "candidate", modality="preference_constraint")
        item = claim({"op": "pending", "offer": ref("o"), "preference": ref("p")},
                     predicate="constraint_unresolved", object_="work_location", scope={"status": "pending"})
        selected = source("o", pending)
        preferences = source("p", pref, "preference")
        self.assertEqual(grade([selected, preferences], item)["verdict"], "pass")
        selected["facts"][0]["polarity"] = "negative"
        self.assertNotEqual(grade([selected, preferences], item)["verdict"], "pass")
        selected["facts"][0]["polarity"] = "positive"
        selected["facts"][0]["modality"] = "prediction"
        self.assertNotEqual(grade([selected, preferences], item)["verdict"], "pass")
        selected["facts"][0]["modality"] = "observation"
        selected["facts"].append(fact("remote_work", "work_location", modality="commitment"))
        self.assertEqual(grade([selected, preferences], item)["verdict"], "needs_review")

    def test_condition_gap_is_not_contradiction(self):
        offered = fact("remote_work", "work_location", modality="permission")
        item = claim({"op": "condition", "offer": ref("o")}, predicate="condition_required",
                     object_="work_location", scope={"condition": "manager_approval"})
        result = grade([source("o", offered)], item)
        self.assertEqual(result["verdict"], "fail")
        self.assertEqual(result["evidence_relation"], "not_established")
        self.assertEqual(result["counter_evidence_ids"], [])
        self.assertEqual(result["limited_evidence_ids"], ["o"])

    def test_derived_checks_detect_same_source_conflict(self):
        offer = fact("remote_work", "work_location", modality="permission",
                     measure=measure(0, "count", "day", upper=2))
        pref = fact("remote_work", "work_location", "candidate", modality="preference_constraint",
                    measure=measure(1, "count", "day"))
        item = claim({"op": "permission_limit", "offer": ref("o"), "preference": ref("p")},
                     predicate="request_within_limit", object_="work_location")
        selected = source("o", offer)
        preferences = source("p", pref, "preference")
        self.assertEqual(grade([selected, preferences], item)["verdict"], "pass")
        selected["facts"].append(fact("remote_work", "work_location", modality="permission",
                                      measure=measure(0, "count", "day", upper=0)))
        self.assertEqual(grade([selected, preferences], item)["verdict"], "needs_review")

    def test_quantified_negative_preference_is_not_no_duty_ban(self):
        offered = fact("on_call", "night_duty", measure=measure(1, "frequency", "shift", "calendar_month"))
        wanted = fact("on_call", "night_duty", "candidate", modality="preference_constraint",
                      measure=measure(1, "frequency", "shift", "calendar_month"))
        another = fact("on_call", "night_duty", "candidate", polarity="negative",
                       modality="preference_constraint", measure=measure(2, "frequency", "shift", "calendar_month"))
        item = claim({"op": "constraint", "offer": ref("o"), "preference": ref("p")})
        prefs = source("p", wanted, "preference")
        prefs["facts"].append(another)
        self.assertEqual(grade([source("o", offered), prefs], item)["verdict"], "needs_review")

    def test_scoped_supersession_cannot_silently_replace_term(self):
        selected = source("offer", self.offer)
        update = source("u", fact("learning_allowance", "training_budget",
                                  measure=measure(500, "amount", "CHF", "calendar_year")),
                        "employer_update")
        update["facts"].append(fact("supersedes", "offer", "u", modality="record_assessment",
                                    scope={"condition": "approval"}))
        result = grade([selected, source("pref", self.pref, "preference"), update], self.claim)
        self.assertEqual(result["verdict"], "needs_review")
        self.assertIn("u", result["evidence_ids"])


if __name__ == "__main__":
    unittest.main()
