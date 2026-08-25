# Jam Coding Role v1.3.1

个人通用 Coding Role：**轻内核、自动分层路由、控制设施按需启用**。

## v1.3.1 minimal update

- root `AGENTS.md` 是项目级 workflow authority；系统、developer 和当前 Owner 指令仍更高；
- Main 自动选择 FAST/STANDARD/HIGH_RISK。STANDARD/HIGH_RISK 满足独立工作流、specialist 或独立 review 条件时，可按项目指令自动委托，不需要用户再说“team”；
- `.ai/PROJECT.md` 统一维护 conda/runtime environment 和 train/eval/smoke command registry；
- Cloud Pro review 先 commit+push 并验证远程 commit，再上传 artifacts 和生成 `PRO_REVIEW_PROMPT.md`；
- 95 MiB 指每个**压缩完成后的 ZIP 文件大小**，不是原始文件大小。

Existing project updates follow `UPDATE_GUIDE_1.3.1.md`. Projects using cloud review copy:

```text
scripts/pro_review_handoff.py -> .ai/scripts/pro_review_handoff.py
templates/PRO_REVIEW_PROMPT.md -> .ai/PRO_REVIEW_PROMPT.md
```

---

## v1.3.0 default behavior retained

- FAST：简单 QA、临时实现/测试、小改动由 Main 直接完成；
- STANDARD：普通实现使用 0–3 个 focused agent，Codex P2P 可直接交换技术信息；
- HIGH_RISK：只覆盖 destructive、external、hardware、难回滚或未授权昂贵工作；
- 不默认创建 team ledger、disk task contract、lease、candidate freeze、memory curator 或 artifact bundle；
- Git commit/push 和外部写入始终需要当前明确授权；Owner-requested cloud Pro handoff is now the explicit handoff authorization described above.

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

## v1.3.0 production hotfixes

- Codex `PreToolUse` uses event-specific allow/deny output and fails closed on malformed strict-policy input;
- repository-local hook commands resolve from the Git root, so starting Codex in a subdirectory remains valid;
- `PostToolUse` records coordination metadata only;
- `SessionStart` consumes pending events once and archives them;
- cloud-facing stage artifacts use a 95 MiB per-ZIP ceiling and semantic, independently readable standard ZIP files with `BUNDLE_INDEX.md`.

After installing or changing project hooks, review the exact hook definitions with Codex `/hooks` before relying on them.

参见 `UPDATE_GUIDE_1.3.1.md`、`UPDATE_LOG.md`、`CHANGELOG.md` 与 `examples/DoorDog-A2_Piper-migration.md`。
