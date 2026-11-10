from __future__ import annotations

from typing import Any

import requests

from tools._shared import TIMEOUT, err

BASE_URL = "https://hn.algolia.com/api/v1"


def _clamp_limit(limit: Any) -> int:
    try:
        value = int(limit)
    except (TypeError, ValueError):
        value = 5
    return max(1, min(20, value))


def search_hackernews(query: str = "", sort: str = "relevance", limit: int = 5) -> dict[str, Any]:
    try:
        query = query.strip() if isinstance(query, str) else ""
        if not query:
            raise ValueError("query must be a non-empty string")
        sort = sort if sort in {"relevance", "date"} else "relevance"
        n = _clamp_limit(limit)
        endpoint = "search_by_date" if sort == "date" else "search"
        response = requests.get(
            f"{BASE_URL}/{endpoint}",
            params={"query": query, "tags": "story", "hitsPerPage": n},
            timeout=TIMEOUT,
        )
        response.raise_for_status()
        items = []
        for hit in response.json().get("hits", [])[:n]:
            object_id = hit.get("objectID") or ""
            discussion = f"https://news.ycombinator.com/item?id={object_id}" if object_id else ""
            items.append({
                "title": hit.get("title") or "",
                "url": hit.get("url") or discussion,
                "discussion_url": discussion,
                "source": "news.ycombinator.com",
                "summary": f"{hit.get('points') or 0} points, {hit.get('num_comments') or 0} comments",
                "date": hit.get("created_at"),
            })
        return {"tool": "search_hackernews", "query": query, "sort": sort, "items": items}
    except Exception as exc:
        return err("search_hackernews", exc)
