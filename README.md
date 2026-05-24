# AI_things

这个仓库用于集中管理多台设备上可复用的 AI 相关配置、Codex skills 和辅助脚本。

当前主要内容：

- `skills/rl-command-manager`: 管理 RL train/play 命令批次，生成 play 命令并做差异分析。
- `skills/roo-qdrant-search`: 从 Codex 查询 Roo Code 写入 Qdrant 的语义代码索引。

## 使用方式

推荐在每台设备上把仓库 clone 到固定位置，然后把需要启用的 skill 链接到 Codex skills 目录：

```bash
git clone git@github.com:Jam-Stark/AI_things.git ~/workspace/AI_things
ln -s ~/workspace/AI_things/skills/rl-command-manager ~/.codex/skills/rl-command-manager
ln -s ~/workspace/AI_things/skills/roo-qdrant-search ~/.codex/skills/roo-qdrant-search
```

如果目标路径已经存在，可以先确认是否需要备份或合并，再替换为软链接。

## 多设备同步流程

```bash
cd ~/workspace/AI_things
git pull
```

在某台设备上新增或修改通用 skill 后：

```bash
git status
git add skills README.md .gitignore
git commit -m "Update shared skills"
git push
```

其他设备再执行 `git pull` 即可同步。

如果某台设备没有 `~/.codex/skills/*/SKILL.md` 用户自定义 skill，则无需新增 `skills/` 目录内容；只确认忽略规则、敏感信息扫描和现有脚本语法即可。

## 注意事项

- 不要提交 `~/.codex/skills/.system/`、`~/.codex/plugins/`、`~/.codex/config.toml`。
- 不要提交 API key、token、密码、本机私有路径、日志、缓存或生成文件。
- 需要密钥的 skill 应通过环境变量读取，例如 `OPENROUTER_API_KEY` 或 `ROO_INDEX_EMBED_API_KEY`。
- 设备差异配置建议放在本机环境变量、未跟踪的 `.env` 文件或单独的 local 配置里。
- 导入其他设备上的 skill 前，先检查是否包含硬编码密钥或本机专用路径。
