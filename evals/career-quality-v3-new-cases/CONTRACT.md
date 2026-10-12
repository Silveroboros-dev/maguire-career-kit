# New cases against the frozen v3 checker

2026-10-12. User authorizes new manually annotated cases, more correct answers,
and an offline run of frozen v3. No network/API/install, Git mutation, commit,
push, product or release changes. Root integrates in the current checkout.
Only this new folder may change. Bind all v1/v2/v3-design/v3 bytes as predecessors.

## Cohort fixed before authoring

40 new selected answer fragments: 20 candidate-fit and 20 preference-fit.
Each family has 12 semantically acceptable, 6 materially defective, and 2
genuinely ambiguous fragments. Overall 24 acceptable / 12 defective / 4 ambiguous.
Source contexts should be new, not lexical/numeric substitutes of prior answers.
Each source snapshot, fragment, normalization and gold is authored manually by
agents and separately reviewed; human_approved=false. No synthetic generation
API or live model judge, and no claim of evaluation on organically sourced jobs.

Gold judges the meaning of the answer given the sources. It must NOT imitate
which operations the frozen checker happens to support. A correct conditional
or bounded inference remains reference-pass even if runtime abstains or rejects.
Use many positive near-neighbors, multi-clause answers and evidence-preserving
transformations; do not make all positives literal copies of source facts.
Ambiguous gold requires real interpretation ambiguity, not merely a missing
checker rule or a known conflict presented with unjustified certainty.

## Roles and exposure

- Two fresh author workers read only SCHEMA.md, author_support.py, this contract,
  and repo instructions. One owns candidate-fit files; the other preference-fit.
  Neither may inspect old checker code/tests/cases/results/design examples or
  call/import the checker. They may know the schema and problem domain.
- Reviewer first forms judgments from raw source/answer text WITHOUT normalized
  claims, authored labels or runtime predictions, saves those judgments; then
  reviews normalization/gold, resolves pre-run issues and writes a new receipt.
  It may later inspect frozen code for explanation but not tune the cohort to it.
- Root knows prior development outcomes, prepares the harness, checks structural
  validity and performs one measured run after code/data/review freezes. Root
  does not edit runtime or choose cases based on observed predictions.

Authors and reviewer operate in the same environment with procedural access
boundaries. These are author/reviewer attestations, not enforced filesystem
isolation, human approval or independent institutional validation. New cases
are post-code-freeze challenge material; do not call them an externally held-out
benchmark. No raw-text extractor is evaluated.

## Immutable runtime and pipeline

Use existing `../career-quality-v3/grade_packets.py` with existing checker.py
unchanged. Expected checker SHA-256:
e4b2699f543e4260128ebfabd61547c92b5c1dba3497acd07ca2f7007f225e33.
The local harness projects raw+normalized artifacts into anonymous packets,
binding exact anchors and coverage. Source IDs and all semantic content are
preserved. Presentation IDs, labels, mutation/failure descriptions, reviewer
judgments and expected explanations never reach grade_fragment.

Freeze raw text, normalization, gold, receipts, harness and ordered packet hashes
before execution. Save all predictions before measuring against gold. Preserve
every technical failure, abstention and semantic error. No case repairs or
runtime edits after predictions; report unexpected results as they are.
Run is local/deterministic with the frozen worker's network/process/I/O guard.
One measurement run, no external operations. A failed harness invocation retains
its files; any needed correction creates a successor freeze/run, never overwrites.

## Measures and acceptance of evidence

Report by grader and overall, with original denominators:

- defective -> pass: missed/accepted error;
- acceptable -> fail: false rejection;
- each gold class -> needs_review: abstention, shown separately; defective
  abstention is NOT detected error, acceptable abstention is NOT acceptance;
- ambiguous -> pass/fail: forced decision; ambiguous -> review: appropriate;
- invalid/execution errors: separate, never excluded silently;
- intended bad claims actually localized vs failures on a correct clause.

Distinguish fragment-level decisions, claim-level localization and quality of
explanations. No grand accuracy merging all stages. Post-run reviewer examines
every disagreement and every newly caught defect; no gold rewrite after seeing
results. A reviewer disagreement is preserved as an annotation caveat.

Before execution: validate all hashes/anchors/IDs, source inventories, typed
schema and review coverage; test identity renumbering, omitted/duplicate/foreign
packets, source drift, metadata exclusion and error-vs-review accounting using
synthetic harness fixtures. Check exact duplicate text against prior sets, but
do not mistake zero exact duplicates for semantic independence.

Reports and local checksums bind artifacts. They are not signatures or external
seals. No commit/push is requested or allowed.
