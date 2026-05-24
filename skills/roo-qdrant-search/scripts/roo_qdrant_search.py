#!/usr/bin/env python3

import argparse
import json
import os
import sys
import textwrap
import urllib.error
import urllib.request
from pathlib import Path


DEFAULT_QDRANT_URL = os.environ.get("ROO_INDEX_QDRANT_URL", "http://127.0.0.1:6333")
DEFAULT_COLLECTION = os.environ.get("ROO_INDEX_COLLECTION")
DEFAULT_COLLECTION_PREFIX = "ws-"
DEFAULT_EMBED_BASE_URL = os.environ.get("ROO_INDEX_EMBED_BASE_URL", "https://openrouter.ai/api/v1")
DEFAULT_EMBED_MODEL = os.environ.get("ROO_INDEX_EMBED_MODEL", "qwen/qwen3-embedding-4b")
DEFAULT_API_KEY = (
    os.environ.get("ROO_INDEX_EMBED_API_KEY")
    or os.environ.get("OPENROUTER_API_KEY")
)
DEFAULT_WORKSPACE_ROOT = os.environ.get("ROO_INDEX_WORKSPACE_ROOT") or os.getcwd()


def build_url(base, path):
    return base.rstrip("/") + path


def http_json(method, url, payload=None, headers=None, timeout=60):
    request_headers = {"Content-Type": "application/json", "User-Agent": "roo-qdrant-search/1.0"}
    if headers:
        request_headers.update(headers)
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, method=method, headers=request_headers)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8")
            return json.loads(body) if body else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} failed with {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"{method} {url} failed: {exc.reason}") from exc


def list_collections(qdrant_url):
    response = http_json("GET", build_url(qdrant_url, "/collections"))
    return [item["name"] for item in response.get("result", {}).get("collections", [])]


def collection_info(qdrant_url, collection):
    response = http_json("GET", build_url(qdrant_url, f"/collections/{collection}"))
    return response.get("result", {})


def scroll_points(qdrant_url, collection, limit):
    payload = {"limit": limit, "with_payload": True, "with_vector": False}
    response = http_json(
        "POST",
        build_url(qdrant_url, f"/collections/{collection}/points/scroll"),
        payload=payload,
    )
    return response.get("result", {}).get("points", [])


def detect_collections(qdrant_url, explicit_collection=None, prefix=DEFAULT_COLLECTION_PREFIX):
    if explicit_collection:
        return [explicit_collection]
    collections = list_collections(qdrant_url)
    matched = [name for name in collections if name.startswith(prefix)]
    if not matched:
        raise RuntimeError(
            f"No collections matched prefix '{prefix}'. Available collections: {', '.join(collections) or '(none)'}"
        )
    return matched


def get_embedding(query, base_url, model, api_key):
    if not api_key:
        raise RuntimeError(
            "Missing embedding API key. Set ROO_INDEX_EMBED_API_KEY or OPENROUTER_API_KEY before using search."
        )
    payload = {"model": model, "input": query, "encoding_format": "float"}
    headers = {"Authorization": f"Bearer {api_key}"}
    response = http_json("POST", build_url(base_url, "/embeddings"), payload=payload, headers=headers)
    data = response.get("data", [])
    if not data or "embedding" not in data[0]:
        raise RuntimeError(f"Unexpected embeddings response: {json.dumps(response)[:500]}")
    return data[0]["embedding"]


def qdrant_search(qdrant_url, collection, vector, limit, score_threshold=None):
    payload = {
        "vector": vector,
        "limit": limit,
        "with_payload": True,
        "with_vector": False,
    }
    if score_threshold is not None:
        payload["score_threshold"] = score_threshold
    response = http_json(
        "POST",
        build_url(qdrant_url, f"/collections/{collection}/points/search"),
        payload=payload,
        timeout=120,
    )
    return response.get("result", [])


def resolve_path(file_path, workspace_root):
    if not file_path:
        return None
    path = Path(file_path)
    if path.is_absolute():
        return str(path)
    return str((Path(workspace_root) / path).resolve())


def trim_chunk(text, max_chars=900):
    text = (text or "").strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def format_result(item, workspace_root):
    payload = item.get("payload", {})
    file_path = payload.get("filePath")
    return {
        "collection": item.get("collection"),
        "score": item.get("score"),
        "filePath": file_path,
        "absolutePath": resolve_path(file_path, workspace_root),
        "startLine": payload.get("startLine"),
        "endLine": payload.get("endLine"),
        "codeChunk": payload.get("codeChunk", ""),
    }


def command_collections(args):
    collections = detect_collections(args.qdrant_url, explicit_collection=args.collection, prefix=args.prefix)
    rows = []
    for name in collections:
        info = collection_info(args.qdrant_url, name)
        params = info.get("config", {}).get("params", {}).get("vectors", {})
        rows.append(
            {
                "name": name,
                "status": info.get("status"),
                "points": info.get("points_count"),
                "vector_size": params.get("size"),
                "distance": params.get("distance"),
            }
        )
    if args.json:
        print(json.dumps(rows, indent=2))
        return
    for row in rows:
        print(
            f"{row['name']}: status={row['status']} points={row['points']} "
            f"vector_size={row['vector_size']} distance={row['distance']}"
        )


def command_peek(args):
    collections = detect_collections(args.qdrant_url, explicit_collection=args.collection, prefix=args.prefix)
    output = []
    for name in collections:
        points = scroll_points(args.qdrant_url, name, args.limit)
        for point in points:
            output.append(
                {
                    "collection": name,
                    "id": point.get("id"),
                    "filePath": point.get("payload", {}).get("filePath"),
                    "absolutePath": resolve_path(point.get("payload", {}).get("filePath"), args.workspace_root),
                    "startLine": point.get("payload", {}).get("startLine"),
                    "endLine": point.get("payload", {}).get("endLine"),
                    "codeChunk": point.get("payload", {}).get("codeChunk", ""),
                }
            )
    if args.json:
        print(json.dumps(output, indent=2))
        return
    for item in output:
        print(f"[{item['collection']}] {item['filePath']}:{item['startLine']}-{item['endLine']}")
        print(trim_chunk(item["codeChunk"], max_chars=args.max_chars))
        print()


def command_search(args):
    collections = detect_collections(args.qdrant_url, explicit_collection=args.collection, prefix=args.prefix)
    vector = get_embedding(args.query, args.embed_base_url, args.embed_model, args.api_key)
    combined = []
    for name in collections:
        results = qdrant_search(
            args.qdrant_url,
            name,
            vector,
            limit=args.limit,
            score_threshold=args.score_threshold,
        )
        for item in results:
            item["collection"] = name
            combined.append(item)
    combined.sort(key=lambda item: item.get("score", 0.0), reverse=True)
    formatted = [format_result(item, args.workspace_root) for item in combined[: args.limit]]
    if args.json:
        print(json.dumps(formatted, indent=2))
        return
    for index, item in enumerate(formatted, start=1):
        location = f"{item['filePath']}:{item['startLine']}-{item['endLine']}"
        print(f"{index}. score={item['score']:.4f} collection={item['collection']} {location}")
        print(f"   abs={item['absolutePath']}")
        chunk = trim_chunk(item["codeChunk"], max_chars=args.max_chars)
        if chunk:
            indented = textwrap.indent(chunk, "   ")
            print(indented)
        print()


def build_parser():
    parser = argparse.ArgumentParser(
        description="Search Roo Code Qdrant indexes with an OpenAI-compatible embeddings API.",
    )
    parser.add_argument("--qdrant-url", default=DEFAULT_QDRANT_URL, help="Qdrant base URL.")
    parser.add_argument("--collection", default=DEFAULT_COLLECTION, help="Search only one collection.")
    parser.add_argument("--prefix", default=DEFAULT_COLLECTION_PREFIX, help="Collection prefix for auto-detect.")
    parser.add_argument(
        "--workspace-root",
        default=DEFAULT_WORKSPACE_ROOT,
        help="Root used to resolve relative filePath values into absolute paths.",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of plain text.")
    parser.add_argument("--max-chars", type=int, default=900, help="Max chunk chars in plain-text output.")

    subparsers = parser.add_subparsers(dest="command", required=True)

    collections_parser = subparsers.add_parser("collections", help="List Roo-indexed collections.")
    collections_parser.set_defaults(func=command_collections)

    peek_parser = subparsers.add_parser("peek", help="Show sample indexed chunks.")
    peek_parser.add_argument("--limit", type=int, default=3, help="Number of sample points per collection.")
    peek_parser.set_defaults(func=command_peek)

    search_parser = subparsers.add_parser("search", help="Semantic search over Roo-indexed chunks.")
    search_parser.add_argument("query", help="Natural-language search query.")
    search_parser.add_argument("--limit", type=int, default=6, help="Total results to return.")
    search_parser.add_argument(
        "--score-threshold",
        type=float,
        default=None,
        help="Optional minimum cosine score threshold.",
    )
    search_parser.add_argument(
        "--embed-base-url",
        default=DEFAULT_EMBED_BASE_URL,
        help="Embeddings API base URL.",
    )
    search_parser.add_argument(
        "--embed-model",
        default=DEFAULT_EMBED_MODEL,
        help="Embedding model ID. Must match Roo's indexing model for reliable retrieval.",
    )
    search_parser.add_argument(
        "--api-key",
        default=DEFAULT_API_KEY,
        help="Embeddings API key. Defaults to ROO_INDEX_EMBED_API_KEY or OPENROUTER_API_KEY.",
    )
    search_parser.set_defaults(func=command_search)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    try:
        args.func(args)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
