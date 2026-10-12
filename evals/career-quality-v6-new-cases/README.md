# Frozen v6 on 40 new career-quality cases

This cohort tests the unchanged v6 runtime on 20 new candidate-fit and 20 new
preference-fit fictional source/answer fragments. Two separate agents authored
raw text, normalized propositions and gold labels. A third agent first judged
raw text alone, then reviewed normalization and gold before predictions.
No checker code, previous cases or target predictions were supplied to authors.
Root has seen earlier experiments. All author/reviewer work is AI-agent work;
`human_approved=false`. The boundary is instructional on a shared filesystem.

This is a contract-informed challenge. The public schema and its structural
addendum influenced encoding; it is not a statistically independent human
holdout. Text overlap is screened separately from reasoning-family overlap.
The initial 12/6/2 label proportions are targets only, never a reason to alter
source-supported cautious answers.

- [Contract](CONTRACT.md) and [authoring rules](AUTHORING.md)
- [Frozen original schema](FROZEN_SCHEMA.md) and [structural clarification](AUTHORING_API_ADDENDUM.md)
- [Raw sources and answers](raw/), [manual normalization](normalized/), [gold](gold/)
- [Review](review/), [run report](runs/new-cases-v6/REPORT.md), [analysis](ANALYSIS.md)

`checker.py`, `v3_core.py`, `grade_packets.py`, and `measurement.py` are exact
copies of frozen v6. The runtime's measurement schema still says v6 regression
because changing the frozen module would violate this experiment; this folder
and receipt identify the new cohort. `PREDECESSOR.json` binds all 492 preexisting
evaluation files, unchanged locally. The new harness only projects reviewed
facts/claims and measures saved outputs. Shape validation is not grading.

Local original experiment commands (complete local receipt tree required):

```sh
python3 -B -m unittest discover -s evals/career-quality-v6-new-cases/tests -v
python3 -B evals/career-quality-v6-new-cases/pipeline.py audit
python3 -B evals/career-quality-v6-new-cases/pipeline.py freeze
python3 -B evals/career-quality-v6-new-cases/pipeline.py run
python3 -B evals/career-quality-v6-new-cases/pipeline.py verify
```

Freeze and start are create-only; do not rerun them over recorded artifacts.
For the **public Git snapshot**, use `python3 -B evals/replay.py verify` instead.
Some local path-bearing receipts are omitted from Git, as documented by
[the publication boundary](../README.md#public-snapshot-versus-local-run-history).
Original frozen bytes stay local; published code, fixtures and saved predictions
are unchanged. No full historical-chain verification is claimed for that subset.

Metrics keep all 40 cases: erroneous accepted answers, false rejections of good
answers, review split by semantic gold, ambiguous forced decisions, invalid or
execution errors, and intended faulty-claim localization. Review counts neither
as acceptance nor successful detection. A rejected answer can still receive the
wrong explanation. Scores here say nothing about interview probability.
