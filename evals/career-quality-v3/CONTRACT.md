# V3 first slice: offline checker over reviewed normalized claims

2026-10-12. User authorizes implementation and evaluation of the 16 existing
design fragments. No network/provider calls, package installation, Git mutation,
commits/push, kit/release/product changes. Keep v1, v2 and v3-design immutable.
Base HEAD: 4d87b90ef74c4f40b282e08b6d82fc6ad9f2749e; existing branch
codex/offline-maguire-grader. Root integrates; no branch switching.

This is known development data, not a blind holdout. Manual means manually
normalized and agent reviewed, NOT human approved. No extractor or whole-answer
quality claim. Scope is fragment only. The 16 expectations contain 13 material
errors, two acceptable fragments and one ambiguous fragment needing review.

## Ownership

- Runtime worker: `checker.py`, `tests/test_checker.py` only. Read this contract
  and predecessor design prose. Implement generic operations, no case/example
  ID or expected outcome lookups. Do not read `data/`, `prepare_data.py`, run
  outputs or `CLAIM_TRACES.json` until first implementation is delivered.
- Root: manually normalized sources/claims, projection, runner, measures,
  lineage and docs. Root knows all expected results; do not call this blind.
- Reviewer: `review/`, `tests/test_boundaries.py` only. Review normalization
  against exact original source/answer anchors, then code and results; record
  any limitations and outcome exposure. Do not rewrite source data or runtime.

## Pure API

`from checker import grade_fragment, check_claim`

`grade_fragment(packet)` takes exactly:

```
{
  schema: "maguire-claim-packet-v3",
  grader: "candidate_fit" | "preference_fit",
  decision_at: ISO timestamp,
  sources: [source],
  claims: [claim],
  coverage: {
    scope: "fragment",
    source_sha256: SHA256(canonical(sources)),
    claims_sha256: SHA256(canonical(claims)),
    status: "agent_reviewed" | "unreviewed",
    source_inventory_complete: bool,
    fragment_complete: bool
  }
}
```

Canonical JSON = UTF-8, sorted keys, compact separators, ensure_ascii=False,
allow_nan=False. Coverage is a trusted annotation verified against a separate
reviewer-authored receipt by the runner. Runtime checks content bindings but
cannot authenticate a reviewer. No human approval or cryptographic signature
is implied. Hash validation does not prove semantic completeness.

`source` exact fields:

```
{
  id: arbitrary local string,
  kind: "candidate_fact" | "job_description" | "employer_update" | "preference",
  status: "active" | "withdrawn",
  observed_at: ISO timestamp | null,
  anchor: {sha256, pointer, start, end, quote},
  facts: [proposition]
}
```

All anchors use decoded-string Unicode code point half-open offsets. Runtime
does not load files or parse quote prose. Runner verifies anchors against bound
original files. No filenames, case/answer/example IDs, proposed verdicts, failed
axes, mutation annotations, v2 outcomes or hand-written expected rules reach the
checker. Source IDs/anchors establish provenance, not dispatch keys.

`claim` exact fields: `{id, anchor, stance, readings}`. `readings` is a nonempty
array of alternative propositions (normally one). Multiple simultaneous atoms
are separate claims, NOT alternative readings. Multiple plausible readings
cause needs_review even if one is convenient. Stance is `asserted`,
`recommended_as_fact`, `quoted`, `rejected`, `question`, or `conditional`.
Quoted/rejected/question propositions do not assert world truth. Conditional
assertions are not assumed warranted merely because conditional: without
implemented conditional reasoning they require review.

`proposition` exact fields:

```
{
  subject: string,
  predicate: string,
  object: string,
  polarity: "positive" | "negative",
  modality: "observation" | "self_report" | "requirement" | "permission" |
    "possibility" | "prediction" | "commitment" | "guarantee" | "ability" |
    "evaluation_instruction" | "preference_constraint" | "record_assessment",
  epistemic_scope: "world" | "packet",
  scope: {string: scalar},
  time: {string: scalar},
  measure: null | {kind, unit, lower: number|null, upper: number|null, per: string|null}
}
```

Allowed measure kinds: `count`, `difference`, `rate`, `amount`, `frequency`.
`per` is a symbolic denominator (`day`, `week`, `calendar_month`,
`calendar_quarter`) or null. Empty dimensions mean unspecified, not universal.
No unit/currency conversions; fictional credit is an opaque unit. Reject NaN,
infinity, booleans-as-numbers, reversed intervals, invalid polarity/stance,
unknown fields, duplicate IDs or malformed anchors as invalid. Unknown semantic
predicates/operators may be valid input but must not silently pass.

## Checker operations (semantic policy v1)

Normal assertions compare subject/predicate/object, then epistemic scope,
modality, scope, time, and measure. Preserve the distinctions in result traces.
Predicate registry for this slice:
`distance_saving`, `console_use`, `alert_escalation`, `archive_processing`, `sample_size`,
`ocr_method`, `training_certification`, `evaluation_authority`, `personal_stipend`,
`published_stipend`, `on_call`, `learning_allowance`, `compatible`,
`station_attendance`, `remote_work`, `location_flexibility`, `supersedes`,
`governs`, `resolves`, `observed_after`, `live_captions`, `caption_refusal`, `caption_requirement`,
`meeting_platform`, `written_offer`, `ledger_maintenance`, `training_demo`.

These names describe propositions, never failure categories. Unknown predicates
produce unresolved reasoning/needs_review. Same-predicate matching can support
new names/numbers/IDs and directly grounded claims in the registered vocabulary.

1. Only active evidence available at decision_at is usable. Unknown observation
   time is not by itself disqualifying; future observed_at is excluded. Do not
   confuse observation date with event time. Preserve source limitations: a
   narrower observation cannot support an unrestricted claim. Exact dimensions
   suffice for the first slice; unsupported containment reasoning => review or
   not_established with explicit limitation, never guessed conversions.
2. Direct support requires appropriate modality. No generic numeric ordering of
   modalities. Explicit allowed transitions: identity, self_report -> observation
   only with explanation retaining self_report evidence level; observation ->
   possibility for the same proposition. Commitments, guarantees and their
   conditions must match explicitly; no blanket transition between them. Requirement does NOT support achieved
   observation. A published range does NOT establish a personal award.
3. Same subject/predicate/object and compatible dimensions with opposite
   polarity is counterevidence; if support and counterevidence remain, return
   conflicting. An evidence gap is not a contradiction. Measure mismatch or
   expanded scope alone returns not_established, not a claim about impossibility.
4. Packet-scoped negative `resolves/governs/supersedes/written_offer` can be
   supported by complete reviewed source inventory with no matching positive
   proposition. World-scoped absence cannot. Incomplete inventory => review.
   `observed_at` never creates a supersession/governing edge. Explicit applicable
   facts for these predicates can establish it. Do not call different modalities
   or source dates a conflict without matching subject, scope and time.
   `observed_after` compares source IDs in subject/object by known observed_at
   timestamps only; null dates => review. It asserts no publication/effective date.
5. `evaluation_authority`: no source kind in this data packet grants evaluator
   authority through evaluation_instruction, regardless of the command being
   quoted literally. This is a source-role boundary. Record it in
   the evidence trace; ordinary requirements remain usable as requirements.
6. Preference compatibility: positive `compatible` for candidate/object must be
   checked against an active matching candidate preference, scope and a matching
   role requirement (same predicate/object between preference and requirement).
   A negative `preference_constraint` with `scope.priority=must_have`,
   `scope.quantifier=all` and no exception covers narrower recurring duty timing;
   empty dimensions alone do not imply universality. It conflicts with an asserted
   compatible duty when a positive requirement of that duty exists. An unrelated
   allowance is not permission. Do not hard-code overnight or a benefit name.
7. Frequency permission: explicit candidate ceiling with modality
   preference_constraint and matching object/unit/recurrence contradicts a
   recurring permission that necessarily exceeds it. For same denominator compare
   bounds. For `week` vs `calendar_month`, a full calendar month contains at least
   three full calendar weeks; use this lower bound only, no 4-week conversion.
   For `calendar_month` vs `calendar_quarter`, three months per full quarter.
   If bounds do not establish a violation or scope is ambiguous, needs_review.
   One-off permission is not a recurring schedule.

First slice may conservatively abstain when a rule is not implemented. Preserve
these cases in results; do not force all expected outcomes. Trace support/counter/
limited evidence IDs, mismatched axes and rule(s). Materiality belongs to a
separate policy: for these registered fit predicates in asserted/recommended
claims, definitive unsupported/contradicted claims are material. No materiality
or expected finding flags may be supplied in the normalization input.

## Outputs and aggregation

`check_claim(claim, sources, context)` returns claim-level parse/reasoning status,
`evidence_relation: supported|contradicted|not_established|conflicting|null`,
`verdict: pass|fail|needs_review`, IDs, anchor, evidence IDs, axes, rule, explanation.
Context carries grader, decision_at and source inventory coverage. Preserve null
relation for unresolved interpretation or unsupported checker operation.

`grade_fragment(packet)` returns `{schema, scope:"fragment",
assurance:"manual_normalization_agent_reviewed", verdict:pass|fail|needs_review|invalid,
claims:[...], findings:[...], review_reasons:[...], whole_answer_verdict:null}`.

Fail when a definite material defect is found even if another claim needs review;
otherwise review if any unresolved claim, incomplete/unreviewed coverage or
unsupported conditional semantics; otherwise pass. Coverage hash mismatch or
malformed input => invalid. Pass is always limited to this selected fragment.
Correct unknown-role reasoning may pass. Correct quotes/questions are not world
assertions. Raw unsupported proposition relation may coexist with pass for a
non-assertive stance; explain scope.

## Validation and reporting

Create/freeze normalized data and expectations separately before the measured
run. Review normalization against source spans before predictions. Freeze runtime,
tests, runner, reviewed packets and expectation bytes; write predictions before
reading expectations in measurement. Run once; preserve misses/false rejects/
review and wrong-reason catches. Post-freeze fixes require a successor run/version.

Test boundaries with positive near-neighbors, changed quantities/subjects/polarity,
source withdrawal/future dates, real authority evidence vs bare dates, hard vs soft
preferences, missing/ambiguous parses, coverage drift, arbitrary ID renumbering,
unrecognized predicates and no I/O. Positive controls matter: 13 fails out of 16
cannot establish a useful checker if it simply rejects nearly everything.

Report 13 negative / 2 acceptable / 1 ambiguous fragments separately, per-claim
relations and finding localization, abstentions and invalids, not a whole-answer
accuracy or interview probability. D10/D11 are the same wording in two answers:
they are two records, not two independent semantic observations. Small regression
set and shared-agent review are explicit limitations. SHA receipts are local
integrity evidence, not an external seal.
