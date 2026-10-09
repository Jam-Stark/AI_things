# 迁移现有项目到 v1.6.0

先读取项目入口、最小 memory 路由和当前安装版本。安装器更新 workflow 与角色配置，保留项目 facts、memory、无关配置/hooks、凭据和运行状态；它不运行 Git、模型、训练或 hook trust 操作。

预览，再在本任务已有授权内应用：

```bash
python3 scripts/migrate_v160.py --root /path/to/project
python3 scripts/migrate_v160.py --root /path/to/project --apply
```

新项目默认使用 generic profile。已有角色配置决定原 profile；需要显式选择可使用 `--profile generic` 或 `--profile doordog`。`doordog` 是可选 IsaacLab 角色集，安装器保留已有专业说明和本机依赖路径；通用源不携带个人目录。使用 bootstrap 时对应参数是 `--role-profile`。

应用结果给出逐文件备份目录。恢复也先预览；恢复操作会备份被替换的当前文件：

```bash
python3 scripts/migrate_v160.py --restore /path/to/backup
python3 scripts/migrate_v160.py --restore /path/to/backup --apply
```

用已安装的 `python3 .ai/scripts/codex_preflight.py --root .` 检查配置。新会话加载角色；hooks 按宿主 `/hooks` 流程审阅信任。显式 prepare → native spawn → record 流程见 `.ai/EXECUTION_TEAM.md`。已有项目中的 HKT 等时间约定、实验命令、交付限额和外部目标保持本地定义。

磁盘安装和静态预检不证明当前宿主已执行 hooks、支持跨 root 控制或应用所有 context 设置；实际证据边界见 [VERIFICATION.md](../VERIFICATION.md)。
