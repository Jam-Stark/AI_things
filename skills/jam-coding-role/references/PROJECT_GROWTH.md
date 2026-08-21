<!-- managed-by: jam-coding-role; file: PROJECT_GROWTH.md -->
# Project Workflow Growth Model

项目 workflow 按真实摩擦增长，不按预设“成熟度仪式”一次性铺满。

## Level 0 — Bootstrap

**适用**：新 repo、单人或单 agent、目标仍在快速变化。

只需要：

```text
AGENTS.md
.ai/ROLE.md
.ai/PROJECT.md
```

实践：

- 单 agent 默认；
- 在 `.ai/PROJECT.md` 写目的、入口、命令、关键约束和最小验收；
- 不创建 role zoo、长期 memory、review gate 或复杂 plan 模板；
- 先完成第一个可运行 vertical slice。

**升级触发**：同一事实被重复查找、同一错误再次发生，或跨 session 上下文开始丢失。

## Level 1 — Repeatable

增加：

```text
.ai/WORKFLOW.md
MEMORY.md
```

实践：

- 记录 durable decisions、known failures、canonical commands；
- 为常见 claim 建立 verification map；
- bug/feature 以 acceptance criteria 驱动；
- root memory 仍保持短小。

**升级触发**：出现多个长期子系统、并行 worktree、排他资源或独立研究流。

## Level 2 — Coordinated

增加按需 runtime adapter 与 subsystem memory：

```text
.codex/...
.omo/...
memory/<subsystem>/...
```

实践：

- capability-based delegation；
- one writer/path/resource；
- Main 统一 scope、integration、Git；
- 工具配置和通用 policy 分离；
- 定期删除 stale adapter、过期 role 和重复规则，不做永久 compatibility museum。

**升级触发**：长训练、正式评估、checkpoint lineage、simulation/hardware evidence 成为项目核心。

## Level 3 — Scientific / Long-running

增加：

```text
.ai/SCIENTIFIC_ENGINEERING.md
experiment/run ledgers
artifact/source-lock contract
worktree/resource routing
```

实践：

- question、event、metric、denominator、admission、stopping 先定义；
- intent / realized telemetry / outcome 分离；
- evidence labels 和 causal boundary；
- long run 有 owner、source、command、output、terminal state；
- negative/inconclusive 是合法结果。

**升级触发**：稳定发布、多用户接口、数据迁移、长期兼容或安全/合规要求。

## Level 4 — Product / Release

按真实需要增加：

- CI/release gates；
- compatibility 与 migration policy；
- security/privacy review；
- ownership、SLO、rollback；
- release artifact 与 deployment verification。

这些要求不能提前反向污染探索期代码。进入此级别后，项目 overlay 应明确哪些 exploratory defaults 已失效。

## Promotion rule

只有看到具体 friction 才升级：

```text
observed failure -> smallest workflow addition -> verify it removes the failure
```

没有触发就不升级。新增机制若连续多个周期没有改变决策、减少错误或节省成本，应删除或降级为参考文档。

## Versioning rule

- `AI_things` 中的 role pack 是 upstream；
- 每个项目复制并 pin 一个版本到 `.ai/`，避免所有 repo 被全局更新瞬间改变；
- 通用原则升级用 `refresh`；
- project overlay 和 memory 永不被自动覆盖；
- 更新后只检查 adapter 引用、配置解析和项目特定 acceptance，不重演全部历史流程。
