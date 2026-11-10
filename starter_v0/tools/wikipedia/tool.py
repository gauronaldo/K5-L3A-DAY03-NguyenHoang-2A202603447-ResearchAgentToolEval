from __future__ import annotations

from typing import Any
from urllib.parse import quote

import requests

from tools._shared import TIMEOUT, err

ALLOWED_LANGS = {"en", "vi"}
USER_AGENT = "AI20k-Day03-Research-Agent/1.0 (educational lab)"


def wikipedia_summary(title: str = "", lang: str = "en") -> dict[str, Any]:
    try:
        title = title.strip() if isinstance(title, str) else ""
        if not title:
            raise ValueError("title must be a non-empty string")
        lang = lang.strip().lower() if isinstance(lang, str) else "en"
        if lang not in ALLOWED_LANGS:
            lang = "en"
        url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{quote(title.replace(' ', '_'), safe='')}"
        response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
        if response.status_code == 404:
            return {"tool": "wikipedia_summary", "title": title, "lang": lang, "error": "not_found", "items": []}
        response.raise_for_status()
        data = response.json()
        page_url = ((data.get("content_urls") or {}).get("desktop") or {}).get("page") or url
        return {"tool": "wikipedia_summary", "title": title, "lang": lang, "items": [{
            "title": data.get("title") or title,
            "url": page_url,
            "source": f"{lang}.wikipedia.org",
            "summary": data.get("extract") or "",
            "description": data.get("description") or "",
        }]}
    except Exception as exc:
        return err("wikipedia_summary", exc)
