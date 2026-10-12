# Career claim graders v5 — offline known-case regression

This isolated successor fixes narrow normalization/checker inconsistencies found
in v4: direct stipend support, canonical day units, current unavailability versus
pending status, and explicit negative supersession. It preserves the 40 raw
fragments and gold, all claim identities, frozen v4 and earlier experiments.
The installable kit and engineering benchmark are unchanged.

Read [CONTRACT.md](CONTRACT.md) for scope, [SCHEMA.md](SCHEMA.md) for the annotation
API, and [NORMALIZATION_CHANGES.md](NORMALIZATION_CHANGES.md) for the exact migration.
The same known cases are reused; this is not a fresh holdout. Human approval is
false. Raw-text extraction and whole career advice are not evaluated.

Pre-run evidence: synthetic paired tests, normalization delta tests, structural
audit, separate agent annotation review and read-only contract challenge. Root
owns freeze/run; workers own disjoint files. No new dependency or network access.

From the software repository root:

```sh
python3 -B -m unittest discover -s evals/career-quality-v5/tests -v
python3 -B evals/career-quality-v5/pipeline.py audit
python3 -B evals/career-quality-v5/pipeline.py freeze
python3 -B evals/career-quality-v5/pipeline.py run
python3 -B evals/career-quality-v5/pipeline.py verify
```

`freeze`/`run` are one-time actions, to be performed only after ready reviews.
For an already completed run use `verify`: it checks predecessor/input/output
bytes and recomputes accounting without executing the checker. Migration refuses
to overwrite normalized data after FREEZE or START exists.

`PREDECESSOR.json` binds all 347 previous evaluation files. `FREEZE.json` binds the
v5 inputs/code and ordered packet identities. `START.json` and the run receipt
bind the one measured run; worker has no gold access. Local digests do not provide
an external seal. Review is agent-based, in a shared environment.

After the run, read [ANALYSIS.md](ANALYSIS.md) for the Russian findings,
[REPORT.md](runs/v5-regression/REPORT.md) for all decisions, and
[measurement.json](runs/v5-regression/measurement.json) for full claim traces.
`comparison.json` compares saved v4 with v5. Report accepted errors, false
rejections and review separately; an abstention is neither acceptance nor detection.

PF3N-04 gold/source interpretation and qualitative/conditional reasoning limits
remain explicit. No commit, push, release, integration or API call is part of this run.
