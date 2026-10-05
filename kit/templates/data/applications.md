# Application register

This is the one authoritative register unless the workspace already has one. Updated: `<YYYY-MM-DD>`.

| Application ID | Employer / role | JD source and capture date | Status | Last event date and provenance | Package path | Next action / due date |
| --- | --- | --- | --- | --- | --- | --- |
| `<APP-001>` |  |  | `considering / draft / reviewed / submitted / response / interview / outcome / withdrawn` |  | `applications/<id>/` |  |

`Draft` means content exists but is unapproved. `Reviewed` means the candidate checked the content; it is not a send. `Submitted` requires a candidate-confirmed send or actual submission record and an event date. Keep response and outcome evidence separate. Do not create a second ledger or duplicate a row on rerun; update by application ID and preserve the dated event history in that application's `notes.md`.
