# Codex team v1.6.0

真实 root/parent 由宿主回执决定，阶段职责由 `.ai/EXECUTION_TEAM.md` 的授权决定；两者不能互换。角色与 effort 来自 `.ai/role-policy.json` 生成的配置，路由见 `.ai/MODEL_ROUTING.md`。Main model/effort 保留 App 选择。

新委托使用短 brief 与 `fork_turns="none"`，写明目标、范围、输入、产出和必要证据。先绑定已有阶段授权，再由 lead 依 EXECUTION_TEAM 的 prepare → native spawn → record 流程亲自创建成员；记录真实回执，不依赖未观测到的 hook 触发。可派生角色由当前安装的 role-policy 中 can_spawn 决定；实际派生还需要有效 grant 和剩余额度。outside_view 使用新上下文，不参与施工或强制审批。

同树使用当前宿主实际暴露的 spawn、send_message、followup_task、interrupt 等原生工具。实际创建者控制自己的 child；peer 技术消息不转移授权，不要求逐条抄送 Planner。跨 root 通过已绑定的阶段通道，不用同树控制工具冒充跨 root 传输。

逻辑 team 共用席位，默认 5（含 lead 和所有支持身份，不含 Planner）；同时遵守宿主更小的上限。native `agents.max_concurrent_threads_per_session` 不是跨 root 额度。未知派生/终止回执保持占位，Astra 唯一身份持续保留。

新会话加载新角色和规则；修改磁盘不证明旧会话已热加载。已注册 hooks 的信任须通过宿主正常流程处理，不能改写 trust。配置、helper 执行、真实派生、通信和实验效果分别报告。
