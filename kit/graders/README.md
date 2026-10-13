# Two fit reviews and optional v8 claim checks

Read [jd-fit.md](jd-fit.md) to review **candidate evidence against JD requirements** and [employer-fit.md](employer-fit.md) to review **JD role terms against explicit candidate preferences**. These are two named human/agent review rubrics. They require the original JD, approved candidate facts/preferences, the exact Maguire answer, and cited source spans. Record a finding for every material requirement or supplied preference; retain unknowns and the original answer. Each assessable axis gets a separate 0–5 half-point score and judgment range, with source-based rationale. These are reviewer judgments, not calibrated probabilities.

## Save each rubric review

Use [review.py and its record format](REVIEW_FORMAT.md) to snapshot the original assessment and supplied sources before review. Fill the two separate draft records, including scores, using the rubrics above, then finalize them into `jd-fit.review.json`, `employer-fit.review.json` and a source-bound receipt. `needs_review` is a retained unscored result only when a required source or candidate goal is genuinely absent; it must name the missing input. `reviewed` means the reviewer completed the review and can include adverse or unknown findings. It is not a semantic PASS. This helper uses Python 3.9+ standard library and does not call models or perform semantic grading. See the [complete local workflow](../README.md#saved-rubric-reviews).

## Optional normalized-claim checker

The bundled Python v8 runtime checks **manually normalized atomic claims**, one fragment at a time. It does not extract claims from prose, decide whether an inventory is complete, score whole answers, or automatically resolve `needs_review`. `pass` applies only to the declared normalized fragment and coverage. A reviewer must check normalization, source completeness, materiality, and unresolved claims before accepting advice. Keep the raw answer and its digest next to the normalized packet. The runtime reports a canonical packet hash; it does not bind the original answer unless the operator records that link separately.

Both modes use the same frozen v8 checker bytes. Prepare JSON Lines rows shaped as `{"packet_sha256":"<SHA-256 of canonical packet>","packet":{...}}` using [SCHEMA.md](SCHEMA.md) and [V7_SCHEMA.md](V7_SCHEMA.md). The packet's `grader` must be `candidate_fit` for `jd-fit` or `preference_fit` for `employer-fit`. Hash canonical JSON with sorted keys, UTF-8, no ASCII escaping, no spaces, and no NaN. Keep exact source/answer quotes and coverage metadata; do not infer a complete packet from a single quote.

[PACKET_FORMAT.md](PACKET_FORMAT.md) gives the exact packet fields inherited by v8. The source kit also includes two **fictional development examples** in `graders/examples/`; they are not installed as candidate data. Their result `pass` or `fail` is limited to each declared normalized fragment, never a complete career decision.

From an installed candidate workspace, using Python 3.9+ standard library only:

```sh
python3 .maguire/kit/graders/grade.py --mode jd-fit --packets jd-packets.jsonl --predictions jd-results.jsonl
python3 .maguire/kit/graders/grade.py --mode employer-fit --packets employer-packets.jsonl --predictions employer-results.jsonl
```

Output files are create-only. The CLI rejects a mismatched mode or malformed envelope before creating output. It preserves the v8 `packet_sha256`, result and `execution_error` envelope. Packet contents are career data: keep them in the candidate workspace, not the kit source or a public repository. This bundle contains only the runtime, rubrics, and schema notes; it contains no eval corpus, expected labels, or private material. [source-manifest.json](source-manifest.json) records the copied runtime bytes.

From the **kit source** to inspect the fictional examples (choose unused output paths):

```sh
python3 kit/graders/grade.py --mode jd-fit --packets kit/graders/examples/jd-fit.jsonl --predictions /tmp/maguire-jd-example-results.jsonl
python3 kit/graders/grade.py --mode employer-fit --packets kit/graders/examples/employer-fit.jsonl --predictions /tmp/maguire-employer-example-results.jsonl
```
