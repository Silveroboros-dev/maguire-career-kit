# Offline career-quality evaluation experiments

Two distinct questions are evaluated: **candidate-fit** (are claims about a
candidate supported by the supplied career evidence and role?) and
**preference-fit** (do employer terms support the claimed match with explicit
candidate preferences?). These are bounded experimental checkers, not interview
probability estimates. The separate Polaris engineering benchmark is not here.

All source texts and example answers are fictional. Cases and semantic labels
were manually authored by AI agents and checked by another AI agent;
`human_approved=false`. These are development and contract-informed challenge
sets, not an independently collected human holdout or real Maguire output.

## Latest evidence and offline use

Start with [the new v6 cohort](career-quality-v6-new-cases/README.md), its
[results](career-quality-v6-new-cases/runs/new-cases-v6/REPORT.md) and
[analysis](career-quality-v6-new-cases/ANALYSIS.md). Frozen v6 code was tested
without adapting it to the new answers. Unknown cases and abstentions stay in
the denominator.

Python 3.9+, standard library only, from the repository root:

```sh
# Verify published hashes, reconstruct anchored inputs and recompute metrics
# from saved predictions. Does not execute the grader or make network calls.
python3 -B evals/replay.py verify

# Optional reproduction: use a NEW output directory outside evals/.
python3 -B evals/replay.py run --output /tmp/maguire-v6-replay

python3 -B -m unittest discover -s evals/career-quality-v6-new-cases/tests -v
python3 -B -m unittest discover -s evals/publication-tests -v
```

The replay worker blocks sockets/process creation and file access during grading
using Python audit hooks. This is a bounded local check, not an OS sandbox for
untrusted programs. No API key, live model, package installation or service is
needed. A replay is explicitly a reproduction, not a new unseen evaluation.

## Preserved experiment history

| Folder | Purpose |
|---|---|
| career-quality-v1 | 24 source cases, 96 example answers, first rule-based graders |
| career-quality-v2 | Known miss fixes and harder prose-level answers |
| career-quality-v3-design | Design for claim-level source, time, scale and modality checks |
| career-quality-v3 | First manually normalized claim checker, 16 examples |
| career-quality-v3-new-cases | Frozen v3 on 40 new cases |
| career-quality-v4 | Normalization contract fixes on the same 40 |
| career-quality-v5 | Further fixes on the same 40 |
| career-quality-v5-new-cases | Frozen v5 on another 40 new cases |
| career-quality-v6 | Expanded coverage and normalization on those same 40 |
| career-quality-v6-new-cases | Frozen v6 on 40 newly authored cases |

Historical statements about no commit/push describe those earlier runs. This
publication adds their reviewed synthetic artifacts to the source repository.
No installer, managed kit instructions, published release or product API was
changed. A future integration needs an explicit adapter and reviewed source
normalization; the checker cannot parse arbitrary career advice on its own.

## Public snapshot versus local run history

`PUBLICATION.json` binds every published file in this folder except itself,
and lists omitted files by path/hash. Original files with absolute private-host
paths remain local and are ignored by Git. No frozen original was redacted or
rewritten. Historic manifests can therefore refer to omitted local command or
review receipts: the complete historical receipt chain is **not** independently
verifiable from this public subset. Use `replay.py verify` for the public
snapshot, not the old `pipeline.py verify` commands in historical documents.

Public verification binds current bytes, checks that the four runtime files
match the original frozen v6 hashes, reconstructs all 40 anchored packets from
reviewed raw/normalized files, and recomputes measurement from saved predictions.
It does not prove who authored an earlier receipt, its wall-clock time, human
approval, or an external cryptographic seal.
