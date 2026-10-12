# Authoring contract: career-quality-v1

Scope: 12 candidate-fit and 12 preference-fit synthetic development cases. No
live generation, provider calls, dependencies, Git changes, real career records,
or engineering-benchmark imports. English fixture text; Russian reading guide.
These are agent-authored proposed labels, not human-approved truth or a holdout.

Each case is a folder `candidate-fit/CF-01` or `preference-fit/PF-01` containing
exactly four JSON files. Use UTF-8, indent 2, trailing newline. Keep source material,
gold and answer labels separate. All prose must be specific to the case.

## input.json

Fields: `schema` = `maguire-quality-input-v1`, `case_id`, `grader` =
`candidate_fit` or `preference_fit`, `data_class` = `synthetic`, `decision_at`
(ISO UTC), `task` (plain task; never desired labels or planted defects),
`jd`: {`title`, `sources`}, `candidate`: {`facts`, `preferences`}.

Each JD source: {`id`, `text`, `observed_at`, `authority`, `supersedes`: []}.
Authority is `job_description` or `employer_update`; supersedes uses source IDs
only when replacement is explicitly part of the scenario. Dates alone do not
establish replacement. No real employer or external URL is needed.
Each fact: {`id`, `text`, `evidence_type`, `observed_at`, `status`, `supersedes`: []}.
Evidence type is `self_report` or `supplied_artifact_excerpt`; status is `active`
or `withdrawn`. Include a current correction source when withdrawing a claim.
Neither evidence type means independently verified.
Each preference: {`id`, `text`, `priority`: `must_have` or `nice_to_have`,
`allowed_exceptions`: [strings], `confirmed_at`}.
All source/fact/preference IDs are unique within a case. Use `jd_*`, `fact_*`,
`pref_*` IDs. No personal details. Include only pertinent context.

## gold.json

Fields: `schema` = `maguire-quality-gold-v1`, `case_id`, `family`, `title`,
`review_status` = `proposed_agent_authored`, `human_approved` = false,
`units`, `forbidden_assessment_targets`, `acceptable_actions`,
`critical_errors`, `notes`.

Each unit: {`target_id`, `kind`, `allowed_labels`: [...],
`acceptable_evidence_sets`: [[source IDs], ...], `rationale`,
`required_points`: [specific propositions], `forbidden_inferences`: [strings]}.
`target_id` is a JD source ID for candidate-fit, or a preference ID for
preference-fit. Keep each tested JD duty sufficiently atomic to map to a source;
a deliberate compound-duty case must explicitly describe its supported subset.
Evidence sets describe sufficient source combinations, not a mandate to quote
one exact substring. Correct answers must include at least one entire allowed
set among their evidence citations. Substring presence alone does not establish
semantic sufficiency. `kind` describes duty/minimum/preferred/expectation, etc.
Candidate-fit labels: supported, partial, unknown, contradicted.
Preference-fit labels: aligned, conflict, unknown.
`forbidden_assessment_targets` lists e.g. entry policy that must not become a
skill assessment. It is not forbidden to mention that policy in reasoning.
Actions: pursue, clarify, pass, show_existing_evidence, verify_skill.
Critical errors: [{`id`, `description`, `target_ids`: [...]}]. These are
case-specific assertions, not automatic gates inferred by the structural checker.

## answers.json

Fields: `schema` = `maguire-quality-answers-v1`, `case_id`, `answers`: four full
answer objects. Give neutral IDs `answer_01` ... `answer_04`; labels belong only
in annotations.json. Two genuinely acceptable variants, two deliberately wrong.
Every answer: {`answer_id`, `assessments`, `conclusion`, `limitations`}.
Assessment: {`target_id`, `label`, `evidence`: [{`source_id`, `quote`}], `rationale`}.
Conclusion: {`action`, `text`, `next_step`}. Limitations is a nonempty string list.
Quotes must be nonempty literal substrings of input text except an expressly
labelled fabricated-quote negative. Actual conclusions must still be evaluated
semantically: copied IDs or correct label words are not proof of a good answer.
The second correct answer can change prose, ordering and/or a permitted next step;
at least four cases in each suite should include a substantive acceptable variant
(different admissible action/evidence combination/label under stated ambiguity),
not only cosmetic paraphrases. Avoid using exact strings as a semantic oracle.

## annotations.json

Fields: `schema` = `maguire-quality-annotations-v1`, `case_id`, `answers`:
four annotations, each {`answer_id`, `expected_verdict`: pass or fail,
`citation_integrity`: pass or fail, `reason`, `mutation`, `expected_findings`}.
Positive: mutation null, expected_findings [].
Negative: mutation {`base_answer_id`: answer_01, `category`, `description`,
`changed_paths`: [...]}; expected_findings is a nonempty list of
{`criterion_id`, `severity`: major or critical, `target_id`, `explanation`}.
Each negative is a full copy of answer_01 with ONE conceptual defect; changing
label and related rationale together is one conceptual defect. List the exact
minimal recursive JSON diff paths (RFC6901; arrays of different lengths are a
single change at the array path). Ignore /answer_id when calculating diffs.
No irrelevant stylistic changes in negative copies. Two different defects per
case. Negatives may retain perfect mechanical validity: that is intentional.

Candidate-fit criteria: CF-COVERAGE, CF-EVIDENCE, CF-LABEL, CF-SCOPE,
CF-UNCERTAINTY, CF-ACTION.
Preference-fit criteria: PF-COVERAGE, PF-INTERPRETATION, PF-EVIDENCE,
PF-UNKNOWN, PF-PRIORITY, PF-ACTION.
Findings target IDs must refer to input items; no global score/probability field.

## Semantic boundaries

An explicit minimum can be contradicted by an explicit counterfact. No past
production experience does not establish inability to do a future duty. A
waiver of entry experience does not establish a skill. Partial requires actual
evidence of a meaningful subset. Mark self-report as such.
Explicit three office days versus a zero-office must-have is a conflict even if
possible employer flexibility is unknown. Accept a conditional clarification
when the candidate explicitly allows asking; do not force a universal pass.
Do not let nice-to-have attributes compensate a must-have. Silence and unresolved
conflicting sources can imply unknown; an old date alone does not invalidate an
otherwise applicable source. Person-owned exceptions must be explicit.

Outputs assess the supplied snapshots only. A synthetic case is not a new model
run or a real outcome. Match scores, review quality and interview probabilities
are distinct. Do not add a semantic grader, paid runner or probability estimator.
