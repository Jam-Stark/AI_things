# Jam Coding Role v1.3.2 — Existing Project Update Guide

本更新只修复两点：Main 的主动委托执行力，以及 Cloud Pro 全量包的 Owner 转交方式。不要重装或重写 team state、hook、memory、long-run、OMO、Claude、训练代码或 durable memory。

## 1. Update source

从 `Jam-Stark/AI_things` 的 `release/jam-coding-role-v1.3.0` 分支取得 `skills/jam-coding-role/`，确认 `VERSION` 为 `1.3.2`。

## 2. Managed core

按项目原有 flags 运行 `bootstrap.py refresh`，更新：

```text
.ai/WORKFLOW.md
.ai/ARTIFACT_HANDOFF.md
.ai/ROLE_VERSION
```

不要覆盖 project-owned runtime config、role TOML 或 durable memory。

## 3. Project-owned minimal merge

最小合并：

- root `AGENTS.md`：加入 `Mandatory delegation gate`。非 FAST 任务在深度工作前检查独立 lane、specialist、独立 review/QA 和并行收益；命中后立即 spawn 最少必要 agent。未委托时记录 `NO_DELEGATION_REASON`。
- `.codex/TEAM.md`：同样加入 proactive gate，防止 Main 先自行完成研究、最后才说“可以委托”。
- `.ai/PROJECT.md`：在 Cloud Pro handoff 中配置 `Pro review document root`，例如 DoorDog 可填 `scriptsFORhuman/pro_reviews`。

## 4. Cloud Pro files

使用 cloud review 的项目更新：

```text
.ai/ARTIFACT_HANDOFF.md
.ai/artifact-sync.toml
.ai/scripts/pro_review_handoff.py
.ai/PRO_REVIEW_PROMPT.md
```

新流程：

```text
Worker artifacts -> Google Drive
Cloud Pro full ZIP -> attached in Pro conversation
Owner -> uploads that ZIP in local Worker conversation
Local Worker -> preserves and extracts it under the configured Pro review document root
```

Cloud Pro 不再尝试把 `pro_delivery__full_review.zip` 上传到 Drive。Drive 任务目录只保存 `worker_delivery__*` 输入包。

## 5. Prompt generation

```bash
python .ai/scripts/pro_review_handoff.py \
  --repo . \
  --release-dir .ai/outgoing-artifacts/<project>/<worktree>/<stage>/<release> \
  --drive-location 'Pro_Space/<project>/<worktree>/<stage>/<release>/' \
  --review-type '阶段验收' \
  --owner-request '检查本阶段效果并制定下一阶段方案'
```

Helper 从 `.ai/artifact-sync.toml` 的 `[pro_review].local_review_root` 读取本地归档根目录，也可用 `--pro-doc-root` 覆盖。

## 6. Verification

```bash
python -m py_compile .ai/scripts/pro_review_handoff.py
python -m unittest -v tests.test_v131
```

并检查：

- Prompt 明确要求 Pro ZIP 作为当前对话附件交付；
- Worker prompt 明确写“Owner 在当前本地 Worker 对话上传”，不去 Drive 查找 Pro ZIP；
- 解包目标位于 `.ai/PROJECT.md` 配置的 Pro review document root；
- `AGENTS.md` 和 `.codex/TEAM.md` 都包含 proactive delegation gate；
- v1.3.2 diff 没有修改 Codex hook/P2P、team state、lease/freeze、memory、long-run、OMO、Claude 或 Worker semantic ZIP implementation。
