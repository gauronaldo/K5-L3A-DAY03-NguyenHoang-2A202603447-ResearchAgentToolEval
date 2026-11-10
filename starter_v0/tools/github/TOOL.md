---
name: github
track: bonus
kind: live_api
provider: GitHub REST API (search/repositories)
requires_env: []
inputs: [query, sort, limit]
outputs: [items]
side_effect: false
---
# github

Tìm repository mã nguồn mở trên GitHub theo từ khóa (framework, thư viện, công cụ).
Dùng khi user hỏi "repo / thư viện / project open-source nào về X", "repo nhiều sao nhất".
KHÔNG dùng để đọc một repo URL cụ thể (dùng `fetch`).

- `GITHUB_TOKEN` là tùy chọn (tăng rate limit); không có token vẫn chạy.
- `sort` ∈ {`stars`, `updated`, `best_match`}; giá trị khác → `best_match`.
- `limit` ép về 1..20.
