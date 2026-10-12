# v4: explicit normalization and bounded claim comparisons

2026-10-12. Authorized: implement v4, keep v3 frozen, evaluate the same 40 cases,
offline, no API/network/install/Git mutation/commit/push. Work only in this folder.
Root integrates; checker worker owns checker.py/tests/test_checker.py; normalization
worker owns migrate_annotations.py/normalized/*/NORMALIZATION_CHANGES.md; reviewer
owns review/* and optional tests/test_review_probes.py; root owns everything else.
No branch/fetch: user's offline/no-Git instruction takes priority over generic
parallel branch workflow. Models: worker gpt-6-sol/high, shared environment.

## Evaluation and limits

This is a known-case regression, not a new blind holdout. Authors and implementers
may inspect v3 failures. Copy raw and gold byte-for-byte from v3-new-cases; keep all
40 fragments, 81 claim identities and 14 gold error identities. No post-run gold
changes or cohort exclusions. Human approval is false. Manual semantic annotation
is reviewed by another agent; raw-text extraction and real source truth are not
tested. The scope is selected fragments, not whole career advice or interview odds.

Fix incorrect typed normalization, including assertion/conditional/advice distinctions,
and add bounded generic operations with explicit source references. No case IDs,
source labels, quote text, gold labels or prose-trigger shortcuts in runtime rules.
Review unknown operations; do not turn every unsupported factual claim into review.
Unsupported inventions (e.g. a certificate not established in supplied evidence)
remain factual failures under a complete reviewed packet. Unknown comparator
capability/context is distinct from absence of evidence for an ordinary assertion.

## Runtime

v3_core.py is an exact local copy of frozen checker, SHA256
e4b2699f543e4260128ebfabd61547c92b5c1dba3497acd07ca2f7007f225e33.
Do not edit that copy. checker.py wraps/reuses its validators and direct comparison;
all v4 changes live separately. No file/network/process access during grading.

SCHEMA.md defines explicit source reference operations and entity/context rules.
The source/claim semantic annotations contain no expected outcome. The grader
computes results from referenced, eligible facts and relevant competing facts;
a reference is a proposed proof operand, never an authority to pass a claim.
Output must retain per-claim evidence IDs, rule, axes and explanation.

## Gates and measures

Before the measured run: semantic annotation review, checker adversarial tests,
harness tests, structural/anchor audit, read-only contract challenge, freeze.
Synthetic tests may execute during development; no whole-cohort predictions until
freeze. Freeze code, annotations, unchanged raw/gold, review, all predecessor hashes
and ordered packet identities. Execute one local run; store predictions before
measurement. Preserve failures; do not change frozen code/data after seeing scores.

Show by family and overall: bad->pass (miss), good->fail (false rejection), all
needs_review split by gold class, ambiguous forced decisions, invalid and execution
errors. Retain denominator40 and intended faulty-claim localization. Compare to
saved v3 results without rerunning v3. Separately review causal explanations:
flagging a bad claim via a generic gap does not prove its true defect was established.
No aggregate accuracy combining abstentions and decisions. Local hashes/sizes
are integrity metadata, not external signatures or human endorsement.
