<!-- managed-by: jam-coding-role; file: CONTEXT_POLICY.md -->
# Model-aware context v1.6.0

Astra：允许原生实验性 notes/history；Sol、Luna：默认 compact。不要把项目级 `features.token_budget.use_history_notes_extension = true` 当成开关；角色、profile 同样不写该键。不要在每个会话里手工猜模型再修改项目全局配置。

Main 项目配置只请求 `features.context_management.experimental_mode = true`，由实际模型 capability、认证/套餐与宿主实现决定是否启用。通用模板不设置 Main 窗口或 compact；现有项目迁移保留已配置的 Main context/compact；移除项目 `features.token_budget.enabled = true`，其他上下文特性按包内策略。API key、自定义 provider 或不满足资格的认证不强制 notes；明确报告实际走 compact。

Astra 子角色开启 experimental_mode，且不钉死 token_budget；Sol/Luna 子角色 experimental_mode=false、token_budget.enabled=false，使用有界窗口和默认 compact。所有子角色都禁止继承 Main 全部历史。

若实际模型切换或上下文行为出现问题，针对该路径核对有效配置与宿主回执；不预先运行模型切换矩阵。项目静态配置不证明子角色预算生效，已有暂停的宿主缺陷不由本版重新开启。

若切换仍失败，先定位有效配置和模型 capability；不要在项目追加 true“强修”。必要时用该模型默认 compact 的新会话并传递短 handoff，标记这是兼容性降级。不要复制整段旧 notes 到新模型。

这里的模型分流依据是上游 Codex 的 `apply_experimental_context` 能力/认证检查，而不是对所有安装版本的保证。当前官方配置参考：https://learn.chatgpt.com/docs/config-file/config-reference 。

实施约束：以上运行验收场景是后续按需验证说明，不是本次安装自动启动的测试任务。Owner 确认实现或报告具体问题后再安排相关测试；未执行项保持 NOT_RUN。
