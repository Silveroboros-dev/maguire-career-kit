# Candidate-fit raw revision history

All versions were authored offline before seeing checker code, previous cases, predictions, or results. The first version was sent to a raw-only reviewer; later wording corrections were disclosed to the integrator. Preserved files are byte-identical to the published SHA-256 digests.

| Version | File | SHA-256 | Bytes | Reason for revision |
| --- | --- | --- | ---: | --- |
| First reviewed | `reviewed-original.json` | `81349f4bd6e7a470bba5be821094e9b3407e487ccd637bef550d49a32d31d3c9` | 14,854 | CF5H-06 only said the new role required five onsite weekdays. The subsequent version makes the zero-remote-day rule explicit so the claimed three current remote days have direct contrary evidence. |
| Remote corrected | `remote-corrected.json` | `3fb5614f99fe5940af73ce7b23ed00a445b8e1ca92d20b41da0f0d42f4ae0ed9` | 14,886 | CF5H-11 described lab Kubernetes use and no production use. The subsequent version adds `only` to support the answer's exclusivity claim. |
| Before domain correction | `pre-domain-correction-raw.json` | `f14edd1549245510e196b3d79f850b3d6bcc7901816d0a8e3cf047e56b36ddee` | 14,891 | Integrator's pre-grader scope review found that nine cases evaluated role terms or personal preferences rather than candidate qualifications. The matching normalized, gold and attestation bytes are preserved beside this raw version. |
| Current candidate-evidence packet | `../../raw/candidate-fit.json` | `8ddcce7a7a0cdc9e9986dbc68eec5b4b436dc31b5b6cbda02d786f3a041404b5` | 15,635 | Replaced CF03, CF05, CF08, CF09, CF10, CF13, CF14, CF16 and CF18 with candidate skill, experience, credential, contribution and scope evidence. The other eleven raw rows are unchanged. An independent raw-only judgment was saved for this exact hash before the revised normalized/gold files were generated. |

The preserved pre-domain-correction normalized packet is `98a06b1893614c13eab0fb251eb62d9430641bca02de63417a4eeb57a6c4c987` (55,429 bytes); gold is `725e808684a0d3ec6b55a2feabe77f6ba1cd16e1943c93141162d99408b8b8f9` (5,517 bytes); attestation is `7db8ecc2fd73d00b1af8016ed6cb45bd1c8a881c5a2a572f86b3b2369ffb5b50` (3,383 bytes).

## CF5H-04 structural correction

The first candidate-evidence normalization used `time.start="2025"` and `time.end="2025"` on CF5H-04's two source facts and two claim readings. The public schema requires YYYY-MM for `start`/`end`; the raw source names only 2025. The correction uses `time.year="2025"` in those four propositions and invents no month. The old normalized packet is preserved as `pre-cf04-time-normalized.json` (`c476e98b42c8398aa8a624c0511b72a427ae3086668ba1ed8abc813c38130135`, 60,878 bytes); the matching helper and attestation are `pre-cf04-time-helper.py` (`9af9f8b9932ece873fca251c7a45916e2ad20e9e4fba29aef510a2317002491e`, 28,661 bytes) and `pre-cf04-time-attestation.json` (`6e850539a0271bf2eeaf8cba308ad8099c81c9a973229b25eaa8bddc9e1e8fba`, 5,033 bytes). The current normalized packet is `db3457cf314f3cf5e59b26ebeb6da17707ccfa256c4b8a1d00dd9cbb35df05eb` (60,750 bytes). Raw and gold hashes are unchanged. The prior review receipt remains immutable; a new structural review receipt is pending.
