# Two fit reviews and optional v8 claim checks

Read [jd-fit.md](jd-fit.md) to review **candidate evidence against JD requirements** and [employer-fit.md](employer-fit.md) to review **JD role terms against explicit candidate preferences**. These are two named human/agent review rubrics. They require the original JD, approved candidate facts/preferences, the exact Maguire answer, and cited source spans. Record a finding for every material requirement or supplied preference; retain unknowns and the original answer. An assessment is a reviewer judgment, not a calibrated match score or hiring probability.

The bundled Python v8 runtime checks **manually normalized atomic claims**, one fragment at a time. It does not extract claims from prose, decide whether an inventory is complete, score whole answers, or automatically resolve `needs_review`. `pass` applies only to the declared normalized fragment and coverage. A reviewer must check normalization, source completeness, materiality, and unresolved claims before accepting advice. Keep the raw answer and its digest next to the normalized packet. The runtime reports a canonical packet hash; it does not bind the original answer unless the operator records that link separately.

Both modes use the same frozen v8 checker bytes. Prepare JSON Lines rows shaped as `{"packet_sha256":"<SHA-256 of canonical packet>","packet":{...}}` using [SCHEMA.md](SCHEMA.md) and [V7_SCHEMA.md](V7_SCHEMA.md). The packet's `grader` must be `candidate_fit` for `jd-fit` or `preference_fit` for `employer-fit`. Hash canonical JSON with sorted keys, UTF-8, no ASCII escaping, no spaces, and no NaN. Keep exact source/answer quotes and coverage metadata; do not infer a complete packet from a single quote.

From an installed candidate workspace, using Python 3.9+ standard library only:

```sh
python3 .maguire/kit/graders/grade.py --mode jd-fit --packets jd-packets.jsonl --predictions jd-results.jsonl
python3 .maguire/kit/graders/grade.py --mode employer-fit --packets employer-packets.jsonl --predictions employer-results.jsonl
```

Output files are create-only. The CLI rejects a mismatched mode or malformed envelope before creating output. It preserves the v8 `packet_sha256`, result and `execution_error` envelope. Packet contents are career data: keep them in the candidate workspace, not the kit source or a public repository. This bundle contains only the runtime, rubrics, and schema notes; it contains no eval corpus, expected labels, or private material. [source-manifest.json](source-manifest.json) records the copied runtime bytes.
