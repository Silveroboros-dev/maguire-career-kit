# v4 contract between manual normalization and checker

Keep v3 source/proposition/anchor fields, with explicit additions below. Canonical
entities and objects denote the same property across source/claim/context; do not
use `required`, `maximum`, `two days`, or `candidate minimum` as competing property
objects. Role and candidate subjects remain distinct. Their relation is explicit
in a claim operation rather than accidentally inferred by equal subject strings.
Do not add inferred compatibility facts to sources. Retain self_report, permission,
requirement, guarantee, status, scope and time truthfully. No extraction model.

Packet exact fields: schema=`maguire-claim-packet-v4`, grader, decision_at, sources,
claims, coverage. Coverage/anchors as v3. Every claim has exact fields:
`id, anchor, stance, readings, check`. `check` is null for ordinary direct claims,
or a typed operation below. Normalized author rows use quote instead of anchor.
Preserve all81 claim IDs and original fragment text. No labels/rationales in packets.

Source facts retain the v3 proposition fields. Additional period `calendar_year`
is allowed. Money must have explicit currency unit and period. Annual source text
is calendar_year, not an opaque annual flag. No unknown value becomes zero.
ISO month dates use YYYY-MM in time.start/time.end. Full date/day arithmetic and
calendar-week/month conversion are outside v4; do not assume four weeks/month.

## Direct facts

The v3 comparator remains the baseline. Add two bounded entailments:
1. A positive count of actual events may support a claim of occurrence without a
   number (source lower > 0, count kind, observation/self_report, same property,
   entity, scope and time). Does not turn ability, permission or possibility into
   observed experience. A zero/unknown lower bound does not establish occurrence.
2. `scope.duration_months_lower` on a ledger/event assertion may be computed from
   explicit source time.start/time.end (YYYY-MM). Use elapsed month difference,
   not inclusive endpoint counting; other scope dimensions must match. Dates and
   matching evidence strength stay required. This bound is inclusive; a prose
   'more than a year' uses 13 whole months for integer-month intervals.

Distinct explicitly recurring weekdays may be manually normalized to their count
per week while retaining year and weekday scope. Document this derivation; never
use historical attendance to claim current availability. Do not broaden time.
`alert_triage` can use direct comparison. Unknown qualitative predicates (e.g.
fit_relevance, evidence_sufficiency, subset_of, verification_needed without a
supported check) stay needs_review. Multiple readings/conditional semantics stay
needs_review. Questions/quotes must not hide asserted premises.

## Fact references and derived claims

A reference is `{source_id: string, fact_index: nonnegative int}` into this packet.
Malformed/foreign references are invalid. Source eligibility is active and acquired
no later than decision_at. Ignore observation recency as an authority signal.
Inactive/future operands => needs_review, never pass. Return evidence IDs for all
operands actually used, including supersession facts or competing evidence.

All derived claims require a single reading and honest stance. Comparisons use
modality=record_assessment, epistemic_scope=packet, subject=candidate, object equal
to the canonical property object in both operands, measure=null. scope/time must
retain the relevant conditions; mismatch must not be silently discarded. A check
does not authorize unrelated reading predicates or arbitrary extra fields.
Reading context must include every material offer qualifier and preference
restriction used in the proof. Never pass an unconditional reading from a
conditional operand. Numeric comparisons require equal non-metadata context;
special operations validate their named dimension mappings explicitly. Unknown
extra dimensions => needs_review rather than silently ignored fields.

### constraint

`{op:'constraint', offer:ref, preference:ref}`. Reading predicate is
constraint_satisfied. `offer` must be employer JD/update; `preference` must be a
preference source with modality preference_constraint. Their predicate and object
must match. Offer subject is employer/role, preference subject candidate. Context
must match after dropping preference-only priority metadata. Exceptions are
material restrictions, not bookkeeping, and must be checked. Explicit
on-call window/conditions must be preserved. All source restrictions remain material.

Numeric offer with observation/commitment/requirement and a positive preference:
the entire offered interval must fit within the allowed preference interval.
Entirely outside => contradicted; overlapping/unknown bounds => needs_review.
Do not infer a guaranteed stipend from ability/possibility/request permission.
Frequency unit/per must agree. Money calendar_year/calendar_month may convert
exactly by factor12, as budget equivalence only (not payment timing). Other unit,
period or category conversions => needs_review. Negative no-duty preference versus
affirmative mandatory duty => contradicted when property/window/context match.

Check competing active employer terms for the same property. Explicit employer
supersedes fact (subject=new source ID, object=old source ID, positive and eligible)
may remove old terms. No silence, timestamp or informal possibility supersedes.
Unresolved conflicting terms => needs_review. An explicit supersedes relation is
also still independently checkable as a direct answer claim.
Also inspect all active relevant preference restrictions: the selected reference
does not allow hiding a second prohibition on the same property. Disjoint explicit
weekday windows may be checked as finite sets (weekday = Monday through Friday);
uninterpretable additional restrictions require review. A competing mandatory
weekday shift cannot be hidden by referencing only a permitted Saturday shift.

### permission_limit

`{op:'permission_limit', offer:ref, preference:ref}`. Predicate request_within_limit.
Offer modality permission with an explicit upper limit; preference specifies the
requested count/range. Desired interval must fit the permission envelope and
preserve scope.condition (e.g. manager_approval). This checks that a request is
within a stated limit; it never proves that the request will be granted.

### pending

`{op:'pending', offer:ref, preference:ref}`. Predicate constraint_unresolved or
confirmation_needed. Same canonical property in offer and preference; explicit
offer scope.status is undecided/pending. This supports an uncertainty statement
or advice to verify, not positive compatibility. For advice use stance=advice,
modality=evaluation_instruction, epistemic_scope=packet. Validate the instruction
semantics through this operation; do not auto-pass all advice. Firm competing
terms on the same property prevent silently treating it as unresolved.

### condition

`{op:'condition', offer:ref}`. Predicate condition_required. Packet record_assessment
of a condition on the offer; same canonical property and scope.condition value.
Offer permission/requirement with that explicit condition supports its statement.
An asserted condition absent from the complete eligible inventory is a factual
evidence gap (fail). Incomplete inventory/unknown comparison semantics => review.
Different explicit conditions do not by themselves prove mutual exclusion;
unsupported added condition is a gap unless contrary evidence establishes denial.

### onboarding

`{op:'onboarding', offer:ref, remote:ref, preference:ref}`. Predicate constraint_satisfied.
Offer is station_attendance, object=onboarding, modality=requirement, count days.
Preference same property with upper bound and scope.requires_remote_after=true.
Remote operand is remote_work permission, time.phase=after_onboarding and
object=work_location. Source must explicitly authorize subsequent remote work.
Check offer days inside allowed maximum and the actual permission condition.
No proof of post-onboarding permission => needs_review. Permission is not a
guarantee of a particular remote schedule.

### schedule_before

`{op:'schedule_before', offer:ref, preference:ref}`. Predicate constraint_satisfied.
Both facts predicate=training_demo, same object. Offer is an exhaustive required
schedule (`scope.only=true`) with time.start_minute/end_minute in [0,1440],
time.zone=role_local and explicit weekday. Preference is negative prohibition
after time.after_minute in same zone. End <= cutoff => supported; later end =>
contradicted. Missing exhaustiveness, overnight/cross-zone schedule => needs_review.

## Structural and semantic review

Checker validates operation schema, reference existence, operand source kinds,
canonical property/entity alignment, modalities and context. Unknown operation or
unsupported well-formed dimension => needs_review; malformed data => invalid.
Review binds each quote and fact to raw text, verifies no invented restrictions,
lost conditions, omitted claims or polarity/stance changes, and lists edits in
NORMALIZATION_CHANGES.md. Runtime never parses case IDs, quotes or gold labels.
