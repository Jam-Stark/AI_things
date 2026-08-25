# Jam Coding Role v1.3.1 — Existing Project Update Guide

本更新是 v1.3.0 的最小增量，不重装 team state、memory、long-run 或 OMO/Claude 角色。后续 Pro 全量交付增补仍保持版本号 `1.3.1`。

## 1. Update source

从 `Jam-Stark/AI_things` 的 `release/jam-coding-role-v1.3.0` 分支取得 `skills/jam-coding-role/`，确认 `VERSION` 为 `1.3.1`。

## 2. Managed core

按项目原有 flags 运行 `bootstrap.py refresh`，更新 `.ai/WORKFLOW.md`、`.ai/ARTIFACT_HANDOFF.md` 和 `.ai/ROLE_VERSION`。不要覆盖 project-owned runtime config、role TOML 或 durable memory。

## 3. Project-owned files

最小合并以下内容：

- root `AGENTS.md`：声明它是项目级 workflow authority；Main 自动选择 FAST/STANDARD/HIGH_RISK；STANDARD/HIGH_RISK 满足条件时不等待用户说“team”即可委托；更高层 system/developer 禁令仍优先。
- `.ai/PROJECT.md`：新增 Environment and command registry，并初始化 primary/train/eval/smoke 行。
- 使用 artifact handoff 的项目：
  - 合并 `.ai/artifact-sync.toml` 的 compressed-ZIP 注释、`[naming]` 和 `[pro_review]`；
  - 更新 `.ai/scripts/stage_artifacts.py`；
  - 更新 `.ai/scripts/pro_review_handoff.py`；
  - 更新 `.ai/PRO_REVIEW_PROMPT.md`。

## 4. Cloud Pro handoff

Owner 请求 cloud Pro review 时，Main 依次完成：审查 diff -> commit in-scope changes -> push branch -> 验证 remote commit -> pack/upload Worker artifacts -> 生成 `PRO_REVIEW_PROMPT.md`。若 review type 未给出，保留 Owner placeholder，不替用户猜测。

```bash
python .ai/scripts/pro_review_handoff.py \
  --repo . \
  --release-dir .ai/outgoing-artifacts/<project>/<worktree>/<stage>/<release> \
  --drive-location 'Pro_Space/<project>/<worktree>/<stage>/<release>/' \
  --review-type '阶段验收' \
  --owner-request '检查本阶段效果并制定下一阶段方案'
```

### Same-folder delivery naming

新 handoff 的 Worker 输入和 Pro 全量输出放在同一任务目录：

```text
worker_delivery__source_and_configs.zip
worker_delivery__logs_and_metrics.zip
worker_delivery__plots_and_evidence.zip
worker_delivery__BUNDLE_INDEX.md
worker_delivery__BUNDLE_MANIFEST.json
worker_delivery__PRO_HANDOFF.md
pro_delivery__full_review.zip
```

历史 release 不需要改名。Prompt helper 优先识别 `worker_delivery__*.zip`，同时兼容旧的无前缀 Worker ZIP；已有 `pro_delivery__*.zip` 不会被误列为本轮审阅输入。

### Pro output

对话窗口按五项给 Owner 精简结果；第 5 项必须给出 Pro ZIP 地址和本地 Worker 解析 prompt。Pro 同时上传 `pro_delivery__full_review.zip`，其中包含：

```text
FULL_REVIEW.md
LOCAL_WORKER_PARSE_PROMPT.md
```

无法上传时必须写 `NOT_UPLOADED`，不得虚构 Drive 地址。

## 5. Command registry maintenance

运行 train/eval/render/deploy 前优先使用 `.ai/PROJECT.md` 中已验证命令。命令成功后更新同一行的 exact command、environment、date 和 evidence；旧命令失效时先标记 `STALE`。

## 6. Verification

- `python -m py_compile .ai/scripts/pro_review_handoff.py .ai/scripts/stage_artifacts.py`
- 确认每个 ZIP 的**压缩后文件大小**不超过 95 MiB；不是检查原始输入大小。
- 在临时或安全分支验证未 push 的 commit 会被 prompt helper 拒绝。
- 运行相关单元测试，确认 Worker ZIP/sidecar 前缀和 Pro full-review ZIP 约定。
- 检查本增补只修改 prompt、handoff helper、artifact naming/docs/tests 和 version logs；`VERSION` 仍为 `1.3.1`。
