# Frozen v6 on 40 new cases

New manually agent-annotated fragments; byte-identical frozen v6 checker. Authors saw only public schema, not prior results. Not human-approved.

| Family | Good: pass / fail / review / invalid | Bad: pass / fail / review / invalid | Ambiguous: pass / fail / review / invalid |
|---|---|---|---|
| candidate-fit | 8 / 0 / 4 / 0 | 0 / 5 / 1 / 0 | 0 / 0 / 2 / 0 |
| preference-fit | 1 / 1 / 11 / 0 | 0 / 3 / 4 / 0 | 0 / 0 / 0 / 0 |
| all | 9 / 1 / 15 / 0 | 0 / 8 / 5 / 0 | 0 / 0 / 2 / 0 |

Missed accepted errors: none.

False rejections: PF6H-20.

Ambiguous forced decisions: none.

Invalid: none.

Execution errors: none.

Needs review by gold class:
- pass: CF6H-09, CF6H-16, CF6H-18, CF6H-19, PF6H-01, PF6H-03, PF6H-05, PF6H-07, PF6H-08, PF6H-10, PF6H-12, PF6H-14, PF6H-16, PF6H-18, PF6H-19
- fail: CF6H-20, PF6H-02, PF6H-13, PF6H-15, PF6H-17
- needs_review: CF6H-05, CF6H-15

Intended faulty claims flagged: 7 / 14.
Bad fragments rejected only for other claims: PF6H-06.
Additional failed claims in bad fragments: [{"case_id": "PF6H-06", "claim_ids": ["c1"]}].

| Case | Gold | Frozen v6 | Failed claims | Review claims |
|---|---|---|---|---|
| CF6H-01 | pass | pass | — | — |
| CF6H-02 | fail | fail | c2 | — |
| CF6H-03 | pass | pass | — | — |
| CF6H-04 | pass | pass | — | — |
| CF6H-05 | needs_review | needs_review | — | c3 |
| CF6H-06 | pass | pass | — | — |
| CF6H-07 | fail | fail | c2 | — |
| CF6H-08 | pass | pass | — | — |
| CF6H-09 | pass | needs_review | — | c2 |
| CF6H-10 | fail | fail | c1 | — |
| CF6H-11 | pass | pass | — | — |
| CF6H-12 | pass | pass | — | — |
| CF6H-13 | fail | fail | c2 | — |
| CF6H-14 | pass | pass | — | — |
| CF6H-15 | needs_review | needs_review | — | c2 |
| CF6H-16 | pass | needs_review | — | c2 |
| CF6H-17 | fail | fail | c2 | c1 |
| CF6H-18 | pass | needs_review | — | c1 |
| CF6H-19 | pass | needs_review | — | c2 |
| CF6H-20 | fail | needs_review | — | c1, c2 |
| PF6H-01 | pass | needs_review | — | c2 |
| PF6H-02 | fail | needs_review | — | c2 |
| PF6H-03 | pass | needs_review | — | c2 |
| PF6H-04 | pass | pass | — | — |
| PF6H-05 | pass | needs_review | — | c1, c2 |
| PF6H-06 | fail | fail | c1 | c2 |
| PF6H-07 | pass | needs_review | — | c2 |
| PF6H-08 | pass | needs_review | — | c2, c3 |
| PF6H-09 | fail | fail | c2 | — |
| PF6H-10 | pass | needs_review | — | c1, c2, c3 |
| PF6H-11 | fail | fail | c1 | c2 |
| PF6H-12 | pass | needs_review | — | c1, c2 |
| PF6H-13 | fail | needs_review | — | c1 |
| PF6H-14 | pass | needs_review | — | c2 |
| PF6H-15 | fail | needs_review | — | c1, c2 |
| PF6H-16 | pass | needs_review | — | c2, c3 |
| PF6H-17 | fail | needs_review | — | c3 |
| PF6H-18 | pass | needs_review | — | c2 |
| PF6H-19 | pass | needs_review | — | c2 |
| PF6H-20 | pass | fail | c2 | c1 |

All denominators retained. Review is neither acceptance nor detection. Localization does not prove causal explanation.
Agent manual normalization/review only; human_approved=false. Frozen v6 code and all predecessors remain unchanged. Different cases cannot establish a paired version improvement.
