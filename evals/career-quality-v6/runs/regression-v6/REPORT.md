# V6 regression on the same 40 cases

Exposed development regression; unchanged raw/gold, revised normalization and v6 checker. Not a blind holdout or human-approved.

| Family | Good: pass / fail / review / invalid | Bad: pass / fail / review / invalid | Ambiguous: pass / fail / review / invalid |
|---|---|---|---|
| candidate-fit | 12 / 0 / 0 / 0 | 0 / 6 / 0 / 0 | 0 / 0 / 2 / 0 |
| preference-fit | 12 / 0 / 1 / 0 | 0 / 6 / 0 / 0 | 0 / 0 / 1 / 0 |
| all | 24 / 0 / 1 / 0 | 0 / 12 / 0 / 0 | 0 / 0 / 3 / 0 |

Missed accepted errors: none.

False rejections: none.

Ambiguous forced decisions: none.

Invalid: none.

Execution errors: none.

Needs review by gold class:
- pass: PF5H-04
- fail: none
- needs_review: CF5H-05, CF5H-13, PF5H-10

Intended faulty claims flagged: 12 / 12.
Bad fragments rejected only for other claims: none.
Additional failed claims in bad fragments: none.

| Case | Gold | V6 | Failed claims | Review claims |
|---|---|---|---|---|
| CF5H-01 | pass | pass | — | — |
| CF5H-02 | fail | fail | c1 | — |
| CF5H-03 | pass | pass | — | — |
| CF5H-04 | pass | pass | — | — |
| CF5H-05 | needs_review | needs_review | — | c1 |
| CF5H-06 | fail | fail | c1 | — |
| CF5H-07 | pass | pass | — | — |
| CF5H-08 | pass | pass | — | — |
| CF5H-09 | fail | fail | c1 | — |
| CF5H-10 | pass | pass | — | — |
| CF5H-11 | pass | pass | — | — |
| CF5H-12 | fail | fail | c1 | — |
| CF5H-13 | needs_review | needs_review | — | c1 |
| CF5H-14 | pass | pass | — | — |
| CF5H-15 | fail | fail | c1 | — |
| CF5H-16 | pass | pass | — | — |
| CF5H-17 | pass | pass | — | — |
| CF5H-18 | fail | fail | c1 | — |
| CF5H-19 | pass | pass | — | — |
| CF5H-20 | pass | pass | — | — |
| PF5H-01 | pass | pass | — | — |
| PF5H-02 | fail | fail | c1 | — |
| PF5H-03 | pass | pass | — | — |
| PF5H-04 | pass | needs_review | — | c1 |
| PF5H-05 | pass | pass | — | — |
| PF5H-06 | fail | fail | c1 | — |
| PF5H-07 | pass | pass | — | — |
| PF5H-08 | fail | fail | c1 | — |
| PF5H-09 | pass | pass | — | — |
| PF5H-10 | needs_review | needs_review | — | c1 |
| PF5H-11 | pass | pass | — | — |
| PF5H-12 | pass | pass | — | — |
| PF5H-13 | pass | pass | — | — |
| PF5H-14 | fail | fail | c1 | — |
| PF5H-15 | pass | pass | — | — |
| PF5H-16 | fail | fail | c1 | — |
| PF5H-17 | pass | pass | — | — |
| PF5H-18 | fail | fail | c1 | — |
| PF5H-19 | pass | pass | — | — |
| PF5H-20 | pass | pass | — | — |

All denominators retained. Review is neither acceptance nor detection. Localization does not prove causal explanation.
Agent manual normalization/review only; human_approved=false. Frozen v5 and all predecessors remain unchanged. Paired development results do not establish generalization.


## Paired v5 → v6 outcomes

| Case | Gold | V5 | V6 |
|---|---|---|---|
| CF5H-01 | pass | needs_review | pass |
| CF5H-02 | fail | needs_review | fail |
| CF5H-03 | pass | needs_review | pass |
| CF5H-04 | pass | pass | pass |
| CF5H-05 | needs_review | needs_review | needs_review |
| CF5H-06 | fail | fail | fail |
| CF5H-07 | pass | pass | pass |
| CF5H-08 | pass | needs_review | pass |
| CF5H-09 | fail | fail | fail |
| CF5H-10 | pass | pass | pass |
| CF5H-11 | pass | needs_review | pass |
| CF5H-12 | fail | fail | fail |
| CF5H-13 | needs_review | needs_review | needs_review |
| CF5H-14 | pass | needs_review | pass |
| CF5H-15 | fail | needs_review | fail |
| CF5H-16 | pass | needs_review | pass |
| CF5H-17 | pass | needs_review | pass |
| CF5H-18 | fail | needs_review | fail |
| CF5H-19 | pass | needs_review | pass |
| CF5H-20 | pass | needs_review | pass |
| PF5H-01 | pass | pass | pass |
| PF5H-02 | fail | fail | fail |
| PF5H-03 | pass | needs_review | pass |
| PF5H-04 | pass | needs_review | needs_review |
| PF5H-05 | pass | needs_review | pass |
| PF5H-06 | fail | needs_review | fail |
| PF5H-07 | pass | pass | pass |
| PF5H-08 | fail | fail | fail |
| PF5H-09 | pass | needs_review | pass |
| PF5H-10 | needs_review | needs_review | needs_review |
| PF5H-11 | pass | needs_review | pass |
| PF5H-12 | pass | pass | pass |
| PF5H-13 | pass | pass | pass |
| PF5H-14 | fail | fail | fail |
| PF5H-15 | pass | pass | pass |
| PF5H-16 | fail | fail | fail |
| PF5H-17 | pass | needs_review | pass |
| PF5H-18 | fail | needs_review | fail |
| PF5H-19 | pass | pass | pass |
| PF5H-20 | pass | needs_review | pass |