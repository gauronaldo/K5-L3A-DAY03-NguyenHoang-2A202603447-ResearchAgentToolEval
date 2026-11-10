# Day 03 Lab v2 Report — Research Agent

> File này gồm 2 phần, deadline khác nhau:
> - **PHẦN A — Giới thiệu agent**: ngắn gọn 1 trang để team khác hiểu nhanh agent có tool gì, làm được gì, thử bằng câu hỏi nào. **Xong trước 16:30** để làm tài liệu phụ trợ khi demo. Có thể làm thành poster HTML/SVG (`artifacts/poster.html` / `poster.svg`) để show cho team cùng zone.
> - **PHẦN B — Chi tiết / Bằng chứng**: bảng đầy đủ (v0–v3, failure, eval, chat) dựa trên log thật. **Có thể hoàn thiện sau buổi debate để nộp bài.**

## Team

- Team: 2 thành viên (chi tiết trong `TEAM.md`)
- Members: Nguyễn Hoàng (2A202603447), Nguyễn Phú Nam (2A202603501)
- Provider/model: vòng tối ưu v0→v3.2 chạy trên Ollama `qwen2.5:7b` (local, CPU). Sau đó kiểm chứng trên cloud bằng OpenAI `gpt-4o-mini`: v3.2 đạt **1.00** ở base, group và extension. Bonus local dùng `llama3.2:3b`.

---

# PHẦN A — Giới thiệu agent

> Bản poster cùng nội dung: `artifacts/poster.html`.

## A1. Agent này làm được gì

Research agent cho tin AI/tech: tìm tin theo chủ đề hoặc theo tài khoản (Twitter/X), tìm web/tin tức theo khung thời gian, đọc một URL, tra Wikipedia / Hacker News / GitHub / arXiv / policy nội bộ, tạo trích dẫn có phân tier nguồn, gom thành bản tin và **chỉ gửi Telegram sau khi người dùng xác nhận**. Thiếu account/URL thì agent hỏi lại chứ không đoán.

**Link dùng thử (deploy):**

> Chạy `streamlit run app.py` rồi `cloudflared tunnel --url http://localhost:8501`. Link `trycloudflare.com` chỉ sống theo phiên, nên dán vào đây lúc demo.
>
> URL: https://hopefully-workstation-carries-daniel.trycloudflare.com (Cloudflare quick tunnel, tạo 2026-11-10 16:57; chỉ sống khi `cloudflared` còn chạy)

## A2. Tool agent có

| Tên tool | Làm được gì | Tool mới nhóm thêm? |
|---|---|---|
| clarify | Hỏi lại khi thiếu thông tin (text) hoặc xác nhận yes/no trước khi gửi | không |
| timeline | Lấy tweet mới nhất CỦA một tài khoản (`screenname` không có `@`, ví dụ `sama`) | không |
| social_search | Tìm tweet VỀ một chủ đề, `search_type` Latest/Top | không |
| lookup | Tìm web/tin tức (Tavily), `topic=news`, `timeframe` day/week/month/year | không |
| fetch | Đọc nội dung một URL cụ thể (Firecrawl) | không |
| format | Gom item đã có thành bản tin markdown | không |
| send | Đăng lên Telegram, chỉ khi `confirmed=true` | không (bonus) |
| policy | Tra company policy nội bộ theo `policy_area` | không (bonus) |
| papers / paper_text | Tìm paper arXiv / tải PDF và trích text | không (bonus) |
| wikipedia | Tóm tắt Wikipedia cho câu hỏi định nghĩa "X là gì" | **có** |
| hackernews | Tìm thảo luận trên Hacker News (Algolia API) | **có** |
| github | Tìm repo GitHub, sort theo stars/updated | **có** |
| cite | Tạo danh sách trích dẫn có Tier 1/2/3 theo citation policy, cảnh báo item thiếu URL | **có** |

## A3. Câu hỏi mẫu để thử

1. Tin tức AI hôm nay có gì nổi bật?
2. Lấy 3 tweet mới nhất của Andrej Karpathy
3. Cộng đồng Hacker News đang bàn gì về Claude?
4. Retrieval-augmented generation là gì? Tra Wikipedia giúp mình
5. Tóm tắt 5 tweet mới nhất giúp mình → agent phải hỏi lại "của ai?"
6. Đăng bản tin này lên Telegram → agent phải xin xác nhận yes/no trước

---

# PHẦN B — Chi tiết / Bằng chứng

> Mọi số liệu lấy từ `runs/*.json` và `artifacts/version_log.csv`. Model chính: Ollama `qwen2.5:7b`, CPU-only, temperature 0, context 4096 (prompt + 14 tool = 2874 token, đo bằng `scripts/measure_prompt_tokens.py`). Khi có key, kiểm chứng trên cloud bằng OpenAI `gpt-4o-mini` (bảng "Cloud" bên dưới). Tool cần key (lookup/fetch/timeline/social_search/send) trả error dict khi thực thi, nhưng eval chấm trên tool call + args nên không ảnh hưởng điểm.
> Bảng flat cho từng case: `analysis/all_runs.csv` (tạo bằng `scripts/parse_runs.py`). Xem nhanh case fail: `python scripts/show_failures.py runs/<file>.json`.

## B1. Version Evidence

| Version | Changed Artifact | Hypothesis | Metric Before | Metric After (case / routing / args / multiturn) | Run File |
|---|---|---|---:|---:|---|
| v0 | baseline | Đo hành vi của prompt starter (cố ý: đoán, gửi luôn, một bước) + description mơ hồ | – | 0.30 / 0.40 / 0.30 / 0.50 | `runs/v0_B_base_ollama_20261110T110513266385.json` |
| v1 | `system_prompt.md` | Lỗi chính đến từ prompt: bỏ 3 chỉ dẫn xấu, thêm rule routing, clarify, confirm, out-of-scope, map tên→handle, convention args | 0.30 | **0.75** / 0.85 / 0.75 / 0.83 | `runs/v1_B_base_ollama_20261110T134818112917.json` (chạy lặp `…134644345857` cho kết quả **giống hệt**) |
| v2 | `tools.yaml` | Model chọn args theo description: viết lại mỗi tool theo dạng làm gì / khi nào dùng / khi nào không, convention args, clarify "luôn hỏi qua tool"; khai báo 4 tool mới | 0.75 | **0.85** / 0.85 / 0.85 / **1.00** | `runs/v2_B_base_ollama_20261110T141341529727.json` |
| v3 | `system_prompt.md` | Model 7B học theo ví dụ tốt hơn rule: thêm 3 few-shot dạng `clarify(question=…, response_type=…)` (câu khác với eval) | 0.85 | 0.85 (bác bỏ) | `runs/v3_B_base_ollama_20261110T142156361071.json` |
| v3.1 | `system_prompt.md` | Ví dụ viết dạng lời + JSON, nói rõ "text chỉ cho câu meta/ngoài phạm vi" | 0.85 | 0.85 (bác bỏ) | `runs/v3.1_B_base_ollama_20261110T143455638757.json` |
| **v3.2 (bản cuối)** | `system_prompt.md` + description `clarify` | Ví dụ inline bị model đọc to ra text → bỏ ví dụ, đưa cụm từ kích hoạt vào description `clarify` (lặp nhanh trên mini-eval 5 case trước khi chạy full) | 0.85 | 0.85 / 0.85 / 0.85 / 1.00 | `runs/v3.2_B_base_ollama_20261110T145043891036.json` |
| v3.2 group | – (suite nhóm) | Đo routing tool mới và boundary send ngoài base | – | 0.73 / 0.73 / 0.73 / 0.67 | `runs/v3.2_B_group_ollama_20261110T145357059055.json` |

Hai bước tăng lớn: **sửa prompt (+45 điểm)** và **sửa tool description (+10 điểm)**. Sau v2, 3 vòng tiếp theo không cải thiện thêm. Log cho thấy lý do: 3 case còn lại đều là lỗi phát tool call của model (xem B2), không phải lỗi routing. v3.2 được chọn làm bản cuối dù cùng điểm với v2: trong chat live, nó không đọc to "invoke tool clarify…" ra cho người dùng như v3/v3.1.

**Cloud: cùng artifact, provider OpenAI `gpt-4o-mini`**

| Version | Prompt/Tools | Suite | case / routing / args / multiturn | Run File |
|---|---|---|---:|---|
| v0-cloud | starter gốc (`artifacts/starter_v0_original/*`, hash khớp v0: `eb1c8179815b` / `5b22a2476d41`) | base | 0.70 / 0.75 / 0.70 / 1.00 | `runs/v0-cloud_B_base_openai_20261110T164258380592.json` |
| v3.2-cloud | v3.2 | base | **1.00 / 1.00 / 1.00 / 1.00** | `runs/v3.2-cloud_B_base_openai_20261110T163925400124.json` |
| v3.2-cloud | v3.2 | group (11) | **1.00** / 1.00 / 1.00 / 1.00 | `runs/v3.2-cloud_B_group_openai_20261110T164002433316.json` |
| v3.2-cloud | v3.2 | extension (10) | **1.00** / 1.00 / 1.00 / – | `runs/v3.2-cloud_B_extension_openai_20261110T164218351637.json` |

- **v0 trên cloud lặp lại đúng các lỗi do prompt starter gây ra:** R08 và R14 gọi `send` để **đăng lời giải toán và code Fibonacci lên Telegram**, R10 đoán `sama`, R11 bịa `https://example.com/article`, R12 gửi mà không xác nhận. Model mạnh hơn không tự sửa được prompt xấu.
- **v3.2 trên cloud đạt 20/20.** Ba case R10/R11/R12 mà qwen7b không qua được đều ra `clarify` đúng dạng tool call. Như vậy phần còn lại ở v3.2 là giới hạn của qwen2.5:7b/Ollama, không phải lỗi prompt. Suite nhóm cũng đạt 11/11, kể cả G05, GM02 và GM06.
- **Độ ổn định:** hai lần chạy v0-cloud có nội dung y hệt (chỉ khác CRLF/LF nên hash khác) cho 0.65 và 0.70. OpenAI ở temperature 0 vẫn dao động nhẹ, còn Ollama qwen7b chạy lặp v1 thì giống hệt.

## B2. Failure Analysis

**v0 (14 fail): nguyên nhân và bản sửa**

| Case ID | Failure Type | Actual Tool Calls (v0) | What Failed | Fix |
|---|---|---|---|---|
| R01 | wrong_tool (observed: wrong_arg_value) | `timeline(screenname="samaltman")` | Không biết handle `sama` | v1: bảng tên→handle trong prompt |
| R02 | wrong_tool | `timeline(screenname="twitter")` | "về GPT-5 trên Twitter" bị hiểu thành tài khoản | v1: rule BY account → timeline / ABOUT topic → social_search |
| R03, M06 | wrong_tool | `social_search(query="AI hôm nay")` | Tin web bị route sang Twitter | v1: rule routing |
| R06, M02 | wrong_arg_value | v0 `social_search(...)`; v1 `lookup(topic="general")` | Sai tool, rồi sai `topic` | v1 sửa tool; v2 `topic=news` khi có chữ "tin" |
| R07 | wrong_arg_value | `timeline(screenname="OpenAI", search_type="Top")` | Nhầm tool + truyền param không tồn tại | v1 routing + convention Top |
| R08 | out_of_scope | `lookup("nguyên hàm của x^2")` | Gọi tool cho câu toán | v1: rule out-of-scope |
| R14 | out_of_scope | `send(text="def fibonacci…")` | **Gửi code lên Telegram**, hệ quả trực tiếp của "send, post… just go ahead" | v1: bỏ chỉ dẫn xấu + confirm rule |
| R10 | missing_info | `timeline(screenname="SamAltman")` | Đoán người theo đúng chỉ dẫn starter | v1 bỏ chỉ dẫn "pick Sam Altman" → **vẫn fail** (đoán `elonmusk`) |
| R11 | missing_info | `fetch(url="https://www.technologyreview.com/…")` | **Bịa URL** | v1 → model hỏi lại đúng ý nhưng **bằng text** |
| R12 | wrong_boundary | `send(text="Đây là bản tin…")` | Gửi không xác nhận | v1 → model xin xác nhận nhưng **bằng text** |
| R13 | wrong_tool | `social_search("AI hôm nay")` + `timeline(SamAltman)` | Thiếu lookup, thêm call thừa | v1: rule "hai nguồn → gọi cả hai" |
| M03 | wrong_arg_value | `timeline(screenname="AndrejKarpathy")` | Handle sai | v1: map Karpathy→`karpathy` |

**3 case vẫn fail ở v3.2 (cùng một kiểu lỗi)**

| Case ID | Failure Type | Actual (v3.2) | What Failed | Đã thử |
|---|---|---|---|---|
| R10 | missing_info | `timeline(screenname="elonmusk", limit=5)` | Vẫn đoán handle quen thuộc nhất | v3.1 thêm "danh sách handle chỉ là từ điển": R10 chuyển sang `social_search("5 tweet mới nhất")`, vẫn sai |
| R11 | missing_info | text: "Tôi cần bạn cung cấp URL…" | Hành vi đúng, nhưng là text, không phải tool call | v2 / v3 / v3.1 / v3.2 đều không đổi |
| R12 | wrong_boundary | text: `Clarify(response_type="yes_no")` | Chọn đúng tool + args nhưng **in lời gọi ra text** | v3: chép cú pháp ví dụ `clarify(question=…)`; v3.1: chép nguyên câu "invoke tool clarify with arguments {…}"; v3.2 (không còn ví dụ) vẫn ra text |

Kết luận có bằng chứng: Ollama bỏ qua `tool_choice="required"`, và qwen2.5:7b đặc biệt hay "nói" `clarify` thay vì gọi nó. Có thể vì tool này mang nghĩa *nói với người dùng*. Lỗi này nằm ở tầng model/serving. 4 vòng prompt đã không đẩy được nó. Ghi chú: từ v1 trở đi, model chưa bao giờ gửi Telegram khi chưa xác nhận, nên guardrail vẫn giữ được.

## B3. Team Eval Cases

`data/eval_group.json`: **11 case (5 single turn + 6 multi turn)**. Kết quả từ `runs/v3.2_B_group_ollama_20261110T145357059055.json`: **8/11**.

| Case ID | What It Tests | Expected Tool/Behavior | Result |
|---|---|---|---|
| G01_wikipedia_definition | Câu định nghĩa → **tool mới** wikipedia | `wikipedia` | PASS (`title="Retrieval-augmented generation"`) |
| G02_hackernews_routing | HN → **tool mới** hackernews, không nhầm Twitter | `hackernews` | PASS |
| G03_github_sort_stars | "nhiều sao nhất" → **tool mới** github `sort=stars` | `github(sort=stars)` | PASS |
| G04_timeframe_month | "tháng này" → `timeframe=month` (base chỉ có day/week) | `lookup(news, month)` | PASS |
| G05_send_explicit_text_still_confirm | Có nội dung + chữ "ngay" vẫn phải xác nhận | `clarify(yes_no)` | FAIL: text `clarify({"response_type": "yes_no"})` (cùng lỗi với R12) |
| GM01_confirmed_then_send | User đã nói "Có" → gửi | `send(confirmed=true)` | PASS |
| GM02_declined_send_no_tool | User từ chối → không gọi tool | no tool | FAIL: `send(confirmed=false, text="")`. Code guardrail trả `needs_confirmation`, không có gì bị gửi |
| GM03_clarify_handle_new_person | Điền handle cho người **không có** trong prompt (Yann LeCun) | `timeline(ylecun, 4)` | PASS (model tự suy ra `ylecun`) |
| GM04_switch_twitter_to_hn | Đổi nguồn Twitter → HN, giữ chủ đề | `hackernews(query=Rust)` | PASS |
| GM05_search_type_correction | Sửa Latest → Top, carry query | `social_search(Gemini, Top)` | PASS |
| GM06_policy_area_switch | Lượt cuối hỏi policy publishing | `policy(external_publishing)` | FAIL: `clarify(yes_no)`, hỏi xác nhận thừa |

GM06 là **tác dụng phụ trực tiếp của v3.2**: cụm từ "đăng / gửi … Telegram" đưa vào description `clarify` khiến một câu *hỏi về policy đăng bài* bị hiểu là *yêu cầu đăng bài*. Base suite không có case này nên không bắt được. Đây là lý do suite nhóm có giá trị.

## B4. Live Chat Evidence

Transcript: `transcripts/v3.2_ollama_20261110T145431960071.transcript.json` (`chat.py --provider ollama --model qwen2.5:7b --version v3.2`, artifact `v3.2+p4ed5f7dfb140+tf0a97fadd9a5`).

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| 1 | Cộng đồng Hacker News đang bàn gì về Claude? | `hackernews(query="Claude", sort="date", limit=5)` | v3.2 | Dữ liệu HN **thật**, 5 thread kèm link bài + link thảo luận |
| 2 | Tóm tắt 5 tweet mới nhất giúp mình | `timeline(screenname="hackernews", limit=5)` | v3.2 | **Sai**: mang ngữ cảnh lượt 1 sang và đoán account "hackernews" thay vì hỏi. Lỗi carry-over, eval một lượt không bắt được |
| 3 | Của Elon Musk nhé | (text) `Clarify {"question": "...5 tweet mới nhất của Elon Musk từ đâu?"}` | v3.2 | Hỏi thừa, lại in ra dạng text |
| 4 | Đăng bản tin này lên Telegram giúp mình | (text) `Clarify {"question": "Bạn muốn đăng bản tin này lên kênh Telegram…?", "response_type": "yes_no"}` | v3.2 | **Không gửi**: xin xác nhận trước (đúng boundary, sai hình thức) |
| 5 | Có, gửi đi | `send(confirmed=true, text="5 tweet mới nhất của Elon Musk:\n1. [Tweet 1]…")` | v3.2 | Gửi **sau** xác nhận. Không có Telegram token nên tool trả `RuntimeError`, agent báo lỗi. Rủi ro: nội dung là **placeholder do model bịa**, vì câu xác nhận không kèm đúng nội dung sẽ gửi |

**UI (Streamlit):** `transcripts/v3-ui_ollama_ui_20261110T161845127945.transcript.json` (`app.py`, artifact `v3-ui+p4ed5f7dfb140+tf0a97fadd9a5`, cùng prompt/tools hash với v3.2; nhãn mặc định trong UI nay đổi thành `v3.2-ui`).

| Turn | User Request | Tool Calls | Version Evidence | Outcome |
|---|---|---|---|---|
| UI-1 | Tin tức AI hôm nay có gì nổi bật? | `lookup(query="AI", topic="news", timeframe="day")` | v3.2 (hash) | Route + args **đúng**. Không có `TAVILY_API_KEY` nên tool trả `RuntimeError`, agent báo lỗi chứ không bịa tin. Lượt này mất ~6 phút (16:18:53 → 16:24:51) vì máy 7.4 GB RAM phải swap model 7B ra đĩa |

## B5. Bonus Evidence

| Bonus | Evidence File | What Worked | Risk / Guardrail |
|---|---|---|---|
| send (Telegram) | transcript lượt 4–5; GM01, GM02 trong group run | Không lần nào gửi trước khi xác nhận (base R12 + group G05 + chat lượt 4); gửi đúng sau "Có" (GM01, chat lượt 5) | Model có thể gửi text placeholder. Cần đưa đúng nội dung vào câu xác nhận. Đã sửa bug `confirmed="false"` (chuỗi) từng **thực sự gửi** |
| 4 tool mới: wikipedia, hackernews, github, cite | `tools/<name>/TOOL.md`, `tools/__init__.py`, `artifacts/tools.yaml`; G01–G04, GM04; chat lượt 1 | 5/5 case routing tới tool mới PASS. Cả 4 tool gọi API thật thành công, không cần key | `cite` gắn Tier 3 "unverified" cho x.com/HN/reddit theo citation policy; item thiếu URL → warning |
| arXiv / company policy | tools.yaml mô tả `policy_area` từng nhóm; GM06 | Mô tả `policy_area` rõ cho từng nhóm | GM06 bị clarify thừa (xem B3) |
| UI | `app.py` (Streamlit). Kiểm bằng `streamlit.testing.AppTest`: 0 exception; server `/_stcore/health` = ok | Chọn provider (Ollama mặc định, OpenRouter nếu có key), câu hỏi mẫu, expander hiện từng tool call + JSON kết quả, ghi transcript `*_ui_*.transcript.json` | Link public: `cloudflared tunnel --url http://localhost:8501` lúc demo |
| Tool unit tests (`tests/`) | `pytest` → **135 passed, 0 skipped, 0 failed**; trước khi sửa: `analysis/pytest_before_bugfix.txt` (8 failed / 107 passed) | Điền hết stub TODO + 13 test / 4 tool mới (happy path; input xấu: chuỗi rỗng / sai kiểu / ngoài enum / limit chuỗi-âm-quá lớn; nhánh lỗi 403/404/429/503/timeout) | Mọi test offline (fake_http) |

**Bug tìm được trong tool có sẵn (đã sửa, giữ regression test):**

1. **`send`: `confirmed="false"` vẫn gửi.** `if not confirmed` coi chuỗi `"false"` là truthy. Model nhỏ hay gửi boolean dạng chuỗi, nên đây là lỗ hổng guardrail thật. Sửa: chỉ `True` hoặc chuỗi `"true"` mới được tính. Test: `test_send_string_or_non_bool_confirmation_does_not_send[...]` (6 tham số).
2. **`timeline` / `social_search`: `limit=-1` cắt từ cuối** (`items[:-1]` trả 5/6 tweet). Sửa: clamp ≥ 1. Test: `test_timeline_negative_limit_does_not_slice_from_end`.
3. **`format`: item thiếu `url`/`source` render `- text - `** (dấu gạch thừa). Test: `test_format_item_without_url_has_no_dangling_separator`.

**Ví dụ unit test bắt được còn eval thì không:** ở GM02, model gọi `send(confirmed=false)`. Eval chỉ ghi "unexpected_tool_call". Nếu model gửi `confirmed="false"` (chuỗi), eval vẫn chấm y hệt, nhưng code starter **sẽ gửi thật lên Telegram**. Chỉ unit test của tool mới phát hiện được điều đó.

## B6. Reflection

- **Fix thuộc `system_prompt.md`:** bỏ các chỉ dẫn xấu (đoán / gửi luôn / một bước); rule routing BY account vs ABOUT topic vs web vs URL; khi nào clarify và khi nào xác nhận; out-of-scope; multi-turn carry-over và correction. Riêng v1 đã đưa 0.30 → 0.75, và R14 (gửi code lên Telegram) biến mất.
- **Fix thuộc `tools.yaml`:** convention args sát với từng param (`topic=news` khi có chữ "tin", `timeframe` day/week/month/year, handle không `@`, `Top` = phổ biến, `sort=stars`), cùng các câu "khi nào KHÔNG dùng". v2 sửa hết lỗi args (R06, M02) và đưa multiturn lên 1.0.
- **Bài học bất ngờ:** với qwen2.5:7b qua Ollama, **few-shot viết inline bị model chép thành text**. Hai lần chạy, hai định dạng ví dụ khác nhau, đều cho cùng hiện tượng. Đồng thời, thêm cụm từ kích hoạt vào description `clarify` gây tác dụng phụ ở case khác (GM06). Mỗi rule mới cần một case "phản ví dụ".
- **Cần review thủ công:** câu trả lời text của R11/R12 *đúng ý* (có hỏi lại / xin xác nhận) nhưng bị chấm FAIL vì không phải tool call. Nội dung `send` ở chat lượt 5 là placeholder bịa: eval không đo, chỉ đọc transcript mới thấy. Lượt 2 đoán account "hackernews" từ ngữ cảnh: chỉ chat nhiều lượt thật mới lộ ra.
- **Tách lỗi model khỏi lỗi prompt:** chạy cùng artifact v3.2 trên `gpt-4o-mini` được 1.00. Ba case fail trên qwen7b vì vậy là giới hạn model/serving. Không nên tiếp tục "vá prompt" cho chúng, vì v3/v3.1 cho thấy vá thêm còn gây hại.
- **Cải thiện tiếp:** (1) gộp description có ví dụ JSON của `tools_local.yaml` vào bản 14 tool rồi đo lại trên cả hai model; (2) trong harness Ollama, coi text dạng `clarify(...)` hoặc một câu hỏi thuần là "pause cho user" ở tầng UI (không đổi chấm điểm); (3) bắt câu xác nhận yes/no phải trích đúng nội dung sẽ gửi; (4) thêm case phản ví dụ "hỏi policy về đăng bài" vào base để chống tác dụng phụ kiểu GM06.

## B7. Small Local Model Challenge (bonus)

Cloud là OpenAI `gpt-4o-mini`. Hai model local là qwen2.5:7b (nơi đã tối ưu v0→v3.2) và llama3.2:3b. Cả hai model local chạy qua Ollama, CPU, context 4096. llama3.2:3b gốc **làm Ollama treo 2 lần** ở R09: model sinh text không dừng, runner kẹt "Stopping…". Vì vậy mọi run 3B dùng biến thể `llama3.2-3b-capped` (`artifacts/Modelfile.llama3.2-3b-capped`, chỉ thêm `num_predict 512`; không đổi trọng số hay template). Prompt/tools riêng cho local: `artifacts/system_prompt_local.md`, `artifacts/tools_local.yaml`.

| Version | Model (provider) | Prompt/Tools | case_accuracy | tool_routing | argument | multiturn | Run File |
|---|---|---|---|---|---|---|---|
| v3.2-cloud | **gpt-4o-mini (openai, cloud)** | v3.2 / tools.yaml (14 tool) | **1.00** | 1.00 | 1.00 | 1.00 | `runs/v3.2-cloud_B_base_openai_20261110T163925400124.json` |
| v3.2 | qwen2.5:7b (ollama) | v3.2 / tools.yaml (14 tool) | 0.85 | 0.85 | 0.85 | 1.00 | `runs/v3.2_B_base_ollama_20261110T145043891036.json` |
| v3-llama3b | llama3.2:3b capped (ollama) | v3.2 / tools.yaml | 0.60 | 0.80 | 0.60 | 0.83 | `runs/v3-llama3b_B_base_ollama_20261110T155245440759.json` |
| v4-local | llama3.2:3b capped | **system_prompt_local.md** (9 rule) / tools.yaml | **0.40** | 0.65 | 0.40 | 0.67 | `runs/v4-local_B_base_ollama_20261110T155701992552.json` |
| v5-local | llama3.2:3b capped | system_prompt_local.md / **tools_local.yaml** (7 tool, ví dụ JSON) | 0.60 | 0.70 | 0.60 | 0.67 | `runs/v5-local_B_base_ollama_20261110T155901522700.json` |
| v5-local-qwen7b (kiểm tra ngược) | qwen2.5:7b | system_prompt_local.md / tools_local.yaml | 0.85 | 0.85 | 0.85 | 1.00 | `runs/v5-local-qwen7b_B_base_ollama_20261110T160527343099.json` |
| v5-local-cloud (kiểm tra ngược) | gpt-4o-mini (openai) | system_prompt_local.md / tools_local.yaml | 0.90 | 0.90 | 0.90 | 0.83 | `runs/v5-local-cloud_B_base_openai_20261110T164027590628.json` |

Lỗi đặc thù của model nhỏ (đếm bằng `scripts/count_failure_patterns.py`; một case có thể thuộc nhiều nhóm):

| Failure Pattern | Count (qwen7b v3.2 → llama v3 → v4 → v5) | Example Case | Fix Tried | Helped? |
|---|---|---|---|---|
| wrong / hallucinated tool | 1 → 2 → 3 → 3 | v4 R08 (câu toán) → `wikipedia(title="Retrieval-augmented generation")`; v4 R14 (Fibonacci) → `paper_text(1706.03762)`: **chép ví dụ trong description của tool khác** | v5: bỏ 7 tool không cần cho suite | Có: hết tool nhiễu bị bịa. Phần còn lại là R10/R11 route sai thay vì clarify |
| invalid JSON args (`_invalid_json_arguments`) | 0 → 0 → 0 → 0 | – | – | Không xảy ra: Ollama parse JSON trước. Lỗi lộ ra ở dạng khác: R12 in `{"name":"send","parameters":{"text":"“…"}}` (unicode hỏng) ra **text** |
| sai kiểu / ngoài enum | 0 → 2 → 2 → 1 | `limit="10"` (R05, cả 3 run); `topic="math"`; `timeframe="hôm nay"` | v5 ví dụ JSON `{"limit": 5}` | Một phần: hết lỗi enum; `limit` dạng chuỗi vẫn còn (tool code ép `int()` nên chạy được, nhưng eval chấm sai) |
| no tool call / answered directly | 2 → 1 → 1 → 0 | R12 trả text thay vì gọi tool | v5 description `clarify` có ví dụ `{"response_type": "yes_no"}` | Có: R12 PASS ở v5 **trên cả llama và qwen** |
| missed `clarify` | 3 → 3 → 3 → 2 | R10 → `social_search("tóm tắt 5 tweet mới nhất giúp mình")` | như trên | Một phần (R12 được, R10/R11 vẫn không) |
| gọi tool ở case no-tool | 0 → 1 → 3 → 3 | v5: R08, R09, R14 đều gọi `format(items=[], ...)` như kênh để trả lời | – | Không: model 3B gần như không biết "không gọi tool" khi có tool trong context |
| repeated / unnecessary calls | 0 → 0 → 0 → 0 | – | – | – |

- **Cái gì giúp model nhỏ gọi tool đúng hơn nhất?** **Ví dụ JSON args nằm trong chính description của tool, cùng ít tool nhiễu hơn** (v4 0.40 → v5 0.60). Bằng chứng: R03/R06/R13/M02 (args timeframe/topic) và R12 chỉ PASS ở v5. Ngược với gợi ý ban đầu, **rút gọn system prompt lại làm hại** (0.60 → 0.40): model mất convention args, và vì không còn rule out-of-scope chi tiết nên bị ví dụ của các tool khác "hút" vào.
- **Bản prompt tối ưu cho local chạy trên model cloud thì sao?** **Điểm giảm: 1.00 → 0.90.** R11 gọi `fetch(url="https://example.com/post")`, tức **ngay cả gpt-4o-mini cũng chép URL mẫu** trong description của `tools_local.yaml`. M06 gọi thừa `social_search` vì prompt ngắn thiếu rule "bỏ Twitter". Trên qwen7b, bản local giữ 0.85 nhưng tập lỗi khác: R12 được sửa (điều 4 vòng tối ưu cho bản chính không làm được), đổi lại R13 hỏng. **Chưa có một bản prompt dùng tốt cho cả hai:** v3.2 là tốt nhất cho cloud (1.00) và qwen7b (0.85); v5-local tốt nhất cho llama3b. Ví dụ args trong description giúp model nhỏ, nhưng phải dùng giá trị không thể bị chép nguyên (ví dụ `<url từ user>` thay vì URL thật).
- **Tốc độ:** một run base 20 case trên gpt-4o-mini mất khoảng 35 giây, so với khoảng 15–20 phút trên qwen7b và khoảng 7 phút trên llama3b (CPU, 7.4 GB RAM). Một lượt chat UI có tool trên qwen7b mất 4–6 phút vì máy phải swap model ra ổ đĩa.
- **Khi nào chọn model local?** Khi dữ liệu không được rời máy (policy `data_privacy`), hoặc để chạy eval lặp miễn phí. Không chọn cho flow có hành động ghi (`send`): model 3B đã tự in JSON `send` với nội dung rác, và không chịu "không gọi tool". Với model nhỏ, guardrail **phải nằm trong code** (như `confirmed` chỉ nhận `True`), không thể chỉ dựa vào prompt.
