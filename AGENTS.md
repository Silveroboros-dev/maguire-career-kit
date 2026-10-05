# Maguire kit source repository

This is a software distribution, not a candidate career workspace. Do not create a CV bank, application register, or personal profile here. `kit/AGENTS.md` is part of the installable payload: it governs a candidate's separate workspace after installation, not this source repository.

Keep changes small and preserve the installer's candidate-data boundary. It owns only its managed instructions and reference templates; it must preserve existing CVs, banks, registers, submitted artifacts, project rules and local edits. Do not add accounts, payments, external services or dependencies without a concrete need and owner authorization.

Use synthetic fixtures for examples and tests. Never commit candidate data, secrets, identity documents, private client details or real application artifacts. Read README.md and CREDITS.md before modifying the distribution. Run `python3 -m unittest discover -s kit/tests -v` for installer changes and report what was verified. Do not imply that a local test proves cloud/mobile behavior.

This checkout is a release mirror, not an independently maintained source master. Keep the source handover explicit; reconcile accepted changes with the development kit before the next release and do not develop both copies independently. Commit, push, release and publish only within the owner's authorized scope.
