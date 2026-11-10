---
name: wikipedia
track: bonus
kind: live_api
provider: Wikipedia REST API
requires_env: []
inputs: [title, lang]
outputs: [items]
side_effect: false
---
# wikipedia

Lấy tóm tắt (lead section) của một trang Wikipedia theo tên khái niệm / người /
tổ chức. Dùng cho câu hỏi định nghĩa, background ổn định ("X là gì", "Y là ai"),
KHÔNG dùng cho tin tức mới (dùng `lookup`).

- Không cần API key. Endpoint: `https://{lang}.wikipedia.org/api/rest_v1/page/summary/{title}`.
- `lang` chỉ nhận `en` hoặc `vi`; giá trị khác bị đưa về `en`.
- `title` rỗng → trả error dict `ValueError`, không gọi mạng.
- 404 → trả `{"error": "not_found"}` để model có thể hỏi lại hoặc chuyển sang `lookup`.
