"""Synthetic boundary controls for the first manually normalized v3 slice."""

import copy
import hashlib
import os
import sys
import unittest
from unittest.mock import patch


HERE = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, HERE)
from checker import check_claim, digest, grade_fragment  # noqa: E402


T0 = "2026-10-12T10:00:00+00:00"
T1 = "2026-10-11T10:00:00+00:00"
T2 = "2026-10-10T10:00:00+00:00"
LATER = "2026-10-13T10:00:00+00:00"


def anchor(quote="synthetic"):
    return {"sha256": hashlib.sha256(quote.encode()).hexdigest(), "pointer": "",
            "start": 0, "end": len(quote), "quote": quote}


def prop(predicate="console_use", subject="candidate", object_="console", **changes):
    value = {"subject": subject, "predicate": predicate, "object": object_,
             "polarity": "positive", "modality": "observation", "epistemic_scope": "world",
             "scope": {}, "time": {}, "measure": None}
    value.update(changes)
    return value


def source(id_="s1", fact=None, **changes):
    value = {"id": id_, "kind": "candidate_fact", "status": "active",
             "observed_at": T1, "anchor": anchor(id_), "facts": [fact or prop()]}
    value.update(changes)
    return value


def claim(id_="c1", reading=None, **changes):
    value = {"id": id_, "anchor": anchor(id_), "stance": "asserted",
             "readings": [reading or prop()]}
    value.update(changes)
    return value


def packet(sources=None, claims=None, **coverage_changes):
    sources = [source()] if sources is None else sources
    claims = [claim()] if claims is None else claims
    coverage = {"scope": "fragment", "source_sha256": digest(sources),
                "claims_sha256": digest(claims), "status": "agent_reviewed",
                "source_inventory_complete": True, "fragment_complete": True}
    coverage.update(coverage_changes)
    return {"schema": "maguire-claim-packet-v3", "grader": "candidate_fit",
            "decision_at": T0, "sources": sources, "claims": claims, "coverage": coverage}


class CheckerTests(unittest.TestCase):
    def test_direct_support_and_id_renumbering(self):
        first = grade_fragment(packet())
        self.assertEqual(first["verdict"], "pass")
        self.assertEqual(first["claims"][0]["evidence_relation"], "supported")
        self.assertEqual(first["claims"][0]["support_evidence_ids"], ["s1"])
        second = grade_fragment(packet([source("evidence_92")], [claim("atom_47")]))
        self.assertEqual(second["verdict"], "pass")
        self.assertEqual(second["claims"][0]["support_evidence_ids"], ["evidence_92"])

    def test_registered_sample_and_missing_support_trace(self):
        sample = prop("sample_size", "study", "reviewed_pages",
                      measure={"kind": "count", "unit": "page", "lower": 75,
                               "upper": 75, "per": None})
        self.assertEqual(grade_fragment(packet([source(fact=sample)],
                                               [claim(reading=sample)]))["verdict"], "pass")
        absent = grade_fragment(packet([source(fact=sample)], [claim(reading=prop("ocr_method"))]))
        result = absent["claims"][0]
        self.assertEqual(result["inspected_source_ids"], ["s1"])
        self.assertIn("supporting_proposition", result["axes"])
        self.assertIn("candidate / ocr_method / console", result["explanation"])

    def test_changed_subject_quantity_and_polarity(self):
        fact = prop("distance_saving", "route_A", "commute",
                    measure={"kind": "difference", "unit": "minute", "lower": 12,
                             "upper": 12, "per": "day"})
        exact = claim(reading=copy.deepcopy(fact))
        self.assertEqual(grade_fragment(packet([source(fact=fact)], [exact]))["verdict"], "pass")
        altered = copy.deepcopy(fact)
        altered["measure"]["lower"] = altered["measure"]["upper"] = 19
        got = grade_fragment(packet([source(fact=fact)], [claim(reading=altered)]))
        self.assertEqual(got["claims"][0]["evidence_relation"], "not_established")
        self.assertIn("measure", got["claims"][0]["axes"])
        altered = dict(fact, subject="route_B")
        got = grade_fragment(packet([source(fact=fact)], [claim(reading=altered)]))
        self.assertEqual(got["claims"][0]["evidence_relation"], "not_established")
        self.assertIn("subject", got["claims"][0]["axes"])
        altered = dict(fact, polarity="negative")
        got = grade_fragment(packet([source(fact=fact)], [claim(reading=altered)]))
        self.assertEqual(got["claims"][0]["evidence_relation"], "contradicted")

    def test_amount_range_and_point_possibility(self):
        band = {"kind": "amount", "unit": "fictional_credit", "lower": 82_000,
                "upper": 128_000, "per": None}
        fact = prop("published_stipend", "role", "advertised_band", measure=band)
        reading = prop("published_stipend", "role", "advertised_band", modality="possibility",
                       measure=dict(band, lower=115_000, upper=115_000))
        self.assertEqual(grade_fragment(packet([source(fact=fact)], [claim(reading=reading)]))["verdict"], "pass")
        outside = copy.deepcopy(reading)
        outside["measure"]["lower"] = outside["measure"]["upper"] = 150_000
        got = grade_fragment(packet([source(fact=fact)], [claim(reading=outside)]))
        self.assertEqual(got["claims"][0]["evidence_relation"], "not_established")
        self.assertIn("measure", got["claims"][0]["axes"])
        personal = prop("personal_stipend", "candidate", "award", measure=band)
        self.assertEqual(grade_fragment(packet([source(fact=fact)], [claim(reading=personal)]))["verdict"], "fail")

    def test_partial_coverage_and_source_status(self):
        empty = packet([], [claim()], source_inventory_complete=False)
        self.assertEqual(grade_fragment(empty)["verdict"], "needs_review")
        for changes in ({"status": "withdrawn"}, {"observed_at": LATER}):
            got = grade_fragment(packet([source(**changes)]))
            self.assertEqual(got["verdict"], "fail")
            self.assertEqual(got["claims"][0]["evidence_relation"], "not_established")
            self.assertEqual(got["claims"][0]["limited_evidence_ids"], ["s1"])
        self.assertEqual(grade_fragment(packet(fragment_complete=False))["verdict"], "needs_review")

    def test_packet_absence_distinguishes_requirement_from_actual_record(self):
        negative = prop("written_offer", "employer", "candidate", polarity="negative",
                        epistemic_scope="packet")
        req = prop("written_offer", "employer", "candidate", modality="requirement")
        self.assertEqual(grade_fragment(packet([source(fact=req, kind="job_description")],
                                               [claim(reading=negative)]))["verdict"], "pass")
        offer = prop("written_offer", "employer", "candidate")
        got = grade_fragment(packet([source(fact=offer, kind="employer_update")],
                                    [claim(reading=negative)]))
        self.assertEqual(got["claims"][0]["evidence_relation"], "contradicted")
        self.assertEqual(grade_fragment(packet([], [claim(reading=negative)],
                                               source_inventory_complete=False))["verdict"], "needs_review")
        world_negative = dict(negative, epistemic_scope="world")
        self.assertEqual(grade_fragment(packet([], [claim(reading=world_negative)]))["verdict"], "fail")

    def test_source_role_authority_and_valid_explicit_authority(self):
        authority = prop("evaluation_authority", "employer", "rubric",
                         modality="evaluation_instruction")
        claim_value = claim(reading=authority)
        blocked = grade_fragment(packet([source(fact=authority, kind="job_description")], [claim_value]))
        self.assertEqual(blocked["claims"][0]["rule"], "source_role_boundary")
        self.assertIn("source_role", blocked["claims"][0]["axes"])
        blocked_candidate = grade_fragment(packet([source(fact=authority, kind="candidate_fact")], [claim_value]))
        self.assertEqual(blocked_candidate["claims"][0]["rule"], "source_role_boundary")
        governing = prop("governs", "employer_update", "role_rule",
                         modality="record_assessment")
        valid = grade_fragment(packet([source(fact=governing, kind="employer_update")],
                                      [claim(reading=governing)]))
        self.assertEqual(valid["verdict"], "pass")

    def test_preference_hard_soft_and_frequency(self):
        compatible = prop("compatible", "candidate", "overnight_duty")
        required = prop("on_call", "role", "overnight_duty", modality="requirement")
        constraint = prop("on_call", "candidate", "overnight_duty", polarity="negative",
                          modality="preference_constraint",
                          scope={"priority": "must_have", "exceptions": False})
        sources = [source("p", constraint, kind="preference"),
                   source("j", required, kind="job_description")]
        got = grade_fragment(packet(sources, [claim(reading=compatible)]))
        self.assertEqual(got["claims"][0]["evidence_relation"], "contradicted")
        soft = copy.deepcopy(sources)
        soft[0]["facts"][0]["scope"]["priority"] = "nice_to_have"
        self.assertNotEqual(grade_fragment(packet(soft, [claim(reading=compatible)]))["verdict"], "pass")
        ceiling = prop("on_call", "candidate", "overnight_duty", polarity="negative",
                       modality="preference_constraint", time={"recurring": True},
                       measure={"kind": "frequency", "unit": "shift", "lower": 0,
                                "upper": 1, "per": "calendar_month"})
        permission = prop("on_call", "candidate", "overnight_duty", modality="permission",
                          time={"recurring": True},
                          measure={"kind": "frequency", "unit": "shift", "lower": 2,
                                   "upper": 2, "per": "week"})
        got = grade_fragment(packet([source(fact=ceiling, kind="preference")],
                                    [claim(reading=permission)]))
        self.assertEqual(got["claims"][0]["rule"], "frequency_ceiling")
        one_off = copy.deepcopy(permission)
        one_off["time"] = {"recurring": False}
        one_off_result = grade_fragment(packet([source(fact=ceiling, kind="preference")],
                                               [claim(reading=one_off)]))
        self.assertNotEqual(one_off_result["claims"][0]["rule"], "frequency_ceiling")
        self.assertEqual(one_off_result["claims"][0]["evidence_relation"], "not_established")

    def test_conditional_quote_ambiguous_and_unknown(self):
        self.assertEqual(grade_fragment(packet([], [claim(stance="quoted")]))["verdict"], "pass")
        self.assertEqual(grade_fragment(packet([], [claim(stance="conditional")]))["verdict"], "needs_review")
        two = claim(readings=[prop(), prop(object_="other_console")])
        self.assertEqual(grade_fragment(packet([], [two]))["claims"][0]["parse_status"], "ambiguous")
        self.assertEqual(grade_fragment(packet([], [claim(reading=prop("unregistered"))]))["verdict"], "needs_review")

    def test_observed_after_is_only_observation_order(self):
        reading = prop("observed_after", "new", "old", modality="record_assessment",
                       epistemic_scope="packet")
        sources = [source("new", observed_at=T1), source("old", observed_at=T2)]
        self.assertEqual(grade_fragment(packet(sources, [claim(reading=reading)]))["verdict"], "pass")
        sources[0]["observed_at"] = None
        self.assertEqual(grade_fragment(packet(sources, [claim(reading=reading)]))["verdict"], "needs_review")
        sources[0]["observed_at"] = T2
        self.assertEqual(grade_fragment(packet(sources, [claim(reading=reading)]))["verdict"], "fail")

    def test_validation_hashes_mutation_and_no_io(self):
        original = packet()
        changed = copy.deepcopy(original)
        changed["claims"][0]["readings"][0]["object"] = "different"
        self.assertEqual(grade_fragment(changed)["verdict"], "invalid")
        changed = packet([source(fact=prop(measure={"kind": "count", "unit": "item",
                                                    "lower": True, "upper": 1, "per": None}))])
        self.assertEqual(grade_fragment(changed)["verdict"], "invalid")
        changed = packet([source()], [claim("s1")])
        self.assertEqual(grade_fragment(changed)["verdict"], "invalid")
        with patch("builtins.open", side_effect=AssertionError("file I/O")), \
             patch("socket.socket", side_effect=AssertionError("socket I/O")), \
             patch("subprocess.Popen", side_effect=AssertionError("process I/O")):
            self.assertEqual(grade_fragment(original)["verdict"], "pass")
            result = check_claim(original["claims"][0], original["sources"],
                                 {"grader": original["grader"], "decision_at": T0,
                                  "coverage": original["coverage"]})
            self.assertEqual(result["verdict"], "pass")


if __name__ == "__main__":
    unittest.main()
