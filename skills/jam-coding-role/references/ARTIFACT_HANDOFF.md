<!-- managed-by: jam-coding-role -->
# Explicit artifact handoff

Artifact handoff is an optional stage-delivery capability. Run it only when the Owner requests a bundle or a named scientific stage explicitly defines artifact delivery. It is not part of ordinary task closure.

## Selection boundary

Use a positive allowlist over relevant untracked/ignored outputs. Scan sensitive names and small text content, reject symlinks, enforce file/bundle limits, and require explicit checkpoint opt-in. Never package the entire untracked tree.

## Single-file cloud limit and semantic splitting

The default cloud-facing ZIP limit is **95 MiB (99,614,720 bytes)**, not 100 MiB. The margin accommodates connector encoding and implementation differences observed with the shared `Pro_Space` folder.

When the full bundle exceeds the limit:

1. create ordinary, independently readable ZIP archives grouped by meaning;
2. prefer names such as:
   - `source_and_configs.zip`;
   - `logs_and_metrics.zip`;
   - `plots_and_evidence.zip`;
   - `checkpoints_part01.zip`;
3. when one semantic group still exceeds the limit, create further ordinary files such as `logs_and_metrics_part01.zip` and `logs_and_metrics_part02.zip`;
4. place a plain-text `BUNDLE_INDEX.md` beside the archives, explaining order, purpose, exact contents, compressed size and anything not packaged;
5. do not add SHA-256 fields to the stage bundle index.

Do **not** create `.z01/.z02/.zip`, `.zip.001`, or similar split-volume archives. A cloud planner usually cannot open one part independently and should not be required to download and reconstruct a local multipart archive.

A single checkpoint that still exceeds 95 MiB after ZIP compression must not be binary-sliced. Exclude nonessential models. An essential oversized checkpoint may use a separately authorized, authenticated rclone exception, but that binary is not assumed to be readable through the normal cloud connector.

## Release namespace

Use one immutable namespace per handoff:

```text
Pro_Space/<project>/<worktree>/<stage>/<timestamp>__<git-short-sha>/
```

Each release contains `BUNDLE_INDEX.md`, `BUNDLE_MANIFEST.json`, `PRO_HANDOFF.md`, and one or more standard ZIP files. Create new releases only; do not overwrite, move, or delete previous releases.

## Authorization and upload

Packing and upload require an explicit Owner request or named stage-closure trigger. The public-write Drive permission is standing authorization for create-only stage artifacts, not authorization to upload arbitrary files, credentials, or an unscreened worktree.

Choose upload capability in this order:

1. connected Google Drive upload action;
2. reliable browser/computer-use upload;
3. authenticated rclone;
4. otherwise produce the release locally and report `NOT_UPLOADED`.

A public editor link does not become anonymous Drive API credentials. Record an upload receipt only after the destination is verified.
