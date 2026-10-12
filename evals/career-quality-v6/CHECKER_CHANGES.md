# V6 checker changes

This local checker accepts `maguire-claim-packet-v6`. `v3_core.py` is unchanged.
The direct predicate registry now names concrete actions in the exposed candidate
cases: handoff recording, demo presentation, incident review facilitation and
follow-up documentation, vendor cutover coordination, Kubernetes use, plan
drafting/review, guide writing, triage time reduction, rollback plan writing and
documentation, course completion and exam, SQL querying, client onboarding,
runbook writing, operator training, and activation-date promise. Registration
does **not** assert these facts. The existing direct comparator still requires
eligible source evidence with matching subject, object, polarity, scope, time,
epistemic scope, compatible modality, and measure. A team outcome cannot prove
personal achievement; sandbox activity cannot prove production experience;
permission or ability cannot prove observed conduct. Fit relevance and skill
transferability are unregistered and remain `needs_review`.
For positive event counts, an eligible explicit denial of that same event with
no count contradicts any asserted lower bound above zero; a simultaneous
positive counted record makes the evidence conflicting instead. This does not
interpret missing counts as zero.

For candidate plan authorship, the checker explicitly inspects eligible positive
and negative candidate-authorship records for the same plan and contribution
context. Opposing records return `authorship_conflict` with both evidence IDs;
a third party's authorship alone does not establish exclusive authorship.

Preference comparisons add only named relations. A documented whole-day ban
covers a mandatory narrower window on the same canonical weekday and zone;
weekday means Monday through Friday. An exhaustive offered window fits a
positive allowed window only if the offered weekdays and every minute are inside
it. The reading must retain the offered window and `only=true`; unknown time or
scope dimensions defer to review. A source's `only=true` is an exhaustive offer
qualifier, so a numeric preference may omit it while the reading must retain it.
The existing numeric bound and period rules still apply.

Onboarding compares station attendance days with the candidate limit and a
separate post-onboarding remote permission. A condition on that permission must
appear as `reading.scope.remote_condition`; it is never attributed to station
attendance. A conditional remote permission also needs an eligible positive
candidate remote-work preference accepting that exact condition and phase;
missing, negative, untimed, or competing terms on that property defer to review.
Mere remote possibility
does not satisfy the operation. The schedule cutoff operation now requires an
actual Monday–Sunday `time.weekday`, same-zone minute fields,
and exhaustive `scope.only=true`. Pending status may coexist with an observed
current unavailability; a first-day need is retained in the advice reading's
time. This supports verifying an unresolved condition, not claiming activation,
approval, a guarantee, or suitability.

Unresolved limits: the registry handles manually normalized propositions, not
raw extraction or semantic paraphrases. Noncanonical or unknown dimension
relations require review. Conditions other than the named remote/onboarding and
weekday/time relations are not generalized. Qualitative fit and transferability,
and conditional reasoning outside these named operations, remain for review.

Verification: `python3 -B -m unittest discover -s evals/career-quality-v6/tests
-p 'test_v6_checker.py' -v` uses invented fixtures only. No v6 target packet
was passed to `grade_fragment` before freeze. The 40 target cases were not used
for predictions while developing this checker.
