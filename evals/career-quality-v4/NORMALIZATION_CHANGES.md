# v4 normalization changes

2026-10-12. This is a manually authored migration of the frozen v3-new-cases
annotations. `migrate_annotations.py` reads predecessor normalized annotations and
the byte-identical v4 raw copies. It does not read gold, predictions, checker code,
or results. `human_approved=false`. A separate semantic reviewer must check these
rows before freeze. The review can establish fidelity to supplied fragments, not
independent truth of the fictional source text or extraction from free prose.

All 40 case IDs, all 81 original claim IDs, and their original quote substrings are
retained. Every direct claim now has `check:null`; typed checks are assigned only
to explicit comparisons. The original fragments and source restrictions remain
the authority for interpreting each annotation. No expected result or failure
label is stored in a normalized row. Annual USD amounts are denominated per
`calendar_year`; this represents annual budget equivalence and says nothing about
payment timing. The underlying source statements remain synthetic.

## Candidate-fit: each proposition

| Case | Source and claim migration |
|---|---|
| CF3N-01 | c1 distance saving unchanged; `check:null`. The one pilot week, self-report basis and 2025 remain. |
| CF3N-02 | c1 console count and c2 personal carton count unchanged; both direct. The team/personal boundary stays explicit. |
| CF3N-03 | c1 triage, c2 escalation and c4 role requirement remain direct; c3 `fit_relevance` remains a separate qualitative unknown, with no invented comparison. |
| CF3N-04 | c1 paper boxes, c2 total boxes and c3 `subset_of` unchanged. The subset statement stays separate from the two counts; no arithmetic alone is used to prove it. |
| CF3N-05 | c1 three-batch sandbox trial and c2 negative production experience unchanged. The latter is a recommended fact with a direct negative reading; no deployment is inferred. |
| CF3N-06 | c1 vendor certificate and c2 demo count unchanged; issuer and 2025 remain. |
| CF3N-07 | c1 panel scoring and c2 chair's final authority unchanged. Candidate non-signatory fact stays in the inventory. |
| CF3N-08 | S1 and c1 now represent recurring Tuesday/Thursday attendance as exactly two days per week; the original scalar weekday scope and 2022 remain. c2 is the distinct 2027 role requirement. c3 relevance and c4 current-availability verification remain qualitative unknowns, so historical attendance does not establish current availability. |
| CF3N-09 | c1 quarterly weekend count unchanged; 2024 and observation modality remain. |
| CF3N-10 | c1 `duration_months_lower` becomes 13, meaning more than 12 elapsed whole months, with 2023-01 and 2024-06 retained. The source has the explicit dates. c2 remains a negative recommended fact about purchase approval; no approval authority is gained. |
| CF3N-11 | c1 evidence-sufficiency stays qualitative; c2 remains unquantified occurrence, now eligible for the bounded positive observed-count entailment from four logged demos. c3 role requirement stays direct. The log does not prove broader teaching capability. |
| CF3N-12 | c1 personal map handling and c2 negative policy-design authorship unchanged. |
| CF3N-13 | c1 attendance at vendor demos and c2 claimed certificate unchanged. Non-completion of an assessment is retained but does not itself prove absence of a certificate; the certificate has no establishing fact in this packet. |
| CF3N-14 | c1 trial OCR and c2 claimed full validation unchanged. Trial status, 14 processed forms and negative larger-collection fact remain separate. |
| CF3N-15 | c1 team total and c2 personal-total claim unchanged; the negative personal processing fact stays explicit. |
| CF3N-16 | c1 historical 2021 escalation and c2 current rota claim unchanged; the negative post-2021 rota fact remains. |
| CF3N-17 | c1 unimplemented estimate and c2 guaranteed implemented saving unchanged; predicted range remains distinct from a guarantee. |
| CF3N-18 | c1 platform ability and c2 assertion of already meeting the live-caption requirement unchanged. Candidate inability and missing captioning service remain separate from the role's all-session requirement. v4 has no operation for this cross-entity ability comparison, so any direct evidence gap is not a demonstrated proof of incompatibility. |
| CF3N-19 | The two readings of c1 remain: support during assigned shifts versus waiting outside them. No reading is silently selected. |
| CF3N-20 | The two readings of c1 remain: joint presentation versus lead presentation. No leadership role is invented. |

## Preference-fit: each proposition

| Case | Source and claim migration |
|---|---|
| PF3N-01 | J01/P01/A share `personal equipment stipend`; $600 and $500 use USD/calendar_year. B is `constraint` over the published amount and candidate minimum. Publication remains observation, not a payment guarantee. |
| PF3N-02 | J02/P02/A share `personal workspace stipend` with USD/calendar_month; B is `constraint` over the entire stated $450–650 interval and $400 floor. |
| PF3N-03 | J03/P03/A share `station attendance`; B is `constraint` over one required day/week and a two-day/week cap. The role and candidate subjects stay distinct. |
| PF3N-04 | J04/P04/A/B share `on-call shift`. The positive Saturday monthly term and cap use `scope.weekday=Saturday`; explicit negative weekday facts are added from both raw sources using `scope.weekday=weekday` (Monday–Friday), preserving the no-weekday restriction. A's “Saturday-only” has `scope.only=true` on the claim, not the source: the raw statement does not expressly exclude Sunday shifts, so that stronger exclusivity is not established. B compares the Saturday term while the checker must inspect the additional same-property restriction. No generic on-call availability is inferred. |
| PF3N-05 | The J05U supersession source and A use exact source IDs J05U→J05; the old three-day and new one-day requirements remain separate. J05/J05U/P05/B/C use `station attendance`; C is `constraint` on the revised fact and candidate cap. B stays a direct statement of the new rule. |
| PF3N-06 | J06 first 30 on-site days is a count on `onboarding`, and its second fact retains permission for `work_location` after onboarding. P06 keeps a 30-day maximum conditional on subsequent remote permission. A uses `onboarding` with all three references; B remains a direct permission statement. No remote-day count or guaranteed schedule is created. |
| PF3N-07 | J07's allowance is `planned`, and its amount is `undecided`; the $1,000 preference is USD/calendar_year. A directly states the undecided amount. B is `pending` with `constraint_unresolved`, preserving that the stated minimum has not been confirmed. No stipend amount is invented. |
| PF3N-08 | A and B remain conditional on a future written offer confirming three remote days. Their two readings, condition scopes, and unset current schedule remain unchanged; no asserted present compatibility check is added. |
| PF3N-09 | J09/A preserve procurement pending and the source's separate current unavailability statement. P09 remains a must-have for team meetings. B is advice with `confirmation_needed` and a `pending` reference; it does not state that captions are provided. |
| PF3N-10 | J10/P10/A/B use the common `learning allowance` property, USD/calendar_year and the original nice-to-have priority. A and B stay direct premises. C stays a question with no asserted eligibility premise. |
| PF3N-11 | J11/P11 use `remote schedule` with the shared manager-approval condition. A is `permission_limit` for a two-day request inside the four-day/week request cap. B is a separate `condition` check. Neither asserts approval or an actual two-day schedule. |
| PF3N-12 | J12/P12/A use `required training demos`. The only required demo is encoded as Wednesday 15:00–16:00 role-local with `only=true`; the candidate's negative after-18:00 restriction is a role-local cutoff. A uses `schedule_before`; its reading retains the weekday, zone and exclusivity, while minute values come from the referenced facts. The offered schedule remains exhaustive only because the raw source says “only.” |
| PF3N-13 | A direct permission and B guarantee claim unchanged. Manager approval and absence of a guaranteed count remain in the source. Permission is not converted to a guaranteed three-day schedule. |
| PF3N-14 | J14N/A use exact negative supersession relation J14N→J14. The informal possibility remains a distinct nonbinding source fact. J14/P14/B use `station attendance`; B is `constraint` against the still active two-day rule and one-day cap. |
| PF3N-15 | J15/P15/A/B share `overnight on-call`. A remains a negative direct assertion while J15 has an affirmative mandatory weekly shift. B is `constraint` between that duty and the candidate's explicit negative prohibition. |
| PF3N-16 | J16's optional platform feature stays distinct from employer action. Its “has not committed” statement is encoded as a negative observation of `caption_enablement_commitment`, not a promise never to enable captions. A remains direct; B is an unsupported future employer commitment under the complete packet. |
| PF3N-17 | J17/P17/A use `personal internet stipend`; $900 uses USD/calendar_year and $200 uses USD/calendar_month. B is `constraint` so the checker must compare budget-equivalent periods. No monthly payment schedule is inferred. |
| PF3N-18 | J18/A keep exam-fee permission up to $1,200 in USD/calendar_year. P18 keeps a distinct $800 USD/calendar_year conference-travel need, and J18's conference-travel exclusion remains negative. B stays a positive direct permission claim; no category conversion is introduced. |
| PF3N-19 | The two readings of “offers” remain possibility after trial versus guarantee. The after-trial agreement condition stays; no reading is selected. |
| PF3N-20 | The two readings of “available” remain advance-request permission versus unconditional guarantee. The all-meetings preference remains separate; no reading is selected. |

## Limits and review focus

The normalizer is manual and outcome-aware in the limited sense that the v3
analysis was available. This is a known-case regression, not blind validation.
Typed references propose proof operands; they are not approvals. The reviewer
should check every added property alignment, weekday restriction, time phase,
status, amount period and negative fact against raw text. In particular, CF03/04,
CF08 relevance/current availability, CF11 sufficiency and PF08 conditional
semantics remain unresolved qualitative reasoning. A structural check can confirm
identity and schema shape; only an independent semantic review can assess whether
these authoring choices faithfully represent the 40 fictional fragments.
