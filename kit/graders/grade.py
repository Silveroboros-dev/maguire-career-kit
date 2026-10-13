#!/usr/bin/env python3
"""Run the bundled v8 fragment checker in one named fit mode, offline."""

import argparse
import json
from pathlib import Path

from grade_packets import execute


MODES = {"jd-fit": "candidate_fit", "employer-fit": "preference_fit"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=MODES, required=True)
    parser.add_argument("--packets", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    args = parser.parse_args()

    rows = [json.loads(line) for line in args.packets.read_text(encoding="utf-8").splitlines()]
    if not rows:
        parser.error("No packets supplied")
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"packet_sha256", "packet"} or not isinstance(row["packet"], dict):
            parser.error("Invalid packet envelope")
        if row["packet"].get("grader") != MODES[args.mode]:
            parser.error("Packet grader does not match selected mode")

    results = execute(rows)
    with args.predictions.open("x", encoding="utf-8") as stream:
        for result in results:
            stream.write(json.dumps(result, ensure_ascii=False, sort_keys=True) + "\n")
    print(json.dumps({"records": len(results),
                      "execution_errors": sum(row["execution_error"] is not None for row in results)}))


if __name__ == "__main__":
    main()
