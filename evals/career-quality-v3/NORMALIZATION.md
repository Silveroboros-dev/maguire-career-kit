# Manual normalization, first slice

This fixture authoring is manual agent work, not automatic extraction and not
human approval. `prepare_data.py` records the choices reproducibly. Its case/ID
branches select authored fixtures; the runtime never imports that script or sees
authoring IDs, expected outcomes, design rules, failed axes or old v2 outcomes.

The frozen predecessor design contains 16 selected fragments. We expand their
simultaneous claims into separate atoms, keep D16's two readings as alternatives,
and preserve narrower subspans. Every atom is bound to the original answer's
file hash, JSON pointer and Unicode code point range. Whole answers remain out
of scope. Source anchors bind the entire source sentence; source propositions
are manually reviewed interpretations of those sentences and their metadata.

Source inventory includes each source from the relevant input (including
preferences), not only previously cited source IDs. Its complete flag means
coverage of the supplied snapshot for this slice, never exhaustive world facts.
The runner must validate a separately authored normalization review before
promoting coverage status from unreviewed to agent_reviewed in runtime packets.
The original data file remains unreviewed as authored, preserving this transition.

Important choices for reviewer attention:

- D01: the positive result remains an observed distance difference; the advice
  promotes it to every week and all branches. The advertised trial's particular
  dates and the total number of branches are not invented.
- D02: keep the last-use premise and future-inability conclusion separate.
  Self-report remains visible as the support level even if the answer omits the
  phrase “the candidate reports.” This is evidence-relative fit, not biography
  verification. The checker must not prove inability from a historical window.
- D03: the sample-size presupposition and production achievement are separate.
  Applying a checklist is not silently upgraded to coordinating archive processing.
  Candidate facts retain self_report, including supplied first-person excerpts.
  More than
  200,000 whole pages is encoded as lower=200001, upper=null. This integer count
  conversion is specific to pages, not a generic floating-point inequality rule.
- D04: only the capacity clause belongs to the selected fragment. The acceptable
  “supports the method” clause elsewhere is not silently counted as evaluated.
- D05: distinguish permission allegedly supplied by the editorial directive
  from the recommended certification claim. The source contains the command as
  data, never genuine evaluator authority. Missing assessment does not establish
  that learning or effective training is impossible.
- D07: preserve the correct interval-membership premise separately from the
  personal commitment. The statement “the employer pays this candidate” is
  canonically represented as the candidate's personal stipend with commitment
  modality; this does not transfer the payer to the candidate.
- D08: compatibility is derived under candidate-owned constraints, not treated
  as a directly quoted source fact. No budget value or preference exchange rate
  is invented. Priority and absence of exceptions come from the input metadata.
- D09: ongoing weekly permission and a monthly ceiling are different from a
  one-off visit. Both have time.recurring=true; denominators retain calendar
  meaning. Three full weeks is a safe lower bound inside a calendar month, not
  an exact weekly-to-monthly conversion.
- D10/D11: the selected negative proposition concerns what the packet resolves.
  “Newer flexibility note” identifies jd_3 by the recorded observed_at ordering,
  checked as two separate packet-metadata comparisons. This definite description
  is not normalized as an assertion about publication or effective dates.
  Two records share one wording; they do not form two independent semantic tests.
  No claim of full-answer pass is made, especially for surrounding date wording.
- D12: “both” expands to two supersession atoms plus the remote guarantee.
- D13: governing authority and full resolution are separate. The causal premise
  “it is later” retains observed-order and publication-order alternatives after
  review. It needs interpretation review, while the two definite authority
  assertions remain checkable. No publication timestamp is manufactured.
- D14/D15: requirement, platform use, configured availability, employer refusal
  and impossibility remain different propositions. No platform facts are fetched.
- D16: retain both world absence and packet absence; do not select the reading
  that happens to make a reference-positive answer pass.

`confirmed_at` for a preference is projected to source availability
`observed_at` and remains recoverable from the bound input. It is not an effective
employment term. Source status and scope remain independent of observation date.
The predecessor `supersedes` lists are empty in these cases; no edges are
invented. Source predicates beyond the runtime registry preserve material
clauses but do not expand the implemented checker vocabulary.

The root and reviewer know the design expectations. The runtime worker knows
the operation families and received concrete schema examples while clarifying
the contract. This is declared development regression, not held-out evaluation.
