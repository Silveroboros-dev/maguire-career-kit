# Career-quality-v2 challenge corpus — author record

The 13 cases under `cases/` are wholly synthetic English snapshots. Their 52 full answers have proposed, agent-authored verdicts: 26 acceptable and 26 deliberately wrong. `human_approved` is `false` in every gold file. `author_cases.py` is the reproducible source for the four JSON files in each case. The corpus is a focused challenge set, not a representative accuracy sample or an externally blind holdout.

| Case | Family | Situation and intended boundary |
| --- | --- | --- |
| CF2-01 | Unsupported quantitative result | A one-week four-branch route trial supports 18 fewer kilometres, not annual fuel savings or recurring network results. |
| CF2-02 | Aggregate certainty | Metadata field design is partial and permission work unknown; neither warrants full workflow readiness. |
| CF2-03 | Recency versus future ability | A 2021 console date fails an explicit two-year minimum without proving future alert-handling incapacity. |
| CF2-04 | Quantified scale | A 75-page OCR sample supports a method, not 200,000-page coordination or daily throughput. |
| CF2-05 | Embedded source directive | A job-text editorial instruction has no authority over the evidence assessment. |
| PF2-01 | Employer exception | Required evening performances conflict with a daytime-only boundary; a separate role may be queried. |
| PF2-02 | Range to personal offer | A stipend band crosses the candidate's threshold but promises no individual amount. |
| PF2-03 | Hard versus soft | A learning allowance does not override a no-overnight-on-call must-have. |
| PF2-04 | Candidate exception scope | One overnight trip per quarter cannot be expanded to monthly travel or banked. |
| PF2-05 | Time denominator | Two station days per week exceed a candidate limit of two per month. |
| PF2-06 | Authority by date | Remote, attendance, and flexibility notices remain unresolved without explicit supersession. |
| PF2-07 | Local to personal scope | Helsinki team practice does not grant a Dublin accountant a written zero-office arrangement. |
| PF2-08 | Missing information | A named meeting platform establishes neither caption availability nor refusal. |

Each folder contains only `input.json`, `gold.json`, `answers.json`, and `annotations.json` in the v1 format. `answer_01` is the base acceptable response; `answer_02` is a substantive acceptable near-neighbor with a different decision explanation, evidence step, or permitted action. `answer_03` and `answer_04` are full copies of `answer_01` with one distinct conceptual defect each. Each negative changes one prose field; its mutation path is the exact recursive JSON diff from `answer_01` after excluding `answer_id`. All 52 answers retain complete target coverage, allowed labels, literal source quotations satisfying a gold evidence set, and an allowed conclusion action. Within each PF case, all four answers also have identical target, label, evidence, and action values. Thus the deliberate failures depend on meaning, not missing metadata.

Author checks on 2026-10-12: verified 5 CF and 8 PF directories, exactly four required files per case, 4 answers and 4 annotations per case, 26 proposed passes and 26 proposed failures, two critical-error descriptions per case, unique source IDs, source dates no later than each decision snapshot, exact literal quote inclusion, acceptable evidence-set and action membership, and PF metadata identity. No v2 grader, grader test, or predicted result was read during authoring. No provider call, network call, install, Git write, real candidate record, or real employer policy was used. Source quotations remain evidence, never operational instructions. Semantic judgments remain subject to independent review before measurement.
