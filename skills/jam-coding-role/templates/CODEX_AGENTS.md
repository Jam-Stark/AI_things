# Codex adapter v1.6.0

遵循 root AGENTS.md 与 `.ai/ROLE.md`。委托时读 `.codex/TEAM.md`；完整阶段读 `.ai/EXECUTION_TEAM.md`。Main model/effort 归 App；项目保留已有 context/compact 设置。

角色生成器、运行时授权与 hook 共用单源 policy。只读配置不等于运行生效；新会话加载后再按真实结果判断。待处理事件与长任务收据保留，通知不等于决定或验收。

本机 linked-worktree hooks 使用 `.ai/scripts/install_codex_hooks.py` 注册仅限目标工作树的用户入口；它保留无关 hooks，不修改 trust。按宿主 `/hooks` 审阅变化。长任务使用既有 supervisor 与持久等待，不建模型轮询循环。
