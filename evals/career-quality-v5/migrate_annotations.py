"""Offline, narrow migration from frozen v4 annotations to v5.

This authoring script reads v4 normalized rows and the copied v5 raw fragments.
It does not import the checker or read gold, packets, or predictions.
"""

from __future__ import annotations

import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
PRIOR = HERE.parent / "career-quality-v4" / "normalized"
FAMILIES = ("candidate-fit", "preference-fit")


def read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def propositions(row: dict):
    """Yield source facts and claim readings without changing their other fields."""
    for source in row["sources"]:
        yield from source["facts"]
    for claim in row["claims"]:
        yield from claim["readings"]


def build(family: str) -> dict:
    document = read(PRIOR / f"{family}.json")
    raw = read(HERE / "raw" / f"{family}.json")
    assert document["family"] == family
    raw_rows = {row["case_id"]: row for row in raw["rows"]}
    assert len(raw_rows) == len(raw["rows"]) == len(document["rows"])
    assert set(raw_rows) == {row["case_id"] for row in document["rows"]}

    day_units = 0
    for row in document["rows"]:
        original = raw_rows[row["case_id"]]
        assert {source["id"] for source in row["sources"]} == {
            source["id"] for source in original["sources"]
        }
        for claim in row["claims"]:
            assert claim["quote"] in original["answer"]["text"]
        for proposition in propositions(row):
            measure = proposition.get("measure")
            if measure is not None and measure["unit"] == "days":
                # A single canonical day unit covers both counts and frequencies.
                # Preserve measure.kind and measure.per: 30 onboarding days is a
                # count, while two station days per week is a frequency.
                assert measure["kind"] in {"count", "frequency"}
                measure["unit"] = "day"
                day_units += 1

    if family == "preference-fit":
        row = next(row for row in document["rows"] if row["case_id"] == "PF3N-09")
        source = next(source for source in row["sources"] if source["id"] == "J09")
        unavailable_now = source["facts"][0]
        assert unavailable_now["predicate"] == "live_captions"
        assert unavailable_now["polarity"] == "negative"
        assert unavailable_now["scope"] == {}
        assert "not yet available" in next(
            source for source in raw_rows["PF3N-09"]["sources"]
            if source["id"] == "J09"
        )["text"]
        unavailable_now["scope"]["status"] = "available_now"
        assert day_units == 2
    else:
        assert day_units == 4

    document["schema"] = "maguire-v5-normalized"
    document["human_approved"] = False
    document["exposure"] = {
        "author": "v5 normalization agent",
        "basis": "manual review of frozen v4 annotations, copied raw fragments, v4 analysis and v5 contract",
        "checker_access": False,
        "predecessor_failure_analysis_seen": True,
        "runtime_predictions_seen": False,
        "v5_runtime_predictions_seen": False,
        "human_approved": False,
        "limitations": "Known-case regression; no independent human review or raw-text extraction test.",
    }
    return document


def main() -> None:
    if (HERE / "FREEZE.json").exists() or (HERE / "START.json").exists():
        raise RuntimeError("v5 is frozen or started; refusing to rewrite annotations")
    output = HERE / "normalized"
    documents = {family: build(family) for family in FAMILIES}
    output.mkdir(exist_ok=True)
    for family, document in documents.items():
        (output / f"{family}.json").write_text(
            json.dumps(document, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )


if __name__ == "__main__":
    main()
