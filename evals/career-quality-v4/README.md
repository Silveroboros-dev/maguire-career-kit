# Career claim graders v4 — known-case offline regression

v4 fixes the normalization/checker contract and adds bounded comparisons in an
isolated folder. Frozen v3 and its saved results remain unchanged. Nothing here
changes the installable `kit/`, external services or the engineering benchmark.

This run reuses the exact 40 raw fragments and gold annotations from the previous
v3 challenge: 24 acceptable, 12 defective, 4 ambiguous. It is a development
regression on known cases, not a fresh holdout. Source/claim interpretation is
manual and agent-reviewed, not human-approved. No raw-text extractor is tested.

## What changed

`SCHEMA.md` defines the actual annotation API: same canonical properties, explicit
fact references, source eligibility, modality, context and period semantics.
Derived claims request a computation; they do not carry an expected answer.
The checker implements numeric constraint comparison, permission-envelope checks,
explicit unresolved status, approval conditions, onboarding exceptions and local
schedule cutoffs. Generic unsupported operations remain reviewable. Ordinary
unsupported inventions remain factual errors under a complete reviewed inventory.

Direct fact comparison gains bounded positive-event existence and elapsed-month
entailments. `v3_core.py` remains an exact byte copy of the old core; `checker.py`
contains v4 changes in a separate wrapper. The copied base is included in the
freeze. No old files are imported as a mutable editing master.

Raw/gold are byte-identical copies. `migrate_annotations.py` reads only old
annotations and raw text, not gold or predictions. It preserves all 81 original
claim IDs and quote spans. Changes and the PF3N-04 interpretation caveat are
documented in `NORMALIZATION_CHANGES.md`. Runtime never examines case labels or
prose to select an answer.

The PF3N-04 caveat is deliberately retained: the gold treats a described Saturday
rota as exhaustive, while strict annotation does not infer an unstated Sunday
prohibition. The run must report any resulting disagreement without changing gold
to improve the score. Unknown qualitative relevance, sufficiency, subset and
conditional operations may also remain `needs_review`.

## Run and evidence

Root owns integration, pipeline and measurement. Separate workers own checker and
normalization. A reviewer checks semantic fidelity and attacks comparisons with
synthetic negative probes before freeze. This is shared-environment agent review,
not externally independent validation.

`PREDECESSOR.json` binds 311 existing files. `FREEZE.json` binds code, annotation,
raw/gold, reviews and ordered content hashes before a single measured run.
`START.json` prevents a second measured start under the same freeze. The worker
reads only projected packets and blocks network/process access plus file I/O
during grading. Predictions are saved before measurement reads gold. `RECEIPT.json`
binds outputs by hash and size; these are local checks, not external signatures.

`measurement.py` keeps the v3 metric definitions, strengthens runtime-result
consistency checks and retains all 40 denominators. Compare the saved v3 and v4
results; v3 is not rerun. False rejections, accepted errors, review by gold class,
forced ambiguity decisions and technical errors stay separate. Flagging the right
claim ID is measured separately from whether the explanation finds the actual defect.

From the software repository root, no installation required:

```sh
python3 -B -m unittest discover -s evals/career-quality-v4/tests -v
python3 -B evals/career-quality-v4/pipeline.py audit
python3 -B evals/career-quality-v4/pipeline.py verify
```

The one-time measured run uses these commands after review is ready:

```sh
python3 -B evals/career-quality-v4/pipeline.py freeze
python3 -B evals/career-quality-v4/pipeline.py run
```

`audit` performs structural/anchor checks only. `verify` verifies bytes, projection,
measurement, baseline comparison and reporting without re-executing the checker.
Never regenerate frozen annotation in place. A later experiment needs a new
version/freeze and retains this evidence.

Read `ANALYSIS.md` for the Russian findings and `runs/v4-regression/REPORT.md` for
all 40 decisions. Full traces are in `measurement.json`, per-case v3/v4 comparison
in `comparison.json`, and separate semantic/preflight/result reviews in `review/`.

All work is offline Python standard library, with no commit, push or release.
