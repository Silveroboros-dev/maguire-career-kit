# Frozen v3: new challenge fragments

Manual agent authoring and review; human_approved=false. Gold was frozen before predictions.

| Family | Good → pass / fail / review / invalid | Bad → pass / fail / review / invalid | Ambiguous → pass / fail / review / invalid |
|---|---|---|---|
| candidate-fit | 7 / 3 / 2 / 0 | 0 / 6 / 0 / 0 | 0 / 0 / 2 / 0 |
| preference-fit | 1 / 10 / 1 / 0 | 0 / 6 / 0 / 0 | 0 / 0 / 2 / 0 |
| overall | 8 / 13 / 3 / 0 | 0 / 12 / 0 / 0 | 0 / 0 / 4 / 0 |

Missed accepted errors: none.

False rejections: CF3N-08, CF3N-10, CF3N-11, PF3N-01, PF3N-02, PF3N-03, PF3N-04, PF3N-05, PF3N-06, PF3N-07, PF3N-09, PF3N-11, PF3N-12.

Ambiguous forced decisions: none.

Invalid: none.

Execution errors: none.

Intended faulty claims flagged: 14 / 14.
Bad fragments rejected only on other claims: none.
Additional failures on non-faulty claims inside bad fragments: none.

Needs review by gold class:
- pass: CF3N-03, CF3N-04, PF3N-08
- fail: none
- needs_review: CF3N-19, CF3N-20, PF3N-19, PF3N-20

All individual decisions (full evidence traces in measurement.json):

| Case | Gold | Actual | Intended bad claims | Failed claims | Review claims |
|---|---|---|---|---|---|
| CF3N-01 | pass | pass | — | — | — |
| CF3N-02 | pass | pass | — | — | — |
| CF3N-03 | pass | needs_review | — | — | c1, c3 |
| CF3N-04 | pass | needs_review | — | — | c3 |
| CF3N-05 | pass | pass | — | — | — |
| CF3N-06 | pass | pass | — | — | — |
| CF3N-07 | pass | pass | — | — | — |
| CF3N-08 | pass | fail | — | c1 | c3, c4 |
| CF3N-09 | pass | pass | — | — | — |
| CF3N-10 | pass | fail | — | c1 | — |
| CF3N-11 | pass | fail | — | c2 | c1 |
| CF3N-12 | pass | pass | — | — | — |
| CF3N-13 | fail | fail | c2 | c2 | — |
| CF3N-14 | fail | fail | c2 | c2 | — |
| CF3N-15 | fail | fail | c2 | c2 | — |
| CF3N-16 | fail | fail | c2 | c2 | — |
| CF3N-17 | fail | fail | c2 | c2 | — |
| CF3N-18 | fail | fail | c2 | c2 | — |
| CF3N-19 | needs_review | needs_review | — | — | c1 |
| CF3N-20 | needs_review | needs_review | — | — | c1 |
| PF3N-01 | pass | fail | — | B | — |
| PF3N-02 | pass | fail | — | B | — |
| PF3N-03 | pass | fail | — | B | — |
| PF3N-04 | pass | fail | — | B | — |
| PF3N-05 | pass | fail | — | C | — |
| PF3N-06 | pass | fail | — | A | — |
| PF3N-07 | pass | fail | — | B | — |
| PF3N-08 | pass | needs_review | — | — | A, B |
| PF3N-09 | pass | fail | — | B | — |
| PF3N-10 | pass | pass | — | — | — |
| PF3N-11 | pass | fail | — | A, B | — |
| PF3N-12 | pass | fail | — | A | — |
| PF3N-13 | fail | fail | B | B | — |
| PF3N-14 | fail | fail | A, B | A, B | — |
| PF3N-15 | fail | fail | A, B | A, B | — |
| PF3N-16 | fail | fail | B | B | — |
| PF3N-17 | fail | fail | B | B | — |
| PF3N-18 | fail | fail | B | B | — |
| PF3N-19 | needs_review | needs_review | — | — | A |
| PF3N-20 | needs_review | needs_review | — | — | A |

Abstention is not detection or acceptance. Claim localization is separate from the correctness of an explanation.
The authors did not inspect runtime; separation was procedural in a shared filesystem, not an externally independent holdout.
