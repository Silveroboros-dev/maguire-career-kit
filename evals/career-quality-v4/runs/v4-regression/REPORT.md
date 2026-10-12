# v4 known-case regression

Unchanged raw fragments and gold; revised manual normalization and checker. Not an independent holdout.

| Family | Good: pass / fail / review / invalid | Bad: pass / fail / review / invalid | Ambiguous: pass / fail / review / invalid |
|---|---|---|---|
| candidate-fit | 8 / 0 / 4 / 0 | 0 / 6 / 0 / 0 | 0 / 0 / 2 / 0 |
| preference-fit | 6 / 1 / 5 / 0 | 0 / 6 / 0 / 0 | 0 / 0 / 2 / 0 |
| all | 14 / 1 / 9 / 0 | 0 / 12 / 0 / 0 | 0 / 0 / 4 / 0 |

Missed accepted errors: none.

False rejections: PF3N-04.

Ambiguous forced decisions: none.

Invalid: none.

Execution errors: none.

Needs review by gold class:
- pass: CF3N-03, CF3N-04, CF3N-08, CF3N-11, PF3N-01, PF3N-02, PF3N-06, PF3N-08, PF3N-09
- fail: none
- needs_review: CF3N-19, CF3N-20, PF3N-19, PF3N-20

Intended faulty claims flagged: 13 / 14.
Bad fragments rejected only for other claims: none.
Additional failed claims in bad fragments: none.

| Case | Gold | v3 | v4 | Failed claims v4 |
|---|---|---|---|---|
| CF3N-01 | pass | pass | pass | — |
| CF3N-02 | pass | pass | pass | — |
| CF3N-03 | pass | needs_review | needs_review | — |
| CF3N-04 | pass | needs_review | needs_review | — |
| CF3N-05 | pass | pass | pass | — |
| CF3N-06 | pass | pass | pass | — |
| CF3N-07 | pass | pass | pass | — |
| CF3N-08 | pass | fail | needs_review | — |
| CF3N-09 | pass | pass | pass | — |
| CF3N-10 | pass | fail | pass | — |
| CF3N-11 | pass | fail | needs_review | — |
| CF3N-12 | pass | pass | pass | — |
| CF3N-13 | fail | fail | fail | c2 |
| CF3N-14 | fail | fail | fail | c2 |
| CF3N-15 | fail | fail | fail | c2 |
| CF3N-16 | fail | fail | fail | c2 |
| CF3N-17 | fail | fail | fail | c2 |
| CF3N-18 | fail | fail | fail | c2 |
| CF3N-19 | needs_review | needs_review | needs_review | — |
| CF3N-20 | needs_review | needs_review | needs_review | — |
| PF3N-01 | pass | fail | needs_review | — |
| PF3N-02 | pass | fail | needs_review | — |
| PF3N-03 | pass | fail | pass | — |
| PF3N-04 | pass | fail | fail | A |
| PF3N-05 | pass | fail | pass | — |
| PF3N-06 | pass | fail | needs_review | — |
| PF3N-07 | pass | fail | pass | — |
| PF3N-08 | pass | needs_review | needs_review | — |
| PF3N-09 | pass | fail | needs_review | — |
| PF3N-10 | pass | pass | pass | — |
| PF3N-11 | pass | fail | pass | — |
| PF3N-12 | pass | fail | pass | — |
| PF3N-13 | fail | fail | fail | B |
| PF3N-14 | fail | fail | fail | A |
| PF3N-15 | fail | fail | fail | A, B |
| PF3N-16 | fail | fail | fail | B |
| PF3N-17 | fail | fail | fail | B |
| PF3N-18 | fail | fail | fail | B |
| PF3N-19 | needs_review | needs_review | needs_review | — |
| PF3N-20 | needs_review | needs_review | needs_review | — |

All denominators retained. Review is neither acceptance nor detection. Localization does not prove causal explanation.
Agent manual normalization/review only; human_approved=false. Old v3 was not rerun or changed.
