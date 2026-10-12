"""Manual, offline v3-new-cases -> v4 semantic annotation migration.

Inputs are predecessor annotations and copied raw fragments only. This authoring
script never imports the checker or reads gold, predictions, or measurements.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / "career-quality-v3-new-cases" / "normalized"


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def fact(row: dict, source_id: str, index: int = 0) -> dict:
    return next(s for s in row["sources"] if s["id"] == source_id)["facts"][index]


def claim(row: dict, claim_id: str) -> dict:
    return next(c for c in row["claims"] if c["id"] == claim_id)


def ref(source_id: str, index: int = 0) -> dict:
    return {"source_id": source_id, "fact_index": index}


def derived(row: dict, claim_id: str, predicate: str, obj: str, check: dict,
            *, stance: str = "asserted", scope: dict | None = None,
            time: dict | None = None) -> None:
    c = claim(row, claim_id)
    c["stance"] = stance
    c["readings"] = [{
        "subject": "candidate", "predicate": predicate, "object": obj,
        "modality": "evaluation_instruction" if stance == "advice" else "record_assessment",
        "polarity": "positive", "epistemic_scope": "packet",
        "scope": scope if scope is not None else {},
        "time": time if time is not None else {}, "measure": None,
    }]
    c["check"] = check


def annual(f: dict) -> None:
    f["scope"].pop("annual", None)
    assert f["measure"]["unit"] == "USD"
    f["measure"]["per"] = "calendar_year"


def migrate_candidate(rows: dict[str, dict]) -> None:
    r = rows["CF3N-08"]
    f = fact(r, "CF3N-08-S1")
    f["measure"] = {"kind": "frequency", "unit": "days", "lower": 2,
                    "upper": 2, "per": "week"}
    c = claim(r, "c1")["readings"][0]
    # Retain the scalar Tuesday/Thursday scope in both source and claim.
    # The 2022 self-report remains historical; the 2027 role fact stays separate.

    r = rows["CF3N-10"]
    claim(r, "c1")["readings"][0]["scope"]["duration_months_lower"] = 13
    # The source and claim both retain 2023-01 through 2024-06.

    # CF3N-11 c2 is intentionally an unquantified occurrence. Its positive
    # observed count is already explicit in the source and remains unchanged.


def migrate_preference(rows: dict[str, dict]) -> None:
    for n in (1, 2, 3, 4, 5, 7, 9, 11, 12, 14, 15, 17):
        r = rows[f"PF3N-{n:02d}"]
        for s in r["sources"]:
            for f in s["facts"]:
                if f["predicate"] == "supersedes":
                    continue
                # This object is a property, shared by offer, preference and
                # comparison. Scope carries bounds, timing and conditions.
                if n == 1: obj, pred = "personal equipment stipend", "stipend"
                elif n == 2: obj, pred = "personal workspace stipend", "stipend"
                elif n in (3, 5, 14): obj, pred = "station attendance", "station_attendance"
                elif n == 4: obj, pred = "on-call shift", "on_call"
                elif n == 7: obj, pred = "learning allowance", "learning_allowance"
                elif n == 9: obj, pred = "team meeting captions", "live_captions"
                elif n == 11: obj, pred = "remote schedule", "remote_work"
                elif n == 12: obj, pred = "required training demos", "training_demo"
                elif n == 15: obj, pred = "overnight on-call", "on_call"
                else: obj, pred = "personal internet stipend", "stipend"
                # A potential trial by some teams is not the role's binding
                # attendance term; retain its distinct subject and modality.
                if n == 14 and s["id"] == "J14N":
                    continue
                f["object"] = obj
                f["predicate"] = pred
        for c in r["claims"]:
            if c["check"] is None:
                for f in c["readings"]:
                    if f["predicate"] == "supersedes":
                        continue
                    if n == 14 and c["id"] == "A":
                        continue
                    if n == 11 and c["id"] == "B":
                        continue
                    f["object"] = obj
                    f["predicate"] = pred

    for n in (1, 7, 10, 17, 18):
        r = rows[f"PF3N-{n:02d}"]
        for s in r["sources"]:
            for f in s["facts"]:
                if f["measure"] and f["measure"]["kind"] == "amount" and (
                    f["scope"].get("annual") or (n in (7, 18) and f["measure"]["per"] is None)
                ):
                    annual(f)
        for c in r["claims"]:
            for f in c["readings"]:
                if f["measure"] and f["measure"]["kind"] == "amount" and (
                    f["scope"].get("annual") or (n == 18 and f["measure"]["per"] is None)
                ):
                    annual(f)

    r = rows["PF3N-01"]
    derived(r, "B", "constraint_satisfied", "personal equipment stipend",
            {"op": "constraint", "offer": ref("J01"), "preference": ref("P01")})

    r = rows["PF3N-02"]
    derived(r, "B", "constraint_satisfied", "personal workspace stipend",
            {"op": "constraint", "offer": ref("J02"), "preference": ref("P02")})

    r = rows["PF3N-03"]
    derived(r, "B", "constraint_satisfied", "station attendance",
            {"op": "constraint", "offer": ref("J03"), "preference": ref("P03")})

    r = rows["PF3N-04"]
    for f in (fact(r, "J04"), fact(r, "P04"), claim(r, "A")["readings"][0]):
        f["scope"] = {"weekday": "Saturday",
                      **({"priority": "must_have"} if f is fact(r, "P04") else {})}
    # "Saturday-only" in answer A excludes other days. The raw source states
    # Saturday and no weekdays but does not expressly exclude Sunday, so keep
    # the stronger exclusivity qualifier only on that claim reading.
    claim(r, "A")["readings"][0]["scope"]["only"] = True
    no_weekday = copy.deepcopy(fact(r, "J04"))
    no_weekday.update(modality="observation", polarity="negative",
                      scope={"weekday": "weekday"}, measure=None)
    next(s for s in r["sources"] if s["id"] == "J04")["facts"].append(no_weekday)
    weekday_ban = copy.deepcopy(fact(r, "P04"))
    weekday_ban.update(polarity="negative",
                       scope={"priority": "must_have", "weekday": "weekday"},
                       measure=None)
    next(s for s in r["sources"] if s["id"] == "P04")["facts"].append(weekday_ban)
    derived(r, "B", "constraint_satisfied", "on-call shift",
            {"op": "constraint", "offer": ref("J04"), "preference": ref("P04")},
            scope={"weekday": "Saturday"})

    r = rows["PF3N-05"]
    for f in (fact(r, "J05U"), claim(r, "A")["readings"][0]):
        f["subject"], f["object"] = "J05U", "J05"
    derived(r, "C", "constraint_satisfied", "station attendance",
            {"op": "constraint", "offer": ref("J05U", 1), "preference": ref("P05")})

    r = rows["PF3N-06"]
    offer, remote, preference = fact(r, "J06"), fact(r, "J06", 1), fact(r, "P06")
    offer.update(predicate="station_attendance", object="onboarding",
                 measure={"kind": "count", "unit": "days", "lower": 30,
                          "upper": 30, "per": None}, time={"phase": "onboarding"})
    remote.update(object="work_location", time={"phase": "after_onboarding"})
    preference.update(predicate="station_attendance", object="onboarding",
                      scope={"priority": "must_have", "requires_remote_after": True},
                      time={"phase": "onboarding"},
                      measure={"kind": "count", "unit": "days", "lower": None,
                               "upper": 30, "per": None})
    claim(r, "B")["readings"][0].update(object="work_location",
                                          time={"phase": "after_onboarding"})
    derived(r, "A", "constraint_satisfied", "onboarding",
            {"op": "onboarding", "offer": ref("J06"), "remote": ref("J06", 1),
             "preference": ref("P06")}, scope={"requires_remote_after": True},
            time={"phase": "onboarding"})

    r = rows["PF3N-07"]
    fact(r, "J07")["scope"] = {"status": "planned"}
    fact(r, "J07", 1)["scope"] = {"status": "undecided"}
    claim(r, "A")["readings"][0]["scope"] = {"status": "undecided"}
    derived(r, "B", "constraint_unresolved", "learning allowance",
            {"op": "pending", "offer": ref("J07", 1), "preference": ref("P07")},
            scope={"status": "undecided"})

    r = rows["PF3N-09"]
    fact(r, "J09", 1)["scope"] = {"status": "pending", "reason": "procurement"}
    claim(r, "A")["readings"][0]["scope"] = {"status": "pending", "reason": "procurement"}
    derived(r, "B", "confirmation_needed", "team meeting captions",
            {"op": "pending", "offer": ref("J09", 1), "preference": ref("P09")},
            stance="advice", scope={"status": "pending", "reason": "procurement"})

    r = rows["PF3N-10"]
    for f in (fact(r, "J10"), fact(r, "P10"),
              claim(r, "A")["readings"][0], claim(r, "B")["readings"][0]):
        f["object"] = "learning allowance"

    r = rows["PF3N-11"]
    derived(r, "A", "request_within_limit", "remote schedule",
            {"op": "permission_limit", "offer": ref("J11"), "preference": ref("P11")},
            scope={"condition": "manager_approval"})
    derived(r, "B", "condition_required", "remote schedule",
            {"op": "condition", "offer": ref("J11")},
            scope={"condition": "manager_approval"})

    r = rows["PF3N-12"]
    offer, preference = fact(r, "J12"), fact(r, "P12")
    offer["scope"] = {"only": True}
    offer["time"] = {"weekday": "Wednesday", "start_minute": 900,
                     "end_minute": 960, "zone": "role_local"}
    preference["time"] = {"after_minute": 1080, "zone": "role_local"}
    derived(r, "A", "constraint_satisfied", "required training demos",
            {"op": "schedule_before", "offer": ref("J12"), "preference": ref("P12")},
            scope={"only": True}, time={"weekday": "Wednesday", "zone": "role_local"})

    r = rows["PF3N-14"]
    for f in (fact(r, "J14N"), claim(r, "A")["readings"][0]):
        f["subject"], f["object"] = "J14N", "J14"
    derived(r, "B", "constraint_satisfied", "station attendance",
            {"op": "constraint", "offer": ref("J14"), "preference": ref("P14")})

    r = rows["PF3N-15"]
    derived(r, "B", "constraint_satisfied", "overnight on-call",
            {"op": "constraint", "offer": ref("J15"), "preference": ref("P15")})

    r = rows["PF3N-17"]
    derived(r, "B", "constraint_satisfied", "personal internet stipend",
            {"op": "constraint", "offer": ref("J17"), "preference": ref("P17")})

    r = rows["PF3N-18"]
    for f in (fact(r, "J18"), claim(r, "A")["readings"][0]):
        f["object"] = "certification exam fees"
    # The exclusion remains a separate negative permission for conference travel.

    r = rows["PF3N-16"]
    no_commitment = fact(r, "J16", 1)
    no_commitment.update(predicate="caption_enablement_commitment",
                         object="team meeting captions", modality="observation",
                         polarity="negative")


def build(family: str) -> dict:
    prior = read(PRIOR / f"{family}.json")
    raw = read(HERE / "raw" / f"{family}.json")
    rows = {r["case_id"]: r for r in prior["rows"]}
    assert set(rows) == {r["case_id"] for r in raw["rows"]}
    for row in prior["rows"]:
        raw_row = next(r for r in raw["rows"] if r["case_id"] == row["case_id"])
        assert {s["id"] for s in row["sources"]} == {s["id"] for s in raw_row["sources"]}
        for c in row["claims"]:
            assert c["quote"] in raw_row["answer"]["text"]
            c["check"] = None
    if family == "candidate-fit":
        migrate_candidate(rows)
    else:
        migrate_preference(rows)
    prior["schema"] = "maguire-v4-normalized"
    prior["human_approved"] = False
    prior["exposure"] = {
        "author": "v4 normalization agent",
        "basis": "manual review of predecessor annotations, raw fragments, v3 analysis and v4 schema",
        "checker_access": False,
        "runtime_predictions_seen": False,
        "human_approved": False,
        "limitations": "Known-case regression; no independent human review or raw-text extraction test.",
    }
    return prior


def main() -> None:
    output = HERE / "normalized"
    output.mkdir(exist_ok=True)
    for family in ("candidate-fit", "preference-fit"):
        document = build(family)
        (output / f"{family}.json").write_text(
            json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
