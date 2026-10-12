# Frozen v5 on new source/answer fragments

This experiment evaluates the unchanged v5 checker on 40 newly authored synthetic
fragments, 20 candidate-fit and 20 preference-fit. Only the dataset and harness are
new; checker.py, v3_core.py, grade_packets.py and measurement.py are exact copies
of the previously frozen v5 files. All 385 predecessor files are bound.

Authors receive the public annotation interface but no checker, old cases or
predictions. A separate agent first records raw-only semantic judgments, then
reviews gold and normalization. Root has prior exposure; all agents share a local
environment. This is not human-approved or a fully isolated human holdout.
Authoring history and review disagreements are preserved before freezing.

The intended correct/error/ambiguous mix is a coverage target, not a labeling
quota. Gold follows source truth. Candidate-fit concerns evidence of candidate
qualifications; preference-fit concerns preferences and employer conditions.
Wrong-family initial cases were replaced before any prediction, retaining history.

`novelty.py` screens prior v1/v2 sources and answer records, v3 selected fragments
and v3-new/v4/v5 raw corpora. Exact and word overlap do not prove new reasoning
families; the review reports structural overlap explicitly. Versioned screens
remain even if pre-freeze authoring changes.

From the repository root:

```sh
python3 -B -m unittest discover -s evals/career-quality-v5-new-cases/tests -v
python3 -B evals/career-quality-v5-new-cases/pipeline.py audit --review review/annotation_review_v2.json
python3 -B evals/career-quality-v5-new-cases/pipeline.py freeze --review review/annotation_review_v2.json --challenge review/challenge_packet_v2.json
python3 -B evals/career-quality-v5-new-cases/pipeline.py run
python3 -B evals/career-quality-v5-new-cases/pipeline.py verify
```

Freeze/run are one-time actions after ready reviews and content checks. `verify`
uses saved predictions, without rerunning the checker. Do not change frozen grader,
case labels or normalizations after the measured run. Keep invalid/error outcomes
in the 40-case denominator. No API, network, install, commit or push is required.

[CONTRACT.md](CONTRACT.md) defines scope and measurements.
[ANALYSIS.md](ANALYSIS.md) explains results in Russian after the run;
[REPORT.md](runs/new-cases-v5/REPORT.md) lists all cases and
[measurement.json](runs/new-cases-v5/measurement.json) preserves all claim traces.
Review, author attestations, FREEZE/START and run receipts provide local lineage,
not an external seal. No paired version-improvement claim is made on different cases.
