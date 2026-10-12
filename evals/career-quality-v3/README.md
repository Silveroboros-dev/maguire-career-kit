# Career quality v3 — first offline claim checker

This folder is the implementation successor to `../career-quality-v3-design`.
It checks **manually normalized, agent-reviewed fragments**, not raw prose or
whole answers. It preserves separate candidate-fit and preference-fit inputs.
There are no dependencies beyond Python's standard library, provider calls,
model weights, services, product integration or installer changes.

The development cohort has 16 known fragments: 13 proposed material errors,
two acceptable fragments with identical wording in separate answers, and one
ambiguous fragment. Review expands them into 29 atomic claims. The two old
false-positive fragments do not establish whole-answer correctness.

## What runs

`checker.py` exposes `grade_fragment(packet)` and `check_claim(claim, sources,
context)`. The full strict contract is in [CONTRACT.md](CONTRACT.md). The public
fragment API validates source and claims hashes, enforces coverage, and returns
`pass`, `fail`, `needs_review` or `invalid`, with `whole_answer_verdict: null`.
The lower-level claim helper validates source binding; only the fragment API can
verify the hash for the complete claim list.

Source/answer statements have typed subject, predicate, object, polarity,
modality, scope, time and quantitative bounds. Registered rules compare those
fields; special bounded rules cover packet absence, recorded observation order,
source-instruction authority, hard preferences and recurring frequency ceilings.
There is no reading of quote prose and no automatic extraction. This is a
checker on a manually prepared representation of meaning.

Only reviewed, complete coverage can permit pass. Coverage verification includes
an agent-authored receipt checked by the runner; a pure checker cannot authenticate
a caller's reviewer flag. Source completeness means the supplied snapshot,
never all facts in the world. Findings identify exact original spans and inspected
source IDs. An absent matching proposition supports `not_established`, not
real-world impossibility. Cross-predicate causal bridges are not reconstructed:
for example a band-to-award error may be reported as missing support for the
personal award rather than a named fallacy about ranges.

## Local commands

From the repository root:

```sh
python3 -B -m unittest discover -s evals/career-quality-v3/tests -v
python3 -B evals/career-quality-v3/pipeline.py verify --output evals/career-quality-v3/runs/first-slice-v3
```

The original freeze and first run use:

```sh
python3 -B evals/career-quality-v3/pipeline.py freeze --review evals/career-quality-v3/review/normalization_review_v2.json
python3 -B evals/career-quality-v3/pipeline.py run --output evals/career-quality-v3/runs/first-slice-v3
```

These create files exclusively and must not overwrite an existing freeze or run.
For a reproduction on the exact frozen version, choose a new output directory.
For runtime/data changes, create a successor version. `prepare_data.py` is fixture
authoring code, not runtime; its output already exists. Do not rerun it over
reviewed or frozen data.

The worker consumes only `packets.jsonl`. It never reads expectations, mappings,
case names, mutation metadata or old verdicts. A Python audit hook prevents
network/process operations in that worker and I/O during the pure checker call.
This is a bounded local execution guard, not an OS sandbox for hostile code.
Predictions are saved before measurement reads the expectation file.

## Evidence and limits

- [NORMALIZATION.md](NORMALIZATION.md): choices and exposure. Initial draft
  normalization and its needs-changes review are preserved, followed by the
  revised ready review. “Manual” means agent review, not human approval.
- `data/normalizations.json`: typed fragments, initially marked unreviewed;
  projection upgrades the status only after checking the separate review.
- `data/expectations.json`: reference decisions used only for measurement.
- `PREDECESSOR.json`: exact prior v1/v2/design bytes.
- `FREEZE.json`: runtime, tests, packet-authoring inputs, reviews and prior drafts.
- `runs/first-slice-v3/`: anonymous packets, mappings, raw predictions, execution,
  measurement, report and local integrity receipt.
- `review/`: normalization, prefreeze code and post-run substantive review.

Report misses, false rejections, review and invalid separately. A review is not
an automatically detected error; an error found in one atom does not erase an
ambiguous second atom. Mechanical relation/span matching and substantive reason
review are distinct. No aggregate score represents real hiring odds or measured
accuracy of a free-text career adviser.

This is a known development regression with shared-environment agent review,
not a blind holdout. The predicates, manual parse and source completeness are
trusted inputs after review. Unsupported operations can abstain; exact scope/time
comparison is intentionally limited. The next independent question is whether
normalization can be performed reliably on new answers. The current run cannot
answer that question. Local hashes are drift evidence, not an external seal.

Future Maguire integration can call the pure API via a versioned adapter after
reviewing normalization coverage. Keep `needs_review` explicit. No changes to
the installable `kit/` have been made by this slice.
