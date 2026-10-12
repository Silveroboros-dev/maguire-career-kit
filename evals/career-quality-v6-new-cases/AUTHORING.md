# New cases for the frozen v6 — author interface and boundary

Create new fictional evidence fragments and manually normalized claims. Offline,
stdlib only, Python -B; no network/API/install/Git writes/commit/push. No actual
personal data. Root integrates; each author owns one family of files. The checker
is already frozen and must not be read, executed or edited by authors.

Allowed: this file, FROZEN_SCHEMA.md, repository AGENTS/README/CREDITS, your own new
family's authoring/raw/normalized/gold files. Forbidden: checker.py, v3_core.py,
grade_packets.py, measurement.py, pipeline.py, tests, prior datasets, prior analysis,
predictions and other author's material. No access to previous conversation supplied
to standalone authors. The directory is shared, not an OS access-control boundary.

Produce 20 cases per family: 12 acceptable (`pass`), 6 defective (`fail`), 2 genuinely
ambiguous (`needs_review`). Case numbers do not encode class: interleave labels.
Use IDs CF6H-01…20 / PF6H-01…20, claim IDs c1,c2,…, source IDs unique per case.
Use 1–4 atomic claims per response; prefer realistic multi-clause responses.

Family definitions:
candidate-fit concerns candidate experience, skill, credentials, personal contribution
and capability against role requirements. preference-fit concerns personal preferences
and employer offer/working conditions. Direct premises in these domains are allowed;
a certificate-versus-role requirement alone is not a preference-fit case. Preserve
initial authored revisions and raw-only judgments when correcting domain mistakes.

Newness means new evidence/answer combinations and diverse reasoning compositions,
not only changing names or numbers. Do not attempt to infer checker implementation
or expected failure modes. At least half the cases should combine two dimensions
(time, scope, source authority, quantifier, modality, amount/category, conditions).
Include useful supported answers as well as unsupported or overstrong assertions.
Hard cases should have clear source-grounded gold, not arbitrary traps or missing
facts the author secretly assumes. Real ambiguity gets multiple faithful readings.
Do not set gold review merely because a comparator may not support a valid inference.

Use source/answer text in English. Gold reasons explain semantic truth from the
given complete source inventory, not what the checker is expected to do. No case
may be discarded or relabeled after grader results. Reviewer may correct authoring
defects before freeze, recording the reason without inspecting predictions.

## Files (JSON UTF-8)

raw/<family>.json:
`{schema:"maguire-v6-new-raw",family,human_approved:false,exposure:{...},rows:[...]}`
Each raw row:
`{case_id,title,decision_at,sources:[{id,text,kind,status,observed_at}],answer:{text}}`.
Use ISO timestamp with timezone, e.g. decision_at 2026-10-12T12:00:00Z. source kind:
candidate_fact/job_description/employer_update/preference; status active/withdrawn.
Use source timing/status only when it matters and gold accounts for it.

normalized/<family>.json:
`{schema:"maguire-v6-new-normalized",family,human_approved:false,exposure:{...},rows:[...]}`
Each normalized row:
`{case_id,sources:[{id,facts:[proposition,...]}],claims:[{id,quote,stance,readings:[proposition,...],check}]}`.
All raw sources must appear with faithful atomic facts. Each claim quote must be
an exact, uniquely occurring substring of its own answer. Cover the full asserted
meaning, including correct premises inside otherwise defective answers. Quote
anchors and packet hashes will be supplied by the harness, not the author.

proposition exact keys:
`{subject,predicate,object,polarity,modality,epistemic_scope,scope,time,measure}`.
subject/predicate/object are nonempty strings. polarity positive/negative.
epistemic_scope world/packet. scope/time are objects with scalar values only.
modality: observation,self_report,requirement,permission,possibility,prediction,
commitment,guarantee,ability,evaluation_instruction,preference_constraint,record_assessment.
stance: asserted,recommended_as_fact,quoted,rejected,question,conditional,advice.
measure: null or `{kind,unit,lower,upper,per}`. Bounds finite numbers or null.
kind: count,difference,rate,amount,frequency. per: null,day,week,calendar_month,
calendar_quarter,calendar_year. Money needs explicit currency and period. Day unit
is `day`, not `days`. Do not encode missing values as zero.

Vocabulary examples (use their actual meaning, not a trick encoding):
distance_saving,console_use,alert_triage,alert_escalation,archive_processing,sample_size,
ocr_method,training_certification,evaluation_authority,stipend,on_call,learning_allowance,
station_attendance,remote_work,location_flexibility,supersedes,governs,resolves,
live_captions,caption_requirement,meeting_platform,written_offer,ledger_maintenance,
training_demo,observed_after. A new faithful predicate is permitted when necessary;
the reference verdict must not change to match presumed checker capability.

Additional public canonical names for concrete facts (use only their actual meanings):
handoff_recording, demo_presentation, incident_review_facilitation,
follow_up_documentation, vendor_cutover_coordination, kubernetes_use,
plan_drafting, plan_review, guide_writing, triage_time_reduction,
rollback_plan_writing, rollback_plan_documentation, course_completion,
certification_exam, sql_query, client_onboarding, runbook_writing,
operator_training, activation_date_promised. This vocabulary is supplied as an
input-contract aid; it does not promise any outcome. New faithful predicates are
allowed when needed, but never invent a narrower fact just to use these names.

`check:null` for direct assertions; typed operations and canonical properties are
specified in FROZEN_SCHEMA.md. This is the documented public interface, not the
implementation. Its references to the previous corpus size are historical and
do not constrain how many claims you author. Never put expected outcomes into
facts or checks. Do not drop conditions/qualifiers to make an operation fit.

gold/<family>.json:
`{schema:"maguire-v6-new-gold",family,human_approved:false,exposure:{...},rows:[...]}`.
Each gold row `{case_id,verdict,reason,error_claim_ids:[...]}`. For pass/review error
IDs empty. For fail list all and only faulty claim IDs; distinguish absence of
support from contradiction. Any firmly erroneous assertion makes a fragment fail
even when other claims are ambiguous. Genuine alternative readings with no settled
error get needs_review, supported facts and careful uncertainty statements get pass.

Save authoring/<family>-attestation.json with exact allowed files actually read,
files authored (SHA256/bytes), author/model identity, human_approved=false,
checker_code_seen=false,previous_cases_seen=false,predictions_seen=false (only when
true), composition/coverage notes, and any limitations. Helpers for constructing
handwritten records are allowed in authoring/<family>.py; no random task generator,
checker import or label-driven normalization. Tell root when raw text is stable so
a separate reviewer can form raw-only judgments before seeing your gold/normalization.


## New cohort discipline

Use diverse fictional subjects and professional contexts. Do not copy familiar
worked examples from the contract or merely vary a numeric limit: combine evidence
selection, scope, timing, modality or attribution in at least half the cases.
Include multiple claims in at least eight cases per family, retaining sound premises
inside flawed answers. A case should remain readable without the normalized form.
All text, source roles/status/timestamps and fictional identities must be authored
here; no personal data, external documents or network lookups. Files are intended
for a public software repository after review: no host/user paths, contacts or IDs.

Canonical proposition shapes remain those of FROZEN_SCHEMA.md. Use exact canonical
names when they genuinely fit; do not force qualitative claims into concrete predicates.
Interleave label classes. Target 12 supported, 6 erroneous, 2 ambiguous answers per
family, but semantics wins over quotas. Preserve initial versions and explain any
pre-freeze revisions. Do not rewrite a valid answer just to obtain a preferred label.
Signal root once raw is stable; then a reviewer reads only raw and saves its own
judgments before seeing your gold/normalization. Author files may exist but remain
outside the reviewer's phase-one read boundary. Do not inspect its judgments until
root asks for a specific pre-freeze semantic correction.

Attestation must use files_authored={relative_path:{sha256,bytes}} (paths relative
this experiment), human_approved=false, checker_code_seen=false,
previous_cases_seen=false, predictions_seen=false, and record actual allowed reads.
No claims that an AI-authored annotation has human approval.
