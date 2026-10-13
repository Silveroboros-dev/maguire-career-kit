# Bounded temporal comparison in v8

`temporal.check(claim, packet, at, direct)` adds three typed implications to the existing direct comparison. It receives the direct result and returns a replacement result only when one of these shapes applies:

- A positive, completed `certification_exam` or `course_completion` dated by `time.month` supports an otherwise identical assertion in the containing `time.year`. It checks the event type, subject, object, scope, modality, source eligibility and observation time. A denial confined to one month does not deny an event for the whole year.
- A candidate's positive `certificate_status` with `scope.status=active` and `time.until=YYYY-MM` supports active status at the decision date when the queried month is strictly before the end month. The end month itself is unresolved because no day or inclusive endpoint is supplied.
- A dated `certificate_expiry` before the decision date, combined with an explicit negative `certificate_renewal` for the same subject and certificate, supports inactive status at that date. A missing or competing renewal record leaves the claim unresolved. A positive active status for the same date conflicts with the expiry implication.

The status rules run only for `time.at` equal to the decision date. The module ignores withdrawn, future-observed, or explicitly superseded candidate sources. It merges temporal implications with the direct result's support and counter evidence; conflicts become `needs_review`. Invalid dates, uncertain boundaries, missing renewal, and material competing renewal evidence do not create a pass.

Verification: `python3 -B -m unittest discover -s evals/career-quality-v8/tests -p test_temporal.py -v` passed 14 synthetic tests. The independent `test_review_probes.py` suite also passed during full discovery. No target 40-case grader was executed for this module.

This is not a general time reasoner. It relies on manually normalized source facts and does not infer arbitrary date intervals, partial months, or whether a credential was renewed after the last observed source when no such fact is in the packet.
