#!/usr/bin/env python3
from __future__ import annotations

import argparse
import difflib
import getpass
import json
import os
import re
import shlex
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


DEFAULT_PAPERS_DIR = Path(os.environ.get("PAPERS_DIR", str(Path.home() / "Papers"))).expanduser()
DEFAULT_OUTPUT_DIR = Path(os.environ.get("DESKTOP_DIR", str(Path.home() / "Desktop"))).expanduser()
DEFAULT_CONFIG_PATH = Path(
    os.environ.get(
        "PDF2ZH_TRANSLATOR_ENV",
        str(Path.home() / ".config" / "pdf2zh-paper-translator" / "env"),
    )
).expanduser()
DEFAULT_MODEL = "gemini-3.5-flash"
DEFAULT_PDF2ZH_BIN = Path.home() / ".local" / "bin" / "pdf2zh"
DEFAULT_ZOTERO_DB = Path.home() / "Zotero" / "zotero.sqlite"
DEFAULT_DOWNLOAD_SUBDIR = "Downloaded"
DEFAULT_LOCAL_MIN_SCORE = 0.35
KEYCHAIN_SERVICE = "pdf2zh-paper-translator-gemini-api-key"
SEMANTIC_FIELDS = ",".join(
    [
        "title",
        "authors",
        "year",
        "externalIds",
        "openAccessPdf",
        "url",
        "citationCount",
        "isOpenAccess",
    ]
)


@dataclass(frozen=True)
class Candidate:
    path: Path
    score: float
    source: str = "local"
    title: str = ""


@dataclass(frozen=True)
class OnlinePaper:
    title: str
    source: str
    paper_id: str = ""
    doi: str = ""
    arxiv_id: str = ""
    pdf_url: str = ""
    landing_url: str = ""
    year: str = ""
    authors: str = ""
    score: float = 0.0


def normalize(value: str) -> str:
    value = value.casefold()
    value = re.sub(r"[^\w]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def acronym(tokens: list[str]) -> str:
    letters = []
    for token in tokens:
        if token and token[0].isascii() and token[0].isalnum():
            letters.append(token[0])
    return "".join(letters)


def query_tokens(query: str) -> list[str]:
    return normalize(query).split()


def effective_local_min_score(query: str, requested_min_score: float, loose: bool) -> float:
    if loose:
        return requested_min_score
    token_count = len(query_tokens(query))
    if token_count >= 6:
        return max(requested_min_score, 0.74)
    if token_count >= 4:
        return max(requested_min_score, 0.62)
    if token_count == 3:
        return max(requested_min_score, 0.50)
    return requested_min_score


def sanitize_filename(value: str, fallback: str = "paper") -> str:
    value = re.sub(r"[/:\\\0]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip(" .")
    value = value[:180].strip(" .")
    return value or fallback


def extract_doi(value: str) -> str | None:
    value = value.strip()
    doi_url_match = re.search(r"https?://(?:dx\.)?doi\.org/(10\.\d{4,9}/\S+)", value, re.I)
    raw = doi_url_match.group(1) if doi_url_match else value
    doi_match = re.search(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+", raw, re.I)
    if not doi_match:
        return None
    return doi_match.group(0).rstrip(").,;")


def extract_arxiv_id(value: str) -> str | None:
    value = value.strip()
    arxiv_url_match = re.search(r"arxiv\.org/(?:abs|pdf)/([^?#\s]+)", value, re.I)
    if arxiv_url_match:
        return arxiv_url_match.group(1).removesuffix(".pdf")
    arxiv_doi_match = re.search(r"10\.48550/arxiv\.(\d{4}\.\d{4,5}(?:v\d+)?)", value, re.I)
    if arxiv_doi_match:
        return arxiv_doi_match.group(1)
    arxiv_match = re.search(r"(?:arxiv\s*:?\s*)?(\d{4}\.\d{4,5}(?:v\d+)?)\b", value, re.I)
    if arxiv_match and ("arxiv" in value.casefold() or value == arxiv_match.group(1)):
        return arxiv_match.group(1)
    return None


def arxiv_pdf_url(arxiv_id: str) -> str:
    return f"https://arxiv.org/pdf/{arxiv_id.removesuffix('.pdf')}.pdf"


def normalize_pdf_url(url: str) -> str:
    if "arxiv.org/abs/" in url:
        arxiv_id = extract_arxiv_id(url)
        if arxiv_id:
            return arxiv_pdf_url(arxiv_id)
    if "arxiv.org/pdf/" in url and not url.lower().endswith(".pdf"):
        return f"{url}.pdf"
    return url


def http_headers(env: dict[str, str]) -> dict[str, str]:
    email = env.get("UNPAYWALL_EMAIL") or env.get("OPENALEX_MAILTO") or ""
    suffix = f" (mailto:{email})" if email else ""
    return {"User-Agent": f"pdf2zh-paper-translator/1.0{suffix}"}


def http_json(url: str, params: dict[str, str], env: dict[str, str], timeout: int = 25) -> dict:
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers=http_headers(env))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError:
        curl = shutil.which("curl")
        if not curl:
            raise
        result = subprocess.run(
            [
                curl,
                "-L",
                "--http1.1",
                "--fail",
                "--silent",
                "--show-error",
                "--max-time",
                str(timeout),
                "-A",
                http_headers(env)["User-Agent"],
                url,
            ],
            text=True,
            capture_output=True,
            check=True,
        )
        return json.loads(result.stdout)


def http_text(url: str, params: dict[str, str], env: dict[str, str], timeout: int = 25) -> str:
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers=http_headers(env))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            return response.read().decode("utf-8")
    except urllib.error.URLError:
        curl = shutil.which("curl")
        if not curl:
            raise
        result = subprocess.run(
            [
                curl,
                "-L",
                "--http1.1",
                "--fail",
                "--silent",
                "--show-error",
                "--max-time",
                str(timeout),
                "-A",
                http_headers(env)["User-Agent"],
                url,
            ],
            text=True,
            capture_output=True,
            check=True,
        )
        return result.stdout


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        if key:
            values[key] = value
    return values


def merged_environment(config_path: Path) -> dict[str, str]:
    env = parse_env_file(config_path)
    env.update(os.environ)
    return env


def init_config(path: Path, force: bool) -> int:
    if path.exists() and not force:
        print(f"Config already exists: {path}")
        print("Use --force to overwrite it.")
        return 0

    path.parent.mkdir(parents=True, exist_ok=True)
    pdf2zh_bin = shutil.which("pdf2zh") or str(DEFAULT_PDF2ZH_BIN)
    content = "\n".join(
        [
            "# Local settings for pdf2zh-paper-translator.",
            "# Keep this file private because it may contain API credentials.",
            "GEMINI_API_KEY=",
            f"GEMINI_MODEL={DEFAULT_MODEL}",
            "UNPAYWALL_EMAIL=",
            f"PAPERS_DIR={DEFAULT_PAPERS_DIR}",
            f"DESKTOP_DIR={DEFAULT_OUTPUT_DIR}",
            f"PDF2ZH_BIN={pdf2zh_bin}",
            f"DOWNLOAD_SUBDIR={DEFAULT_DOWNLOAD_SUBDIR}",
            "",
        ]
    )
    path.write_text(content, encoding="utf-8")
    path.chmod(0o600)
    print(f"Wrote config template: {path}")
    print("Fill GEMINI_API_KEY once, or use --store-api-key to save it in Keychain.")
    return 0


def store_api_key() -> int:
    security = shutil.which("security")
    if not security:
        print("macOS security command was not found; use --init-config instead.", file=sys.stderr)
        return 1
    key = getpass.getpass("Gemini API key: ").strip()
    if not key:
        print("No key entered.", file=sys.stderr)
        return 1
    cmd = [
        security,
        "add-generic-password",
        "-U",
        "-a",
        getpass.getuser(),
        "-s",
        KEYCHAIN_SERVICE,
        "-w",
        key,
    ]
    subprocess.run(cmd, check=True)
    print(f"Stored Gemini API key in macOS Keychain service: {KEYCHAIN_SERVICE}")
    return 0


def read_keychain_api_key() -> str | None:
    security = shutil.which("security")
    if not security:
        return None
    cmd = [
        security,
        "find-generic-password",
        "-a",
        getpass.getuser(),
        "-s",
        KEYCHAIN_SERVICE,
        "-w",
    ]
    result = subprocess.run(cmd, text=True, capture_output=True)
    if result.returncode != 0:
        return None
    key = result.stdout.strip()
    return key or None


def discover_pdf2zh(env: dict[str, str], explicit: str | None) -> str:
    choices = [
        explicit,
        env.get("PDF2ZH_BIN"),
        shutil.which("pdf2zh"),
        str(DEFAULT_PDF2ZH_BIN),
    ]
    for choice in choices:
        if not choice:
            continue
        candidate = Path(os.path.expanduser(choice))
        if candidate.exists() and os.access(candidate, os.X_OK):
            return str(candidate)
        resolved = shutil.which(choice)
        if resolved:
            return resolved
    raise SystemExit("Could not find an executable pdf2zh. Pass --pdf2zh-bin PATH.")


def list_pdfs(root: Path) -> list[Path]:
    if not root.exists():
        raise SystemExit(f"Papers directory does not exist: {root}")
    return sorted(
        p
        for p in root.rglob("*.pdf")
        if p.is_file() and not p.name.endswith(("-mono.pdf", "-dual.pdf"))
    )


def score_path(query: str, path: Path, root: Path) -> float:
    normalized_query = normalize(query)
    normalized_name = normalize(path.stem)
    try:
        normalized_rel = normalize(str(path.relative_to(root).with_suffix("")))
    except ValueError:
        normalized_rel = normalize(str(path.with_suffix("")))

    if not normalized_query:
        return 0.0
    if normalized_query == normalized_name:
        return 1.0
    if normalized_query in normalized_name:
        return 0.96
    if normalized_query in normalized_rel:
        return 0.92

    query_tokens = normalized_query.split()
    name_tokens = normalized_name.split()
    rel_tokens = normalized_rel.split()

    name_acronym = acronym(name_tokens)
    compact_query = normalized_query.replace(" ", "")
    if len(compact_query) >= 2 and compact_query in name_acronym:
        return 0.91

    query_set = set(query_tokens)
    name_set = set(name_tokens)
    rel_set = set(rel_tokens)
    overlap = len(query_set & rel_set) / max(len(query_set), 1)
    name_ratio = difflib.SequenceMatcher(None, normalized_query, normalized_name).ratio()
    rel_ratio = difflib.SequenceMatcher(None, normalized_query, normalized_rel).ratio()
    token_ratio = len(query_set & name_set) / max(len(query_set), 1)
    return max(name_ratio, rel_ratio * 0.92, overlap * 0.88, token_ratio * 0.9)


def find_candidates(query: str, root: Path) -> list[Candidate]:
    direct = Path(os.path.expanduser(query))
    if direct.exists() and direct.is_file() and direct.suffix.lower() == ".pdf":
        return [Candidate(direct.resolve(), 1.0)]

    candidates = [Candidate(path, score_path(query, path, root)) for path in list_pdfs(root)]
    candidates.sort(key=lambda item: (-item.score, len(str(item.path)), str(item.path)))
    return candidates


def print_candidates(candidates: list[Candidate], limit: int) -> None:
    for index, candidate in enumerate(candidates[:limit], start=1):
        title = f" title={candidate.title}" if candidate.title else ""
        print(f"[{index}] score={candidate.score:.3f} source={candidate.source}{title} {candidate.path}")


def choose_candidate(args: argparse.Namespace, root: Path, allow_miss: bool = False) -> Path | None:
    candidates = find_candidates(args.query, root)
    if not candidates:
        if allow_miss:
            return None
        raise SystemExit("No PDF files found.")

    if args.list:
        print_candidates(candidates, args.top)
        raise SystemExit(0)

    if args.select is not None:
        index = args.select - 1
        if index < 0 or index >= min(args.top, len(candidates)):
            print_candidates(candidates, args.top)
            raise SystemExit(f"--select must be between 1 and {min(args.top, len(candidates))}.")
        return candidates[index].path

    best = candidates[0]
    second = candidates[1] if len(candidates) > 1 else None
    ambiguous = second is not None and second.score >= max(0.6, best.score - 0.08)
    min_score = effective_local_min_score(args.query, args.min_score, args.loose_local_match)
    if best.score < min_score:
        if allow_miss:
            return None
        print("No reliable local paper match. Top candidates:")
        print_candidates(candidates, args.top)
        raise SystemExit(f"Best local score {best.score:.3f} is below required {min_score:.3f}. Use --loose-local-match to force low-confidence local matching.")
    if ambiguous:
        print("The paper query is ambiguous. Top candidates:")
        print_candidates(candidates, args.top)
        raise SystemExit("Re-run with --select N or use a more specific title fragment.")
    return best.path


def zotero_attachment_path(raw_path: str, attachment_key: str, zotero_db: Path, papers_dir: Path) -> Path | None:
    if not raw_path:
        return None
    if raw_path.startswith("attachments:"):
        return papers_dir / raw_path.removeprefix("attachments:")
    if raw_path.startswith("storage:"):
        return zotero_db.parent / "storage" / attachment_key / raw_path.removeprefix("storage:")
    if raw_path.startswith("file://"):
        return Path(urllib.parse.unquote(urllib.parse.urlparse(raw_path).path))
    path = Path(os.path.expanduser(raw_path))
    return path if path.is_absolute() else None


def find_zotero_candidates(query: str, papers_dir: Path, zotero_db: Path) -> list[Candidate]:
    if not zotero_db.exists():
        return []
    sql = """
        SELECT
            COALESCE(title.value, attachment_title.value, '') AS item_title,
            attach.key AS attachment_key,
            ia.path
        FROM itemAttachments ia
        JOIN items attach ON attach.itemID = ia.itemID
        LEFT JOIN itemData title_data
            ON title_data.itemID = COALESCE(ia.parentItemID, ia.itemID)
            AND title_data.fieldID = 1
        LEFT JOIN itemDataValues title ON title.valueID = title_data.valueID
        LEFT JOIN itemData attachment_title_data
            ON attachment_title_data.itemID = ia.itemID
            AND attachment_title_data.fieldID = 1
        LEFT JOIN itemDataValues attachment_title ON attachment_title.valueID = attachment_title_data.valueID
        WHERE (ia.contentType = 'application/pdf' OR ia.path LIKE '%.pdf%' OR ia.path LIKE 'attachments:%')
          AND ia.path IS NOT NULL
    """
    uri = f"file:{zotero_db}?mode=ro&immutable=1"
    candidates: list[Candidate] = []
    try:
        with sqlite3.connect(uri, uri=True) as conn:
            for title, attachment_key, raw_path in conn.execute(sql):
                path = zotero_attachment_path(raw_path, attachment_key, zotero_db, papers_dir)
                if not path or not path.exists() or path.suffix.lower() != ".pdf":
                    continue
                score = max(
                    score_path(query, path, papers_dir),
                    difflib.SequenceMatcher(None, normalize(query), normalize(title or "")).ratio(),
                )
                candidates.append(Candidate(path=path, score=score, source="zotero", title=title or ""))
    except sqlite3.Error as exc:
        print(f"Warning: failed to search Zotero SQLite: {exc}", file=sys.stderr)
        return []
    candidates.sort(key=lambda item: (-item.score, len(str(item.path)), str(item.path)))
    return candidates


def choose_zotero_candidate(args: argparse.Namespace, papers_dir: Path, zotero_db: Path, allow_miss: bool) -> Path | None:
    candidates = find_zotero_candidates(args.query, papers_dir, zotero_db)
    if args.zotero_list:
        if candidates:
            print_candidates(candidates, args.top)
        else:
            print("No Zotero PDF attachment candidates found.")
        raise SystemExit(0)
    if not candidates:
        if allow_miss:
            return None
        raise SystemExit("No Zotero PDF attachment candidates found.")
    best = candidates[0]
    second = candidates[1] if len(candidates) > 1 else None
    ambiguous = second is not None and second.score >= max(0.6, best.score - 0.08)
    min_score = effective_local_min_score(args.query, args.min_score, args.loose_local_match)
    if best.score < min_score:
        if allow_miss:
            return None
        print("No reliable Zotero attachment match. Top candidates:")
        print_candidates(candidates, args.top)
        raise SystemExit(f"Best Zotero score {best.score:.3f} is below required {min_score:.3f}. Use --loose-local-match to force low-confidence Zotero matching.")
    if ambiguous:
        print("The Zotero query is ambiguous. Top candidates:")
        print_candidates(candidates, args.top)
        raise SystemExit("Use a more specific title fragment.")
    return best.path


def semantic_paper_from_payload(payload: dict, score: float = 0.0) -> OnlinePaper:
    external = payload.get("externalIds") or {}
    oa_pdf = payload.get("openAccessPdf") or {}
    authors = "; ".join(a.get("name", "") for a in (payload.get("authors") or []) if a.get("name"))
    return OnlinePaper(
        title=payload.get("title") or "",
        source="semantic",
        paper_id=payload.get("paperId") or "",
        doi=external.get("DOI") or "",
        arxiv_id=external.get("ArXiv") or "",
        pdf_url=normalize_pdf_url(oa_pdf.get("url") or ""),
        landing_url=payload.get("url") or "",
        year=str(payload.get("year") or ""),
        authors=authors,
        score=score,
    )


def search_semantic(query: str, max_results: int, env: dict[str, str]) -> list[OnlinePaper]:
    params = {
        "query": query,
        "limit": str(max_results),
        "fields": SEMANTIC_FIELDS,
        "openAccessPdf": "",
    }
    try:
        payload = http_json("https://api.semanticscholar.org/graph/v1/paper/search", params, env)
    except (urllib.error.URLError, subprocess.CalledProcessError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"Warning: Semantic Scholar search failed: {exc}", file=sys.stderr)
        return []
    papers: list[OnlinePaper] = []
    for item in payload.get("data") or []:
        score = difflib.SequenceMatcher(None, normalize(query), normalize(item.get("title") or "")).ratio()
        paper = semantic_paper_from_payload(item, score=score)
        if paper.pdf_url or paper.arxiv_id or paper.doi:
            papers.append(paper)
    return papers


def search_arxiv(query: str, max_results: int, env: dict[str, str]) -> list[OnlinePaper]:
    quoted_query = query.replace('"', " ").strip()
    params = {
        "search_query": f'ti:"{quoted_query}"' if quoted_query else f"all:{query}",
        "start": "0",
        "max_results": str(max_results),
    }
    try:
        xml_text = http_text("https://export.arxiv.org/api/query", params, env)
    except (urllib.error.URLError, subprocess.CalledProcessError, TimeoutError) as exc:
        print(f"Warning: arXiv search failed: {exc}", file=sys.stderr)
        return []

    namespace = {"atom": "http://www.w3.org/2005/Atom"}
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        print(f"Warning: arXiv search returned invalid XML: {exc}", file=sys.stderr)
        return []

    papers: list[OnlinePaper] = []
    for entry in root.findall("atom:entry", namespace):
        title = re.sub(r"\s+", " ", (entry.findtext("atom:title", default="", namespaces=namespace) or "")).strip()
        entry_id = entry.findtext("atom:id", default="", namespaces=namespace) or ""
        arxiv_id = extract_arxiv_id(entry_id) or entry_id.rsplit("/", 1)[-1]
        pdf_url = arxiv_pdf_url(arxiv_id) if arxiv_id else ""
        year = (entry.findtext("atom:published", default="", namespaces=namespace) or "")[:4]
        authors = "; ".join(
            author.findtext("atom:name", default="", namespaces=namespace) or ""
            for author in entry.findall("atom:author", namespace)
        )
        score = difflib.SequenceMatcher(None, normalize(query), normalize(title)).ratio()
        papers.append(
            OnlinePaper(
                title=title,
                source="arxiv",
                paper_id=entry_id,
                arxiv_id=arxiv_id,
                pdf_url=pdf_url,
                landing_url=entry_id,
                year=year,
                authors=authors,
                score=score,
            )
        )
    return papers


def semantic_lookup_by_id(paper_id: str, env: dict[str, str]) -> OnlinePaper | None:
    encoded = urllib.parse.quote(paper_id, safe=":")
    try:
        payload = http_json(
            f"https://api.semanticscholar.org/graph/v1/paper/{encoded}",
            {"fields": SEMANTIC_FIELDS},
            env,
        )
    except (urllib.error.URLError, subprocess.CalledProcessError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"Warning: Semantic Scholar lookup failed for {paper_id}: {exc}", file=sys.stderr)
        return None
    return semantic_paper_from_payload(payload, score=1.0)


def openalex_paper_from_work(work: dict, query: str) -> OnlinePaper:
    urls: list[str] = []
    for location_key in ("best_oa_location", "primary_location"):
        location = work.get(location_key) or {}
        if location.get("pdf_url"):
            urls.append(location["pdf_url"])
    for location in work.get("locations") or []:
        if location.get("pdf_url"):
            urls.append(location["pdf_url"])
    open_access = work.get("open_access") or {}
    oa_url = open_access.get("oa_url") or ""
    if oa_url and (".pdf" in oa_url.casefold() or "/pdf" in oa_url.casefold() or "arxiv.org/" in oa_url.casefold()):
        urls.append(open_access["oa_url"])

    doi = (work.get("doi") or "").removeprefix("https://doi.org/")
    title = work.get("title") or ""
    pdf_url = next((normalize_pdf_url(url) for url in urls if url), "")
    arxiv_id = extract_arxiv_id(doi) or extract_arxiv_id(pdf_url) or ""
    authorships = work.get("authorships") or []
    authors = "; ".join(
        author.get("author", {}).get("display_name", "")
        for author in authorships
        if author.get("author", {}).get("display_name")
    )
    return OnlinePaper(
        title=title,
        source="openalex",
        paper_id=work.get("id") or "",
        doi=doi,
        arxiv_id=arxiv_id,
        pdf_url=pdf_url,
        landing_url=work.get("id") or "",
        year=str(work.get("publication_year") or ""),
        authors=authors,
        score=difflib.SequenceMatcher(None, normalize(query), normalize(title)).ratio(),
    )


def search_openalex(query: str, max_results: int, env: dict[str, str]) -> list[OnlinePaper]:
    params = {"search": query, "per-page": str(max_results)}
    mailto = env.get("OPENALEX_MAILTO") or env.get("UNPAYWALL_EMAIL")
    if mailto:
        params["mailto"] = mailto
    try:
        payload = http_json("https://api.openalex.org/works", params, env)
    except (urllib.error.URLError, subprocess.CalledProcessError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"Warning: OpenAlex search failed: {exc}", file=sys.stderr)
        return []
    return [
        paper
        for paper in (openalex_paper_from_work(work, query) for work in payload.get("results") or [])
        if paper.pdf_url or paper.doi
    ]


def unpaywall_pdf_url(doi: str, env: dict[str, str]) -> str | None:
    email = env.get("UNPAYWALL_EMAIL") or env.get("OPENALEX_MAILTO")
    if not email:
        return None
    encoded = urllib.parse.quote(doi, safe="")
    try:
        payload = http_json(f"https://api.unpaywall.org/v2/{encoded}", {"email": email}, env)
    except (urllib.error.URLError, subprocess.CalledProcessError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"Warning: Unpaywall lookup failed for DOI {doi}: {exc}", file=sys.stderr)
        return None
    locations = [payload.get("best_oa_location") or {}, *(payload.get("oa_locations") or [])]
    for location in locations:
        url = location.get("url_for_pdf") or location.get("url")
        if url:
            return normalize_pdf_url(url)
    return None


def direct_online_papers(query: str, env: dict[str, str]) -> list[OnlinePaper]:
    if query.startswith(("http://", "https://")):
        arxiv_id = extract_arxiv_id(query)
        doi = extract_doi(query) or ""
        pdf_url = arxiv_pdf_url(arxiv_id) if arxiv_id else normalize_pdf_url(query)
        return [OnlinePaper(title=Path(urllib.parse.urlparse(query).path).stem or query, source="url", doi=doi, arxiv_id=arxiv_id or "", pdf_url=pdf_url, landing_url=query, score=1.0)]

    arxiv_id = extract_arxiv_id(query)
    if arxiv_id:
        return [OnlinePaper(title=f"arXiv {arxiv_id}", source="arxiv", arxiv_id=arxiv_id, pdf_url=arxiv_pdf_url(arxiv_id), score=1.0)]

    doi = extract_doi(query)
    if doi:
        paper = semantic_lookup_by_id(f"DOI:{doi}", env)
        if paper:
            return [paper]
        return [OnlinePaper(title=doi, source="doi", doi=doi, score=1.0)]
    return []


def search_online_papers(query: str, max_results: int, env: dict[str, str]) -> list[OnlinePaper]:
    papers = direct_online_papers(query, env)
    if not papers:
        papers.extend(search_semantic(query, max_results, env))
        time.sleep(1.05)
        papers.extend(search_arxiv(query, max_results, env))
        time.sleep(1.05)
        papers.extend(search_openalex(query, max_results, env))

    seen: set[tuple[str, str, str]] = set()
    unique: list[OnlinePaper] = []
    for paper in sorted(papers, key=lambda item: (-item.score, -bool(item.pdf_url), item.source, item.title)):
        key = (normalize(paper.title), paper.doi.casefold(), paper.arxiv_id.casefold())
        if key in seen:
            continue
        seen.add(key)
        unique.append(paper)
    return unique


def print_online_candidates(papers: list[OnlinePaper], limit: int) -> None:
    for index, paper in enumerate(papers[:limit], start=1):
        identifier = paper.doi or (f"arXiv:{paper.arxiv_id}" if paper.arxiv_id else paper.paper_id)
        pdf = f" pdf={paper.pdf_url}" if paper.pdf_url else ""
        year = f" year={paper.year}" if paper.year else ""
        print(f"[{index}] score={paper.score:.3f} source={paper.source}{year} id={identifier} title={paper.title}{pdf}")


def download_url_to_pdf(url: str, destination: Path, env: dict[str, str]) -> Path:
    url = normalize_pdf_url(url)
    destination.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers=http_headers(env))
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            data = response.read()
    except urllib.error.URLError:
        curl = shutil.which("curl")
        if not curl:
            raise
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            temp_path = Path(temp.name)
        try:
            subprocess.run(
                [
                    curl,
                    "-L",
                    "--http1.1",
                    "--fail",
                    "--silent",
                    "--show-error",
                    "--max-time",
                    "120",
                    "-A",
                    http_headers(env)["User-Agent"],
                    "-o",
                    str(temp_path),
                    url,
                ],
                check=True,
            )
            data = temp_path.read_bytes()
        finally:
            temp_path.unlink(missing_ok=True)
    if not data.startswith(b"%PDF"):
        raise RuntimeError(f"Downloaded content from {url} is not a PDF")
    destination.write_bytes(data)
    return destination


def online_pdf_urls(paper: OnlinePaper, env: dict[str, str]) -> list[str]:
    urls: list[str] = []
    if paper.pdf_url:
        urls.append(paper.pdf_url)
    if paper.arxiv_id:
        urls.append(arxiv_pdf_url(paper.arxiv_id))
    if paper.doi:
        unpaywall_url = unpaywall_pdf_url(paper.doi, env)
        if unpaywall_url:
            urls.append(unpaywall_url)
    unique: list[str] = []
    for url in urls:
        if url and url not in unique:
            unique.append(url)
    return unique


def online_download_dir(args: argparse.Namespace, env: dict[str, str], papers_dir: Path) -> Path:
    raw = args.download_dir or env.get("DOWNLOAD_DIR")
    if raw:
        return Path(os.path.expanduser(raw))
    subdir = env.get("DOWNLOAD_SUBDIR") or DEFAULT_DOWNLOAD_SUBDIR
    path = Path(os.path.expanduser(subdir))
    return path if path.is_absolute() else papers_dir / path


def download_online_pdf(args: argparse.Namespace, env: dict[str, str], papers_dir: Path) -> Path | None:
    papers = search_online_papers(args.query, args.online_top, env)
    if args.online_list:
        if papers:
            print_online_candidates(papers, args.online_top)
        else:
            print("No online paper candidates found.")
        raise SystemExit(0)
    if not papers:
        return None

    direct_query = bool(args.query.startswith(("http://", "https://")) or extract_arxiv_id(args.query) or extract_doi(args.query))
    usable = [paper for paper in papers if paper.score >= args.online_min_score or direct_query]
    if not usable:
        print("No reliable online paper match. Top candidates:")
        print_online_candidates(papers, args.online_top)
        return None

    if args.dry_run:
        print("Online dry run candidates:")
        print_online_candidates(usable, min(args.online_top, len(usable)))
        best = usable[0]
        urls = online_pdf_urls(best, env)
        if urls:
            print(f"Would download: {urls[0]}")
        else:
            print("Best online candidate has no direct OA PDF URL.")
        return None

    download_dir = online_download_dir(args, env, papers_dir)
    errors: list[str] = []
    for paper in usable[: args.online_top]:
        filename = sanitize_filename(
            " - ".join(part for part in [paper.year, paper.title] if part),
            fallback=paper.paper_id or paper.doi or "paper",
        )
        destination = unique_destination(download_dir / f"{filename}.pdf", args.overwrite)
        urls = online_pdf_urls(paper, env)
        for url in urls:
            try:
                print(f"Downloading OA PDF from {paper.source}: {paper.title}")
                print(f"URL: {url}")
                return download_url_to_pdf(url, destination, env)
            except Exception as exc:
                errors.append(f"{paper.title} via {url}: {exc}")
                continue
    if errors:
        print("Online download attempts failed:", file=sys.stderr)
        for error in errors[:5]:
            print(f"- {error}", file=sys.stderr)
    return None


def resolve_input_pdf(args: argparse.Namespace, env: dict[str, str], papers_dir: Path) -> Path | None:
    if args.no_online and args.force_online:
        raise SystemExit("--no-online and --force-online cannot be used together.")

    allow_online = not args.no_online
    if not args.force_online and not args.online_list:
        if not args.zotero_list:
            local = choose_candidate(args, papers_dir, allow_miss=allow_online)
            if local:
                return local
        if not args.no_zotero:
            zotero_db = Path(os.path.expanduser(args.zotero_db or env.get("ZOTERO_DB") or str(DEFAULT_ZOTERO_DB)))
            zotero = choose_zotero_candidate(args, papers_dir, zotero_db, allow_miss=allow_online)
            if zotero:
                return zotero
        if args.zotero_list:
            return None

    if allow_online:
        return download_online_pdf(args, env, papers_dir)
    return None


def unique_destination(path: Path, overwrite: bool) -> Path:
    if overwrite or not path.exists():
        return path
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    return path.with_name(f"{path.stem}-{stamp}{path.suffix}")


def copy_results(temp_dir: Path, original_pdf: Path, output_dir: Path, overwrite: bool) -> list[Path]:
    expected = [
        temp_dir / f"{original_pdf.stem}-mono.pdf",
        temp_dir / f"{original_pdf.stem}-dual.pdf",
    ]
    result_files = [p for p in expected if p.exists()]
    if len(result_files) < 2:
        result_files = sorted(temp_dir.glob("*.pdf"))
    if not result_files:
        raise SystemExit(f"pdf2zh finished but no PDF outputs were found in {temp_dir}")

    output_dir.mkdir(parents=True, exist_ok=True)
    copied: list[Path] = []
    for source in result_files:
        destination = unique_destination(output_dir / source.name, overwrite)
        shutil.copy2(source, destination)
        copied.append(destination)
    return copied


def run_translation(args: argparse.Namespace, env: dict[str, str], pdf_path: Path) -> list[Path]:
    api_key = env.get("GEMINI_API_KEY") or read_keychain_api_key()
    if not api_key and not args.dry_run:
        raise SystemExit(
            "GEMINI_API_KEY is not configured. Run this script with --store-api-key or --init-config."
        )

    model = args.model or env.get("GEMINI_MODEL") or DEFAULT_MODEL
    output_dir = Path(
        os.path.expanduser(args.output_dir or env.get("DESKTOP_DIR") or str(DEFAULT_OUTPUT_DIR))
    )
    pdf2zh_bin = discover_pdf2zh(env, args.pdf2zh_bin)

    cmd = [
        pdf2zh_bin,
        str(pdf_path),
        "-s",
        f"gemini:{model}",
        "-li",
        args.lang_in,
        "-lo",
        args.lang_out,
        "-t",
        str(args.thread),
    ]
    if args.pages:
        cmd.extend(["-p", args.pages])

    print(f"Matched paper: {pdf_path}")
    print(f"Gemini model: {model}")
    print(f"Output dir: {output_dir}")

    if args.dry_run:
        print("Dry run command:")
        print(shlex.join([*cmd, "-o", "<temporary-output-dir>"]))
        print(f"API key configured: {'yes' if api_key else 'no'}")
        return []

    command_env = os.environ.copy()
    command_env.update(env)
    command_env["GEMINI_API_KEY"] = api_key
    command_env["GEMINI_MODEL"] = model

    with tempfile.TemporaryDirectory(prefix="pdf2zh-paper-") as temp:
        temp_dir = Path(temp)
        final_cmd = [*cmd, "-o", str(temp_dir)]
        subprocess.run(final_cmd, check=True, env=command_env)
        return copy_results(temp_dir, pdf_path, output_dir, args.overwrite)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Find a local paper PDF and translate it with pdf2zh + Gemini."
    )
    parser.add_argument("query", nargs="?", help="Paper title, filename fragment, acronym, or PDF path.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH), help="Local env config file.")
    parser.add_argument("--init-config", action="store_true", help="Create a local config template.")
    parser.add_argument("--force", action="store_true", help="Overwrite config template with --init-config.")
    parser.add_argument("--store-api-key", action="store_true", help="Store Gemini API key in macOS Keychain.")
    parser.add_argument("--papers-dir", help="Directory to search for PDF papers.")
    parser.add_argument("--output-dir", "--desktop-dir", dest="output_dir", help="Directory for final PDFs.")
    parser.add_argument("--pdf2zh-bin", help="Path to the pdf2zh executable.")
    parser.add_argument("--zotero-db", help="Path to local Zotero zotero.sqlite.")
    parser.add_argument("--model", help=f"Gemini model. Default: {DEFAULT_MODEL}.")
    parser.add_argument("--lang-in", default="en", help="Source language code.")
    parser.add_argument("--lang-out", default="zh", help="Target language code.")
    parser.add_argument("--thread", type=int, default=4, help="pdf2zh translation threads.")
    parser.add_argument("--pages", help="Page selection such as 1-3,7.")
    parser.add_argument("--list", action="store_true", help="List top matching PDFs and exit.")
    parser.add_argument("--zotero-list", action="store_true", help="List top matching Zotero PDF attachments and exit.")
    parser.add_argument("--online-list", action="store_true", help="List top online OA paper candidates and exit.")
    parser.add_argument("--top", type=int, default=8, help="Number of candidates to show.")
    parser.add_argument("--online-top", type=int, default=5, help="Number of online candidates to search or try.")
    parser.add_argument("--select", type=int, help="Use Nth candidate from the ranked list.")
    parser.add_argument("--min-score", type=float, default=DEFAULT_LOCAL_MIN_SCORE, help="Minimum auto-match score for short local queries.")
    parser.add_argument("--loose-local-match", action="store_true", help="Allow low-confidence local/Zotero matches for long title queries.")
    parser.add_argument("--online-min-score", type=float, default=0.75, help="Minimum title score for online auto-download.")
    parser.add_argument("--no-zotero", action="store_true", help="Skip local Zotero attachment lookup.")
    parser.add_argument("--no-online", action="store_true", help="Disable Semantic Scholar/arXiv/Unpaywall/OpenAlex fallback.")
    parser.add_argument("--force-online", action="store_true", help="Skip local/Zotero lookup and use online OA fallback.")
    parser.add_argument("--download-dir", help="Directory for downloaded original PDFs. Default: PAPERS_DIR/Downloaded.")
    parser.add_argument("--download-only", action="store_true", help="Download or resolve the original PDF and stop before translation.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite same-named Desktop outputs.")
    parser.add_argument("--dry-run", action="store_true", help="Show match and command without translating.")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    config_path = Path(os.path.expanduser(args.config))

    if args.init_config:
        return init_config(config_path, args.force)
    if args.store_api_key:
        return store_api_key()
    if not args.query:
        parser.error("query is required unless using --init-config or --store-api-key")

    env = merged_environment(config_path)
    papers_dir = Path(os.path.expanduser(args.papers_dir or env.get("PAPERS_DIR") or str(DEFAULT_PAPERS_DIR)))
    pdf_path = resolve_input_pdf(args, env, papers_dir)
    if not pdf_path:
        if args.dry_run:
            return 0
        raise SystemExit("Could not resolve an original PDF from local, Zotero, or OA online sources.")
    if args.download_only:
        print(f"Resolved original PDF: {pdf_path}")
        return 0
    copied = run_translation(args, env, pdf_path)
    for path in copied:
        print(f"Wrote: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
