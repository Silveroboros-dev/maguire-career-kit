# Post-run semantic review: frozen v6 on 40 new cases

This is a read-only review of the one saved run, `runs/new-cases-v6`. The run's `FREEZE.json` SHA-256 is `1f60c0a4e5224896c4711fd03b861e65df90dcef697f37db67b279ebfb33615a`; `predictions.jsonl` is `41563ec390401b28c06c303571f19f2cb4dee18b2660ea128a02ec5b910a3554`; `measurement.json` is `223f8e67cac113b416d0b47eebbbd079c3f39d77b22f761ff698582178ee7849`. The saved receipt binds the run artifacts. `python3 -B evals/career-quality-v6-new-cases/pipeline.py verify --output evals/career-quality-v6-new-cases/runs/new-cases-v6` verified all 40 packets and 492 predecessor files with `reran_checker=false`. No cohort grading or data changes occurred during this review.

Gold has 25 supported, 13 erroneous, and 2 ambiguous fragments. Among supported fragments, the checker passed 9, failed 1, and deferred 15. Among erroneous fragments, it passed none, failed 8, and deferred 5. Both ambiguous fragments were deferred. There were no invalid or execution-error rows. The narrow accepted-error count is zero, but 22 of 40 fragments were deferred and only 9 of 25 supported fragments passed. The preference family accounts for 11 supported deferrals and the one false rejection. Intended faulty-claim localization is 7 of 14; one bad fragment, PF6H-06, was rejected solely for a correct clause. Review is neither error detection nor acceptance.

The main interpretive limit is at the annotation/runtime interface. All 11 typed checks returned `operation_shape` before reaching their comparison logic. Their packet readings use an object such as `stipend` or `station_attendance` where the frozen operation requires the exact offer object; several operand objects and contexts also do not match. These are normalization-contract mismatches, so this run does not measure how well the frozen numeric, schedule, or condition operations would reason over canonical packets. Four clauses contain multiple conjunctive propositions in `readings`; the frozen checker treats multiple entries as alternative readings and defers them. Other faithful concepts are outside its direct predicate registry. No post-run repair or rerun is warranted under this frozen contract.

## Every reviewed or mismatched fragment

| Case | Gold → measured | Claim-level assessment |
| --- | --- | --- |
| CF6H-05 | review → review | `c3` is qualitative onboarding transferability; `unknown_predicate` correctly leaves it for review. |
| CF6H-09 | pass → review | True cutover observation `c2` uses `cutover_observation`, outside direct coverage. |
| CF6H-15 | review → review | `c2` is qualitative preparation for customer demos; `unknown_predicate` is an appropriate deferral. |
| CF6H-16 | pass → review | True pending-certificate status `c2` uses `certificate_status`, outside direct coverage. |
| CF6H-17 | fail → fail | Faulty personal vendor coordination `c2` was found. True checklist documentation `c1` was deferred as an unknown predicate. |
| CF6H-18 | pass → review | `c1` faithfully covers both tool building and staff use, but two conjunctive readings trigger `alternative_readings`; this is a normalization-interface mismatch. |
| CF6H-19 | pass → review | True peer review of a guide `c2` uses `guide_review`, outside direct coverage. |
| CF6H-20 | fail → review | Both the true 2024 personal count `c1` and false 2025 personal attribution `c2` use `incident_handling`, outside direct coverage; the faulty claim was not localized. |
| PF6H-01 | pass → review | True five-day induction fit `c2` uses an unregistered `station_attendance_fit` assessment. The direct station and remote premises passed. |
| PF6H-02 | fail → review | Faulty allowance-fit `c2` stopped at `operation_shape`; its 1,200-versus-1,800 comparison was never evaluated. |
| PF6H-03 | pass → review | Supported Saturday-only/weekday-ban fit `c2` stopped at `operation_shape`. |
| PF6H-05 | pass → review | Both careful statements about conflicting active attendance terms use unregistered assessment predicates; neither falsely settles the current rule. |
| PF6H-06 | fail → fail | Correct historical statement `c1` was falsely rejected because normalization encoded a withdrawn draft's listing as a role-level stipend commitment; the worker excludes the withdrawn source. Faulty current-fit `c2` stopped at `operation_shape`. This is a source-fidelity defect missed before freeze, and the fragment rejection gives no intended-error localization. |
| PF6H-07 | pass → review | Supported Tuesday cutoff fit `c2` stopped at `operation_shape`; the stated schedule `c1` passed. |
| PF6H-08 | pass → review | Supported annual/monthly budget equivalence `c2` stopped at `operation_shape`; true unspecified reimbursement schedule `c3` uses an unregistered predicate. |
| PF6H-10 | pass → review | True first-quarter and possible later travel `c1,c3` use unregistered `business_travel`; fit `c2` stopped at `operation_shape`. |
| PF6H-11 | fail → fail | The false one-day requirement `c1` was detected. The false fit against a two-day requirement `c2` stopped at `operation_shape`, so only one of two faulty claims was localized. |
| PF6H-12 | pass → review | The true written four-day pattern and Friday fit `c1,c2` use unregistered work-pattern predicates. |
| PF6H-13 | fail → review | `c1` combines tentative feasibility with an unsupported assertion that a manager decides; the source names the team. Two conjunctive readings trigger `alternative_readings` before that authority error is tested. |
| PF6H-14 | pass → review | Supported CHF 100-versus-CHF 80 stipend fit `c2` stopped at `operation_shape`; the direct offer premise passed. |
| PF6H-15 | fail → review | The direct three-trip requirement `c1` uses unregistered `overnight_travel`; false two-trip fit `c2` stopped at `operation_shape`. |
| PF6H-16 | pass → review | Supported onboarding cap `c2` stopped at `operation_shape`. `c3` faithfully includes role permission and candidate acceptance, but their two conjunctive readings trigger `alternative_readings`. |
| PF6H-17 | fail → review | Correct supersession and four-day premises `c1,c2` passed; false fit with a three-day cap `c3` stopped at `operation_shape`. |
| PF6H-18 | pass → review | True acceptance of the internal demo `c2` uses unregistered `demo_presentation_fit`; the monthly requirement and absence of public demos passed. |
| PF6H-19 | pass → review | `c2` includes true Saturday/Sunday no-duty premises plus fit assessments; multiple conjunctive readings trigger `alternative_readings`. |
| PF6H-20 | pass → fail | The careful possibility `c1` uses an unregistered predicate. Advice to confirm approval `c2` was encoded as direct `confirmation_needed` with no supporting proposition, so the worker returned `evidence_gap` and falsely rejected the supported answer. This is an annotation/coverage interaction, not evidence that Portugal is disallowed. |

The other 14 fragments matched gold without any reviewed clause. In particular, CF6H-02, CF6H-07, CF6H-10, CF6H-13, and PF6H-09 had their faulty claims directly rejected; their sound premises passed.

## Faulty-claim localization

| Bad case | Intended faulty claims | Flagged | Assessment |
| --- | --- | --- | --- |
| CF6H-02 | `c2` | `c2` | Personal attribution from a team result detected. |
| CF6H-07 | `c2` | `c2` | Permission did not establish delivery. |
| CF6H-10 | `c1` | `c1` | Sandbox use did not establish production use. |
| CF6H-13 | `c2` | `c2` | Withdrawn, incorrect author record did not support guide authorship. |
| CF6H-17 | `c2` | `c2` | Team coordination did not establish candidate coordination. |
| CF6H-20 | `c2` | none | Unregistered incident-handling predicate caused review. |
| PF6H-02 | `c2` | none | Derived comparison stopped at shape. |
| PF6H-06 | `c2` | none; `c1` falsely failed | Historical draft was misrepresented by normalization; derived fit stopped at shape. |
| PF6H-09 | `c2` | `c2` | Pending procurement did not establish a first-day guarantee. |
| PF6H-11 | `c1,c2` | `c1` | Wrong required count detected; derived fit stopped at shape. |
| PF6H-13 | `c1` | none | Conjunctive readings prevented authority assessment. |
| PF6H-15 | `c2` | none | Derived comparison stopped at shape. |
| PF6H-17 | `c3` | none | Derived comparison stopped at shape. |

This is a contract-informed, agent-authored challenge cohort with repeated reasoning families and no human approval. It cannot support a paired improvement claim against an older, different cohort or a claim that the checker generalizes to arbitrary career prose. The run is useful evidence that the source-to-packet contract needs clearer canonical examples and a representation for multi-fact claims before these cases can measure the intended comparison operations. Any such repair belongs to a new version with new data and a new run, preserving this frozen result.
