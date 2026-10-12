# V6 claim checker: known-case regression

This folder repairs manual normalization and extends bounded claim checks while
preserving frozen v5 and all predecessor artifacts. It evaluates the same 40
fictional fragments and the same semantic gold labels used in
`../career-quality-v5-new-cases/`. Raw/gold bytes, 61 claim IDs and quote anchors
are immutable. Only normalization, schema and checker/harness are revised here.

The implementers have seen v5 outcomes. This is development regression evidence,
not an independent holdout or a claim about general career-advice quality. Labels
and normalization are agent-authored and separately AI-reviewed, human_approved=false.
No live model or external API is called. No dependencies are installed.

[CONTRACT.md](CONTRACT.md) defines authority and evidence boundaries.
[SCHEMA.md](SCHEMA.md) defines the v6 normalization/checker contract.
[CHECKER_CHANGES.md](CHECKER_CHANGES.md) and
[NORMALIZATION_CHANGES.md](NORMALIZATION_CHANGES.md) describe changes and limits.
[ANALYSIS.md](ANALYSIS.md) records the measured outcome after the single run.

From the repository root, before the freeze:

```sh
python3 -B -m unittest discover -s evals/career-quality-v6/tests -v
python3 -B evals/career-quality-v6/pipeline.py audit
python3 -B evals/career-quality-v6/pipeline.py freeze
python3 -B evals/career-quality-v6/pipeline.py run
```

Freeze/run are exclusive, single-use actions after final ready reviews. Tests use
invented fixtures and must not grade the target 40 packets before freeze. The
worker saves predictions before the parent compares them against gold. No frozen
artifact or gold label is repaired in place after seeing outcomes.

To verify a completed run without regrading:

```sh
python3 -B evals/career-quality-v6/pipeline.py verify
```

`runs/regression-v6/REPORT.md` and `measurement.json` preserve all 40 outcomes,
missed accepted errors, false rejections, needs_review by gold class, technical
failures and claim localization. `comparison.json` joins v5/v6 by source/answer
content identity, not packet hash or presentation case number. All denominators
remain present. Both normalization and checker changed; this run alone cannot
attribute the measured delta to one of those stages.

PREDECESSOR binds 454 existing files. FREEZE, START, run receipt and post-run review
provide local lineage, not an external cryptographic seal. Source IDs can contain
case-like strings, but gold labels, titles and author reasons are not worker inputs.
No commit, push, integration, release or application submission is performed.
