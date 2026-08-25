# Jam Coding Role v1.3.1 — Existing Project Update Guide

本更新是 v1.3.0 的最小增量，不重装 team state、memory、long-run 或 OMO/Claude 角色。

## 1. Update source

从 `Jam-Stark/AI_things` 的 `release/jam-coding-role-v1.3.0` 分支取得 `skills/jam-coding-role/`，确认 `VERSION` 为 `1.3.1`。

## 2. Managed core

按项目原有 flags 运行 `bootstrap.py refresh`，更新 `.ai/WORKFLOW.md`、`.ai/ARTIFACT_HANDOFF.md` 和 `.ai/ROLE_VERSION`。不要覆盖 project-owned runtime config、role TOML 或 durable memory。

## 3. Project-owned files

最小合并以下内容：

- root `AGENTS.md`：声明它是项目级 workflow authority；Main 自动选择 FAST/STANDARD/HIGH_RISK；STANDARD/HIGH_RISK 满足条件时不等待用户说“team”即可委托；更高层 system/developer 禁令仍优先。
- `.ai/PROJECT.md`：新增 Environment and command registry，并初始化 primary/train/eval/smoke 行。
- 使用 artifact handoff 的项目：合并 `.ai/artifact-sync.toml` 的 compressed-ZIP 注释和 `[pro_review]`；复制 `scripts/pro_review_handoff.py` 到 `.ai/scripts/`，复制 `templates/PRO_REVIEW_PROMPT.md` 到 `.ai/PRO_REVIEW_PROMPT.md`。

## 4. Cloud Pro handoff

Owner 请求 cloud Pro review 时，Main 依次完成：审查 diff -> commit in-scope changes -> push branch -> 验证 remote commit -> pack/upload -> 生成 `PRO_REVIEW_PROMPT.md`。若 review type 未给出，保留 Owner placeholder，不替用户猜测。

```bash
python .ai/scripts/pro_review_handoff.py \
  --repo . \
  --release-dir .ai/outgoing-artifacts/<release> \
  --drive-location 'Pro_Space/<project>/<worktree>/<stage>/<release>/' \
  --review-type '阶段验收' \
  --owner-request '检查本阶段效果并制定下一阶段方案'
```

## 5. Command registry maintenance

运行 train/eval/render/deploy 前优先使用 `.ai/PROJECT.md` 中已验证命令。命令成功后更新同一行的 exact command、environment、date 和 evidence；旧命令失效时先标记 `STALE`。

## 6. Verification

- `python -m py_compile .ai/scripts/pro_review_handoff.py`
- 确认每个 ZIP 的**压缩后文件大小**不超过 95 MiB；不是检查原始输入大小。
- 在临时或安全分支验证未 push 的 commit 会被 prompt helper 拒绝。
- 检查 v1.3.0 -> v1.3.1 diff 仅包含本指南列出的 route、handoff、command registry、prompt helper、tests 和 version logs。
