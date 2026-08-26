# Jam Coding Role v1.3.2

个人通用 Coding Role：**轻内核、自动分层路由、主动委托、控制设施按需启用**。

## v1.3.2 fixes

- 非 FAST 任务在深度工作前必须执行 `Mandatory delegation gate`；存在独立 lane、specialist、独立 review/QA 或明显并行收益时，Main 立即启动最少必要 agent，不等待用户说“team”。
- STANDARD 通常在触发时使用 1–3 个 focused agent；保持单 agent 时记录 `NO_DELEGATION_REASON`。
- HIGH_RISK 的副作用仍等待 Owner 授权，但安全的只读调查、source trace 和风险 review 可以先按 gate 并行。
- Cloud Pro 只读取 Drive 中的 Worker artifacts，不再尝试把自己的全量 ZIP 上传到 Drive。
- Pro 在当前对话附上 `pro_delivery__full_review.zip`；Owner 将该 ZIP 上传到本地 Worker 对话；Worker 保存并解压到 `.ai/PROJECT.md` 配置的 Pro review document root。

Existing project updates follow `UPDATE_GUIDE_1.3.2.md`.

Cloud-review projects update:

```text
scripts/pro_review_handoff.py -> .ai/scripts/pro_review_handoff.py
templates/PRO_REVIEW_PROMPT.md -> .ai/PRO_REVIEW_PROMPT.md
templates/ARTIFACT_SYNC.toml -> .ai/artifact-sync.toml
references/ARTIFACT_HANDOFF.md -> .ai/ARTIFACT_HANDOFF.md
```

---

## v1.3.1 behavior retained

- root `AGENTS.md` 是项目级 workflow authority；系统、developer 和当前 Owner 指令仍更高；
- Main 自动选择 FAST/STANDARD/HIGH_RISK；
- `.ai/PROJECT.md` 维护 conda/runtime environment 和 train/eval/smoke command registry；
- Cloud Pro review 前 commit+push 并验证远程 commit，再上传 Worker artifacts 和生成 prompt；
- 95 MiB 指每个**压缩完成后的 ZIP 文件大小**，不是原始文件大小；
- 对话窗口给 Owner 精简结果；Pro 全量版仍是 `pro_delivery__full_review.zip`，但从 v1.3.2 起通过 Owner 对话转交，不再走 Drive。

## v1.3.0 lean default retained

- FAST：简单 QA、临时实现/测试、小改动由 Main 直接完成；
- STANDARD：普通实现使用 0–3 个 focused agent，Codex P2P 可直接交换技术信息；
- HIGH_RISK：只覆盖 destructive、external、hardware、难回滚或未授权昂贵工作；
- 不默认创建 team ledger、disk task contract、lease、candidate freeze、memory curator 或 artifact bundle；
- Git commit/push 和外部写入始终需要当前明确授权；Owner-requested cloud Pro handoff 是 `.ai/ARTIFACT_HANDOFF.md` 定义的显式授权例外。

## 最小初始化

```bash
python scripts/bootstrap.py init /path/to/project
```

默认只安装行为核心、route table、project overlay 和候选触发式 memory governance，不创建 `MEMORY.md` 或持久 team state。

## 按需增加能力

```bash
python scripts/bootstrap.py init /path/to/project \
  --profile scientific \
  --runtime codex \
  --runtime omo \
  --runtime claude \
  --memory \
  --codex-coordination-state \
  --long-run-supervisor \
  --stage-workflow \
  --artifact-sync
```

OMO Team Mode 只有显式加入 `--omo-team-mode` 时生成启用配置。安装 coordination tooling 不等于激活 ledger；默认仍为 inactive。

## 审计

使用与初始化相同的 flags：

```bash
python scripts/bootstrap.py audit /path/to/project ...
```

审计会检查 requested files、JSON/TOML/Python、Claude 单 agent、OMO 配置、team-state inactive default、artifact explicit trigger，以及 OpenCode 是否保持 lazy loading。

## Production hotfixes retained

- Codex `PreToolUse` uses event-specific allow/deny output and fails closed on malformed strict-policy input;
- repository-local hook commands resolve from the Git root;
- `PostToolUse` records coordination metadata only;
- `SessionStart` consumes pending events once and archives them;
- Worker stage artifacts use a 95 MiB per-ZIP compressed-size ceiling and independently readable semantic ZIP files.

After installing or changing project hooks, review the exact hook definitions with Codex `/hooks` before relying on them.

参见 `UPDATE_GUIDE_1.3.2.md`、`UPDATE_LOG.md`、`CHANGELOG.md` 与 `examples/DoorDog-A2_Piper-migration.md`。
