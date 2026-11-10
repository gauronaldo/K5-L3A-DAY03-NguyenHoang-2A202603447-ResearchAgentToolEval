from __future__ import annotations

import re
from typing import Any

from tools._shared import domain

TIER3_DOMAINS = ("x.com", "twitter.com", "reddit.com", "news.ycombinator.com", "facebook.com", "threads.net", "t.me")
TIER2_DOMAINS = (
    "reuters.com", "apnews.com", "bloomberg.com", "theverge.com", "techcrunch.com", "wired.com",
    "nytimes.com", "ft.com", "bbc.com", "vnexpress.net", "tuoitre.vn", "arstechnica.com",
)
ARXIV_ID = re.compile(r"(\d{4}\.\d{4,5}(?:v\d+)?)")


def _tier(url: str, source: str) -> int:
    host = domain(url) or source.lower()
    if source.startswith("@") or any(host.endswith(d) for d in TIER3_DOMAINS):
        return 3
    if any(host.endswith(d) for d in TIER2_DOMAINS):
        return 2
    return 1


def build_citations(items: list[dict[str, Any]] | None = None, style: str = "markdown") -> dict[str, Any]:
    if not isinstance(items, list):
        items = []
    style = style if style in {"markdown", "plain"} else "markdown"
    citations: list[str] = []
    warnings: list[str] = []
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            warnings.append(f"item {index}: not an object, skipped")
            continue
        title = str(item.get("title") or "").strip() or "(untitled)"
        url = str(item.get("url") or "").strip()
        source = str(item.get("source") or domain(url) or "").strip()
        if not url:
            warnings.append(f"item {index} ({title}): missing source URL, policy requires a URL for every fact")
        tier = _tier(url, source)
        notes = [f"Tier {tier}"]
        arxiv = ARXIV_ID.search(url) if "arxiv.org" in url else None
        if arxiv:
            notes.append(f"arXiv:{arxiv.group(1)}, not peer reviewed")
        if tier == 3:
            notes.append("early signal / unverified")
        if url:
            link = f"[{source or url}]({url})" if style == "markdown" else url
        else:
            link = "no URL"
        citations.append(f"[{index}] {title} — {link} ({'; '.join(notes)})")
    return {
        "tool": "build_citations",
        "style": style,
        "citations": citations,
        "text": "\n".join(citations),
        "warnings": warnings,
        "count": len(citations),
    }
