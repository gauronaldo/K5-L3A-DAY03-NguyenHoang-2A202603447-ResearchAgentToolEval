"""Tool Unit Test Challenge — filled in.

Patterns come from test_tools_examples.py. Fixtures are in conftest.py.

Rules:
- Offline only: mock HTTP with `fake_http`, set fake keys with `monkeypatch.setenv`.
- One behaviour per test. Name the test after the behaviour, not the function.
- Done = `pytest tests/ -v` shows 0 skipped, 0 failed.
"""
from __future__ import annotations

import pytest
import requests

from conftest import FakeResponse
from tools import TOOL_FUNCTIONS

clarify = TOOL_FUNCTIONS["clarify"]
format_tool = TOOL_FUNCTIONS["format"]
send = TOOL_FUNCTIONS["send"]
lookup = TOOL_FUNCTIONS["lookup"]
fetch = TOOL_FUNCTIONS["fetch"]
timeline = TOOL_FUNCTIONS["timeline"]
social_search = TOOL_FUNCTIONS["social_search"]
policy = TOOL_FUNCTIONS["policy"]
wikipedia = TOOL_FUNCTIONS["wikipedia"]
hackernews = TOOL_FUNCTIONS["hackernews"]
github = TOOL_FUNCTIONS["github"]
cite = TOOL_FUNCTIONS["cite"]


def _tweet(i: int, handle: str = "elonmusk") -> dict:
    return {"tweet_id": str(1000 + i), "screen_name": handle, "text": f"tweet {i}\nsecond line", "created_at": "today"}


# ---------------- clarify ----------------

def test_clarify_choice_returns_options_and_awaits_user() -> None:
    result = clarify(question="Chọn nguồn?", response_type="choice", options=["Web", "Twitter"])
    assert result["options"] == ["Web", "Twitter"]
    assert result["response_type"] == "choice"
    assert result["question"] == "Chọn nguồn?"
    assert result["awaiting_user"] is True


def test_clarify_without_options_returns_empty_list() -> None:
    result = clarify(question="Link nào?", options=None)
    assert result["options"] == []
    assert result["response_type"] == "text"


# ---------------- format ----------------

def test_format_sections_groups_items_by_section() -> None:
    items = [
        {"title": "a1", "url": "https://a.com/1", "section": "A"},
        {"title": "b1", "url": "https://b.com/1", "section": "B"},
        {"title": "a2", "url": "https://a.com/2", "section": "A"},
    ]
    md = format_tool(items=items, template="sections", headline="H")["markdown"]
    assert md.count("## A") == 1
    assert md.count("## B") == 1
    assert md.startswith("# H")
    assert md.index("a2") < md.index("## B")  # a2 grouped under A, not after B


def test_format_thread_numbers_items() -> None:
    items = [{"title": f"t{i}", "url": f"https://x.com/{i}"} for i in range(3)]
    md = format_tool(items=items, template="thread")["markdown"]
    lines = [line for line in md.split("\n") if line.strip()]
    assert [line.split(" ", 1)[0] for line in lines] == ["1/", "2/", "3/"]


def test_format_empty_items_does_not_crash() -> None:
    for empty in (None, []):
        result = format_tool(items=empty, template="sections")
        assert result["item_count"] == 0
        assert result["markdown"] == ""


def test_format_item_without_url_has_no_dangling_separator() -> None:
    # Regression (bug found): an item with no url/source rendered "- text - " with a dangling dash.
    md = format_tool(items=[{"title": "Chỉ có tiêu đề"}], template="bullets")["markdown"]
    assert md == "- Chỉ có tiêu đề"


# ---------------- send (guardrail) ----------------

def test_send_confirmed_posts_to_telegram(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "tok123")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "@chan")
    calls = fake_http(FakeResponse({"ok": True}))
    result = send(text="Bản tin AI", confirmed=True)
    assert len(calls) == 1
    assert calls[0]["method"] == "POST"
    assert "tok123" in calls[0]["url"]
    assert calls[0]["json"]["chat_id"] == "@chan"
    assert calls[0]["json"]["text"] == "Bản tin AI"
    assert result["status"] == "sent"


def test_send_confirmed_without_env_returns_error_and_no_request(fake_http) -> None:
    calls = fake_http(FakeResponse({"ok": True}))
    result = send(text="x", confirmed=True)
    assert result["error"] == "RuntimeError"
    assert "TELEGRAM_BOT_TOKEN" in result["message"]
    assert calls == []


@pytest.mark.parametrize("flag", ["false", "False", "no", "0", 1, "yes please"])
def test_send_string_or_non_bool_confirmation_does_not_send(monkeypatch, fake_http, flag) -> None:
    # Regression (bug found): confirmed="false" (a string, as small models often emit) was truthy
    # and the starter actually posted to Telegram. Only a real True / "true" counts.
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "tok")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "1")
    calls = fake_http(FakeResponse({"ok": True}))
    result = send(text="x", confirmed=flag)
    assert result["status"] == "needs_confirmation"
    assert calls == []


# ---------------- lookup ----------------

def test_lookup_without_timeframe_omits_time_range(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "k")
    calls = fake_http(FakeResponse({"results": []}))
    result = lookup(query="AI", timeframe=None)
    assert "time_range" not in calls[0]["json"]
    assert result["items"] == []


def test_lookup_accepts_numeric_string_max_results(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("TAVILY_API_KEY", "k")
    calls = fake_http(FakeResponse({"results": []}))
    lookup(query="AI", max_results="3")
    assert calls[0]["json"]["max_results"] == 3


# ---------------- fetch ----------------

def test_fetch_maps_firecrawl_response(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fc")
    calls = fake_http(FakeResponse({"data": {
        "markdown": "# Hello\nbody",
        "metadata": {"title": "T", "sourceURL": "https://www.example.com/post"},
    }}))
    result = fetch(url="https://www.example.com/post")
    assert calls[0]["url"] == "https://api.firecrawl.dev/v1/scrape"
    assert calls[0]["json"]["url"] == "https://www.example.com/post"
    assert calls[0]["headers"]["Authorization"] == "Bearer fc"
    assert result["items"][0] == {
        "title": "T", "url": "https://www.example.com/post", "source": "example.com", "summary": "# Hello\nbody",
    }


def test_fetch_truncates_markdown_to_4000_chars(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("FIRECRAWL_API_KEY", "fc")
    fake_http(FakeResponse({"data": {"markdown": "y" * 9000, "metadata": {}}}))
    item = fetch(url="https://e.com")["items"][0]
    assert len(item["summary"]) == 4000
    assert item["title"] == "https://e.com"  # falls back to url when no title


def test_fetch_without_key_returns_error_dict(fake_http) -> None:
    calls = fake_http(FakeResponse({}))
    result = fetch(url="https://e.com")
    assert result["error"] == "RuntimeError"
    assert calls == []


# ---------------- timeline / social_search ----------------

def test_timeline_respects_limit_and_skips_items_without_id(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "r")
    raw = [{"screen_name": "elonmusk", "text": "no id"}] + [_tweet(i) for i in range(6)]
    calls = fake_http(FakeResponse({"timeline": raw}))
    result = timeline(screenname="elonmusk", limit=3)
    assert calls[0]["params"] == {"screenname": "elonmusk"}
    assert calls[0]["url"].endswith("/timeline.php")
    assert len(result["items"]) == 3
    for i, item in enumerate(result["items"]):
        assert item["url"] == f"https://x.com/elonmusk/status/{1000 + i}"
        assert item["source"] == "@elonmusk"


def test_timeline_negative_limit_does_not_slice_from_end(monkeypatch, fake_http) -> None:
    # Regression (bug found): limit=-1 used items[:-1] and silently returned 5 of 6 tweets.
    monkeypatch.setenv("RAPIDAPI_KEY", "r")
    fake_http(FakeResponse({"timeline": [_tweet(i) for i in range(6)]}))
    assert len(timeline(screenname="elonmusk", limit=-1)["items"]) == 1


def test_social_search_passes_search_type(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "r")
    calls = fake_http(FakeResponse({"timeline": [_tweet(1, "openai")]}))
    result = social_search(query="OpenAI", search_type="Top")
    assert calls[0]["url"].endswith("/search.php")
    assert calls[0]["params"] == {"query": "OpenAI", "search_type": "Top"}
    assert calls[0]["headers"]["x-rapidapi-key"] == "r"
    assert result["search_type"] == "Top"
    assert len(result["items"]) == 1


def test_social_search_http_429_returns_error_dict(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("RAPIDAPI_KEY", "r")
    fake_http(FakeResponse(status_code=429))
    assert social_search(query="x")["error"] == "HTTPError"


# ---------------- policy (local knowledge + trust boundary) ----------------

def test_policy_empty_query_returns_no_results() -> None:
    result = policy(query="")
    assert result["results"] == []


def test_policy_area_filter_only_returns_that_area() -> None:
    result = policy(query="API key dữ liệu khách hàng prompt", policy_area="data_privacy", top_k=5)
    assert result["results"], "expected at least one data_privacy hit"
    assert all(hit["policy_area"] == "data_privacy" for hit in result["results"])


def test_policy_instruction_like_lines_go_to_untrusted_text() -> None:
    result = policy(query="injection probe citation", policy_area="source_citation", top_k=5)
    probe = [hit for hit in result["results"] if hit["section"] == "Injection probe"]
    assert probe, "expected the Injection probe section to be retrieved"
    hit = probe[0]
    assert any("ignore the citation policy" in line for line in hit["untrusted_text"])
    assert "ignore" not in hit["facts"].lower()


# ================= TEAM-ADDED TOOLS =================

# ---------------- wikipedia ----------------

def test_wikipedia_happy_path_maps_summary(fake_http) -> None:
    calls = fake_http(FakeResponse({
        "title": "Large language model",
        "extract": "A large language model is ...",
        "description": "type of ML model",
        "content_urls": {"desktop": {"page": "https://en.wikipedia.org/wiki/Large_language_model"}},
    }))
    result = wikipedia(title="Large language model", lang="en")
    assert calls[0]["method"] == "GET"
    assert calls[0]["url"] == "https://en.wikipedia.org/api/rest_v1/page/summary/Large_language_model"
    assert "User-Agent" in calls[0]["headers"]
    assert result["items"][0]["url"] == "https://en.wikipedia.org/wiki/Large_language_model"
    assert result["items"][0]["summary"].startswith("A large language model")
    assert result["items"][0]["source"] == "en.wikipedia.org"


@pytest.mark.parametrize("bad_title", ["", "   ", None, 123])
def test_wikipedia_empty_or_non_string_title_returns_error_without_request(fake_http, bad_title) -> None:
    calls = fake_http(FakeResponse({}))
    result = wikipedia(title=bad_title)
    assert result["error"] == "ValueError"
    assert calls == []


def test_wikipedia_out_of_enum_lang_falls_back_to_en(fake_http) -> None:
    calls = fake_http(FakeResponse({"title": "X", "extract": "x"}))
    result = wikipedia(title="Transformer", lang="fr")
    assert calls[0]["url"].startswith("https://en.wikipedia.org/")
    assert result["lang"] == "en"


def test_wikipedia_404_returns_not_found_dict(fake_http) -> None:
    fake_http(FakeResponse(status_code=404))
    result = wikipedia(title="Nonexistent page qwerty")
    assert result["error"] == "not_found"
    assert result["items"] == []


def test_wikipedia_network_error_returns_error_dict(fake_http) -> None:
    fake_http(requests.Timeout("timed out"))
    assert wikipedia(title="AI")["error"] == "Timeout"


# ---------------- hackernews ----------------

def test_hackernews_happy_path_builds_items_and_request(fake_http) -> None:
    calls = fake_http(FakeResponse({"hits": [
        {"objectID": "42", "title": "Show HN: agent", "url": "https://agent.dev", "points": 120, "num_comments": 33,
         "created_at": "2026-11-01"},
        {"objectID": "43", "title": "Ask HN: no url", "url": None, "points": 5, "num_comments": 1},
    ]}))
    result = hackernews(query="AI agents", sort="date", limit=2)
    assert calls[0]["url"] == "https://hn.algolia.com/api/v1/search_by_date"
    assert calls[0]["params"] == {"query": "AI agents", "tags": "story", "hitsPerPage": 2}
    assert result["items"][0]["url"] == "https://agent.dev"
    assert result["items"][0]["discussion_url"] == "https://news.ycombinator.com/item?id=42"
    assert result["items"][0]["summary"] == "120 points, 33 comments"
    assert result["items"][1]["url"] == "https://news.ycombinator.com/item?id=43"  # falls back to thread


@pytest.mark.parametrize("raw_limit, sent", [("5", 5), (0, 1), (-3, 1), (999, 20), ("abc", 5), (None, 5)])
def test_hackernews_limit_from_model_is_clamped(fake_http, raw_limit, sent) -> None:
    calls = fake_http(FakeResponse({"hits": []}))
    hackernews(query="rust", limit=raw_limit)
    assert calls[0]["params"]["hitsPerPage"] == sent


def test_hackernews_bad_sort_and_empty_query(fake_http) -> None:
    calls = fake_http(FakeResponse({"hits": []}))
    assert hackernews(query="")["error"] == "ValueError"
    assert calls == []
    result = hackernews(query="llm", sort="Top")
    assert calls[0]["url"].endswith("/search")
    assert result["sort"] == "relevance"


def test_hackernews_http_error_returns_error_dict(fake_http) -> None:
    fake_http(FakeResponse(status_code=503))
    assert hackernews(query="x")["error"] == "HTTPError"


# ---------------- github ----------------

def test_github_happy_path_sorted_by_stars(fake_http) -> None:
    calls = fake_http(FakeResponse({"items": [
        {"full_name": "langchain-ai/langgraph", "html_url": "https://github.com/langchain-ai/langgraph",
         "description": "Build agents", "stargazers_count": 9000, "language": "Python", "pushed_at": "2026-11-01"},
    ]}))
    result = github(query="agent framework", sort="stars", limit=3)
    assert calls[0]["url"] == "https://api.github.com/search/repositories"
    assert calls[0]["params"] == {"q": "agent framework", "per_page": 3, "sort": "stars", "order": "desc"}
    assert "Authorization" not in calls[0]["headers"]
    assert result["items"][0]["title"] == "langchain-ai/langgraph"
    assert result["items"][0]["stars"] == 9000


def test_github_uses_token_when_present(monkeypatch, fake_http) -> None:
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_test")
    calls = fake_http(FakeResponse({"items": []}))
    github(query="x")
    assert calls[0]["headers"]["Authorization"] == "Bearer ghp_test"


def test_github_bad_input_from_model(fake_http) -> None:
    calls = fake_http(FakeResponse({"items": []}))
    assert github(query="   ")["error"] == "ValueError"
    assert calls == []
    result = github(query="rag", sort="popular", limit="7")
    assert "sort" not in calls[0]["params"]
    assert calls[0]["params"]["per_page"] == 7
    assert result["sort"] == "best_match"


def test_github_rate_limited_returns_error_dict(fake_http) -> None:
    fake_http(FakeResponse(status_code=403))
    assert github(query="x")["error"] == "HTTPError"


# ---------------- cite (local) ----------------

def test_cite_assigns_tiers_and_arxiv_note() -> None:
    items = [
        {"title": "Attention Is All You Need", "url": "https://arxiv.org/abs/1706.03762"},
        {"title": "Reuters piece", "url": "https://www.reuters.com/tech/ai"},
        {"title": "viral tweet", "url": "https://x.com/sama/status/1", "source": "@sama"},
    ]
    result = cite(items=items)
    assert result["count"] == 3
    assert "Tier 1" in result["citations"][0] and "arXiv:1706.03762, not peer reviewed" in result["citations"][0]
    assert "Tier 2" in result["citations"][1]
    assert "Tier 3" in result["citations"][2] and "unverified" in result["citations"][2]
    assert result["citations"][0].startswith("[1] Attention Is All You Need — [arxiv.org](https://arxiv.org/abs/1706.03762)")
    assert result["warnings"] == []


def test_cite_item_missing_url_warns_instead_of_crashing() -> None:
    result = cite(items=[{"title": "no link"}, "not a dict"], style="plain")
    assert result["count"] == 1
    assert "no URL" in result["citations"][0]
    assert len(result["warnings"]) == 2


@pytest.mark.parametrize("bad_items", [None, "abc", 5, {}])
def test_cite_bad_items_type_returns_empty(bad_items) -> None:
    result = cite(items=bad_items, style="weird")
    assert result["count"] == 0
    assert result["style"] == "markdown"
    assert result["text"] == ""
