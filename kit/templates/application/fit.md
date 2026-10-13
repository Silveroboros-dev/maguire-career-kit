# Two-sided fit assessment

Application ID: `<APP-...>`

JD snapshot / source / capture date: `<job.md, source, date>`

Selected CV / approved bank facts / preferences: `<paths, versions, date>`

Rubrics: `.maguire/kit/graders/jd-fit.md` and `.maguire/kit/graders/employer-fit.md`

Assessment date: `<YYYY-MM-DD>`

## JD fit

How well does the candidate's documented evidence support the stated work?

| Material duty or qualification | Essential / qualification / nice-to-have | Exact JD source and quote | Candidate claim/source and quote | Supported / partial / unknown / contradicted | Reason, concrete gap and scope limit |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  | `unknown` |  |

Keep personal contribution, leadership, reference/prototype work, production operation and measured adoption distinct. Missing evidence is not proof of missing ability. Contradicted requires actual conflicting evidence. Do not silently strengthen tenure or make a preferred tool mandatory.

## Employer and role fit

How well do the known role terms support the candidate's explicit goals and constraints?

| Goal, preference or constraint | Must-have / nice-to-have | Candidate source/date | Role term: exact source and quote | Aligned / conflict / unknown | Tradeoff or missing information |
| --- | --- | --- | --- | --- | --- |
|  |  |  |  | `unknown` |  |

Keep hard blockers visible. Company culture, actual team conditions and hiring flexibility remain unknown when the supplied sources do not establish them. Owner decisions and action budgets govern execution; they are not employer terms or proof of JD alignment. Never average these two sections into a match percentage.

## Decision and action

Advisory recommendation: `pursue / hold / decline / insufficient information`

Reason and decisive evidence: `<brief>`

Candidate's actual decision and date: `<pending, or explicit owner decision>`

Current next action: `<one bounded useful step, or none>`

If a step is useful: `<prerequisite, deliverable, estimated effort, what result changes the decision>`

Return condition, if the owner supplied one: `<condition, or none>`

An existing defer/stop permits no work now. A new material fact may be shown for reconsideration without automatically reopening work. Do not manufacture investigations, documents, reminders or exercises.

## Evidence review records

Original assessment snapshot and SHA-256: `<review bundle/assessment.original and bound digest>`

JD-fit review: `<bundle/jd-fit.review.json; reviewer/method/status>`

Employer-fit review: `<bundle/employer-fit.review.json; reviewer/method/status>`

Record receipt and optional revised assessment: `<bundle/receipt.json; revised path or none>`

Create the original snapshot with `graders/review.py init` before reviewing or editing this assessment; finalize both completed review drafts as described in the installed README. Keep review records separate from the working assessment. A saved review is not semantic certification.

## Evidence review findings

Material omissions / unsupported or overstated claims / unresolved contradictions: `<findings or none>`

Review method and reviewer: `<agent/human rubric review; optional normalized checker run or not run>`

Optional checker: `<packet and raw-answer digests, result paths, pass/fail/needs_review/invalid by fragment, review still needed>`

Preserve the exact original answer and distinguish factual review from candidate usefulness and hiring outcomes. A valid quote or a completed checker command does not certify the whole assessment. This is advisory, not a hiring probability or ATS score.
