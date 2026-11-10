---
name: hackernews
track: bonus
kind: live_api
provider: Hacker News Algolia API
requires_env: []
inputs: [query, sort, limit]
outputs: [items]
side_effect: false
---
# hackernews

Tìm thảo luận/bài đăng trên Hacker News (cộng đồng dev/tech) qua Algolia API.
Dùng khi user hỏi "trên Hacker News / HN / cộng đồng dev nói gì về X".
KHÔNG dùng cho Twitter/X (dùng `social_search`) hay tin báo chí (dùng `lookup`).

- Không cần API key. `sort=relevance` → `/search`, `sort=date` → `/search_by_date`.
- `limit` được ép về khoảng 1..20 (chuỗi số như `"5"` cũng nhận; giá trị hỏng → 5).
- Chỉ lấy `tags=story`. Item có `discussion_url` trỏ về thread HN.
