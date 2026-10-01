# Jam Coding Role v1.5.0 — Verification

当前本地版本为 v1.5.0：默认 Sol/medium、子任务上限 5、迁移保留 Main context/compact。v1.3.0 内容仅为历史，不代表当前 hooks 行为；当前 SessionStart/PostCompact 不自动归档未处理事件。


## Completed against the repository implementation

```text
Python syntax compilation                               PASS
JSON / JSONC parse                                      PASS
TOML parse                                              PASS
Bundled unit tests                                      13 / 13 PASS
Minimal bootstrap creates no MEMORY.md or team state    PASS
Full optional bootstrap remains lazy-loaded             PASS
OpenCode optional docs are not globally preloaded       PASS
Standalone Claude Agent capability is denied            PASS
OMO Team Mode appears only with explicit flag           PASS
Coordination tooling defaults to inactive               PASS
Adaptive ephemeral Codex spawn remains allowed          PASS
Strict writer contract and exclusive lease checks       PASS
Candidate freeze requires formal review/QA purpose      PASS
Memory inbox is created only by a durable candidate      PASS
Long-run receipt works without activating team ledger   PASS
Artifact bundle requires explicit stage handoff          PASS
Checkpoint default exclusion and sensitive-name scan    PASS
PreToolUse no-op success emits no stdout                 PASS
PreToolUse deny omits unsupported `continue`             PASS
Malformed strict hook input fails closed                 PASS
Repo-local hooks resolve scripts from Git root            PASS
PostToolUse persistence is metadata-only                 PASS
SessionStart pending events deliver/archive once         PASS
95 MiB semantic standard-ZIP splitting                   PASS
Oversized checkpoint is not binary-sliced                PASS
```

## Evidence boundary

The checks establish package structure, helper behavior and synthetic local workflows. They do not establish:

```text
real production repository migration                    NOT RUN BY GENERIC PACK
real Codex MultiAgentV2 P2P session                     NOT RUN
real OMO Team Mode session                              NOT RUN
real tmux/GPU/IsaacLab training                         NOT RUN
Google Drive upload                                     NOT RUN
robot hardware action                                   NOT RUN
```

Project migrations must separately verify protected paths, local Git authorization, actual runtime evidence and any project-specific overlay.

## v1.5.0 — 2026-09-23

Main/App model ownership; preserved explicit Main context budgets; five-child ceiling; GPT-6 Sol/medium default and Luna/Sol roles; one Astra/medium child identity per team; model-gated notes/compact; bounded Main-to-Main outbox; opt-in Linux owned-tool cleanup. No Jev integration. New Codex bootstrap installs v150-assets; refresh does not silently overwrite old project configs. Existing targets use the reviewed migration kit. Native hooks/transport/model switching require local effective-runtime acceptance. Legacy long-run, artifact, memory and coordination scripts are preserved, not rewritten.

## v1.5.0 本地证据（2026-09-23）

技能 frontmatter 校验、通用 Codex assets 静态预检和 bootstrap Codex dry-run 通过。迁移入口实际用于 7 个 DoorDog 工作树，每个目标静态预检通过。真实 App hook 拦截、有效模型配置、模型切换、双 Main 通信与进程回收均 NOT_RUN；未运行包内测试矩阵。旧版 PASS 不向新版运行结论延伸。
