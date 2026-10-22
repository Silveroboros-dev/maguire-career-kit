# Maguire Career Kit

Turn your career experience into a reusable evidence bank. Assess a job against that evidence, prepare a CV or application draft, and keep a record of what you actually sent.

This is a small, file-based kit for your own agent and private workspace: instructions, blank templates, synthetic examples, and an optional Python installer. You review the claims and decide what to send.

Release v0.1.7 includes Git checkpoints in your actual career folder, Markdown-to-DOCX/PDF export using an existing resume's design, and a tool that queries and updates the application register without loading it all into agent context. The Git helper reuses a repository rooted in that folder or initializes one there; Git in a cloud runtime is not a local copy on your computer. Python helpers use the standard library. The agent reuses available document tools or follows the [free export setup instructions](kit/tools/EXPORT.md#install-the-free-fallback-when-needed) for missing Pandoc/LibreOffice converters.

[Maguire Agent](https://maguire-agent.silveroboros.chatgpt.site/) · [Download v0.1.7](https://github.com/Silveroboros-dev/maguire-career-kit/releases/tag/v0.1.7) · [Full setup guide](kit/README.md) · [Worked example](kit/examples/end-to-end/README.md)

## Your career workspace

One private workspace holds three connected parts: your CV versions, a bank of career stories and evidence, and records for each role you assess. Preferences and a single application register connect them. Your agent can compare a role's requirements with examples from across your career and reuse those records for the next application. See the [record map and ownership rules](kit/README.md#how-your-career-workspace-fits-together).

## Two fit assessments

For each role, Maguire applies two separate agent rubrics:

- **JD fit:** your documented experience against the role's material requirements.
- **Employer/role fit:** the stated role terms against your goals, preferences and hard constraints.

Both include separate 0–5 half-point scores, judgment ranges, sources, gaps and unknowns. An unscored axis is allowed only when required candidate evidence or goals are genuinely absent, with the missing input named. The ranges express reviewer judgment, not statistical confidence. Local assessments preserve the original answer and separate source-bound rubric review records with the [review helper](kit/README.md#saved-rubric-reviews). A strong result on one side does not erase a blocker on the other. Your decision remains yours, including deferring or stopping with no extra work.

The release includes the existing v8 offline claim checker in two modes for optional evidence checking. It requires explicitly normalized claims and reviewed source anchors; it does not automatically understand a CV or certify a whole answer. Unsupported cases remain `needs_review`. See the [grader guide](kit/graders/README.md).

## Start on a computer

Clone the release source, keeping it separate from your private career folder. With Python 3.9 or later, run:

```sh
git clone --branch v0.1.7 https://github.com/Silveroboros-dev/maguire-career-kit.git
cd maguire-career-kit
python3 kit/install.py --portable /absolute/path/to/your-private-career-folder
```

For the extracted release ZIP instead, run `python3 install.py --portable /absolute/path/to/your-private-career-folder` from the extracted `maguire-career-kit-v0.1.7/` directory. The ZIP places `install.py` at its root; the source repository keeps it under `kit/`.

Portable mode installs the complete kit under `.maguire/kit/` and explicitly loads its canonical skill without writing to protected `.agents` paths. Omit `--portable` in an ordinary terminal if a discoverable skill copy is wanted. Downloaded releases may be stored in a disjoint `.maguire/download/` folder inside the private workspace.

Open that career folder as your primary Codex project. Follow the [first-run instructions](kit/README.md#first-run-adopt-the-existing-folder) to adopt an existing archive, or the [empty-archive instructions](kit/README.md#if-you-do-not-have-a-career-archive-yet) to begin with the documents and stories you have.

The installer copies instructions, blank reference templates, both grader rubrics, the optional offline Python checker and local workflow tools. It does not execute those tools during installation. On first local onboarding the agent sets up or reuses Git in your career folder, uses your existing resume as the design reference, and operates on the one application register through the helper. It does not import your CV, create career facts, submit applications, or connect accounts during installation. It preserves conflicting local edits and leaves an incoming copy for review.

## Start on a phone

Follow the [mobile guide](https://maguire-agent.silveroboros.chatgpt.site/kit/#mobile). If ChatGPT Work Cloud is available to you, provide the kit instructions, both fit rubrics and the documents you choose in a private project. Start with one CV and one job description; ask for a fit assessment and a reviewable draft. Save the resulting records and verify that a new task can read them.

This is a manual route, not an installed mobile plugin. Work persistence and independent phone onboarding still need testing. Cloud use means the files you provide are processed by that platform; a private cloud project is not storage on your phone.

## Other agents

Use the [manual local or cloud path](kit/README.md#other-agents). Give the agent the kit README, workspace rules, skill, both fit rubrics, and only the templates and career files needed for the task. A cloud agent without access to your career folder must return named records for you to save in a location you control. The optional installer does not guarantee that another client discovers the Codex-oriented files; check the client's actual project instructions and storage before relying on continuity. No other-agent onboarding has been independently tested.

## What is included

- `kit/skills/`: the career-workspace workflow.
- `kit/templates/`: blank bank, CV index, preferences, application and submission records.
- `kit/examples/`: fictional candidate scenarios, explicitly separated from real records.
- `kit/graders/`: JD-fit and employer-fit rubrics, optional offline v8 claim checks, source bindings and fictional examples.
- `kit/tools/`: local Git control, DOCX/PDF export and bounded application-register operations, with task-specific instructions.
- `kit/install.py` and `kit/tests/`: standard-library installer, grader and preservation checks.

Keep real CVs, identity documents, client information, credentials and applications outside this repository. Do not upload them in issues or pull requests. Fit judgments are advisory; the kit does not promise interviews, an ATS bypass, or hiring probabilities.

## Development and status

Run the installer checks from the repository root:

```sh
python3 -m unittest discover -s kit/tests -v
```

The current release is v0.1.7. It adds local Git control, resume-reference DOCX/PDF export with a free-converter setup cheat sheet, and bounded application-register operations. It retains the separate numeric JD-fit and employer-fit judgments and version .2 saved review records introduced in v0.1.6. The optional v8 claim checker is unchanged and retains its explicit manual normalization/review boundary. The workflow respects owner defer/stop and separates execution policy from employer evidence. Earlier records remain readable; the installer preserves local edits and candidate-owned data.

The installer copies all three local workflow tools in normal and portable modes; it leaves candidate records untouched and installs no converter packages. When export is requested, the agent first uses suitable available tools without a new purchase. Otherwise it follows the skill's setup cheat sheet to install missing free Pandoc for DOCX and LibreOffice/`soffice` for PDF, then verifies a sample export. The [export guide](kit/tools/EXPORT.md) separates file conversion from layout/text inspection and candidate approval.

From v0.1.1 onward, this repository is the authoritative kit source. The former Commerce copy is a historical baseline. The Maguire website is a separate project: it hosts the customer journey and copies of released artifacts. Its page sources are not included here. Report improvements through GitHub issues or pull requests.

Release ZIPs include the kit README and installer at the top level, plus `LICENSE` and `CREDITS.md`. GitHub Releases provide the ZIP and detached manifest; the separate Site distributes copies of released artifacts and may need synchronization after a release. The manifest records the full source commit, tag, original path and hash of each file, and archive hash. Compare the commit and assets on GitHub; a checksum hosted beside a ZIP proves matching bytes, not an independent signature of origin.

To reproduce a release from its committed tag:

```sh
python3 scripts/build_release.py v0.1.7 /absolute/path/to/release-output --release-date 2026-10-22
```

The build requires Git and a clean source checkout. It reads committed files, writes outside this repository, and never packages the Site pages or candidate records. There is no hosted job-search API, payment service, automatic update channel, or published installable plugin in this package.

Pushing a new `vMAJOR.MINOR.PATCH` tag runs the repository's release workflow: it tests the tagged source, builds the ZIP, checksum and manifest, uploads all three to a draft GitHub Release, then publishes after checking the complete asset set. Existing releases are preserved. The separate Site must receive the same generated files and updated download links.

## License and credits

Released under [MIT](LICENSE). See [credits](CREDITS.md) for the career-ops project that helped inform the workflow.
