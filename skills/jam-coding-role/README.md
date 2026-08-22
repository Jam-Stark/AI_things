# Jam Coding Role v1.3.0

个人通用 Coding Role：**轻内核、按需启用控制设施**。

## 默认行为

- FAST：简单 QA、临时实现/测试、小改动由 Main 直接完成；
- STANDARD：普通实现使用 0–3 个 focused agent，Codex P2P 可直接交换技术信息；
- HIGH_RISK：只覆盖 destructive、external、hardware、难回滚或未授权昂贵工作；
- 不默认创建 team ledger、disk task contract、lease、candidate freeze、memory curator 或 artifact bundle；
- Git commit/push 和外部写入始终需要当前明确授权。

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

参见 `UPDATE_LOG.md`、`CHANGELOG.md` 与 `examples/DoorDog-A2_Piper-migration.md`。
