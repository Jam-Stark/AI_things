---
name: pdf2zh-paper-translator
description: Resolve academic paper PDFs from the user's local Papers library, Zotero/ZotMoov attachments, or legal open-access online sources such as Semantic Scholar, arXiv, Unpaywall, and OpenAlex, then translate them to Chinese with PDFMathTranslate/pdf2zh using Gemini. Use when Codex is asked to find or download a paper by title, DOI, arXiv ID, URL, or filename, run pdf2zh non-interactively with a stored Gemini API key/model, save any downloaded original PDF into SharedWorkspace/Papers, and place generated mono/dual translated PDFs on the user's Desktop.
---

# PDF2ZH Paper Translator

## Workflow

Use `scripts/translate_paper.py` for deterministic translation instead of launching `pdf2zh -i`.

Default resolver order:
- Search PDFs recursively under `PAPERS_DIR`; if unset, the script defaults to `~/Papers`.
- Search local Zotero attachment records, resolving ZotMoov `attachments:` paths against the same Papers directory.
- If no reliable local match exists, search legal OA online sources: direct URL, DOI, arXiv ID, Semantic Scholar, Unpaywall, and OpenAlex.
- Save any downloaded original PDF to `PAPERS_DIR/Downloaded` before translation.
- Use PDFMathTranslate via the local `pdf2zh` command.
- Use Gemini service with `-s gemini:<model>`.
- Write generated `*-mono.pdf` and `*-dual.pdf` files to `DESKTOP_DIR`; if unset, the script defaults to `~/Desktop`.

## First-Time Setup

If the Gemini API key is not already configured, run one setup path:

```bash
python3 "$HOME/.codex/skills/pdf2zh-paper-translator/scripts/translate_paper.py" --store-api-key
```

This stores the key in macOS Keychain under `pdf2zh-paper-translator-gemini-api-key`.

Alternative local env-file setup:

```bash
python3 "$HOME/.codex/skills/pdf2zh-paper-translator/scripts/translate_paper.py" --init-config
```

Then edit `~/.config/pdf2zh-paper-translator/env` and set `GEMINI_API_KEY=...`. Keep that file local and out of source control. Set `PAPERS_DIR` to the local ZotMoov/Google Drive Papers directory and `DESKTOP_DIR` to the preferred output directory when the defaults do not match the current device.

## Translate A Paper

Preferred system command:

```bash
pdf2zh "Proximal Policy Optimization Algorithms"
```

The user's `~/.local/bin/pdf2zh` is a wrapper. For a paper title, DOI, arXiv ID, or URL, it invokes this skill's `translate_paper.py`. For original PDFMathTranslate behavior, use:

```bash
pdf2zh --raw [pdf2zh args...]
pdf2zh --pdf2zh-help
pdf2zh -i
```

Run the script with the user's paper name or filename fragment:

```bash
python3 "$HOME/.codex/skills/pdf2zh-paper-translator/scripts/translate_paper.py" "Proximal Policy Optimization Algorithms"
```

Use `--dry-run` to verify the match and command without invoking the API:

```bash
python3 "$HOME/.codex/skills/pdf2zh-paper-translator/scripts/translate_paper.py" "ppo" --dry-run
```

Force online OA lookup without using local copies:

```bash
python3 "$HOME/.codex/skills/pdf2zh-paper-translator/scripts/translate_paper.py" "Proximal Policy Optimization Algorithms" --force-online --dry-run
```

Download an original OA PDF into the Papers library without translating:

```bash
python3 "$HOME/.codex/skills/pdf2zh-paper-translator/scripts/translate_paper.py" "arXiv:1707.06347" --download-only
```

If the query is ambiguous, list candidates and select by index:

```bash
python3 "$HOME/.codex/skills/pdf2zh-paper-translator/scripts/translate_paper.py" "agent" --list
python3 "$HOME/.codex/skills/pdf2zh-paper-translator/scripts/translate_paper.py" "agent" --select 2
```

## Useful Overrides

- `--model gemini-3.5-flash` changes the Gemini model.
- `--pages 1-3,7` translates selected pages.
- `--lang-in en --lang-out zh` controls languages.
- `--papers-dir PATH` searches another library.
- `--output-dir PATH` writes translated PDFs somewhere other than Desktop.
- `--pdf2zh-bin PATH` uses a specific `pdf2zh` executable.
- `--force-online` skips local/Zotero lookup and searches online OA sources.
- `--no-online` disables online fallback.
- `--online-list` lists online candidates without downloading.
- `--download-only` resolves or downloads the original PDF and stops before translation.
- `--download-dir PATH` writes downloaded original PDFs somewhere other than `PAPERS_DIR/Downloaded`.
- `--loose-local-match` permits low-confidence local/Zotero matches for long titles; avoid it unless the user explicitly wants fuzzy local-only matching.
- `UNPAYWALL_EMAIL` in the env config enables Unpaywall DOI fallback.

The local `pdf2zh` uv tool reads Gemini credentials from `GEMINI_API_KEY` and accepts model selection through `-s gemini:<model>`, so the script supplies both from the config, Keychain, or environment.

For full paper-title queries, local and Zotero matching uses a stricter dynamic threshold. If no high-confidence local match exists, let the resolver continue to online OA sources instead of translating a merely related local paper.
