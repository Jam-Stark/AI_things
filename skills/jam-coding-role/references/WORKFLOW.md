<!-- managed-by: jam-coding-role; file: WORKFLOW.md -->
# Adaptive Project Workflow

这套 workflow 的目标是让项目从单 agent 起步，并只在真实复杂度出现时增加 memory、team、review 和运行纪律。它不是固定流水线。

## 1. 路由：选择最低充分协作级别

### Direct

适用于位置和行为都清楚的 bounded work：问答、局部修复、明确配置、单文件文档。

```text
minimal context -> change/read -> matching evidence -> report
```

默认不 spawn agent，不创建 plan 文件，不新增 memory 结构。

### Focused

适用于普通跨文件实现、调试或设计：

```text
route context -> trace real path -> acceptance plan -> implement incrementally
-> verify each acceptance criterion -> integrate
```

可按需使用 1–3 个 agent；没有独立并行价值时仍由 Main 完成。

### Coordinated

仅在下列情况升级：

- 两个以上真正独立的研究或实现流；
- 路径、GPU、仿真进程、端口、数据目录等资源需要显式 lease；
- 跨子系统且 blast radius 高；
- 长运行、外部写入、硬件动作或难回滚变更；
- 用户明确要求 team 或独立 review。

升级增加的是 ownership、approval 和 evidence discipline，不是固定角色数量或重复检查。

## 2. Multi-agent：能力池，不是工位流水线

常用 capability：

- **Scout / Researcher**：定位真实路径、外部 API、历史证据和未知；
- **Builder**：在明确 write boundary 内实现；
- **Verifier / Reviewer**：验证一个具体 claim 或风险；
- **Runner**：拥有一个排他 runtime resource 和运行证据；
- **Curator**：把已验证结果机械地写入 durable memory。

同一 agent 可承担多个相邻 capability。不要为了“完整团队”生成没有独立产出的角色。

### Spawn 条件

只在满足至少一项时 spawn：

- 工作可并行且结果能独立交付；
- 子问题需要明显不同的专业上下文；
- 独立验证能降低材料性风险；
- 主 agent 的 context 会因深度探索显著膨胀；
- 排他资源需要单独 owner。

### 委托合同

```text
OUTCOME: 可观察结果与停止条件
CONTEXT: 已蒸馏事实、相关路径、仍存未知
BOUNDARY: 可读范围、唯一可写路径、排他资源
ACCEPTANCE: 通过条件
EVIDENCE: 允许或需要的最小证据
NON-GOALS: 禁止扩张的事项
```

子 agent 返回：status、result、touched paths、命令与实际输出、未验证声明、blocker、可选 memory candidate。泛泛的“done”不构成交付。

### Ownership

- Main 拥有 scope、agent/resource allocation、integration、external writes、Git 和最终结论。
- 一个 path 或排他 runtime resource 同一时间只有一个 writer/owner。
- read-only discovery 可并行；共享写路径必须串行。
- peer 可直接交换 bounded `QUESTION / FINDING / HANDOFF / BLOCKED`，但不能扩 scope、授权写入或改变成本。
- 完成的 agent 应结束；不保留空闲团队作为项目常驻仪式。

## 3. Verification：由 claim 驱动，不由固定次数驱动

先把 acceptance criterion 映射到最低足够证据：

| Claim | 通常最低证据 |
|---|---|
| 文件或配置结构正确 | inspect + parse/static |
| 纯函数或 bug 修复 | reproducer/test |
| API 或集成路径可用 | integration/runtime |
| 仿真行为改变 | controlled runtime + telemetry |
| 算法更优或具因果性 | registered experiment/ablation |
| 实机可用或安全 | hardware verification |

规则：

- bug 在可低成本确定性复现时，先建立 reproducer，再修复；
- refactor 至少证明 before/after behavior contract；
- runtime 语义不能只靠 static pass；
- 一个 acceptance criterion 可有一个必要证据；不要用“只准一个命令”限制不同层级的必要证明；
- 同一 claim 已被足够证明后，不重复跑同类检查求安心；
- pre-existing failure 要隔离和报告，不顺手修复。

## 4. Memory：从一个文件开始，按检索压力成长

### Level 0：无 memory

新项目或一次性任务不创建 memory。

### Level 1：root `MEMORY.md`

当同一事实、命令、失败模式或决策第二次需要被重新发现时，建立简短 router/ledger。

推荐 entry：

```text
Fact/decision:
Scope:
Evidence:
Consequence:
Status:
Read when:
Updated:
```

### Level 2：subsystem routes

仅当 root 文件已难以快速定位时拆成：

```text
MEMORY.md
memory/<subsystem>/MEMORY.md
memory/<subsystem>/<entry>/description.md
```

`TODO.md` / `DONE.md` 只在项目确实需要长期执行状态时增加。

### 写入规则

- 先读最短相关 route，不让所有 agent 重读整棵 memory；
- 只记录 durable knowledge，不复制长源码、日志和对话；
- runtime/experiment 证据写清 artifact、source、checkpoint 和 run 条件；
- speculative idea 放 plan/research note，不写成 current truth；
- memory 变更本身也遵循 single writer。

## 5. Runtime、长任务与资源

- 每个 GPU、仿真进程、显示、端口、硬件、输出目录或共享数据集明确 owner。
- 长任务在启动前记录 command、source revision、config、resource、output path、stopping condition。
- 运行超过交互窗口时使用项目认可的持久 session/job system；不要高频 polling。
- 运行结果按 `RUNNING / PASS / FAIL / INCONCLUSIVE / CANCELLED / NOT_RUN` 表述。
- 取消、超时、缺 artifact 和自然完成是不同状态。
- 未看到的本地日志或 artifact 不得假设存在。

## 6. Runtime adapter 必须薄

推荐 canonical hierarchy：

```text
AGENTS.md                       # repository entry/router
.ai/ROLE.md                     # stable behavior kernel
.ai/PROJECT.md                  # project facts and overrides
.ai/WORKFLOW.md                 # this workflow
.ai/SCIENTIFIC_ENGINEERING.md   # optional profile
MEMORY.md                       # optional memory router
.codex/* / .omo/* / CLAUDE.md  # tool adapters only
```

原则：

- 通用原则只在 `.ai/ROLE.md` 定义一次；
- project invariants 只在 `.ai/PROJECT.md` 定义一次；
- model、effort、concurrency 和 tool names 只在各 runtime config 中定义；
- adapter 只说明“读什么、如何映射 capability、有哪些工具限制”，不复制核心 policy；
- 发现 stale path、已删除 gate 或互相矛盾的 model setting 时，修正 source of truth，而不是继续兼容。

## 7. Git 与 closure

- 先保护用户已有 dirty work；不 reset、stash、discard 或覆盖无关修改。
- 只有被授权的 integrator 执行 stage、commit、push 或 merge。
- 结束前检查实际 diff/path boundary、acceptance evidence 和仍在运行的 writer/resource。
- 报告证据实际达到的等级；未运行的检查显式写出。
