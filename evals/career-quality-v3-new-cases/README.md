# New manual cases for frozen career-quality v3

An isolated offline challenge of the existing claim checker. No changes to the
kit, engineering benchmark, old cases, checker or its worker. No external API,
package installation, commit or push. Python standard library only.

The 40 fictional answer fragments contain 24 acceptable answers, 12 defective
answers and 4 ambiguous answers. Each family contributes 20 fragments. This
increases the positive examples from 2 in the earlier 16-fragment regression to
24 in this separate cohort. Do not pool those cohorts as independent samples.

Two fresh author agents received the schema without old runtime/data/results.
A separate agent saved raw-text judgments before opening their annotations and
gold. Review found and corrected annotation gaps before predictions; original
inputs and both reviews remain under `review/`. Final normalization has 81 claim
atoms. These are manually authored and reviewed **by agents**; no human approval
is recorded. Shared-filesystem procedural separation is not a blind external
holdout. The source contexts are fictional, not captured production failures.

## Files and boundaries

- `raw/`: source snapshots and selected answer fragments.
- `normalized/`: manually interpreted source facts and answer claims.
- `gold/`: semantic verdicts, reasons and intended faulty claim IDs.
- `author_*.py`: reproducible authoring, never imported by grading runtime.
- `review/`: raw-only judgments, annotation reviews, archived initial inputs,
  preflight challenge and eventual result review.
- `pipeline.py`: source anchors, projection, freeze, execution and measurement.
- `tests/test_pipeline.py`: synthetic harness integrity/accounting tests.
- `PREDECESSOR.json`: byte bindings for 271 files in previous experiments.
- `FREEZE.json`: created before predictions, binding inputs/code/reviews and
  ordered projected packet hashes.
- `START.json`: exclusive one-run marker created before worker execution.
- `runs/new-cases-v3/`: immutable packets, mapping, predictions, execution record,
  measurement, mechanically rendered report and hash/size receipt.
- `ANALYSIS.md`: post-run interpretation, including failure and review lists.

Projection preserves normalized semantics and binds quotations to exact raw
bytes plus decoded string spans. It excludes titles, gold, author reasons and
review judgments. The unchanged `../career-quality-v3/grade_packets.py` receives
only `{packet_sha256, packet}` rows. Its audit guard blocks network/process access
and I/O during grading. IDs within source/claim structures remain stable for
references; they are not secret and are not an assurance of semantic independence.

The checker evaluates typed, reviewed claims. It does not extract claims from
ordinary prose, verify real-world source truth, judge a complete career answer,
or estimate interview probability. Unknown semantic predicates are retained
honestly in annotation rather than deleting assertions to improve scores.

## Reproduce checks

From the repository root, without installing anything:

```sh
python3 -B -m unittest discover -s evals/career-quality-v3-new-cases/tests -v
python3 -B evals/career-quality-v3-new-cases/pipeline.py audit --review review/annotation_review_v2.json
python3 -B evals/career-quality-v3-new-cases/pipeline.py verify
```

One-time preparation and execution (exclusive files; do not rerun over artifacts):

```sh
python3 -B evals/career-quality-v3-new-cases/pipeline.py freeze --review review/annotation_review_v2.json --challenge review/challenge_packet_v2.json
python3 -B evals/career-quality-v3-new-cases/pipeline.py run
```

`audit` calls only frozen structural validators, never prediction functions.
`verify` recomputes projection/accounting and verifies artifacts, without rerunning
the checker. A repeated run is refused by `START.json`; a later experiment needs
a new root/freeze and must preserve this one. Do not regenerate author data after
freeze. Hashes and sizes provide local integrity, not an external signature.

## Accounting

Report `bad → pass` as a missed accepted error, `good → fail` as a false rejection,
and all `needs_review` separately by semantic gold class. A bad answer deferred
to review is not counted as a detected error. Ambiguous answers forced to pass
or fail and technical invalids are separate. Preserve all 40 denominators.

Additionally compare the actual failed claim IDs with manually annotated faulty
claims. Rejecting a fragment for an innocent clause does not earn credit for
finding its intended defect. This localizes flags; explanation/relationship
correctness needs the separate result review. No single aggregate accuracy is
used to collapse these distinctions.
