# Structural API clarification before predictions

The frozen SCHEMA remains unchanged. Root extracted only public structural syntax
from the frozen validator to clarify missing serialization details. No behavior,
thresholds, prior cases or outcomes are supplied. Authors must record this read.

A typed check has `op` and exactly these operand keys:

| op | operand keys | reading predicate |
|---|---|---|
| constraint | offer, preference | constraint_satisfied |
| permission_limit | offer, preference | request_within_limit |
| pending | offer, preference | constraint_unresolved or confirmation_needed |
| condition | offer | condition_required |
| onboarding | offer, remote, preference | constraint_satisfied |
| schedule_before | offer, preference | constraint_satisfied |

Each operand is exactly `{"source_id": "source-id", "fact_index": 0}`;
index is zero-based. Example syntax only:
`{"op":"constraint","offer":{"source_id":"employer","fact_index":0},"preference":{"source_id":"candidate","fact_index":0}}`.
Use the operation matching the raw claim; no forced operation for an unrelated
statement. Direct claims retain `check:null`. Unsupported faithful concepts may
remain outside bounded coverage.

Structural enums:
- source kind: candidate_fact, job_description, employer_update, preference
- source status: active, withdrawn
- modality: observation, self_report, requirement, permission, possibility,
  prediction, commitment, guarantee, ability, evaluation_instruction,
  preference_constraint, record_assessment
- stance: asserted, recommended_as_fact, quoted, rejected, question, conditional, advice
- polarity: positive, negative; epistemic_scope: world, packet
- measure kind: count, difference, rate, amount, frequency
- measure per: null, day, week, calendar_month, calendar_quarter, calendar_year
- scope/time: dictionaries with scalar values, no nested objects or arrays.
- money amounts require explicit period; annual equivalence is encoded according
  to the frozen schema without inventing a payment frequency.

This clarification does not alter raw cases or semantic labels. Any later
source-fidelity correction must preserve the earlier file and be reviewed again.

Pre-run correction: root initially copied base enums without the v6 extensions.
`advice` stance and `calendar_year` period are admitted by v6. The initial
addendum is preserved; no data label or checker prediction motivated this fix.
