# Local Git for the career workspace

On a local first run, make Git part of the normal workflow: preserve an existing repository rooted in the chosen career folder, or initialize one there. The source checkout and the candidate's career folder are separate repositories. No GitHub account, remote or network connection is needed.

With Python 3.9+ and Git installed, run from the career folder:

```sh
python3 .maguire/kit/tools/workspace_git.py --workspace . init
python3 .maguire/kit/tools/workspace_git.py --workspace . status
```

Initialization does not import, stage or commit career documents. It preserves existing repository configuration, ignore rules and instructions. For a newly created repository only, `.git/info/exclude` keeps installed kit, downloaded releases and discoverable skill copies out of routine status. Career records remain visible. If the folder belongs to a parent repository, the helper stops instead of silently committing into that parent or creating a nested repository. Choose the intended repository root or a separate career folder deliberately.

## Review and save a checkpoint

Review the changed files after a coherent piece of authorized career work. Use explicit paths so unrelated files stay out of the checkpoint:

```sh
python3 .maguire/kit/tools/workspace_git.py --workspace . diff --path cv-index.md --path data/applications.md
python3 .maguire/kit/tools/workspace_git.py --workspace . checkpoint --path cv-index.md --path data/applications.md --message "Record reviewed CV source and application decision"
```

The helper returns JSON. `status` includes untracked files. `diff` separates working, staged and untracked previews, each bounded to 200 lines by default; use `--max-lines` from 1 to 1000 when needed. Binary or large untracked documents are named for separate inspection. A truncated preview is not a complete review: narrow `--path` or inspect the named file before committing it.

A checkpoint requires individual relative file paths, not directories, wildcards or `git add .`. Tracked deletions are supported. The helper refuses symlink paths, paths outside the career folder, managed kit payload, ignored files and unrelated staged changes. It does not force-add or unstage the owner's files. Existing Git hooks and filters retain their ordinary behavior. If a hook rejects a checkpoint, the helper restores its own staging when the index has not changed independently; inspect `status` after an error. Do not run simultaneous index-changing commands in another tool while checkpointing.

Git needs the candidate's real chosen commit identity. Existing local or global configuration is used. When it is missing, the helper stops before staging; it does not invent a name or email. The candidate can set their preferred identity for this repository only:

```sh
git config --local user.name "Your chosen name"
git config --local user.email "Your chosen email"
```

Use actual chosen values rather than these placeholders. A private local repository does not require an employer or public email address. These commands change this repository's configuration only.

## Inspect and recover an earlier version

```sh
git log --oneline -- cv-index.md
git show <commit>:cv-index.md
```

Replace `<commit>` with the selected checkpoint hash. Inspect the old version, then save it under a **new** filename before deciding whether to replace the current file. For example, an agent can retrieve the bytes with `git show` and write `recovered/cv-index-<commit>.md` using exclusive creation. Preserve the current version and show the comparison. The helper intentionally provides no destructive reset, clean or restore command.

Keep coherent local checkpoints as work progresses, and tell the candidate which paths and commit were saved. Do not push, add a remote or publish career records merely because Git is initialized. A local commit records file history; it is not evidence that an application was sent. Git history is not an off-machine backup.

## Cloud and phone use

This workflow requires access to the actual career filesystem and a Git executable. Git initialized in a temporary cloud runtime is history in that runtime, not on the candidate's computer. State the real storage location and its persistence limits. A cloud agent without local access should return named files for the candidate to save and checkpoint locally; do not claim that local Git was configured.
