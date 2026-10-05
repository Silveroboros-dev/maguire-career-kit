# Maguire Career Kit

Turn your career experience into a reusable evidence bank. Assess a job against that evidence, prepare a CV or application draft, and keep a record of what you actually sent.

This is a small, file-based kit for your own agent and private workspace: instructions, blank templates, synthetic examples, and an optional Python installer. You review the claims and decide what to send.

[Maguire Agent](https://maguire-agent.silveroboros.chatgpt.site/) · [Full setup guide](kit/README.md) · [Worked example](kit/examples/end-to-end/README.md)

## Start on a computer

Download or clone this source repository, keeping it separate from your private career folder. With Python 3.9 or later, run:

```sh
git clone https://github.com/Silveroboros-dev/maguire-career-kit.git
cd maguire-career-kit
python3 kit/install.py /absolute/path/to/your-private-career-folder
```

Open that career folder as your primary Codex project. Follow the [first-run instructions](kit/README.md#first-run-adopt-the-existing-folder) to adopt an existing archive, or the [empty-archive instructions](kit/README.md#if-you-do-not-have-a-career-archive-yet) to begin with the documents and stories you have.

The installer copies instructions and blank reference templates. It does not import your CV, create career facts, submit applications, or connect accounts. It preserves conflicting local edits and leaves an incoming copy for review.

## Start on a phone

Follow the [mobile guide](https://maguire-agent.silveroboros.chatgpt.site/kit/#mobile). If ChatGPT Work Cloud is available to you, provide the kit instructions and the documents you choose in a private project. Start with one CV and one job description; ask for a fit assessment and a reviewable draft. Save the resulting records and verify that a new task can read them.

This is a manual route, not an installed mobile plugin. Work persistence and independent phone onboarding still need testing. Cloud use means the files you provide are processed by that platform; a private cloud project is not storage on your phone.

## What is included

- `kit/skills/`: the career-workspace workflow.
- `kit/templates/`: blank bank, CV index, preferences, application and submission records.
- `kit/examples/`: fictional candidate scenarios, explicitly separated from real records.
- `kit/install.py` and `kit/tests/`: standard-library installer and preservation checks.

Keep real CVs, identity documents, client information, credentials and applications outside this repository. Do not upload them in issues or pull requests. Fit judgments are advisory; the kit does not promise interviews, an ATS bypass, or hiring probabilities.

## Development and status

Run the installer checks from the repository root:

```sh
python3 -m unittest discover -s kit/tests -v
```

This repository packages the file-based v0.1 kit with repository documentation. The original v0.1 download remains unchanged. There is no hosted job-search API, payment service, automatic update channel, or published installable plugin in this package.

This repository is currently a release mirror of the existing Maguire development kit, which remains the editable source until an explicit handover. Report improvements through GitHub issues or pull requests. Accepted changes must be reconciled with that source before the next release; the two copies are not developed independently.

## License and credits

Released under [MIT](LICENSE). See [credits](CREDITS.md) for the career-ops project that helped inform the workflow.
