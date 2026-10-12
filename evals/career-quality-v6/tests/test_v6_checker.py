"""Invented fixtures for the bounded v6 checker; never load target packets."""

import copy
from pathlib import Path
import sys
import unittest


HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import checker  # noqa: E402


ANCHOR = {"sha256": "0" * 64, "pointer": "", "start": 0, "end": 0, "quote": ""}


def fact(subject, predicate, obj, polarity="positive", modality="self_report",
         scope=None, time=None, measure=None, epistemic_scope="world"):
    return {"subject": subject, "predicate": predicate, "object": obj,
            "polarity": polarity, "modality": modality, "epistemic_scope": epistemic_scope,
            "scope": scope or {}, "time": time or {}, "measure": measure}


def measure(kind="count", unit="day", lower=1, upper=1, per=None):
    return {"kind": kind, "unit": unit, "lower": lower, "upper": upper, "per": per}


def source(sid, kind, facts, status="active", observed_at=None):
    return {"id": sid, "kind": kind, "status": status, "observed_at": observed_at,
            "anchor": copy.deepcopy(ANCHOR), "facts": facts}


def claim(reading, check=None, stance="asserted", cid="claim-x"):
    return {"id": cid, "anchor": copy.deepcopy(ANCHOR), "stance": stance,
            "readings": [reading], "check": check}


def packet(sources, claims, complete=True):
    return {"schema": checker.SCHEMA, "grader": "candidate_fit" if claims[0]["check"] is None else "preference_fit",
            "decision_at": "2026-02-01T00:00:00Z", "sources": sources, "claims": claims,
            "coverage": {"scope": "fragment", "source_sha256": checker.digest(sources),
                         "claims_sha256": checker.digest(claims), "status": "agent_reviewed",
                         "source_inventory_complete": complete, "fragment_complete": True}}


def result(sources, claim_row):
    return checker.grade_fragment(packet(sources, [claim_row]))["claims"][0]


def ref(sid, index=0):
    return {"source_id": sid, "fact_index": index}


class DirectClaims(unittest.TestCase):
    def test_registered_action_uses_exact_event_and_modality(self):
        performed = fact("candidate", "demo_presentation", "renewal briefing",
                         scope={"project": "fictional"}, time={"year": "2023"})
        reading = copy.deepcopy(performed)
        self.assertEqual(result([source("resume-a", "candidate_fact", [performed])], claim(reading))["verdict"], "pass")
        incapable = copy.deepcopy(performed)
        incapable["modality"] = "ability"
        self.assertNotEqual(result([source("resume-a", "candidate_fact", [incapable])], claim(reading))["verdict"], "pass")
        unrelated = copy.deepcopy(performed)
        unrelated["scope"] = {"project": "another"}
        self.assertNotEqual(result([source("resume-a", "candidate_fact", [unrelated])], claim(reading))["verdict"], "pass")

    def test_negative_event_and_personal_attribution(self):
        reading = fact("candidate", "sql_query", "live orders",
                       scope={"environment": "production"})
        denial = copy.deepcopy(reading)
        denial["polarity"] = "negative"
        self.assertEqual(result([source("record-a", "candidate_fact", [denial])], claim(reading))["verdict"], "fail")
        team = copy.deepcopy(reading)
        team["subject"] = "team"
        self.assertNotEqual(result([source("record-a", "candidate_fact", [team])], claim(reading))["verdict"], "pass")
        lab = copy.deepcopy(reading)
        lab["scope"] = {"environment": "sandbox"}
        self.assertNotEqual(result([source("record-a", "candidate_fact", [lab])], claim(reading))["verdict"], "pass")

    def test_unquantified_denial_refutes_positive_event_count(self):
        reading = fact("candidate", "demo_presentation", "renewal briefing",
                       scope={"project": "fictional"}, measure=measure("count", "demo", 2, 2))
        denial = copy.deepcopy(reading)
        denial["polarity"] = "negative"
        denial["measure"] = None
        checked = result([source("record-a", "candidate_fact", [denial])], claim(reading))
        self.assertEqual((checked["verdict"], checked["rule"]), ("fail", "event_nonoccurrence"))
        self.assertEqual(checked["counter_evidence_ids"], ["record-a"])
        support = copy.deepcopy(reading)
        checked = result([source("record-a", "candidate_fact", [denial]),
                          source("record-b", "candidate_fact", [support])], claim(reading))
        self.assertEqual((checked["verdict"], checked["rule"]), ("needs_review", "event_count_conflict"))

    def test_authorship_conflict_is_inspected_independent_of_source_order_and_ids(self):
        authored = fact("candidate", "plan_drafting", "migration note",
                        scope={"project": "fictional", "contribution": "personal"}, time={"year": "2022"})
        denied = copy.deepcopy(authored)
        denied["polarity"] = "negative"
        rows = [source("alpha", "candidate_fact", [authored]), source("beta", "candidate_fact", [denied])]
        reading = copy.deepcopy(authored)
        for chosen in (rows, list(reversed(rows))):
            checked = result(chosen, claim(reading, cid="any-id"))
            self.assertEqual((checked["verdict"], checked["rule"]), ("needs_review", "authorship_conflict"))
            self.assertEqual(set(checked["evidence_ids"]), {"alpha", "beta"})
        renamed = copy.deepcopy(rows)
        renamed[0]["id"], renamed[1]["id"] = "fiction-1", "fiction-2"
        self.assertEqual(result(renamed, claim(reading, cid="renamed"))["rule"], "authorship_conflict")

    def test_fit_relevance_remains_review(self):
        reading = fact("candidate", "fit_relevance", "new responsibility")
        self.assertEqual(result([], claim(reading))["verdict"], "needs_review")

    def test_withdrawn_or_future_source_cannot_support_action(self):
        performed = fact("candidate", "operator_training", "inventory handbook")
        reading = copy.deepcopy(performed)
        for invalid_source in (
                source("old", "candidate_fact", [performed], status="withdrawn"),
                source("future", "candidate_fact", [performed], observed_at="2027-01-01T00:00:00Z")):
            self.assertNotEqual(result([invalid_source], claim(reading))["verdict"], "pass")


class PreferenceClaims(unittest.TestCase):
    def _constraint(self, offer, pref, reading_scope, reading_time):
        sources = [source("offer", "job_description", [offer]), source("pref", "preference", [pref])]
        reading = fact("candidate", "constraint_satisfied", offer["object"],
                       modality="record_assessment", epistemic_scope="packet",
                       scope=reading_scope, time=reading_time)
        return result(sources, claim(reading, {"op": "constraint", "offer": ref("offer"), "preference": ref("pref")}))

    def test_whole_day_ban_covers_required_window(self):
        window = {"weekday": "Sunday", "zone": "role_local", "start_minute": 600, "end_minute": 720}
        offer = fact("role", "on_call", "support rota", modality="requirement", time=window,
                     measure=measure("frequency", "day", 1, 1, "week"))
        pref = fact("candidate", "on_call", "support rota", polarity="negative",
                    modality="preference_constraint", time={"weekday": "Sunday", "zone": "role_local"})
        checked = self._constraint(offer, pref, {}, window)
        self.assertEqual(checked["verdict"], "fail")
        pref["time"]["weekday"] = "weekday"
        self.assertNotEqual(self._constraint(offer, pref, {}, window)["verdict"], "fail")

    def test_exhaustive_window_inside_allowed_window_with_disjoint_ban(self):
        window = {"weekday": "Saturday", "zone": "role_local", "start_minute": 660, "end_minute": 780}
        offer = fact("role", "on_call", "support rota", modality="requirement", scope={"only": True}, time=window)
        pref = fact("candidate", "on_call", "support rota", modality="preference_constraint",
                    time={"weekday": "Saturday", "zone": "role_local", "start_minute": 600, "end_minute": 840})
        ban = fact("candidate", "on_call", "support rota", polarity="negative",
                   modality="preference_constraint", time={"weekday": "weekday", "zone": "role_local"})
        sources = [source("offer", "job_description", [offer]), source("pref", "preference", [pref, ban])]
        reading = fact("candidate", "constraint_satisfied", "support rota", modality="record_assessment",
                       epistemic_scope="packet", scope={"only": True}, time=window)
        check = {"op": "constraint", "offer": ref("offer"), "preference": ref("pref")}
        checked = result(sources, claim(reading, check))
        self.assertEqual(checked["verdict"], "pass", checked)
        reading["scope"] = {}
        self.assertEqual(result(sources, claim(reading, check))["verdict"], "needs_review")
        reading["scope"] = {"only": True}
        offer["time"]["unexplained"] = "x"
        reading["time"]["unexplained"] = "x"
        self.assertEqual(result(sources, claim(reading, check))["verdict"], "needs_review")

    def test_remote_condition_belongs_to_remote_permission(self):
        offer = fact("role", "station_attendance", "onboarding", modality="requirement",
                     time={"phase": "onboarding"}, measure=measure(upper=2, lower=2))
        remote = fact("role", "remote_work", "work_location", modality="permission",
                      scope={"condition": "lead_approval"}, time={"phase": "after_onboarding"})
        pref = fact("candidate", "station_attendance", "onboarding", modality="preference_constraint",
                    scope={"requires_remote_after": True}, time={"phase": "onboarding"},
                    measure=measure(lower=0, upper=3))
        remote_pref = fact("candidate", "remote_work", "work_location", modality="preference_constraint",
                           scope={"condition": "lead_approval"}, time={"phase": "after_onboarding"})
        sources = [source("offer", "job_description", [offer]), source("remote", "job_description", [remote]),
                   source("pref", "preference", [pref, remote_pref])]
        reading = fact("candidate", "constraint_satisfied", "onboarding", modality="record_assessment",
                       epistemic_scope="packet", scope={"requires_remote_after": True, "remote_condition": "lead_approval"},
                       time={"phase": "onboarding"})
        check = {"op": "onboarding", "offer": ref("offer"), "remote": ref("remote"), "preference": ref("pref")}
        checked = result(sources, claim(reading, check))
        self.assertEqual(checked["verdict"], "pass", checked)
        reading["scope"].pop("remote_condition")
        self.assertEqual(result(sources, claim(reading, check))["verdict"], "needs_review")
        reading["scope"]["remote_condition"] = "lead_approval"
        remote["modality"] = "possibility"
        self.assertEqual(result(sources, claim(reading, check))["verdict"], "needs_review")
        remote["modality"] = "permission"
        remote_pref["polarity"] = "negative"
        self.assertEqual(result(sources, claim(reading, check))["verdict"], "needs_review")
        remote_pref["polarity"] = "positive"
        generic_ban = fact("candidate", "remote_work", "work_location", polarity="negative",
                           modality="preference_constraint", scope={"condition": "lead_approval"})
        sources[2]["facts"].append(generic_ban)
        self.assertEqual(result(sources, claim(reading, check))["verdict"], "needs_review")
        sources[2]["facts"].pop()
        sources[2]["facts"].pop()
        self.assertEqual(result(sources, claim(reading, check))["verdict"], "needs_review")

    def test_schedule_requires_exhaustiveness_and_canonical_weekday(self):
        time = {"weekday": "Thursday", "zone": "role_local", "start_minute": 600, "end_minute": 720}
        offer = fact("role", "training_demo", "practice session", modality="requirement",
                     scope={"only": True}, time=time)
        pref = fact("candidate", "training_demo", "practice session", polarity="negative",
                    modality="preference_constraint", time={"weekday": "Thursday", "zone": "role_local", "after_minute": 780})
        sources = [source("offer", "job_description", [offer]), source("pref", "preference", [pref])]
        reading = fact("candidate", "constraint_satisfied", "practice session", modality="record_assessment",
                       epistemic_scope="packet", scope={"only": True}, time={"weekday": "Thursday", "zone": "role_local"})
        check = {"op": "schedule_before", "offer": ref("offer"), "preference": ref("pref")}
        self.assertEqual(result(sources, claim(reading, check))["verdict"], "pass")
        offer["time"]["end_minute"] = 840
        self.assertEqual(result(sources, claim(reading, check))["verdict"], "fail")
        offer["scope"].pop("only")
        self.assertEqual(result(sources, claim(reading, check))["verdict"], "needs_review")
        offer["scope"]["only"] = True
        offer["time"]["weekday"] = "Funday"
        pref["time"]["weekday"] = "Funday"
        reading["time"]["weekday"] = "Funday"
        self.assertEqual(result(sources, claim(reading, check))["verdict"], "needs_review")
        offer["time"]["weekday"] = "Thursday"
        pref["time"]["weekday"] = "Thursday"
        reading["time"]["weekday"] = "Thursday"
        offer["polarity"] = "negative"
        self.assertEqual(result(sources, claim(reading, check))["verdict"], "needs_review")

    def test_pending_current_status_supports_first_day_verification_only(self):
        unavailable = fact("role", "live_captions", "meeting access", polarity="negative",
                           modality="observation", scope={"status": "available_now"})
        pending = fact("role", "live_captions", "meeting access", modality="observation",
                       scope={"status": "pending"})
        pref = fact("candidate", "live_captions", "meeting access", modality="preference_constraint",
                    time={"phase": "first_day"})
        sources = [source("offer", "employer_update", [unavailable, pending]),
                   source("pref", "preference", [pref])]
        reading = fact("candidate", "confirmation_needed", "meeting access", modality="evaluation_instruction",
                       epistemic_scope="packet", scope={"status": "pending"}, time={"phase": "first_day"})
        check = {"op": "pending", "offer": ref("offer", 1), "preference": ref("pref")}
        checked = result(sources, claim(reading, check, stance="advice"))
        self.assertEqual(checked["verdict"], "pass")
        pending["modality"] = "possibility"
        self.assertEqual(result(sources, claim(reading, check, stance="advice"))["verdict"], "needs_review")


if __name__ == "__main__":
    unittest.main()
