# AI_things

这个仓库用于集中管理多台设备上可复用的 AI 配置、Codex skills、Coding Roles 和辅助脚本。

当前主要内容：

- `skills/jam-coding-role`：通用 Coding Role 与项目 AI workflow bootstrap，当前版本 **v1.6.0**。提供 root/child execution lead 双入口、阶段内自主执行、Outside view 和单源角色配置；memory、长任务和 artifact handoff 按需启用。
- `skills/pdf`：PDF 读取、生成与渲染验证工作流，强调用 Poppler/PNG 预览检查版式。
- `skills/pdf2zh-paper-translator`：从本地 Papers/Zotero/ZotMoov 或合法开放来源解析论文 PDF，并通过 pdf2zh + Gemini 翻译为中英双语/中文 PDF。
- `skills/ppt-master`：多格式资料到 SVG 页面再到 PPTX 的演示文稿生成流水线，包含模板、图表和图片生成辅助脚本。
- `skills/revise-paper`：系统修订 Overleaf/多文件 LaTeX 论文，覆盖结构、语言、公式、图表、BibTeX、匿名化和投稿前检查。
- `skills/rl-command-manager`：管理 RL train/play 命令批次，生成 play 命令并做差异分析。
- `skills/roo-qdrant-search`：从 Codex 查询 Roo Code 写入 Qdrant 的语义代码索引。
- `skills/scientific-figure-making`：按 figures4papers 风格创建论文、幻灯片和报告使用的出版级 Matplotlib 图表，覆盖柱状图、趋势图、热力图和多面板布局。
- `skills/tensor-formula-viz`：为张量、矩阵、向量公式或代码路径生成形状与计算语义严格对齐的可视化。
- `skills/zotero-zotmoov`：记录 Zotero Desktop + ZotMoov 的本地导入、附件移动和验证流程。

## 使用方式

推荐在每台设备上把仓库 clone 到固定位置，然后把需要启用的 skill 链接到 Codex skills 目录：

```bash
git clone git@github.com:Jam-Stark/AI_things.git ~/workspace/AI_things
ln -s ~/workspace/AI_things/skills/jam-coding-role ~/.codex/skills/jam-coding-role
ln -s ~/workspace/AI_things/skills/rl-command-manager ~/.codex/skills/rl-command-manager
ln -s ~/workspace/AI_things/skills/roo-qdrant-search ~/.codex/skills/roo-qdrant-search
ln -s ~/workspace/AI_things/skills/pdf ~/.codex/skills/pdf
ln -s ~/workspace/AI_things/skills/pdf2zh-paper-translator ~/.codex/skills/pdf2zh-paper-translator
ln -s ~/workspace/AI_things/skills/ppt-master ~/.codex/skills/ppt-master
ln -s ~/workspace/AI_things/skills/revise-paper ~/.codex/skills/revise-paper
ln -s ~/workspace/AI_things/skills/scientific-figure-making ~/.codex/skills/scientific-figure-making
ln -s ~/workspace/AI_things/skills/tensor-formula-viz ~/.codex/skills/tensor-formula-viz
ln -s ~/workspace/AI_things/skills/zotero-zotmoov ~/.codex/skills/zotero-zotmoov
```

如果目标路径已经存在，先确认是否需要备份或合并，再替换为软链接。

## 新项目 AI workflow bootstrap

最小通用项目：

```bash
python ~/workspace/AI_things/skills/jam-coding-role/scripts/bootstrap.py init \
  /path/to/new-project
```

Codex + OMO + standalone Claude 的 ML/RL、simulation 或 robotics 项目，可以先只安装运行时路由：

```bash
python ~/workspace/AI_things/skills/jam-coding-role/scripts/bootstrap.py init \
  /path/to/new-project \
  --profile scientific \
  --runtime codex \
  --runtime omo \
  --runtime claude
```

只有真实需要时再增加设施：

```bash
  --memory \
  --codex-coordination-state \
  --long-run-supervisor \
  --stage-workflow \
  --artifact-sync \
  --omo-team-mode
```

然后从真实 code/config 填写项目内 `.ai/PROJECT.md`，并使用相同参数运行：

```bash
python ~/workspace/AI_things/skills/jam-coding-role/scripts/bootstrap.py audit \
  /path/to/new-project \
  --profile scientific \
  --runtime codex \
  --runtime omo \
  --runtime claude
```

`init`、`refresh` 和 `migrate_v160.py` 默认只预览，添加 `--apply` 才写入并备份。Codex 的三条入口共用生成器，更新 managed workflow/角色并定向清理已知旧组织规则，保留项目 overlay、memory、无关配置/hooks 和运行状态。使用新会话加载更新；完整说明见 [迁移示例](skills/jam-coding-role/examples/migrate-existing-project.md)。

## Jam Coding Role v1.6.0

通用默认包含 12 种职责、38 个注册配置。execution lead 可由 Owner 独立启动，也可由 Planner 派生；Outside view 使用新上下文，只提出建议。角色能力与有效阶段授权共同决定转派，多个父节点共享 team 额度。Main model/effort 由 App 选择，已有 context 设置保留。

新项目不预置私人路径、云端文件夹或上传授权。已有项目保留其 role profile；可选 IsaacLab profile 用于需要该领域角色的项目。OMO 和 standalone Claude 继续使用各自 runtime 规则。

安装或修改 hooks 后，通过宿主 `/hooks` 检查与信任。配置解析、显式 A/B 实际运行、跨 root 通信和自动回调是不同证据；已知限制见 [VERIFICATION.md](skills/jam-coding-role/VERIFICATION.md)，版本历史见 [CHANGELOG.md](skills/jam-coding-role/CHANGELOG.md)。

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
- `jam-coding-role` 的 universal core 受 Karpathy-inspired guidelines 启发，但项目必须复制并 pin 版本，runtime/model/tool 细节留在项目配置中，避免全局更新导致所有 repo 同时漂移。
- `pdf2zh-paper-translator` 需要 `GEMINI_API_KEY`，可通过 macOS Keychain、环境变量或本机 `~/.config/pdf2zh-paper-translator/env` 提供；本地论文库路径用 `PAPERS_DIR` 配置，输出目录可用 `DESKTOP_DIR` 配置。
- `ppt-master` 的图片生成后端通过 `IMAGE_BACKEND` 和各服务商的环境变量配置，例如 `GEMINI_API_KEY`、`OPENAI_API_KEY`、`QWEN_API_KEY`、`ZHIPU_API_KEY` 等；不要把实际密钥写入仓库。
- `revise-paper` 来源于 `CISLab-HKUST/revise-paper`，采用 CC BY-NC-SA 4.0；使用时需要完整 LaTeX 工程，并建议安装 `latexmk` 与 PDF 页面渲染工具。
- `scientific-figure-making` 来源于 `ChenLiu-1996/figures4papers` 的同名目录；用于有明确出版目标的 Matplotlib 图表，并建议同时导出高分辨率 PNG 与 PDF/SVG 矢量版本。
- `tensor-formula-viz` 来源于 `wdkns/wdkns-skills` 的 `skills/tensor-formula-viz`；默认使用可编辑 TikZ，中文图建议使用 XeLaTeX 和 Fandol 字体集。
- `zotero-zotmoov` 的设备路径通过 `ZOTERO_DATA_DIR`、`ZOTERO_PROFILE_DIR`、`ZOTERO_DB` 和 `PAPERS_DIR` 配置。
