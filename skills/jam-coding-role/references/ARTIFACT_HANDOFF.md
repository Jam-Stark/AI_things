<!-- managed-by: jam-coding-role -->
# Explicit artifact and cloud Pro handoff

Artifact handoff is an optional stage-delivery capability. Run it only when the Owner requests a bundle/cloud review or a named scientific stage explicitly defines artifact delivery. It is not part of ordinary task closure.

## Cloud Pro handoff order

An Owner request to send the current stage to a cloud Pro reviewer authorizes the **in-scope handoff commit and push** unless the Owner explicitly says otherwise. Main must still exclude unrelated changes and respect branch protection.

Before generating the cloud prompt:

1. inspect the Git diff and commit only the stage's Git-visible source/config/document changes;
2. push the configured current/review branch;
3. verify the remote-tracking branch resolves to the same commit as local `HEAD`;
4. record repository URL、branch and full commit SHA;
5. pack and upload the selected artifacts;
6. generate `PRO_REVIEW_PROMPT.md` naming the exact Drive release and ZIP files.

If commit/push is not authorized, branch policy blocks it, or the remote commit cannot be verified, stop and report the handoff as blocked. Do not give the cloud reviewer a prompt that claims access to unpublished code.

## Selection boundary

Use a positive allowlist over relevant untracked/ignored outputs. Scan sensitive names and small text content, reject symlinks, enforce file/bundle limits, and require explicit checkpoint opt-in. Never package the entire untracked tree.

## Compressed-ZIP cloud limit and semantic splitting

The default limit applies to the **final compressed size of each generated `.zip` file**, not to the raw source files inside it. Every cloud-facing ZIP must be at most **95 MiB (99,614,720 bytes)**; the margin below 100 MB accommodates connector encoding and implementation differences observed with `Pro_Space`.

When a generated ZIP exceeds the compressed-size limit:

1. create ordinary, independently readable ZIP archives grouped by meaning;
2. prefer names such as `source_and_configs.zip`、`logs_and_metrics.zip`、`plots_and_evidence.zip`、`checkpoints_part01.zip`;
3. when one semantic group still exceeds the limit, create further ordinary files such as `logs_and_metrics_part01.zip` and `logs_and_metrics_part02.zip`;
4. place a plain-text `BUNDLE_INDEX.md` beside the archives, explaining order, purpose, exact contents, **compressed ZIP size** and anything not packaged;
5. do not add SHA-256 fields to the stage bundle index.

Do not create `.z01/.z02/.zip`、`.zip.001` or similar split-volume archives. A single checkpoint whose own generated ZIP still exceeds 95 MiB must not be binary-sliced. Exclude nonessential models; an essential oversized checkpoint may use a separately authorized authenticated rclone exception.

## Release namespace

Use one immutable namespace per handoff:

```text
Pro_Space/<project>/<worktree>/<stage>/<timestamp>__<git-short-sha>/
```

Each release contains `BUNDLE_INDEX.md`、`BUNDLE_MANIFEST.json`、`PRO_HANDOFF.md`、`PRO_REVIEW_PROMPT.md` and one or more standard ZIP files. Create new releases only; do not overwrite, move or delete previous releases.

## Cloud Pro prompt requirements

The prompt must identify:

- remote repository URL、branch and exact commit;
- Google Drive release location and exact ZIP names;
- review type: diagnosis、stage acceptance、fact check、QA or Owner-specified equivalent; when absent, leave an obvious Owner placeholder;
- the cloud limitation: no access to unbundled local logs、resolved runtime、IsaacLab/GPU/hardware state;
- permission for local AI to make production-environment judgments rather than obeying over-strict cloud gates.

Required answer order:

1. any requested preliminary answer;
2. insight and findings;
3. the requested diagnosis/acceptance/fact-check/QA result;
4. optional novelty: overlooked algorithm、engineering or data contribution.

## Authorization and upload

Packing and upload require an explicit Owner request or named stage-closure trigger. The public-write Drive permission is standing authorization for create-only stage artifacts, not authorization to upload arbitrary files, credentials or an unscreened worktree.

Choose upload capability in this order: connected Google Drive upload action; reliable browser/computer-use; authenticated rclone; otherwise produce the release locally and report `NOT_UPLOADED`.

A public editor link does not become anonymous Drive API credentials. Record an upload receipt only after the destination is verified.
