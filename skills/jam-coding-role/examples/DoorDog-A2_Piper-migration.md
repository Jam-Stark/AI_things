# DoorDog A2_Piper — Jam Coding Role v1.3.0 迁移指南

适用目标：`Jam-Stark/DoorDog@A2_Piper`。迁移只改变 AI workflow、runtime adapter 与可选协调工具，不改机器人、IsaacLab、RL、训练或评估代码。

## 设计结论

DoorDog 的日常任务必须继续保持 lean：

```text
FAST / 普通 STANDARD
  -> Main 或少量 focused agent
  -> prompt 内协调与 Codex P2P
  -> 不初始化 persistent team state

出现真实协调风险
  -> 只启用所需设施
  -> ledger / lease / freeze / verdict / long-run / artifact 相互独立
```

v1.3.0 不再把完整协调平台当作默认流程。

## 受保护内容

迁移不得覆盖：

```text
.codex/config.toml
.codex/agents/
MEMORY.md
memory/a2-piper/
机器人与 RL source
logs_rl / logs_eval / checkpoint / render / video
```

保留当前 Codex role specialization 和模型配置，只替换 root/router、Codex/OMO/Claude adapters、`.ai/*` policy 与可选 helper scripts。

## 条件启用规则

| 情况 | 设施 |
|---|---|
| 简单 QA、临时实现/测试、小改动 | 无持久设施 |
| 普通跨文件实现、单 writer | 可用少量 agent/P2P；不要求 disk contract |
| 多 writer 或排他 GPU/IsaacSim/display/port/output | team state + 必要 lease |
| 正式 code/IsaacLab review 或 formal runtime QA | candidate freeze + scope-bound verdict |
| 已验证 durable fact | memory candidate；需要时再由 curator 重构 |
| >30 分钟运行或断线连续性 | long-run receipt/tmux/pending event |
| Owner 要求或 stage 明确交付 | artifact allowlist bundle / Pro_Space handoff |

触发一项不自动启用其余设施。

## Git 行为

通用迁移脚本必须默认不 commit。只有当前 Owner 指令明确授权时，才能传入 commit flags。

DoorDog 专用交付包中的 `APPLY_PROMPT.md` 已为那一次迁移明确授权：

1. pre-migration checkpoint commit；
2. workflow migration commit；
3. 不 push。

在其他项目或其他迁移轮次中，不得复用该授权。

## 推荐执行

先在包目录预演：

```bash
python apply_doordog_v1_3.py \
  --repo /path/to/DoorDog \
  --dry-run \
  --checkpoint-commit \
  --migration-commit
```

确认受保护路径和覆盖范围后，在当前 Owner 授权下执行：

```bash
python apply_doordog_v1_3.py \
  --repo /path/to/DoorDog \
  --apply \
  --checkpoint-commit \
  --migration-commit \
  --confirm-user-authorized-commit
```

脚本不得执行 `push`、`reset`、`stash`、`clean`、`rebase`、`merge`、force-add ignored artifacts 或任何训练/硬件操作。

## 迁移后验收

- `.codex/config.toml` 与 `.codex/agents/` 逐字节保持；
- root `AGENTS.md` 是 lazy route table；
- OpenCode 只 preload core route，不 preload scientific/team/artifact 等条件文档；
- Claude standalone 禁止 Agent；
- OMO Team Mode 默认关闭；
- team state 安装后仍为 inactive，FAST/普通 STANDARD 不产生 `.ai/runtime/team/`；
- artifact pack 缺少明确 trigger/confirmation 时必须拒绝；
- Git status 与两个 local commit 符合 Owner 本轮授权；
- 不执行 push。
