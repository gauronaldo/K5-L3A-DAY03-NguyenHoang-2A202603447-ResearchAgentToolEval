---
name: cite
track: bonus
kind: local_formatter
requires_env: []
inputs: [items, style]
outputs: [citations, text, warnings, count]
side_effect: false
---
# cite

Tạo danh sách trích dẫn nguồn từ các item đã thu thập (output của lookup/fetch/papers/
timeline/...), theo Source And Citation Policy nội bộ:

- Gán tier nguồn: arXiv/paper/blog chính thức → Tier 1; báo chí → Tier 2;
  x.com/twitter/reddit/HN/forum hoặc source dạng `@handle` → Tier 3 (`early signal / unverified`).
- arXiv: ghi arXiv ID + ghi chú "not peer reviewed".
- Item thiếu `url` → thêm vào `warnings` (policy: mọi fact cần source URL), không crash.
- `style` ∈ {`markdown`, `plain`}. Không gọi mạng.
