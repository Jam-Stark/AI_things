<!-- managed-by: jam-coding-role; file: EXECUTION_TEAM.md -->
# 独立执行一个已批准阶段

Owner/Planner 给出目标、允许调整范围、资源/运行预算、完成条件和明确 gate。execution lead 按这份现有 plan 执行；运行状态只是可检查的投影，不是第二份批准文本。绑定 stage/revision、真实 host/thread、授权来源、写入范围、操作、资源和额度。

## 两个入口

A：Owner 在新 session 粘贴 `templates/START_A_ROOT_zh.md` 的交接内容。它是 root lead，App 选择模型，绑定 Planner 端点。

B：Planner 以 `execution_lead` 或已注册 effort 变体实际 spawn lead。它保留 child 身份，自己创建 specialist、接收结果与继续阶段，不要求 Planner 代建成员。交接内容见 `templates/START_B_CHILD_zh.md`。

同一阶段只有一个整合责任人。lead 可拆分已授写入与资源，子授权只能是父授权的子集；重叠写入/排他资源串行。普通 specialist 不自行提交、推送或发布；lead 的 commit/push 权限分别来自明确授权。不会因缺少提交权停在无法交付 diff 的状态。

默认逻辑工作席位 5，含 lead、specialist、sub-specialist、Outside view 和 Planner 已启动的支持角色，不含 Planner。root lead 也计 1；child lead 不重复计数。默认 lead 以下最多两条派生边，阶段可明确收紧或调整；宿主限制始终生效。不使用未文档化的 native max_depth。Astra 保留全 team 唯一 deep_researcher 身份。

## 连续执行与决定

在阶段明确允许的调整范围内自主执行；只有超出该范围、触及明确 gate，或无法在既有授权内解决的问题，才请求裁定。该规则包括已批准的奖励、比较条件、checkpoint、seed 和方法迭代。负结果本身不自动变为异常；已批评估和对照继续完成。

到达真实 gate 时提交所需证据，只暂停相关依赖链。普通通知未回复不阻塞已有授权；没有回复永远不产生新授权。阶段完成交付一次整合结果，不擅自开启未批阶段。

## 通信与恢复

同树技术协作直接 P2P，生命周期由实际创建者管理。不强制将每条技术消息抄送 Planner。跨 root 绑定逻辑 team/stage/revision、实际端点和唯一传输入口；优先已有原生能力或当前宿主明确支持的控制入口。

上报只需 PLAN_GATE、DECISION_REQUIRED、STAGE_RESULT。事件 queued / delivered / handled 与有来源的决定分开；入队不能声称对端已处理。旧 revision 不覆盖新计划，event ID 不代替 supervisor 的稳定 run_key。

无获支持的发送入口时明确 CROSS_ROOT_UNSUPPORTED，并保留事件与阶段结果；不得静默改用旧 queue、UI 操作、rollout 改写或抢占活跃线程的第二 app-server。授权内不依赖新决定的工作继续，真正 gate 仍有效。

Dot 只跟进明确绑定的任务，转达实质失败、决定请求和完整交付；Owner 的决定保留来源与 revision。它不改科研计划、不调度 GPU、不另建同阶段执行队。需当前账户完成一次无副作用往返才能标已验证；没有真实闭环时标 DOT_NOT_VERIFIED，不用产品文档代替。

长训练沿用 `.ai/LONG_RUNNING_TASKS.md`；不派 agent 轮询。启动用 `(stage, revision, approved_step, approved_attempt)` 关联原 job/receipt，回执未知先核对原任务，不盲目重跑。

## 运行接口

运行时命令以 `.ai/scripts/workflow_state.py --help`、`stage_channel.py --help` 和当前实际 tools schema 为准。示例投影在 `templates/STAGE_CONTRACT.example.json`，它本身不构成授权。在当前任务的证据记录中说明实际安装和验收范围。

### 阶段绑定与派生

下面的参数来自真实宿主记录与现有批准 plan；不是按角色昵称猜 ID。先查看当前身份：

```bash
python3 .ai/scripts/workflow_state.py identity --transcript /absolute/rollout.jsonl
python3 .ai/scripts/workflow_state.py team-init --session REAL_ROOT_ID --team TEAM_ID --transcript /absolute/rollout.jsonl
python3 .ai/scripts/workflow_state.py bind-stage --actor PLANNER_ID --plan /absolute/stage.json
```

阶段授权签发者与接手的 Planner 可以是不同 root：`authorization.issuer_actor` 和 `source_ref` 始终保留原签发者及真实 Owner 指令；可选 `planner_actor` 指定已在同一 team 登记的实际 root。省略或 null 表示仍由签发者担任 Planner。初次绑定由原签发者执行，root grant 交给指定 Planner；后续 revision 不得借此更换签发者或 Planner。

A 入口的两个 root 使用同一 team 与单机状态权威，`responsible_actor` 填真实 lead ID。B 入口先用 `lead_task_name`、`lead_role` 绑定待创建 lead；实际 spawn 回执才绑定真实 child，不将它登记为 root。`authorization.source_ref` 指向真实 Owner 指令所在的 rollout 文件行，`plan_ref` 指向已有计划。

lead 为成员投影已批准的子范围并登记，再显式检查和预留，随后用原生 spawn 亲自创建成员：

```bash
python3 .ai/scripts/workflow_state.py subgrant --actor LEAD_ID --parent-grant GRANT_ID --task-name specialist --role worker --grant /absolute/member-grant.json
python3 .ai/scripts/workflow_state.py prepare-spawn --actor LEAD_ID --task-name specialist
```

使用原生 `spawn_agent` 的实际角色、task_name 与 `fork_turns="none"` 创建成员后，立即将原始工具回执保存并登记：

```bash
python3 .ai/scripts/workflow_state.py record-spawn --actor LEAD_ID --task-name specialist --result /absolute/native-spawn-result.json
```

`prepare-spawn` 预留的是明确标为 project 的请求，不冒充 native tool_use_id；重复 prepare 复用原预留，不能据此重复 spawn。`record-spawn` 核对真实 child transcript、创建者、角色与 task path，未知回执保持占位。原生 hook 若执行，会与同一预留对账，不重复计数；这套显式流程不依赖 hook 是否被当前宿主触发，也不将 CLI 调用记成 hook 验收通过。完成后用真实 `reconcile-terminal` 回收成员席位，普通技术消息不需要额外确认链。

子授权文件只需当前 scope、budget 和 `delegate_depth_left`，不能扩出父授权。完成状态由真实回执更新；若宿主返回形状未识别，用 `reconcile-spawn` / `reconcile-terminal` 对照真实 transcript，不重复创建任务。`--state` 只用于明确的单机共同状态位置或隔离演练；生产默认复用现有 git-common-dir 数据库，不另开额度。

### 跨 root 通道

所附适配器使用已运行的 Codex App Server Unix 控制 socket，并依赖 Node.js 和 `ws`。该路径在一个本地部署中完成过往返；新宿主仍需确认端点、权限与实际处理结果，不启动第二个服务。对已卸载的绑定线程，先在同一入口 resume，再按 idle/active 选择 start/steer；不改变对方模型、sandbox 或 approval 设置。

```bash
python3 .ai/scripts/stage_channel.py --root . --actor ACTUAL_SENDER bind --binding /absolute/binding.json
python3 .ai/scripts/stage_channel.py --root . --actor ACTUAL_SENDER send --binding-id BINDING_ID --event /absolute/event.json
python3 .ai/scripts/stage_channel.py --root . --actor ACTUAL_RECIPIENT handle --event-id EVENT_ID --result-ref /absolute/result.json
python3 .ai/scripts/stage_channel.py --root . --actor ACTUAL_RECIPIENT status --event-id EVENT_ID
```

用 `templates/BINDING.example.json`、`EVENT.example.json`、`DECISION.example.json` 从已批准阶段填值。消息 handled 不产生批准；明确决定通过 `decide` 独立登记来源和 revision。重复事件复用原回执，传输结果未知先核对原线程。Dot 仍需当前账户实际接入与闭环证据，不能拿本机跨 root 通过代替。

supervisor prepare 需要跨消息恢复时附加 `--stage-team TEAM --stage-id STAGE --plan-revision REV --approved-step STEP --approved-attempt N`；这五项构成稳定 run_key，重复 prepare/launch 使用原 receipt。已有长任务调用方式继续保留，不重新启动或改写旧 receipt。
