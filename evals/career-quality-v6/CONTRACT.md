# V6: normalization and bounded claim coverage regression

User authority: offline local implementation and evaluation only; no network/API,
dependency installation, Git writes, commit or push. Root is integrator; workers
edit disjoint files in the existing checkout. This overrides branch/fetch workflow.
Stdlib Python with -B. Preserve all 454 PREDECESSOR files byte for byte.

## Evaluated claim

Repair normalization and extend bounded source-based claim checks on the SAME
40 raw source/answer cases from career-quality-v5-new-cases. Raw and gold files
stay byte-identical; keep all 61 claim IDs and anchors. No new inference facts,
lost qualifiers, modality strengthening, deletion or relabeling to improve scores.
Source interpretation/normalization and checker code may change only in this v6
folder, with per-case rationale and review. v3_core.py stays unchanged; checker.py
is a local v6 successor. Runtime packet schema is maguire-claim-packet-v6.

This is an exposed development regression, not a new blind holdout. Implementers
and reviewer may see old outcomes; new v6 cohort predictions are prohibited before
freeze. Unit/adversarial tests must use separate invented fixtures, not grade the
40 target packets. Shape-only target validation is allowed. Freeze reviewed data,
runtime and harness after tests and bounded read-only challenge; run once and
preserve predictions before measurement. No post-run repairs or exclusions.

## Work ownership

Root: harness, worker/measurement schema envelope, tests/test_pipeline.py,
tests/test_new_cohort.py, contract, predecessor manifest, freeze/run/report.
Checker worker: checker.py, tests/test_v6_checker.py, CHECKER_CHANGES.md.
Normalization worker: normalized/*.json, SCHEMA.md, NORMALIZATION_CHANGES.md,
normalization_attestation.json. It may inspect checker but does not edit it.
Reviewer: review/* and tests/test_v6_review_probes.py only; no implementation edits.
No worker may write raw/gold, predecessor versions, or another owner's files.

## Required semantics and boundaries

Use an explicit bounded predicate registry with existing source/time/scope/modality
checks, not universal trust in arbitrary predicates or direct equality alone.
Unknown qualitative fit/transferability remains review. Preserve contradictions,
team-versus-person attribution, production-versus-sandbox scope and event occurrence.
Expand context relations only for documented dimensions; unknown or contradictory
qualifiers must fail closed. State relations between current pending status and
future availability, whole-day prohibitions and narrower windows, conditional
remote permission and onboarding. Do not imply request approval or payment guarantee.

Source-backed pending status is observation of status, not promise of activation.
Use canonical weekdays/time fields and retain exhaustive/condition qualifiers in
claims. Prefer refusing unsupported qualitative judgments to fabricated confidence.
Specific proposals/limits and implementation evidence belong in SCHEMA/changes.

## Measurements and lineage

Reuse previous definitions: fail→pass misses; pass→fail false rejections;
needs_review split by gold; ambiguous forced decisions; invalid/execution errors;
intended faulty-claim localization including rejection of other clauses. All 40
stay in denominators. Pair v5 and v6 by canonical source/answer identity, not packet
hash (normalization/code schema changes packets). Report per-family and overall,
plus per-case transitions. A paired improvement here is not generalization evidence.

Review binds six data files, schema, changes and manually reviewed claim coverage.
Preflight challenge binds exact runtime/harness/tests and prior challenge receipt;
ready means no scoped execution blocker, not authority or correctness. User already
authorized the offline run. No extra approval is required. FREEZE/START use exclusive
creation. Worker receives no gold/reasons; source IDs may retain case-like strings.
Offline worker blocks socket/process calls, and file I/O while grading. Not OS isolation.
Local hashes are integrity metadata, not external signatures. All annotations and
reviews are agent-authored, human_approved=false. After run reviewer examines all
errors/deferred cases and localization; frozen artifacts stay unchanged.
