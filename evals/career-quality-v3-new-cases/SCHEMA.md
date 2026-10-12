# Author packet: typed claims and raw fictional source snapshots

Author only your assigned family (candidate-fit or preference-fit). Do not read
other eval folders or import/check runtime. Write files through author_support.
Keep text English (matching prior language) and short, clear, realistic. Do not
reuse names or answers from prior work. No real candidate/employer data.

Each scenario includes raw source text and one selected short answer fragment;
one case may contain multiple simultaneous claims. A fragment is not a complete
career assessment. All material claims inside it must be normalized. Prefer
1–3 claims, avoiding an unreviewable ontology or excessive narrative.

Source fields: id, kind (`candidate_fact`, `job_description`, `employer_update`,
`preference`), status (`active`, `withdrawn`), observed_at (ISO timezone timestamp
or null), text. This is observation/acquisition time, never publication/effective
time unless the text separately establishes that. Source facts reflect what is
actually asserted, including self-report, conditions, quantities and limits.
Do not turn a JD obligation into the candidate's achievement. Candidate facts
must retain their actual evidence level.

Proposition fields (all present):
```
subject: string
predicate: string
object: string
polarity: positive | negative
modality: observation | self_report | requirement | permission | possibility |
          prediction | commitment | guarantee | ability | evaluation_instruction |
          preference_constraint | record_assessment
epistemic_scope: world | packet
scope: object with scalar values only
time: object with scalar values only
measure: null | {kind,unit,lower,upper,per}
```
Measure kind: count/difference/rate/amount/frequency; lower/upper finite number
or null; per null/day/week/calendar_month/calendar_quarter. Unspecified values
are not zero, infinite scope or known absence. Unit is an opaque string.

Vocabulary available for CLAIM predicates (source facts may have additional
faithful predicates): distance_saving, console_use, alert_escalation,
archive_processing, sample_size, ocr_method, training_certification,
evaluation_authority, personal_stipend, published_stipend, on_call,
learning_allowance, compatible, station_attendance, remote_work,
location_flexibility, supersedes, governs, resolves, observed_after, live_captions,
caption_refusal, caption_requirement, meeting_platform, written_offer,
ledger_maintenance, training_demo. Use a shared canonical entity/predicate for
semantically equivalent references; never choose predicates to encode expected
error categories or create fake mismatches.

Claim: id, quote (exact nonempty unique substring of answer.text), stance,
readings. Stance: asserted/recommended_as_fact/quoted/rejected/question/conditional.
Readings is [proposition] normally. Multiple plausible readings of ONE phrase
are alternative propositions in the same claim. Simultaneous atoms are different
claims. Questions/quotations may embed asserted premises; split those separately.
Do not label a bad assertion as quoted merely to match a desired gold outcome.

Preference conventions: scope.priority=must_have|nice_to_have, scope.exceptions
boolean only when explicit; scope.quantifier=all for an explicit universal ban.
Other role/team/time/conditions remain separate scope/time keys. Recurring
frequency can use time.recurring=true and measure.per. `observed_after` uses
source IDs in subject/object and epistemic_scope=packet. Do not use publication
predicates unless an ambiguous reading must explicitly preserve that uncertainty.

Authoring function shape:
```
case(id, title, sources=[source(..., facts=[p(...),...])],
     answer="...", claims=[claim(...)], expected="pass|fail|needs_review",
     reason="reference semantic rationale", error_claim_ids=[...],
     review_reason=null or explanation, tags=[...])
```
Expected is a manual meaning judgment, not a prediction of runtime. For each
fail, list actual faulty claim IDs; for pass/review this list is empty. Each
family must have exactly 12 pass, 6 fail, 2 needs_review. Include positive
transformations (e.g. narrower valid scope, justified quantitative bounds,
direct explicit terms, constrained recommendations), not only literal restatements.
Negatives should retain correct evidence/premises where useful. Mark uncertainty
honestly; do not invent current policy, market prices, probability or facts.

Save source authoring script `author_candidate.py` or `author_preference.py` and
call save_family("candidate-fit"|"preference-fit", cases, exposure). These scripts
and helper are data authoring only, never runtime. Run Python -B to avoid pycache.
Report case counts, family coverage, unresolved interpretations, exposure.

Pre-run annotation-review addendum (2026-10-12): if the listed vocabulary cannot
faithfully express an explicit assertion (such as relevance, a subset relation,
or evidence sufficiency), retain it as a distinct claim with an honest additional
predicate. Do not omit it or fabricate a matching source fact. Unknown runtime
support is an evaluation outcome, not grounds to change a semantic gold label.
This refinement was made before any new-case prediction; it does not change v3.
