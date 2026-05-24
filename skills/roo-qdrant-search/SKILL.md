---
name: roo-qdrant-search
description: Search Roo Code codebase indexes stored in Qdrant from Codex. Use when the user wants Codex to reuse Roo Code semantic search data, inspect Roo-created Qdrant collections, validate indexed payloads, or query indexed code chunks instead of relying only on raw file search. This skill is especially relevant for Roo setups that use Qdrant plus an OpenAI-compatible embedding provider such as OpenRouter.
---

# Roo Qdrant Search

Use this skill to query the same semantic index that Roo Code has already written into Qdrant.

The bundled script can:

- list Roo-created collections and their vector sizes
- inspect sample indexed chunks
- generate a query embedding with an OpenAI-compatible embeddings API
- search one or more Qdrant collections and return scored code chunks

## Quick Start

Run these commands from the workspace root when possible:

```bash
python3 scripts/roo_qdrant_search.py collections
python3 scripts/roo_qdrant_search.py peek --limit 2
python3 scripts/roo_qdrant_search.py search "where is the checkpoint loading logic?" --limit 6
```

Use `--json` when you want machine-readable results.

## Defaults

The script defaults reflect the current Roo setup that motivated this skill:

- Qdrant URL: `http://127.0.0.1:6333`
- collection selection: all collections matching `ws-*`
- embedding base URL: `https://openrouter.ai/api/v1`
- embedding model: `qwen/qwen3-embedding-4b`
- embedding API key env var: `ROO_INDEX_EMBED_API_KEY` or `OPENROUTER_API_KEY`

Roo payloads are expected to include:

- `filePath`
- `startLine`
- `endLine`
- `codeChunk`

Read the referenced files with normal workspace tools before making detailed claims or code changes. Treat the semantic hits as retrieval, not final evidence.

## Workflow

1. Run `collections` when you need to confirm that Roo indexing exists and see available collections.
2. Run `peek` when you need to inspect payload structure or sanity-check which repository a collection contains.
3. Run `search` for semantic retrieval.
4. Open the top matching files with normal read tools and verify the surrounding code before answering or editing.

## Search Guidance

- Prefer searching all `ws-*` collections unless the user asks for a specific collection.
- Use `--collection <name>` when multiple Roo-indexed workspaces exist and you need to isolate one.
- Use `--score-threshold` to suppress weak matches.
- If results look wrong, confirm the embedding model matches Roo's configured model. Mixed embedding models degrade recall badly.
- Use `--workspace-root` when the current working directory is not the root that `filePath` is relative to.

## Environment Overrides

- `ROO_INDEX_QDRANT_URL`
- `ROO_INDEX_COLLECTION`
- `ROO_INDEX_EMBED_BASE_URL`
- `ROO_INDEX_EMBED_MODEL`
- `ROO_INDEX_EMBED_API_KEY`
- `ROO_INDEX_WORKSPACE_ROOT`

## Failure Modes

- If Qdrant is unreachable, verify the local container is running and the URL is correct.
- If the embedding request fails because outbound network is sandboxed, rerun the command with escalation.
- If `search` reports a missing API key, ask the user to expose the same embedding provider key Roo uses through an env var.
- If there are no `ws-*` collections, Roo has not indexed this workspace yet or indexing was cleared.

## Script

Use `scripts/roo_qdrant_search.py` for all operations in this skill.
