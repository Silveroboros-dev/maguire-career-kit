# Frozen v5 on 40 new cases

New manually agent-annotated fragments; byte-identical frozen v5 checker. Authors saw only public schema, not prior results. Not human-approved.

| Family | Good: pass / fail / review / invalid | Bad: pass / fail / review / invalid | Ambiguous: pass / fail / review / invalid |
|---|---|---|---|
| candidate-fit | 3 / 0 / 9 / 0 | 0 / 3 / 3 / 0 | 0 / 0 / 2 / 0 |
| preference-fit | 6 / 0 / 7 / 0 | 0 / 4 / 2 / 0 | 0 / 0 / 1 / 0 |
| all | 9 / 0 / 16 / 0 | 0 / 7 / 5 / 0 | 0 / 0 / 3 / 0 |

Missed accepted errors: none.

False rejections: none.

Ambiguous forced decisions: none.

Invalid: none.

Execution errors: none.

Needs review by gold class:
- pass: CF5H-01, CF5H-03, CF5H-08, CF5H-11, CF5H-14, CF5H-16, CF5H-17, CF5H-19, CF5H-20, PF5H-03, PF5H-04, PF5H-05, PF5H-09, PF5H-11, PF5H-17, PF5H-20
- fail: CF5H-02, CF5H-15, CF5H-18, PF5H-06, PF5H-18
- needs_review: CF5H-05, CF5H-13, PF5H-10

Intended faulty claims flagged: 7 / 12.
Bad fragments rejected only for other claims: none.
Additional failed claims in bad fragments: none.

| Case | Gold | Frozen v5 | Failed claims | Review claims |
|---|---|---|---|---|
| CF5H-01 | pass | needs_review | — | c2 |
| CF5H-02 | fail | needs_review | — | c1 |
| CF5H-03 | pass | needs_review | — | c1, c2, c3 |
| CF5H-04 | pass | pass | — | — |
| CF5H-05 | needs_review | needs_review | — | c1 |
| CF5H-06 | fail | fail | c1 | — |
| CF5H-07 | pass | pass | — | — |
| CF5H-08 | pass | needs_review | — | c1, c2 |
| CF5H-09 | fail | fail | c1 | — |
| CF5H-10 | pass | pass | — | — |
| CF5H-11 | pass | needs_review | — | c1, c2 |
| CF5H-12 | fail | fail | c1 | — |
| CF5H-13 | needs_review | needs_review | — | c1 |
| CF5H-14 | pass | needs_review | — | c1, c2 |
| CF5H-15 | fail | needs_review | — | c1 |
| CF5H-16 | pass | needs_review | — | c1, c2 |
| CF5H-17 | pass | needs_review | — | c1, c2 |
| CF5H-18 | fail | needs_review | — | c1, c2 |
| CF5H-19 | pass | needs_review | — | c1, c2 |
| CF5H-20 | pass | needs_review | — | c1, c2, c3, c4 |
| PF5H-01 | pass | pass | — | — |
| PF5H-02 | fail | fail | c1 | — |
| PF5H-03 | pass | needs_review | — | c1 |
| PF5H-04 | pass | needs_review | — | c1 |
| PF5H-05 | pass | needs_review | — | c1 |
| PF5H-06 | fail | needs_review | — | c1 |
| PF5H-07 | pass | pass | — | — |
| PF5H-08 | fail | fail | c1 | — |
| PF5H-09 | pass | needs_review | — | c1 |
| PF5H-10 | needs_review | needs_review | — | c1 |
| PF5H-11 | pass | needs_review | — | c1 |
| PF5H-12 | pass | pass | — | — |
| PF5H-13 | pass | pass | — | — |
| PF5H-14 | fail | fail | c1 | — |
| PF5H-15 | pass | pass | — | — |
| PF5H-16 | fail | fail | c1 | — |
| PF5H-17 | pass | needs_review | — | c1 |
| PF5H-18 | fail | needs_review | — | c1 |
| PF5H-19 | pass | pass | — | — |
| PF5H-20 | pass | needs_review | — | c3, c4 |

All denominators retained. Review is neither acceptance nor detection. Localization does not prove causal explanation.
Agent manual normalization/review only; human_approved=false. Frozen v5 code and all predecessors remain unchanged. Different cases cannot establish a paired version improvement.
