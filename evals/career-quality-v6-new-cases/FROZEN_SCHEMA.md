# V6 normalized input contract

This is a manual, agent-authored normalization of the same 40 fictional raw
source/answer cases as `career-quality-v5-new-cases`. The 61 existing claim IDs
and exact answer quotes are fixed. Raw and gold files are copied byte for byte.
The cohort and v5 outcomes are known to the authors; this is an exposed
development regression. No v6 target predictions are available during editing.
`human_approved=false` throughout. The packet projected by `pipeline.py` uses
`schema=maguire-claim-packet-v6`; author files use
`schema=maguire-v6-normalized`.

## Author file shape and provenance

Each family file has `schema`, `family`, `human_approved`, `exposure`, and 20
`rows`. A row has `case_id`, `sources`, and `claims`. Source IDs exactly match the
raw row. Each normalized source has `id` and nonempty `facts`. Claim rows have
`id`, `quote`, `stance`, `readings`, and `check`. Each quote is an exact unique
substring of its raw answer. `check=null` marks a direct claim. A typed check
references source facts by `{source_id, fact_index}`. The pipeline adds raw source
and answer anchors, source kind/status/timestamp, decision time, and coverage.
No label, expected result, rationale, or prediction enters a packet.

The exposure object says old checker code, cases, and v5 results were seen;
`v6_predictions_seen=false` is the relevant prospective assertion. The separate
attestation binds exact bytes of both normalized files and these documents.

## Proposition and source interpretation

Every fact/reading uses exactly `subject`, `predicate`, `object`, `polarity`,
`modality`, `epistemic_scope`, `scope`, `time`, and `measure`. A measure, when
present, has `kind`, `unit`, `lower`, `upper`, and `per`. `null` bounds are unknown,
never zero. Canonical day unit is `day`. Money has an explicit currency and
calendar period. Year-only source text uses `time.year`; month dates use YYYY-MM.
No source text is treated as an instruction to the grader.

Identity and attribution are literal. Candidate, role, team, and named people
are distinct subjects. A team outcome does not establish personal contribution;
permission to shadow does not establish presentation; sandbox activity does not
establish production activity. A withdrawn draft is not active evidence.
Observation, self-report, permission, requirement, preference, possibility,
commitment, and guarantee are distinct modalities. Pending procurement is an
observed *status*, not a promise of availability, approval, or payment.

The direct comparator may handle documented concrete predicates with exact
entity, object, scope, time, polarity, modality, and measure checks. Positive
actual counts may support unnumbered occurrence, but permission or possibility
cannot. Explicit YYYY-MM start/end can support an integer elapsed-month lower
bound; no date precision is invented. Source conflicts remain visible. Qualitative
transferability (`fit_relevance`) stays `needs_review`; a direct predicate name
alone cannot turn an opinion into a fact. An unknown or unsupported well-formed
predicate/dimension requires review; malformed structure is invalid.

## Named context relations for derived checks

All derived readings have subject `candidate`, epistemic scope `packet`,
measure `null`, and the operation's stated predicate/modality. They retain every
material qualifier used to make the answer: phase, role, location, category,
approval condition, weekday, time window, status, and exhaustiveness. Matching
is operation-specific, not a generic subset or string-equality shortcut.

* `constraint`: compares a concrete employer term with a candidate preference
  for the same canonical property. Numeric offer bounds must fit the preference
  interval. Budget amounts in the same currency can be converted between
  calendar year and calendar month by exactly 12 only as budget equivalence;
  this proves no payment schedule. No foreign-exchange conversion is supported.
  `scope.only=true` on a finite offer inventory is retained in
  a reading even when a preference is broader. Relevant competing terms and
  all active restrictions must be inspected; explicit `supersedes` resolves an
  older term, while mere recency does not.
* For `on_call`, `time.weekday` is one named day or `weekday` (Monday through
  Friday). `time.start_minute`/`end_minute` define a role-local half-open offer
  or allowed window. A negative preference with the weekday and no minutes bans
  that whole day; a narrower mandatory window on that day remains prohibited.
  An exhaustive Saturday-only offer can be shown disjoint from a weekday ban.
  Missing/unknown weekday, zone, window, or exhaustiveness cannot be presumed.
* `permission_limit` checks that a requested count fits a stated permission cap
  under the same explicit condition and phase. It does not imply approval.
* `onboarding` compares required station days with a cap and separately checks
  permission for remote work after onboarding. It also requires an explicit,
  active candidate `remote_work` preference accepting the same condition and
  after-onboarding phase. Missing, negative, or competing candidate acceptance
  requires review. `scope.remote_condition` in the reading names the remote
  permission condition; it does not attach that condition to station
  attendance. A possible future approval remains possible.
* `schedule_before` compares an exhaustive required training demo with a
  same-weekday, same-zone after-time prohibition. Canonical `time.weekday` is
  an actual named day from Monday through Sunday, not the `weekday` set token;
  `scope.only=true` is retained in the reading. End time at or
  before cutoff supports; later end contradicts. Cross-zone, overnight,
  nonexhaustive, or imprecise schedules require review.
* `pending` interprets an observed `scope.status=pending` employer term against
  a concrete preference. `confirmation_needed` is advice to verify a pending
  status, not a positive fit decision. A negative `available_now` fact and a
  pending procurement fact can coexist. `time.phase=first_day` on a preference
  and reading stays material even when the pending offer has no date. No pending
  status supplies a first-day activation promise.
* `condition` checks an explicit condition on a permission or requirement. It
  cannot manufacture a condition absent from complete eligible source inventory.

The bounded checker implementation owns exact admissible predicate and dimension
lists. Unsupported qualitative fit, transferability, unapproved future outcomes,
uninterpretable qualifiers, contradictory sources, and mismatched context remain
review cases. The schema does not claim to parse arbitrary career prose or infer
unstated compatibility.
