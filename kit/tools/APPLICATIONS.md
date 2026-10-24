# Application register helper

Use `applications.py` for routine register reads and changes instead of loading the entire application history into the agent's context. Python 3.9 or later is enough; there are no third-party dependencies or network calls. The helper never sends an application.

The existing candidate-owned `data/applications.md` (or the authoritative path in the workspace map) remains the **one register**. No database, JSON sidecar, or second ledger is created. JSON is only the command's response and the dated audit entries inside that same Markdown file. Existing role `notes.md` files can retain the candidate's longer decisions and source documents.

## Start or adopt

Run commands from the candidate's career workspace after installation. Always pass its actual authoritative register with `--register` **before** the subcommand. Do not point at the kit's blank reference template.

If there is already a register, query it first:

```sh
python3 .maguire/kit/tools/applications.py --register data/applications.md list --limit 10
```

The helper recognizes exactly the seven columns in `templates/data/applications.md`. It supports an existing register using that schema and removes only the exact empty shipped placeholder when adding a first record. It preserves existing prose, untouched rows, and all previous events. Fenced Markdown examples do not count as live tables.

For an existing custom schema, an error leaves the file unchanged. Keep using that authority; inspect only the needed rows with the available file tools, or agree an explicit in-place migration with the candidate. Do not initialize a competing register to make the helper work.

Only when no register exists, choose its path, create its parent directory if needed, and initialize:

```sh
mkdir -p data
python3 .maguire/kit/tools/applications.py --register data/applications.md init
```

`init` refuses to overwrite any existing file. Mutations refuse source-repository paths, `.maguire/kit/`, `.maguire/download/`, and `.agents/skills/` reference copies. The installer itself never creates or changes candidate records.

## Add, find, and update

Use a stable application ID already recorded in the role folder. Names below are fictional examples, not candidate evidence:

```sh
python3 .maguire/kit/tools/applications.py --register data/applications.md add --id APP-001 --role 'Fictional Co / Analyst' --jd-source 'inputs/JD.txt; captured 2026-10-21' --status considering --package applications/APP-001/ --next-action 'Candidate decides whether to proceed' --date 2026-10-21 --provenance 'Candidate requested assessment'

python3 .maguire/kit/tools/applications.py --register data/applications.md find --id APP-001
python3 .maguire/kit/tools/applications.py --register data/applications.md find --query 'Analyst' --limit 10
python3 .maguire/kit/tools/applications.py --register data/applications.md list --status draft --limit 10

python3 .maguire/kit/tools/applications.py --register data/applications.md update --id APP-001 --status draft --next-action 'Candidate reviews draft' --date 2026-10-22 --provenance 'Reviewable draft saved' --event 'Initial draft; unresolved claims remain excluded'
```

`add` requires `--id`, `--role`, `--date`, and `--provenance`; status defaults to `considering`. Missing JD source or next action is `Unknown`; the default package link is `applications/<id>/`. The helper records links, not new role folders or invented career facts. Adding a duplicate ID fails; use `update`. Updating an unknown ID fails.

`update` requires the ID, actual event date, provenance, and at least one field or `--event`. It changes only supplied fields and the last-event cell. Accepted fields are `--role`, `--jd-source`, `--status`, `--package`, and `--next-action`. Every actual mutation appends a dated audit event containing the previous and resulting record in the same atomic file change. An identical field update with identical date/provenance is a no-op unless an explicit event or send confirmation was supplied. There is no delete operation. Corrections and resubmissions add events rather than erasing earlier states.

Valid statuses are `considering`, `draft`, `reviewed`, `submitted`, `response`, `interview`, `outcome`, and `withdrawn`. Preparing a draft or reviewing it is not sending it. To move into `submitted`, supply an actual event date and provenance plus **either** `--confirmed-send` (explicit candidate confirmation) **or** `--submission-evidence` (a reference to actual submission evidence):

```sh
python3 .maguire/kit/tools/applications.py --register data/applications.md update --id APP-001 --status submitted --date 2026-10-23 --provenance 'Candidate confirmed sending the reviewed package' --confirmed-send --event 'Exact sent artifacts retained in the role submitted folder'
```

Use that command only after such confirmation exists. These flags record the caller's statement; the helper does not authenticate evidence, inspect sent files, or prove sending. Preserve exact sent artifacts or the checked submission manifest separately. A follow-up update to an already-submitted row does not assert a new send; for a real resubmission, add a dated `--event` and explicit send confirmation/evidence again.

IDs are 1–80 letters, digits, dots, underscores or hyphens, starting with a letter or digit. Fields must be single-line text of at most 2000 characters; the last-event field includes date and provenance within that limit. Leading/trailing whitespace on new values is trimmed. Pipes and backslashes are escaped for the Markdown table and decoded in JSON results. Newlines/control characters, invalid ISO dates, unknown statuses, duplicate IDs, malformed rows and unsupported schemas fail without replacing the register.

## Small responses and local preservation

`list` and `find` return JSON with `records`, `matched`, `offset`, `limit`, and `has_more`. The default limit is 20; allowed limits are 1–100. Use `--offset 20` for a subsequent page. A missing exact ID returns an empty list. Text queries are case-insensitive and search the current row fields; they do not load audit history or source documents into the response. Add/update responses contain just the changed record and `changed` flag. Errors are JSON on stderr with a nonzero exit status.

The helper reads the Markdown file locally and filters it in Python, so the model receives only the selected records. It does not provide a persistent index or claim constant-time queries for arbitrarily large histories. Read a selected role's notes only when the task needs them. Without local Python execution, use a bounded direct read of the existing register and report that the helper was unavailable.

Writes use a same-directory temporary file, preserve POSIX permission bits where `os.fchmod` is available, flush the data and atomically replace the register. On Windows, which has no `os.fchmod`, the temporary file retains its inherited ACL; POSIX permission bits are not translated into Windows permissions. A neighboring `applications.md.lock` excludes other helper writers; an existing lock causes an error instead of waiting or guessing that it is stale. Do not delete a live writer's lock. After a crash, inspect the lock/process and current register before manually removing a stale lock. Existing file bytes are checked again before replacement to detect ordinary concurrent manual edits. Arbitrary external editors do not honor this cooperative lock; avoid simultaneous manual/helper edits. Symlink mutation paths are refused. A new register is created without overwriting a concurrently created file. Use a local filesystem supporting atomic replacement and hard links.

Keep the register and its audit history private, and use the workspace's local Git history for recovery. These are local file checks, not tests of mobile/cloud storage or proof of an application's delivery.
