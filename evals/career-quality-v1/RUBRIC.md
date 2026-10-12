# Product-quality rubrics — proposed v1

Judge the quality of the analysis, not the desirability of the candidate or role.
A well-supported negative recommendation can be a fully acceptable answer. An
optimistic answer with fabricated evidence cannot. Do not infer hiring probability.

All gold labels are proposed author annotations. Different prose, row ordering,
valid evidence combinations and explicitly allowed next actions are acceptable.
Required points are semantic propositions, never exact-match strings. An allowed
label paired with a contradictory explanation is still wrong. Source IDs and
exact quotes establish traceability, not entailment.

## Candidate → JD

| Criterion | Passing behavior | Failure to identify |
| --- | --- | --- |
| CF-COVERAGE | Substantively assesses every material gold duty; extra prose is harmless | Omits or substitutes a duty; duplicate mention does not restore coverage |
| CF-EVIDENCE | Sources support this exact claim and preserve personal scope, dates and evidence type | Prototype as production, team outcome as personal contribution, wrong or fabricated quote |
| CF-LABEL | supported has relevant sufficient evidence; partial has a real supported subset; unknown lacks enough evidence; contradicted has explicit counterevidence | Inflated certainty, missing evidence treated as inability, a waiver treated as competence |
| CF-SCOPE | Distinguishes minimum, preferred experience, future duty and entry policy | Invented mandatory condition or inferred skill presented as an explicit employer gate |
| CF-UNCERTAINTY | Explains what the supplied sources can and cannot establish | Self-report described as independent verification; excluded/corrected fact reused |
| CF-ACTION | Concrete step addresses the actual gap and states proof limits | Unnecessary task, vague repetition, small exercise claimed to prove production ownership |

An explicit minimum of three years can conflict with an explicit one-year
history. Lack of past operations experience does not prove inability to learn a
future duty. Previous deployment being optional does not establish operations
skill. Currency of evidence must be evaluated against the actual requirement;
an old date alone is not proof that a skill disappeared.

## Role → candidate expectations

| Criterion | Passing behavior | Failure to identify |
| --- | --- | --- |
| PF-COVERAGE | Every material stated preference receives a reasoned assessment | Omits a decisive restriction |
| PF-INTERPRETATION | Preserves the person's threshold, priority and explicit exceptions | Invents flexibility, ignores an allowed exception, changes monthly to weekly |
| PF-EVIDENCE | cited role terms entail aligned/conflict; source scope is respected | Job title or marketing phrase used as proof of actual working conditions |
| PF-UNKNOWN | Silence or unresolved conflicting evidence remains unknown, with a useful question | Invents employer exception, salary offer or team practice |
| PF-PRIORITY | No soft advantage overrides a hard condition without the person's authorization | Pay, prestige or skills fit used to cancel a must-have |
| PF-ACTION | Advice follows the current conditions and candidate-owned options | Unconditional pursuit despite hard conflict, or a claim that an exception is impossible |

Explicit three office days versus zero mandatory office days is a conflict even
when possible employer flexibility is unknown. Conditional clarification may be
reasonable where the scenario permits asking; do not force all conflicts to one
universal action. A later document supersedes an earlier condition only when the
scenario establishes that authority. Date order by itself is insufficient.

## Verdicts and measurement

`pass` means the answer satisfies the case's semantic requirements without a
material error. `fail` requires an evidence-backed finding, not merely different
wording. Severity `major` means a material evaluation or action error; `critical`
means an error that corrupts a decisive requirement, claim or mandatory condition
as specified for the case. Report each finding and its target; do not silently
average a critical error away. A small copy-edit issue is not a failing defect.

When testing a future grader, compare its findings to these annotations only
after the annotations have been reviewed. Keep these denominators separate:

- Incorrect answers accepted / incorrect answers actually evaluated.
- Correct answers rejected / correct answers actually evaluated.
- Intended defects identified / intended defects actually evaluated, by family.
- Ungraded or invalid evaluations / all attempted evaluations.
- Candidate-fit: material-duty coverage, status correctness, supported conclusions,
  invented requirements and actionable advice.
- Preference-fit: missed hard conflicts, invented conflicts, correct treatment of
  unknowns, preserved priorities and permitted actions.

Do not drop omissions from the coverage denominator. A grader infrastructure
failure or abstention is neither an accepted answer nor a candidate's zero score.
These 24 development cases cannot establish general accuracy, outcome uplift or
interview-probability calibration. This package specifies no aggregate score or
statistically validated release threshold.
