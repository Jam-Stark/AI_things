---
name: zotero-zotmoov
description: Use when working with the user's Zotero library, especially importing papers or PDFs, organizing Zotero collections, comparing Semantic Scholar libraries, or anything involving ZotMoov-managed Google Drive attachment storage. This skill records that the user stores Zotero PDFs through ZotMoov in Google Drive and prefers local Zotero Desktop workflows when attachment files must be visible and moved by ZotMoov.
---

# Zotero + ZotMoov

## User Setup

- Zotero local data directory: set `ZOTERO_DATA_DIR` when it is not `~/Zotero`.
- Zotero profile: set `ZOTERO_PROFILE_DIR` when direct profile inspection is needed.
- ZotMoov target directory: set `PAPERS_DIR` to the local Google Drive/ZotMoov `Papers` directory.
- Zotero base attachment path uses the same Google Drive `Papers` directory.
- Relative linked attachment paths are enabled.
- ZotMoov is used as the user's main cloud-file workflow for PDFs.
- Hidden ZotMoov preference `extensions.zotmoov.process_synced_files` may be set to `true`, but do not rely on sync events unless verified locally.

## Core Rule

When the user asks to import papers together with PDFs, prefer a local Zotero Desktop/Connector workflow so ZotMoov can see local attachment creation and move/copy PDFs into the Google Drive `Papers` directory.

Do not assume `mcp__zotero__.add_items_by_doi` or `mcp__zotero__.import_pdf_to_zotero` will appear immediately in the user's open Zotero Desktop library. Those tools may operate through Zotero Web/API state. If local Zotero auto-sync or file sync is disabled, the user may not see imported items or PDFs locally, and ZotMoov will not process them.

## Preferred Import Workflow

1. Confirm Zotero Desktop is running:
   `curl -s http://127.0.0.1:23119/connector/ping`
2. Confirm the current save target:
   `curl -s -X POST http://127.0.0.1:23119/connector/getSelectedCollection -H 'Content-Type: application/json' -d '{}'`
3. If the target collection is correct, use Zotero Connector endpoints:
   - `/connector/saveItems` to create the parent item metadata in the selected collection.
   - `/connector/saveAttachment` with the same session ID to attach local PDF bytes to the saved parent item.
4. Wait for ZotMoov's automatic processing delay.
5. Verify in local SQLite that the items are in the target collection and attachments are linked into the Google Drive path.

If the target collection is not correct and there is no safe programmatic way to switch it, ask the user to select the desired Zotero collection before importing.

## Existing Items And New Collections

Adding existing Zotero items to a new collection does not necessarily trigger ZotMoov. Collection membership changes and attachment-file movement are separate.

For collection-only organization, it is acceptable to update `collectionItems` or use a Zotero collection API if available. Keep all existing memberships unless the user explicitly asks to move items.

For file-path organization, be explicit about the tradeoff: a Zotero attachment normally has one physical linked path. Moving an attachment into a new collection folder such as `Embodied_AI/loco-manipulation` can move it out of its prior physical folder even if Zotero collection membership is preserved. Do not bulk-move old PDFs just because a paper was added to another collection unless the user confirms that the new collection should become the attachment's primary file directory.

## Verification Queries

Use read-only immutable SQLite when Zotero may be open:

```sh
ZOTERO_DB="${ZOTERO_DB:-${ZOTERO_DATA_DIR:-$HOME/Zotero}/zotero.sqlite}"
sqlite3 -header -column "file:${ZOTERO_DB}?mode=ro&immutable=1" 'SQL'
```

Useful checks:

- Collection item counts under `collections` and `collectionItems`.
- Imported item presence by DOI/title in local `itemData`.
- Attachment status in `itemAttachments`.
- ZotMoov-linked attachments typically have `linkMode=2` and `path` beginning with `attachments:`.
- Confirm physical files under the Google Drive `Papers` directory with `find`.

## Safety

- Before direct SQLite writes, confirm Zotero is closed and back up `zotero.sqlite`.
- Do not modify metadata, delete attachments, or remove existing collection memberships unless the user asks.
- Prefer local Zotero Connector for new imports with PDFs; use Zotero MCP for metadata/library tasks only when local Zotero visibility and ZotMoov movement are not required, or after explaining the sync limitation.
