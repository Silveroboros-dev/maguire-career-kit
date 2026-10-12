# v5 normalization changes

2026-10-12. `migrate_annotations.py` is an offline, narrow migration from the
frozen v4 normalized annotations and copied v5 raw fragments. It does not read
gold, checker code, packets, or predictions. The author reviewed the v4 analysis
and therefore knows v4's reported failures; this is a known-case regression, not
an independent blind evaluation. The v5 annotations are agent-authored and
`human_approved=false`. No v5 runtime predictions were inspected during authoring.

The migration makes exactly seven proposition edits:

| Case | Proposition | Change and raw-text basis |
|---|---|---|
| CF3N-08 | Source `CF3N-08-S1` fact 0; source `CF3N-08-JD` fact 0; claim `c1` reading 0; claim `c2` reading 0 | Set `measure.unit` from `days` to canonical `day`. Each remains `kind=frequency`, `per=week`, with its existing bounds, weekday scope, and distinct 2022 history versus 2027 requirement. |
| PF3N-06 | Source `J06` fact 0; source `P06` fact 0 | Set `measure.unit` from `days` to canonical `day`. Both remain `kind=count`, `per=null`, with their existing 30-day bounds and onboarding context. This does not turn an onboarding count into a recurring weekly frequency. |
| PF3N-09 | Source `J09` fact 0 | Set the negative current-unavailability fact's `scope` to `{"status":"available_now"}`. The raw source says captions are “not yet available”; the separate positive `pending` procurement fact and advice remain unchanged. This scope is specific to this literal current-status statement, not a rule for all negative facts. |

The document schema changes to `maguire-v5-normalized` and exposure metadata now
records v4 analysis knowledge. PF3N-14/A and B annotations remain unchanged: the
raw informal note explicitly does not amend the two-day rule, and the existing
negative `supersedes` fact is enough for the checker to determine the active term.
PF3N-04 exclusivity, CF3N-18, and all qualitative or ambiguous claims also remain
unchanged. The `stipend` direct predicate remains in the annotations; its registry
support is a checker contract change.

Structural audit after migration: 40 case IDs, 81 original claim IDs and quote
substrings, 66 source IDs, 98 source facts, and 14 typed operations are retained.
There are 42 candidate-fit claims and 39 preference-fit claims. Each quote remains
a substring of its copied raw answer. All v4 proposition differences are the
seven edits listed above. The script refuses to rewrite annotations if v5
`FREEZE.json` or `START.json` exists. This audit does not establish semantic
correctness beyond the inspected raw fragments or predict v5 checker outcomes.
