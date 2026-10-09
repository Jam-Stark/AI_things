# Jam Coding Role v1.6.0

完整阶段交给 execution lead：Owner 新建独立 root，或 Planner 直接派生 child。两者在已批准范围内自主组队、排障、验证和交付；明确 gate 或范围外问题才请求决定。新增 outside_view，用新上下文审视问题定义，不设审批门。

Owner 交付遵循 `references/ROLE.md`：清楚回答问题、给出证据，并主动选有用的图示或交互解释。短问题直接回答。角色、入口和按需文档各保留一份职责，减少重复 prompt。

```bash
python3 scripts/bootstrap.py init /path/to/project --runtime codex
python3 scripts/bootstrap.py refresh /path/to/project --runtime codex
python3 scripts/bootstrap.py refresh /path/to/project --runtime codex --apply
python3 scripts/migrate_v160.py --root /path/to/project
python3 scripts/migrate_v160.py --root /path/to/project --apply
```

新项目默认安装通用 12 种角色、38 个配置；已有项目保留其 role profile。可选 `doordog` profile 增加 IsaacLab 两种角色，但依赖路径等项目事实由 `.ai/PROJECT.md` 或既有本地角色说明提供。bootstrap 使用 `--role-profile doordog`，迁移器使用 `--profile doordog`。

init/refresh/migrate 均默认 dry-run，用 `--apply` 执行；改变的文件有可恢复备份。保留 App 的 Main 模型选择、已配置 context、项目文档、研究改动、运行收据与配额身份。旧组织限制定向替换；可选 artifact 模板不预置远程目标或上传授权。迁移与恢复示例见 [migrate-existing-project.md](examples/migrate-existing-project.md)。

新增 lead 默认 Sol6.1/high，可选 xhigh/max；outside 默认 Sol6.1/xhigh。原有 Sol effort 变体、Luna 窄任务和 Astra 唯一 medium 身份保留。默认逻辑席位5包含lead，派生授权深度默认2；以实际阶段和宿主上限为准。

具体能力、当前安装和仍未验证的宿主行为见 `VERIFICATION.md`。磁盘更新不使已打开会话自动重载；新会话启用，hooks 信任交给宿主正常流程。阶段消息传输和 Dot 需要真实端到端证据。
