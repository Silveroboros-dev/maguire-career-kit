# V6 normalization changes and source audit

2026-10-12. This is an exposed repair of the same 40 fictional v5-new cases.
The author read the prior v5 analysis/results and v5 checker behavior. The v6
40-packet predictions have not been run or inspected. All annotations and this
audit are agent-authored; `human_approved=false`. No raw answer, source text,
gold label, claim ID, quote, stance, predicate, object, polarity, numeric bound,
or fact reference was changed. The exact 61 claim ID/quote pairs and 40 source
inventories are retained. Candidate-fit propositions are byte-equivalent to v5;
only its file-level schema/exposure declaration changes.

Paths below use `/rows[case_id=...]/sources[id=...]/facts/N` or
`/rows[case_id=...]/claims[id=...]/readings/N`. `scope.* -> time.*`
means remove the former key and put the same literal value at the latter path.
The row/claim identifiers make each path stable even if JSON list order changes.

| Case | Exact old → new paths | Raw-text reason |
|---|---|---|
| PF5H-03 | `claims[c1]/readings/0/scope.condition="manager_approval"` → `scope.remote_condition="manager_approval"` | Approval qualifies remote work *after* onboarding; two mandatory station days have no approval condition. The condition remains visible in the derived answer. |
| PF5H-05 | `sources[s1]/facts/0`, `sources[s2]/facts/0`, and `claims[c1]/readings/0`: `scope.weekday="Saturday"` → `time.weekday="Saturday"`; `scope.window_start_minute`/`scope.window_end_minute` → `time.start_minute`/`time.end_minute`, preserving 660/780 for offer and reading and 600/840 for allowed preference. `sources[s2]/facts/1/scope.weekday_set="Monday-Friday"` → `time.weekday="weekday"`. `claims[c1]/readings/0/scope.only`: absent → `true`. | Source states the *only* shift is Saturday 11:00–13:00 in role-local time; preference accepts Saturday 10:00–14:00 but forbids Monday–Friday duty. The answer's no-weekday assertion depends on exhaustiveness. No day or minute value was altered. |
| PF5H-06 | `sources[s1]/facts/0`: Sunday and 660/780 window move from `scope` to `time`; `sources[s2]/facts/0` and `claims[c1]/readings/0`: `scope.weekday="Sunday"` → `time.weekday="Sunday"`. `claims[c1]/readings/0/time.start_minute/end_minute`: absent → 660/780. | The employer mandates a narrow Sunday 11:00–13:00 window every week, while the candidate bans *all* Sunday on-call duty. The reading now retains the offer window; the source prohibition remains whole-day, without invented window bounds. Weekly frequency stays on the offer. |
| PF5H-09 | `sources[s1]/facts/0/modality`: `possibility` → `observation`; `scope.status="pending"` unchanged. | “Still undecided; no amount has been approved” observes the allowance's pending status. It does not assert a possible or guaranteed payment. The separate negative approved-amount fact remains. |
| PF5H-11 | `claims[c1]/readings/0/scope.only`: absent → `true`. | “No other travel” exhausts this role's Basel client-site travel inventory. The reading still keeps Basel, this-role scope, one day per calendar month, and the two-day cap. |
| PF5H-17 | `sources[s1]/facts/0`, `sources[s2]/facts/0`, `claims[c1]/readings/0`: `scope.weekday="Wednesday"` → `time.weekday="Wednesday"`; `claims[c1]/readings/0/scope.only`: absent → `true`. | The source says the only required Wednesday demo is 09:00–12:30, and the ban begins after 13:00 in the same role-local zone. Existing minute values and zone remain. |
| PF5H-18 | The three parallel offer/preference/reading paths move `scope.weekday="Tuesday"` → `time.weekday="Tuesday"`; `claims[c1]/readings/0/scope.only`: absent → `true`. | The only required Tuesday demo ends at 15:00, beyond the 14:00 cutoff. The answer omits “only,” but the derived comparison still depends on the source's exhaustive schedule. Minute values and zone remain. |
| PF5H-20 | `sources[s1]/facts/1/modality` and `claims[c2]/readings/0/modality`: `possibility` → `observation`; pending status unchanged. | “Procurement is pending” reports status. The separate current unavailability remains a negative observation with `status=available_now`, and no activation date remains a negative observation. The first-day preference and advice keep `time.phase=first_day`; this does not imply first-day availability. |

The case paths in this table are under `/rows[case_id=...]/`. Every other
proposition is unchanged. For each other case, the source-level audit retained
these boundaries:

| Cases | Source-faithful boundary retained |
|---|---|
| CF5H-01–04 | Ledger duration and weekly handoffs; shadowing permission versus demo presentation; personal review facilitation/owners versus role requirement; alert triage versus SRE escalation. |
| CF5H-05–08 | Recorded-caption testing versus live operation; former employer permission versus current role; OCR experience versus certification; engineering signoff on pilot cutovers. |
| CF5H-09–12 | Candidate CISSP denial versus role requirement; candidate escalation versus lead decisions; personal lab only versus production and role requirement; two processed of five archive boxes. |
| CF5H-13–16 | Contradictory active authorship sources, including Jo as the second source's positive author; written bilingual guides versus live onboarding; team 30% triage reduction and absent individual attribution; pilot rollback plans versus production use. |
| CF5H-17–20 | Withdrawn certification draft versus active course/exam correction; synthetic sandbox SQL versus production customer database; two French and two English onboarding sessions; pilot runbook, three trained operators, and no production use. |
| PF5H-01–02 | Annual/monthly course-fee budget equivalence versus conference-only allowance. |
| PF5H-04, PF5H-07–08 | Conditional remote approval remains unapproved; request limits retain manager approval, probation phase, and no approval claim. |
| PF5H-10, PF5H-12–16 | Competing live onboarding terms; paid post-probation leadership hours; explicit signed supersession; superseded four-day term; committed stipend versus unapproved possible stipend. |
| PF5H-19 | The blanket remote-work prohibition remains in the source inventory with `status=withdrawn`; the Friday permission is active and retains supervisor approval. The withdrawn term is not an active conflict. |

The unchanged CF5H-19 bilingual summary fact is a finite manual reading of two
French and two English sessions, not a claim of separate simultaneous bilingual
sessions. Qualitative transferability in CF5H-05 remains unsupported by the
bounded predicates. PF5H-04 stays conditional and PF5H-10 preserves
contradictory active terms; no normalization was changed to force a pass/fail outcome.

## Byte binding

| File | v5-new SHA-256 | v6 SHA-256 |
|---|---|---|
| `raw/candidate-fit.json` | `8ddcce7a7a0cdc9e9986dbc68eec5b4b436dc31b5b6cbda02d786f3a041404b5` | same |
| `raw/preference-fit.json` | `7dbdd88b9c0cbb83e23e7aacba554f0a65b175eb4dac3d861ce14a0913fdfff0` | same |
| `gold/candidate-fit.json` | `e9da4250f0c486a4b1d0340f5a378a2c63f60d6e063f397862f828e6465c0718` | same |
| `gold/preference-fit.json` | `a0d0d6651b581af6977d2b0e636ad8b5aea0eb72e894f9169f20a8ddc4dace94` | same |
| `normalized/candidate-fit.json` | `db3457cf314f3cf5e59b26ebeb6da17707ccfa256c4b8a1d00dd9cbb35df05eb` | `5ff8dea2ea5c5e2d2040329e5c2366d1f9bcf334d27688cde905dd9bec6ff460` |
| `normalized/preference-fit.json` | `67c13fdf43f59d1f2d712e0c8bff5b4bf3d8b1ca630a0c44b3291fc12f3d7821` | `dd7d54a3620e93c051e5f0d20c1f340fd85b19f2d2f4556c540686a02cf771ed` |

The v6 normalized hashes above are also listed in
`normalization_attestation.json`, which binds this change log and `SCHEMA.md` by
SHA-256 and byte count. The hashes are local integrity metadata, not external
signatures or a substitute for the independent semantic review.
