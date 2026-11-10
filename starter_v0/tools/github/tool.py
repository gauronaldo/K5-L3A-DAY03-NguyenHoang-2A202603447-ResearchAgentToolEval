from __future__ import annotations

import os
from typing import Any

import requests

from tools._shared import TIMEOUT, err

API_URL = "https://api.github.com/search/repositories"


def search_github_repos(query: str = "", sort: str = "stars", limit: int = 5) -> dict[str, Any]:
    try:
        query = query.strip() if isinstance(query, str) else ""
        if not query:
            raise ValueError("query must be a non-empty string")
        try:
            n = max(1, min(20, int(limit)))
        except (TypeError, ValueError):
            n = 5
        params: dict[str, Any] = {"q": query, "per_page": n}
        if sort in {"stars", "updated"}:
            params["sort"] = sort
            params["order"] = "desc"
        else:
            sort = "best_match"
        headers = {"Accept": "application/vnd.github+json", "User-Agent": "AI20k-Day03-Research-Agent"}
        token = os.getenv("GITHUB_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        response = requests.get(API_URL, params=params, headers=headers, timeout=TIMEOUT)
        response.raise_for_status()
        items = [{
            "title": repo.get("full_name") or "",
            "url": repo.get("html_url") or "",
            "source": "github.com",
            "summary": repo.get("description") or "",
            "stars": repo.get("stargazers_count"),
            "language": repo.get("language"),
            "updated": repo.get("pushed_at"),
        } for repo in response.json().get("items", [])[:n]]
        return {"tool": "search_github_repos", "query": query, "sort": sort, "items": items}
    except Exception as exc:
        return err("search_github_repos", exc)
