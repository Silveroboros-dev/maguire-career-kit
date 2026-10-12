# Frozen v5 on 40 new manually annotated cases

2026-10-12. User-authorized offline evaluation only: no grader tuning, API/network,
dependency installation, Git mutation, commit or push. Work only in this folder.
Root integrates; standalone gpt-6-sol/high authors own one family each; a third
standalone gpt-6-sol/high reviewer first judges raw text without author labels.
Shared filesystem boundaries are instructions and attested access, not OS isolation.

## Evaluated claim and composition

Evaluate the already frozen v5 claim checker on 40 newly authored fictional career
answer fragments: 20 candidate-fit, 20 preference-fit. Target composition is 12
supported, 6 erroneous, 2 ambiguous per family, retaining a majority of correct
answers. Gold is semantic truth from the complete supplied source inventory;
independent review may identify a composition deviation, which must be disclosed
rather than forcing labels. All 40 remain in measured accounting, including invalid
or execution failures. No post-run exclusions, label changes or input repairs.

Source interpretation and normalized claims are manually authored by agents, not
human-approved. Raw-text extraction and full career-advice quality are not evaluated.
No interview probability claim. This is a fresh contract-informed challenge, not
a statistically representative sample or fully independent human blind holdout.
Root knows previous outcomes; authors and raw-only reviewer must not inspect them.
The public schema itself describes supported operations and limitations. Exact
overlap and lexical comparisons nominate repeats, not proof of semantic novelty.

## Frozen runtime and author boundaries

checker.py, v3_core.py, grade_packets.py and measurement.py must remain byte-identical
to career-quality-v5 and to its freeze. FROZEN_SCHEMA.md is the same public schema.
No runtime code, rule, registry, threshold or measurement definition is changed.
PREDECESSOR.json binds every pre-existing evaluation file (385 at creation), including
all earlier corpora, code, reviews and saved predictions. Keep their bytes unchanged.

AUTHORING.md is the closed author input interface. Authors see only it, the schema,
repository instructions and their own authored family. No checker/tests/prior cases/
predictions. Each author returns a bound exposure attestation. Raw-only reviewer
sees raw source/answer files before labels/normalization; saves versioned judgments
with input hashes and actual access attestation. Then compares gold and normalization
for missing claims, lost qualifiers and unsupported facts. Document adjudications
before freeze, preserving earlier judgment files. Human approval stays false.

Unknown comparison capability does not make a supported claim semantically ambiguous.
Review in gold is reserved for actual unresolved readings or evidence conflicts.
Defective fragments must identify each faulty assertion separately from sound premises.
Normalization may propose a typed operation, never an expected outcome. Preserve
meaning even when the frozen checker cannot implement it.

## Preflight and one measured run

New harness adapts v5 projection/runner to the new cohort without modifying its four
frozen runtime files. Unit tests use invented fixtures and must not execute these
40 packets. Structural audit calls only validation, not grading. Bind new raw/gold/
normalized, author attestations, raw-only judgments, final semantic review, novelty
screen/review and final contract challenge before freezing the dataset/harness.

Challenge is read-only and bounded to evidence identity, frozen-runtime equality,
exposure, normalization review, counts, projections, outcome accounting and offline
single-run behavior. Do not repair or broaden the grader because a probe fails.
Ready challenge means no scoped execution blocker, not correctness or new authority.

Save create-only FREEZE, START, packet projection and predictions. Grade once with
the copied frozen worker; it receives no gold/author reasons/metadata. Network and
process access are blocked, and grading file I/O is blocked. Predictions are saved
before comparing them with labels. Frozen files must never be edited after results.

## Measurement and limitations

Reuse exact v5 measurement definitions: bad→pass misses; good→fail false rejections;
needs_review split by gold; ambiguous forced decisions; invalid/execution errors;
intended faulty-claim localization and failures on wrong clauses. Abstention is
neither acceptance nor detection. Show per-family and overall denominators. Compare
specific claims to sources and trace, not only aggregate match counts.

This new cohort has different identities; do not claim a paired v4/v5 improvement
from its metrics. Saved v5 development scores may be context only, clearly separate.
Reviewer examines all disagreements and missed claim IDs after predictions saved.
Report checker limitations versus normalization/gold disputes separately; preserve
the original measured result in either case. Local receipts are integrity metadata,
not external signatures. No frozen grader repair, release or integration is authorized.
