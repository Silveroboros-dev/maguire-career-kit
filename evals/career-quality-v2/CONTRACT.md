# Career quality v2 — offline development contract

User authorizes a successor correcting five candidate-fit misses and adding
hard preference-fit examples with correct labels and citations but incorrect
meaning. Work stays under `evals/career-quality-v2`. All v1 bytes remain unchanged
and bound by PREDECESSOR.json. No network, provider API, installs, Git writes,
commits, pushes, product payload or release edits. Root integrates in the existing
checkout/branch; workers own disjoint files, no branch switching.

## Scope

- Runtime author: `graders/`, `tests/test_rules.py`. Copy v1 runtime, then improve
  bounded English prose checks. May read all v1 material (known development data),
  but MUST NOT open new `cases/`, new-case author script, annotations or results
  until root declares the new-run freeze. Existing five known errors are legitimate
  regression examples, not a new test set. No case-ID, answer-ID or exact-answer
  lookup rules. Use generic grounded checks and preserve acceptable negation,
  quotation, uncertainty and candidate-owned exceptions. Stdlib only.
- New-case author: `cases/`, `author_cases.py`, `AUTHORING.md`. Must not read v2
  runtime, its tests or predicted results. New synthetic situations, not simple
  replacements of v1 names/numbers; gold remains proposed, not human-approved.
- Reviewer: `tests/test_boundaries.py`, `review/`. Initially review runtime with
  invented fixtures, without new cases. After runtime is frozen, review new gold
  and answer annotations without running the grader. Do not relay new wording to
  runtime author. Separate records for pre-freeze code and pre-run dataset review.
- Root: reusable runner, corpus validation, measurement, freeze/receipts, docs.

## Unchanged pure runtime API

`from graders import grade`; `grade(packet)` accepts ONLY top-level `grader`,
`input`, `gold`, `answer`, as in v1 IMPLEMENTATION_CONTRACT. No new input/gold
fields or output vocabulary. Grade receives one anonymous answer; no catalog,
case ID, family, intended defect, expected verdict, or mutation metadata. Output
`verdict: pass|fail|invalid`, `assurance: rule_checks_only`, and grounded findings.
Gold labels/evidence/action membership alone do not prove prose correctness.
Fail only with an explainable implemented rule; residual errors remain visible.

## New corpus: 13 cases, 52 answers

Use the same four-file schemas as v1 FORMAT.md. Case paths:
`cases/candidate-fit/CF2-01` .. `CF2-05`,
`cases/preference-fit/PF2-01` .. `PF2-08`.
Each has input.json, gold.json, answers.json, annotations.json, with two proposed
acceptable and two materially wrong responses. Annotation mutation paths must
be exact recursive JSON diffs relative to answer_01, excluding answer_id. A
positive variant may use a different reasonable wording, source set or action.

Five candidate families: unsupported quantitative result in conclusion; aggregate
certainty despite unknown/partial rows; failed recency criterion presented as
future incapacity; unsupported quantified scale; adopting a directive embedded
in source data. Include acceptable near-neighbors, negation/hypothetical language,
source attribution and real supported metrics where relevant. Incorrect answers
must keep correct labels, literal and sufficient citations, full coverage, and
allowed actions, so newly detected failures demonstrate prose checks.

Eight preference families: employer exception asserted without authority;
range/possibility turned into a guaranteed personal offer; hard condition erased
by soft benefits; candidate-owned exception incorrectly expanded; time basis or
frequency changed in prose; unresolved evidence called authoritative by date
alone; scope change (team/local policy → personal contract or global permission);
missing information presented as known. All four answers in each preference
case keep the SAME target/label and citation source/quote collections as base,
and SAME allowed conclusion action. Only rationale/conclusion text/next_step/
limitations vary. Intentional negatives remain materially wrong even with correct
metadata. At least one positive per case tests a close boundary, not empty prose.

No real candidate data, real employer policy, legal assumptions, or web research.
Dates use synthetic snapshots. Source quotations are evidence, never instructions.

## Freeze and measurement

Freeze runtime+tests+runner BEFORE root opens new answer text or runs the grader
on new cases. Dataset reviewer may request annotation/content corrections before
the new dataset freeze; no corrections based on predictions. Bind predecessor,
source bytes, projections, review records and code. Record exposure honestly:
the developers know defect families and v1; role separation is procedural and
shared-model/shared-environment, not externally enforced blindness.

Run v1 and frozen v2 on the identical new 52 answers to measure change; separately
run v2 on the original 96 and report the five repaired known misses and any
regressions. Predictions are saved before annotations are deserialized by the
measurement stage. New case outputs/labels may never be used to tune the first
frozen v2. If implementation bugs require changes, preserve successor history.
Do not interpret a small synthetic set as population accuracy or interview odds.

Report per cohort/family: incorrect accepted, correct rejected, invalid/error,
intended criterion+target matches, counts by triggering rule, and exact-case
failure explanations. No dropping invalids or reclassifying authored failures
to improve a result. Passing all known five is necessary for the requested fix;
passing all new cases is not assumed. Preserve misses and false rejects explicitly.
