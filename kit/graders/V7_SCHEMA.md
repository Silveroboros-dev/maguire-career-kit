# V7 normalized input and checker contract

V7 reuses the v6 source, proposition, claim, anchor, and coverage fields. Author
files use `maguire-v7-normalized`; projected packets use
`maguire-claim-packet-v7`. A proposition has exactly `subject`, `predicate`,
`object`, `polarity`, `modality`, `epistemic_scope`, `scope`, `time`, and `measure`.
`readings` are alternative interpretations of **one** claim. Simultaneous facts
are separate claims, each anchored to an exact substring of its original claim.
The checker never reads answer prose, case IDs, gold, or normalization rationale.

## Canonical identity and derived assertions

For a typed comparison, both operands name the same semantic property in
`predicate` **and** `object`. The object is the property (for example,
`transport`, `required_trips`, or `station_attendance_after_onboarding`), not
"offer" versus "minimum", "old" versus "current", or an amount. The reading
uses that same object. Source provenance and status distinguish old from current
terms; the measure carries quantity, unit, bound, and period. `scope` contains
only material qualifiers such as category, phase, condition, location, and
exhaustiveness. Numeric operand values do not appear in `scope`. `time` holds
the material phase, year, weekday, or explicit local window. These dimensions
cannot be silently dropped or filled by the checker.

The existing operations are `constraint(offer,preference)`,
`permission_limit(offer,preference)`, `pending(offer,preference)`,
`condition(offer)`, `onboarding(offer,remote,preference)`, and
`schedule_before(offer,preference)`. Each operand is exactly
`{"source_id":str,"fact_index":nonnegative_int}`. A supported derived
comparison has exactly one reading with subject `candidate`, positive polarity,
`record_assessment` modality, `packet` epistemic scope, null measure, and the
operation's registered predicate. Advice is allowed only where the operation
explicitly defines it. The reading carries the offer's scope and time exactly,
except for the named pending, onboarding, and schedule relations inherited from
v6. For `constraint`, the preference has the same context and time, except the
documented exhaustive window/whole-day relations. An offer's `only=true` stays
in the reading and may be absent from the candidate preference. These
structural requirements are checked by `validate_packet` before grading;
semantic compatibility and evidence still require grading.

An undated positive standing preference (`time={}`) may compare with a dated
offer phase; the reading must retain the offer time, so the result is scoped to
that phase. A `written_offer:true` qualifier on an offer may be absent from the
preference but stays in the reading. An active source's
`offer_inventory:"current"` similarly scopes a listed absence to the current
offer package, and stays in the reading. No other offer-only qualifier is
dropped.

An explicit current negative observation of a property with null measure
contradicts a positive numeric preference whose lower bound is above zero,
when object, material context, and time align and no competing active term
exists. This evaluates the current package only when its source carries
`offer_inventory:"current"`. A
withdrawn positive draft does not become current evidence. A replacement term
is identified by an eligible `supersedes` fact whose subject is the update
source ID and object is the superseded source ID.

## Historical source content

`{"op":"source_statement","source":REF}` asks whether a named document
said a proposition, not whether that proposition governs the current offer.
The one reading uses the **source ID** as subject and `packet` epistemic scope;
its predicate, object, polarity, modality, scope, time, and measure represent
the stated proposition. A referenced source may be withdrawn, but must have
been observed by the decision time. The exact referenced fact must match.
A wrong amount, polarity, condition, or source fails only when reviewed source
inventory is complete; missing or future evidence stays review. This operation
cannot support a current employer commitment.

## Advice about an explicit unknown

`{"op":"confirm_unknown","unknown":REF,"field":"approved_country_list"}`
is the bounded country-approval advice relation. The referenced active employer
`remote_work` permission must explicitly contain
`scope.approved_country_list="unspecified"` and be observed by the decision
time; an explicitly superseded source cannot support the advice. Its reading
has stance `advice`, subject `candidate`, predicate
`confirmation_needed`, object `country_approval`, positive polarity,
`evaluation_instruction` modality, `packet` epistemic scope, null measure,
`scope={"location": NONEMPTY_COUNTRY, "approval":"unknown"}`, and the same
time as the source fact. The rule supports asking for confirmation only. It
does not establish that the country is approved, that permission was granted,
or that the candidate can work there. An explicit active term for the named
country, whether approving or denying it, makes this unknown-field advice
`needs_review` because the country-specific status is no longer unresolved by
the referenced list alone. Any asserted permission or claimed
availability must use a different rule and evidence.

Unknown direct predicates, qualitative fit/transferability, unresolved
conditions, and noncanonical relations retain `needs_review`. Direct actions
still require eligible evidence with matching subject, object, context,
polarity, modality, and measure. The structural validator checks supported
operation shape without assigning any verdict.

The concrete direct predicates added to the inherited v3 registry are
`handoff_recording`, `demo_presentation`, `incident_review_facilitation`,
`follow_up_documentation`, `vendor_cutover_coordination`, `kubernetes_use`,
`plan_drafting`, `plan_review`, `guide_writing`, `triage_time_reduction`,
`rollback_plan_writing`, `rollback_plan_documentation`, `course_completion`,
`certification_exam`, `sql_query`, `client_onboarding`, `runbook_writing`,
`operator_training`, `activation_date_promised`, `incident_handling`,
`cutover_observation`, `certificate_status`, `checklist_documentation`,
`tool_building`, `pilot_use`, `guide_review`, `business_travel`,
`overnight_travel`, `work_pattern`, `reimbursement_schedule`, and
`remote_work_approval_authority`. The packet-level derived predicates are
`constraint_satisfied`, `request_within_limit`, `constraint_unresolved`,
`confirmation_needed`, and `condition_required`; `alert_triage` and `stipend`
are also registered as concrete direct predicates. Registration does not make
a proposition true and does not grant qualitative fit status.
