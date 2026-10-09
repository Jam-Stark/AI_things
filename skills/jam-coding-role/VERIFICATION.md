# v1.6.0 验证范围

2026-10-09。以下区分通用发布包检查与已有部署观察；本文件不附私人会话、原始 rollout 或本机证据目录。

## 通用发布包

在一个隔离的本地目录执行了一次 `bootstrap.py init --runtime codex --apply`、生成的 `codex_preflight.py` 和 `bootstrap.py refresh --runtime codex`：

- fresh init 通过，通用 12 种职责、38 个配置；预检为 `STATIC_PASS`。
- refresh 没有待改变文件；无关配置、原有 Main context、用户 hooks、项目文档、memory 约定和运行状态保持不变。
- skill-creator `quick_validate.py` 通过；这证明 skill 结构有效，不证明模型决策质量。
- 通用默认不含个人目录、云端文件夹 ID 或站立上传授权。可选 `doordog` profile 增加 IsaacLab 两种角色，专业路径仍来自安装项目。

这些检查验证本地生成与安装行为，不保证所有操作系统、Codex 版本、账户或模型都具备相同能力。安装器不运行模型、训练或 hook trust 操作。

## 已有部署的运行观察

v1.6.0 runtime 曾在一个 Linux/Codex 部署中通过显式 A/B 生命周期：root lead 创建 member，以及 Planner 创建 child execution lead、再由 lead 创建 member。实际身份、P2P、回执登记、完成对账和阶段验收均有本地证据。跨 root 消息的 handled 回执、重复事件与 supervisor 稳定 run_key 也完成过验证。此次通用化保留这些运行逻辑，没有重新执行全套运行测试。

使用流程是 prepare → native spawn → record；CLI 验证记录不冒充原生 hook 回调。原始材料由部署项目保管，不随通用包公开。

## 尚未证明的能力

- 已有部署的四项 hook 已配置并经用户信任，但自动回调没有得到对应执行记录，原因仍为 `INCONCLUSIVE`。
- Dot 闭环、active-turn steer 和其他宿主上的跨 root 控制未验收。Unix socket 适配器需要目标宿主实际提供端点、权限、Node.js 与 `ws`。
- 角色中的 context/compact 是配置意图；已知继承问题没有由本版修复。磁盘更新不证明已打开会话会热加载。

新宿主应使用真实任务中必要的有界证据确认所需能力；不要因本文件而启动例行模型或训练矩阵。接口与设计来源见 [WORKFLOW_SOURCES.md](references/WORKFLOW_SOURCES.md)。
