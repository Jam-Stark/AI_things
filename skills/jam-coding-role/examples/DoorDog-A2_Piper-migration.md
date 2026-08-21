# DoorDog A2_Piper — Coding Role / Codex / OMO 精准迁移方案

适用基线：`Jam-Stark/DoorDog@A2_Piper`。本方案只修改 AI workflow 与 authority routing，不改变 DoorDog 的机器人、RL、训练或评估代码。

## 0. 最终决策

不要把 Karpathy-style guidelines 继续 append 到现有 root `AGENTS.md`。DoorDog 已经有成熟的 multi-agent、memory、IsaacLab、长任务和 evidence 机制；继续叠加会扩大重复与 semantic drift。

目标结构应为：

```text
Karpathy-inspired behavior kernel
            +
DoorDog project overlay
            +
shared adaptive workflow
            +
thin Codex / OMO adapters
```

稳定原则只定义一次，项目事实只定义一次，runtime/model/tool setting 只定义在各自配置中。

## 1. 当前审计 findings

### F1 — 三份 workflow 重复维护

当前 root `AGENTS.md`、`.codex/TEAM.md`、`.omo/AGENTS.md` 都重复定义 routing、implementation-first、review ceiling、memory gate、writer/resource ownership、wait/tmux 和 Git authority。任一文件更新都会产生 drift。目标状态应是 root router + `.ai/*` canonical docs，Codex/OMO 只做能力映射。

### F2 — legacy adapters 引用已经删除的旧体系

`.github/instructions/codingRole.instructions.md` 和 `.github/instructions/omo-coding-role.instructions.md` 仍引用 `.codex/contracts/`、`PF1/PF2/PF3`、`Plan + explicit user Approval`、`frozen-candidate independent review` 以及 review PASS 后 memory gate。当前 `.codex/AGENTS.md` 和 agent-system memory 已说明这些机制被移除；legacy adapter 会把旧 workflow 重新注入某些 client，必须替换。

### F3 — model/effort source 冲突

prose 中把 Main 描述为 `Sol/high`，`.codex/config.toml` 实际为 `gpt-5.6-sol/max`。模型、effort、concurrency 和 sandbox 不应写入 canonical policy prose。唯一 source 应是 `.codex/config.toml` 与 `.codex/agents/*.toml`。

### F4 — “implementation-first + 用户确认前不加 test”过于绝对

更准确的规则是：明确授权的 change 要实际实现；实施前先定义 acceptance；可低成本确定性复现的 bug 先建 reproducer；IsaacLab runtime semantic change 至少要有匹配 runtime evidence；algorithm claim 需要 formal evaluation；不添加与 acceptance 无关的测试或防护。

### F5 — “最多一个 proof command”不能覆盖不同 evidence level

config change 可能只需 parse；reward/transition change 需要 static + runtime；算法主张还需要 experiment。应限制“重复同类验证”，而不是限制“总证据数量”。

### F6 — 机器和 runtime 细节混入 universal policy

具体 model names、固定本机路径、sleep 数字、工具名和并发数是 runtime/project facts，不是通用行为。保留在 `.codex/config.toml`、agent files、`.ai/PROJECT.md` 或 runtime adapter。

### F7 — DoorDog memory 值得保留，不应重做

root `MEMORY.md -> memory/a2-piper/MEMORY.md` 已形成高价值 durable ledger；v19–v25 沉淀了 event alignment、因变量、realized telemetry、admission、unit、gate validity、causal boundary 等可复用规则。迁移只改变入口和 authority，不压平现有 memory。

## 2. 目标文件结构

```text
AGENTS.md                         # repository router + authorization
.ai/
  ROLE.md                         # pin 的通用 behavior kernel
  WORKFLOW.md                     # adaptive route/team/memory/evidence
  SCIENTIFIC_ENGINEERING.md       # ML/RL/robotics extension
  PROJECT.md                      # DoorDog-specific facts/invariants
  ROLE_VERSION
MEMORY.md                         # 保留现有 router
memory/                           # 保留现有 entries
.codex/
  AGENTS.md                       # 薄 adapter
  TEAM.md                         # capability -> agent mapping
  config.toml                     # 唯一 model/effort/concurrency source
  agents/*.toml                   # role specialization
.omo/
  AGENTS.md                       # OMO tool/category mapping
.github/instructions/
  codingRole.instructions.md      # legacy router
  omo-coding-role.instructions.md # legacy router
```

## 3. 保留、替换与停止激活

### 保留

- root `MEMORY.md` 与全部 `memory/`；
- `.codex/agents/*.toml` 的角色能力和 sandbox setting；
- `.codex/config.toml` 作为 runtime config；
- `.omo/plans/`、`.omo/drafts/`、`.omo/run-continuation/` 的真实项目产物；
- IsaacLab high-level API、fail-fast、one writer/resource、Main-only Git 等 project discipline；
- `scriptsFORhuman/` 的 plan/run ledger 与 artifact contracts。

### 替换

- root `AGENTS.md`；
- `.codex/AGENTS.md`；
- `.codex/TEAM.md`；
- `.omo/AGENTS.md`；
- 两个 `.github/instructions/*coding*` adapters；
- `memory/agent-system/architecture/*` 中关于旧 authority hierarchy 的 current summary。

### 不再作为 active rule

- 已删除 `.codex/contracts/` 的引用；
- PF1/PF2/PF3；
- frozen-candidate/reviewer-wave 旧状态机；
- 固定“只准一个命令”；
- 固定“用户确认前不得写任何 test”；
- prose 中的 model/effort/concurrency 数值；
- runtime adapter 对 universal role 的复制。

## 4. 迁移步骤

在独立 worktree/branch 中完成，避免和训练代码 round 混写：

```bash
git switch -c chore/ai-role-v2
```

### Step 1 — pin 通用 core

从 `AI_things/skills/jam-coding-role` 执行：

```bash
python scripts/bootstrap.py init /path/to/DoorDog \
  --profile scientific \
  --runtime codex \
  --runtime omo
```

DoorDog 已存在同名文件，因此 `init` 会安全跳过。手动复制或用受控 migration commit 写入：

```text
references/ROLE.md                   -> DoorDog/.ai/ROLE.md
references/WORKFLOW.md               -> DoorDog/.ai/WORKFLOW.md
references/SCIENTIFIC_ENGINEERING.md -> DoorDog/.ai/SCIENTIFIC_ENGINEERING.md
VERSION                              -> DoorDog/.ai/ROLE_VERSION
```

### Step 2 — root `AGENTS.md`

```markdown
# DoorDog AI entrypoint

本文件是 repository-level authority router。system/developer/user 指令之后，按以下顺序读取：

1. `.ai/ROLE.md`：通用 coding behavior；
2. `.ai/PROJECT.md`：DoorDog facts、invariants、commands、overrides；
3. `.ai/WORKFLOW.md`：非平凡 work、delegation、memory、evidence；
4. `.ai/SCIENTIFIC_ENGINEERING.md`：IsaacLab、ML/RL、simulation、robotics、formal evaluation；
5. root `MEMORY.md`：只在 prior decision、failure、progress 或 run evidence 相关时按 route 读取。

`.codex/*`、`.omo/*`、`CLAUDE.md`、`.github/instructions/*` 是 runtime adapters，不得重定义或弱化上述 canonical files。

## Authorization

- answer/explain/inspect/diagnose/review/research/plan：默认只读；
- build/fix/refactor/update：授权 exact in-scope local edits 与匹配的 non-destructive evidence；
- destructive operation、external write、material scope expansion、未授权昂贵长跑或 hardware action：先请求；
- 不覆盖、reset、stash、discard 用户或其他 worktree/agent 的既有修改；
- Git stage/commit/push/merge 只由 Main 在明确授权下执行。

## DoorDog non-negotiables

- 先 trace 真实执行 code/config/dependency path；plan、memory、文件名和旧文档不能替代 code truth。
- IsaacLab API change 前读取最小相关 local source 和当前 official docs；优先 high-level API。
- observation/action/reward/termination/reset/stage、tensor shape/dtype/device、unit/frame/timebase 和 checkpoint lineage 必须显式保持。
- invalid simulation/training state fail visibly；不以 fallback、silent catch、default tensor、类型压制或无依据 clipping 掩盖。
- evidence level 与 claim 对齐：static、runtime、experiment、hardware 不得互相冒充。
- experiment 必须区分 intended config、realized telemetry 和 outcome；因变量在正确物理事件上测量。
- 一个 path、GPU、IsaacSim、display、port、output root 同时只有一个 writer/owner。
- reference worktree 默认只读；active worktree、GPU lease 和输出路径以 `.ai/PROJECT.md` 与当轮用户指令为准。
- remote agent 看不到的本地 `logs_rl`、`logs_eval` 或 artifact 不得假设存在。

## Runtime routing

- Codex：读 `.codex/AGENTS.md`；需要 delegation 时再读 `.codex/TEAM.md`。
- OpenCode/OMO：读 `.omo/AGENTS.md`。
- 其他 client：通过自己的薄 adapter 路由到本文件和 `.ai/*`。

## Completion

Main 在交付前确认实际 diff/path boundary、匹配的 acceptance evidence、未结束的 writer/resource 和未验证声明。报告 actual evidence，不写 “should pass”。
```

### Step 3 — `.ai/PROJECT.md`

```markdown
# DoorDog A2_Piper project overlay

## Purpose and current milestone

DoorDog 在 A2+PiPER 上研究长时域 legged loco-manipulation door opening：Teacher PPO、push/pull task families、vision Student distillation，以及 arm-base interaction/force causality。当前 milestone 必须从 root `MEMORY.md` 路由到对应 subsystem/round 读取，不在本文件硬编码具体候选 checkpoint。

## Sources of truth

1. 当前 worktree 中真实 executable code 与 resolved config；
2. 真实 runtime/training/eval artifacts 及其 source/checkpoint lineage；
3. root `MEMORY.md` 路由后的 current entry；
4. `scriptsFORhuman/` plan/ledger：表示 intent、registration 与 execution record，不自动证明代码或 runtime；
5. local IsaacLab source 与当前 official docs；
6. external paper/repo；
7. 明确标记的 inference。

发生冲突时先报告冲突，再以对应 domain 的直接证据为准。code truth、runtime truth、experiment truth 和 owner intent 是不同 domain。

## Primary paths

- environment: `gr00t/rl/envs/door/door_open_a2_base.py`
- recurrent actor/critic: `gr00t/rl/trl/modules/actor_critic_modules_recurrent.py`
- PPO trainer: `gr00t/rl/trl/trainer/ppo_trainer_a2_base_api.py`
- experiment config: `gr00t/rl/config/exp/wbmanip/door_open_a2_base_lstm.yaml`
- observation config: `gr00t/rl/config/obs/wbmanip/door_open_a2_base.yaml`
- reward config: `gr00t/rl/config/rewards/wbmanip/reward_door_open_a2_base.yaml`
- project memory: `MEMORY.md -> memory/a2-piper/MEMORY.md`
- long-term route: `scriptsFORhuman/a2_piper_longterm_TODO.md`
- formal outputs: use the current log-layout memory contract; never infer an artifact path from version naming alone。

Verify these paths before each material change；update this overlay only when the canonical path itself changes。

## Architecture facts to re-check before edits

- The door task currently uses a high-level recurrent policy with base-command and arm/gripper actions；the A2 low-level locomotion skill is loaded as a frozen prior in the current teacher path。
- Stage/reset、action ordering、recurrent history、frozen-policy compose、control/physics timebase and door sign/handedness are coupled contracts。
- These are current facts，not permanent design rules。Read the executing code before relying on them。

## Verification map

| Claim | Minimum evidence |
|---|---|
| Markdown/YAML/TOML/Python structure | targeted parse/import/static |
| reward/obs/action/stage semantic | minimal real IsaacLab runtime + telemetry |
| trainer/update/checkpoint behavior | real update/checkpoint smoke |
| policy/algorithm improvement | registered formal evaluation with source lock |
| causality | controlled intervention/ablation with bounded claim |
| sim-to-real or hardware safety | explicit real hardware validation |

Different acceptance criteria may require different evidence levels。不要重复 equivalent checks after they are sufficient。

## Scientific invariants

- metric 必须绑定正确 event；round summary 必须含本轮因变量；
- success-rate saturation 时使用直接 mechanics/behavior-quality metric；
- classification 优先 realized telemetry，统一单位；intended bucket 只表示 sampling；
- admission population 先通过 baseline-vitals；
- derived gate 先证明 unit/monotonicity/identifiability；
- admission/gate 不能结构性惩罚被检假设为真；
- post-hoc descriptive finding 不升级为 preregistered causal PASS；
- matched-prefix、short horizon、simulation-only 等限制写进结论；
- `NOT_SUPPORTED / INCONCLUSIVE / NOT_ADMITTED / UNRESOLVED / NOT_RUN` 均为合法终局。

## Runtime and resources

- GPU、IsaacSim、display、port、output directory 和 hardware 为 exclusive resources，由 Main 分配 owner。
- 长任务记录 source revision、resolved config、checkpoint、command、seed/device、output、stopping condition 与 terminal state。
- 使用当前项目认可的 persistent job/session 方式；不高频 polling。
- 本机路径通过 project/local environment 配置；canonical policy 不硬编码个人 home path。
- reference worktree 默认只读；三个 worktree 的 active ownership 以当轮用户指令和 long-term route 为准。

## Compatibility and error policy

- exploratory/research code 不默认保存 legacy compatibility；只有真实 consumer contract 或用户要求时保留。
- 删除旧路径前确认 active call sites 和 artifact readers。
- fail fast 适用于 internal invalid state；外部 I/O、hardware、用户数据的真实边界错误必须清楚处理。
- 不为普通研究实现附加无关 security hardening。

## Hardware boundary

实机工作必须遵守 A2、PiPER 和完整集成系统的官方 safety/risk assessment、急停、负载、电气、线束、工作空间与人员隔离要求。simulation evidence 不能替代 hardware evidence。
```

迁移前必须用当前分支实际代码复核上面列出的 paths 和 architecture facts；若已有变化，以代码为准并更新 overlay。

### Step 4 — `.codex/AGENTS.md`

```markdown
# DoorDog Codex adapter

Root `../AGENTS.md` and routed `.ai/*` files are canonical。

This directory contains only：

- runtime config in `.codex/config.toml`；
- role definitions in `.codex/agents/*.toml`；
- capability mapping in `.codex/TEAM.md`。

Do not recreate removed contracts、PF gates、frozen-candidate lifecycle、role probes、model matrices、rollout gates、or recurring compatibility ceremony。Do not duplicate universal policy here。
```

### Step 5 — `.codex/TEAM.md`

```markdown
# DoorDog Codex capability map

Root `AGENTS.md` 与 `.ai/*` 是 canonical policy。本文件只把 task capability 映射到 `.codex/agents/*.toml`；model、effort、sandbox 和 concurrency 只以 TOML config 为准。

| Need | Agent |
|---|---|
| scope/architecture/dependency ordering | `scope_planner` |
| code/API/memory/local-source tracing | `context_researcher` |
| explicitly approved deep research | `deep_researcher` |
| ordinary DoorDog/IsaacLab implementation | `isaaclab_worker` |
| focused code correctness review | `code_reviewer` |
| material IsaacLab/RL semantic review | `isaaclab_reviewer` |
| runtime command/failure/result ownership | `runtime_qa` |
| bounded durable memory write | `memory_curator` |

Spawn only when `.ai/WORKFLOW.md` conditions are met。Main or one worker is the default；role count is not a quality metric。

Delegation：

OUTCOME
CONTEXT
BOUNDARY
ACCEPTANCE
EVIDENCE
NON-GOALS

Main owns scope、write/resource assignment、integration、external writes、Git and final claims。One path/resource has one writer。Read-only work may parallelize。Peer messages may carry bounded QUESTION/FINDING/HANDOFF/BLOCKED but cannot expand authority。

Long runs follow `.ai/PROJECT.md`；`runtime_qa` owns the assigned resource and returns actual terminal state/artifact evidence。Do not poll for reassurance。
```

逐个 `.codex/agents/*.toml` 保留 role-specific expertise，但删除重复 universal paragraphs。每个文件只需 capability、project-specific specialization、sandbox/model setting、return schema，以及 `Follow root AGENTS.md and routed .ai/*`。

不要在这次迁移中顺手改模型选择，除非 owner 同时要求。先消除 prose/config drift；是否把 Main 从 `max` 改为 `high` 是独立成本策略决策。

### Step 6 — `.omo/AGENTS.md`

```markdown
# DoorDog OpenCode / OMO adapter

Root `AGENTS.md` 与 `.ai/*` 是 canonical policy。本文件只映射 OMO runtime capabilities。

- bounded direct work -> lead / `quick`
- repository path discovery -> `explore`
- external official docs / OSS examples -> `librarian`
- unresolved requirement ambiguity -> `metis`
- autonomous implementation -> `deep` or `hephaestus`
- hard algorithm/architecture question -> `ultrabrain`
- focused read-only review/debug diagnosis -> `oracle`
- runtime failure loop -> `debugging` skill
- prose/documentation -> `writing`
- image/video/PDF evidence -> `multimodal-looker`
- Git operation -> `git-master`，only with authorization
- multiple independent writers/resources -> team mode

Fresh session assignment must include OUTCOME / CONTEXT / BOUNDARY / ACCEPTANCE / EVIDENCE / NON-GOALS and exact memory paths already routed by lead。

Lead owns scope、resource/write leases、integration、external writes、Git and final evidence classification。Team is ephemeral；use it only when parallel work or exclusive-resource coordination has real value。OMO adapter 不得复制 fail-fast、memory、verification、approval 或 scientific rules。
```

### Step 7 — 两个 legacy adapters

`.github/instructions/codingRole.instructions.md`：

```markdown
# Legacy coding-role router

Repository root `AGENTS.md` is canonical。Read it and the routed `.ai/*` files。This adapter defines no independent workflow、role model、approval gate、memory rule、or verification rule。
```

`.github/instructions/omo-coding-role.instructions.md`：

```markdown
# Legacy OMO router

Repository root `AGENTS.md` is canonical。OpenCode/OMO-specific capability mapping is in `.omo/AGENTS.md`。This adapter defines no independent workflow and must not restore removed contracts、gates、or candidate lifecycles。
```

### Step 8 — `.codex/config.toml`

本次迁移只建立 single source，默认不改变成本选择。保留当前真实配置或由 owner 单独决策：

```toml
model = "gpt-5.6-sol"
model_reasoning_effort = "max"

[agents]
enabled = true
max_concurrent_threads_per_session = 5
default_subagent_model = "gpt-5.6-terra"
default_subagent_reasoning_effort = "high"
interrupt_message = true
```

之后 Markdown 不再复制这些数值。

### Step 9 — 更新 agent-system memory

更新 `memory/agent-system/architecture/description.md`，只记录：canonical hierarchy 已变为 `AGENTS.md -> .ai/* -> runtime adapters`；universal policy 与 runtime config 已分离；stale contracts/PF/frozen-candidate references 已清除；static reference/TOML parse 达到什么 evidence；Codex/OMO 真 spawn 或真实 task rollout 若未运行，必须写 `NOT_RUN`。

不要为迁移重建长期 synthetic eval ceremony。后续只在真实 task 暴露 workflow defect 时记录。

## 5. 静态验收

```bash
# 1) stale references 必须为零
rg -n \
  '\.codex/contracts|PF[123]|frozen[-_ ]candidate|reviewer wave|Plan \+ explicit user Approval' \
  AGENTS.md .ai .codex .omo .github/instructions memory/agent-system

# 2) model/effort prose drift
rg -n 'gpt-5\.|Sol/|Terra/|Luna/|reasoning_effort|max_concurrent' \
  AGENTS.md .ai .codex/TEAM.md .omo/AGENTS.md .github/instructions
# 期望：只在 TOML/runtime-specific agent files 出现。

# 3) TOML parse
python - <<'PY'
from pathlib import Path
import tomllib

for path in [Path(".codex/config.toml"), *Path(".codex/agents").glob("*.toml")]:
    tomllib.loads(path.read_text())
    print("PASS", path)
PY

# 4) canonical managed core
python /path/to/AI_things/skills/jam-coding-role/scripts/bootstrap.py audit . \
  --profile scientific --runtime codex --runtime omo

# 5) diff boundary
git diff --check
git status --short
```

`audit` 只对 managed core 做 hash 比较，并检查 root/adapter 是否正确路由，不覆盖 `.ai/PROJECT.md`、memory 或 runtime mapping。

## 6. 行为验收

静态 PASS 只能证明结构一致。用真实任务做三次轻量 rollout：

1. **Direct**：一个 bounded doc/config change，确认不 spawn 无用 agent；
2. **Focused**：一个跨文件 code task，确认先 trace + acceptance，再实现并做匹配 evidence；
3. **Coordinated**：一个 read-heavy research + 独立 runtime/resource task，确认 ownership、handoff 和 evidence level。

每次只记录实际缺陷。不要恢复旧的 role matrix、synthetic eval、frozen candidate 或 reviewer wave。

## 7. 从 A2_Piper 抽象出的长期原则

这些原则已进入 `SCIENTIFIC_ENGINEERING.md`：

- **event alignment**：在用户真正要求的物理事件上测量；
- **dependent-variable visibility**：每轮 summary 直接包含本轮因变量；
- **ceiling awareness**：success 饱和时换 mechanics/quality axis；
- **realization over intent**：按 realized telemetry 与统一单位解释；
- **admission before inference**：baseline vitals 先通过；
- **validated gates**：derived metric 先证明单位、单调性、可识别性；
- **gate/hypothesis decoupling**：准入规则不能惩罚假设为真；
- **bounded causality**：intervention、restore quality、horizon、population、simulation/hardware 边界写进结论；
- **negative results are first-class**：不为得到 PASS 改 denominator 或 reducer；
- **source lock**：code/config/checkpoint/evaluator/artifact lineage 可追溯；
- **timebase discipline**：control step、physics step、sensor sample 与秒不能混用；
- **memory as current truth**：保留可复用结论，不保存流程噪声。

## 8. 最终验收标准

迁移完成必须同时满足：

- universal behavior 只有一份 canonical source；
- DoorDog-specific truth 只有一份 project overlay；
- model/effort/concurrency 只有 TOML source；
- Codex/OMO/legacy clients 都路由到同一 policy；
- stale deleted paths/gates 为零；
- 现有 A2_Piper memory、artifact discipline、worktree/resource rules 无损；
- verification 由 claim 决定，不再被“一条命令”或“用户确认前无 test”绝对限制；
- 没有因整合 role 而引入新的 mandatory agent/review/memory ceremony。
