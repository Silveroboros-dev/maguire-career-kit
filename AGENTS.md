# Maguire kit source repository

This is a software distribution, not a candidate career workspace. Do not create a CV bank, application register, or personal profile here. `kit/AGENTS.md` is part of the installable payload: it governs a candidate's separate workspace after installation, not this source repository.

Keep changes small and preserve the installer's candidate-data boundary. It owns only its managed instructions and reference templates; it must preserve existing CVs, banks, registers, submitted artifacts, project rules and local edits. Do not add accounts, payments, external services or dependencies without a concrete need and owner authorization.

Use synthetic fixtures for examples and tests. Never commit candidate data, secrets, identity documents, private client details or real application artifacts. Read README.md and CREDITS.md before modifying the distribution. Run `python3 -m unittest discover -s kit/tests -v` for installer changes and report what was verified. Do not imply that a local test proves cloud/mobile behavior.

From v0.1.1 onward, this repository is the authoritative kit source. The former Commerce copy is a historical baseline; do not develop it as a competing master. The Maguire Site is a separate project containing pages and generated release copies, not the kit authoring source. Build releases from a committed tag using `scripts/build_release.py`; preserve older released bytes. Update `REQUIRED_TEMPLATES` when adding a required template. Commit, push, release and publish only within the owner's authorized scope.
