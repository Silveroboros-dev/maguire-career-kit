# Offline grader baseline — execution contract

Authorized 2026-10-12: implement candidate-fit and preference-fit graders and
evaluate all 96 existing answers. No network, provider calls, installations,
commits, staging, pushes, installer changes, or edits to the frozen case files.
The earlier FORMAT prohibition on adding a grader described the authoring stage;
this later user request authorizes the implementation stage.

## Scope and responsibility

Root integrates on the existing local `codex/offline-maguire-grader` branch,
base `4d87b90ef74c4f40b282e08b6d82fc6ad9f2749e`. Workers share the checkout but
own disjoint new files and perform no Git mutations. The runtime worker owns
`graders/` and `tests/test_graders.py`; the boundary reviewer owns
`tests/test_grader_boundaries.py` and `review/grader_code_review_v1.json`.
Root owns projection, execution, measurement, receipts, and documentation.

## Runtime contract

`from graders import grade`; `grade(packet) -> dict` is a pure standard-library
Python function, with no filesystem, subprocess, network or model access.

Packet exact top-level keys:

- `grader`: `candidate_fit` or `preference_fit`.
- `input`: only `decision_at`, `task`, `jd`, `candidate` from the input fixture.
- `gold`: only `units`, `forbidden_assessment_targets`, `acceptable_actions`.
- `answer`: only `assessments`, `conclusion`, `limitations` from ONE answer.

No case/answer presentation IDs, dataset paths, family names, expected verdicts,
mutation metadata, critical-error catalog, or other answers enter this function.
Source and target IDs remain for joins; their spelling must not affect decisions.
Gold is a proposed rubric, not a known verdict for this answer. Required points
are not exact-string requirements. Do not match against canned answers, case IDs,
or substrings chosen from the deliberate mutations.

Result must include `verdict` (`pass`, `fail`, or `invalid`), `findings` (list of
`criterion_id`, `severity`, `target_id` [may be null for global findings], `code`,
`path`, `explanation`), and `assurance: rule_checks_only`. Additional diagnostic
fields are permitted. Invalid packets are technical failures, not advice defects.
Every failing finding must identify an implemented rule and actual evidence.
`pass` means no material error detected by these bounded rules; it does not
certify all the semantic propositions in RUBRIC.md. No aggregate quality score
or probability is produced.

## Evaluation design

Implement evidence/label/coverage/action checks plus bounded semantic rules
where a conservative rule has explicit grounds. Report remaining prose checks
as unsupported; do not pretend deterministic matching establishes entailment.
Workers authoring the runtime and boundary tests must not read `answers.json`
or `annotations.json` before the first full run. The root and earlier authors
have seen this development corpus: this is NOT an independent blind holdout.

Before the first 96-answer run, bind runtime, projection, evaluator, tests,
rubric, contract and original MANIFEST bytes in a local freeze receipt. Preserve
every completed run. Generate anonymous projected packets, deterministic shuffled
order and a separate content-bound identity map. Save predictions BEFORE opening
annotations for measurement. Measure false acceptances, false rejections, invalid
results, and exact criterion+target localization separately. An answer rejected
for another reason does not prove that its intended defect was found.

Do not tune rules after seeing the first run to hide misses. Implementation or
measurement bugs require an explained successor version and retained predecessor.
These local hashes detect drift but are not an independent external seal.

## Completion evidence

Verify all 24 cases/96 responses, zero dropped or duplicated records, no expected
labels entering runtime, ID/order invariance, malformed-input handling, leakage
rejection, actual negative and acceptable prose boundaries, and receipt binding.
Recheck the existing case-file MANIFEST and Git HEAD. Report the two confusion
matrices, each missed defect and false rejection, and limitations of development
data, proposed gold and rule-only semantics. No product release gate is claimed.
