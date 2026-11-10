"""Streamlit UI for the Research Agent.

Run from starter_v0/:
    streamlit run app.py
Then (optional) expose it:  cloudflared tunnel --url http://localhost:8501

Re-uses chat.py's multi-round tool loop, so behaviour and transcripts match the CLI.
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from chat import run_model_tool_loop, safe_slug, trim_history, write_transcript, now_iso
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
load_lab_env(ROOT)

PROVIDER_KEYS = {
    "openrouter": "OPENROUTER_API_KEY",
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "gemini": "GEMINI_API_KEY",
}
EXAMPLES = [
    "Tin tức AI hôm nay có gì nổi bật?",
    "Lấy 3 tweet mới nhất của Andrej Karpathy",
    "Mọi người đang bàn gì về GPT-5 trên Twitter?",
    "Trên Hacker News đang nói gì về AI agents?",
    "Retrieval-augmented generation là gì? Tra Wikipedia giúp mình",
    "Repo GitHub nhiều sao nhất về LLM agent framework?",
    "Theo policy công ty, đăng bản tin lên Telegram có cần xác nhận không?",
    "Đăng bản tin này lên Telegram giúp mình",
]


def available_providers() -> list[str]:
    providers = [name for name, key in PROVIDER_KEYS.items() if os.getenv(key)]
    return providers + ["ollama"]


st.set_page_config(page_title="Research Agent", page_icon="🔎", layout="wide")

with st.sidebar:
    st.header("⚙️ Cấu hình")
    provider_name = st.selectbox("Provider", available_providers())
    default_model = {"ollama": os.getenv("OLLAMA_MODEL", "qwen2.5:7b"), "openrouter": "openai/gpt-4o-mini"}.get(provider_name, "")
    model = st.text_input("Model", value=default_model) or None
    version = st.text_input("Version label", value="v3-ui")
    max_rounds = st.slider("Max tool rounds", 1, 6, 4)
    st.caption("Prompt: artifacts/system_prompt.md · Tools: artifacts/tools.yaml")

    declarations = load_tool_declarations(ARTIFACTS_DIR / "tools.yaml")
    with st.expander(f"🧰 {len(declarations)} tools", expanded=False):
        for item in declarations:
            st.markdown(f"**`{item['name']}`** — {item.get('description', '').split('.')[0]}.")

    if st.button("🧹 Cuộc hội thoại mới"):
        for key in ("history", "messages", "transcript", "transcript_path"):
            st.session_state.pop(key, None)
        st.rerun()

    st.subheader("💡 Câu hỏi mẫu")
    for example in EXAMPLES:
        if st.button(example, key=f"ex_{example}", use_container_width=True):
            st.session_state["pending_prompt"] = example

st.title("🔎 Research Agent")
st.caption("Tìm tin theo chủ đề / theo tài khoản, đọc URL, tra Wikipedia / Hacker News / GitHub / arXiv / policy nội bộ, "
           "trích dẫn nguồn, và chỉ gửi Telegram khi bạn xác nhận.")

system_prompt_path = ARTIFACTS_DIR / "system_prompt.md"
tools_path = ARTIFACTS_DIR / "tools.yaml"
artifact_version = build_artifact_version(version, system_prompt_path, tools_path)

if "transcript" not in st.session_state:
    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = "_".join([safe_slug(version), safe_slug(provider_name), "ui", timestamp])
    st.session_state["transcript_path"] = ROOT / "transcripts" / f"{transcript_id}.transcript.json"
    st.session_state["transcript"] = {
        "transcript_id": transcript_id,
        **artifact_version_dict(artifact_version),
        "provider": provider_name,
        "model": model,
        "system_prompt": str(system_prompt_path),
        "tools": str(tools_path),
        "history_window": 5,
        "max_tool_rounds": max_rounds,
        "source": "streamlit_ui",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }
    st.session_state["history"] = []
    st.session_state["messages"] = []


def render_rounds(rounds: list[dict[str, Any]]) -> None:
    for rnd in rounds:
        for event in rnd.get("tool_results", []):
            result = event.get("result", {})
            icon = "⚠️" if isinstance(result, dict) and result.get("error") else "🔧"
            with st.expander(f"{icon} {event['tool']}({json.dumps(event.get('args', {}), ensure_ascii=False)[:120]})"):
                st.json(result, expanded=False)


for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        if message.get("rounds"):
            render_rounds(message["rounds"])
        st.markdown(message["content"])

prompt = st.chat_input("Hỏi agent…") or st.session_state.pop("pending_prompt", None)
if prompt:
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    system_prompt = system_prompt_path.read_text(encoding="utf-8")
    tools = to_openai_tools(load_tool_declarations(tools_path))
    history = st.session_state["history"]
    messages = [{"role": "system", "content": system_prompt}, *trim_history(history, 5), {"role": "user", "content": prompt}]
    transcript = st.session_state["transcript"]
    turn_record: dict[str, Any] = {
        "turn_index": len(transcript["turns"]) + 1,
        "started_at": now_iso(),
        "user": prompt,
        "status": "started",
    }

    with st.chat_message("assistant"):
        with st.spinner("Agent đang suy nghĩ / gọi tool…"):
            try:
                result = run_model_tool_loop(
                    provider=make_provider(provider_name),
                    messages=messages,
                    tools=tools,
                    model=model,
                    max_tool_rounds=max_rounds,
                )
                turn_record.update(result)
                answer = result["assistant_text"] or "(không có nội dung)"
                if result["status"] == "waiting_for_user":
                    answer = f"❓ {answer}"
                history += [{"role": "user", "content": prompt}, {"role": "assistant", "content": answer}]
            except Exception as exc:  # show the error, keep the UI alive
                result = {"rounds": []}
                answer = f"**Lỗi provider:** `{type(exc).__name__}: {exc}`"
                turn_record.update({"status": "provider_error", "error": f"{type(exc).__name__}: {exc}"})
        render_rounds(result.get("rounds", []))
        st.markdown(answer)

    st.session_state["messages"].append({"role": "assistant", "content": answer, "rounds": result.get("rounds", [])})
    turn_record["ended_at"] = now_iso()
    transcript["turns"].append(turn_record)
    write_transcript(st.session_state["transcript_path"], transcript)
    st.caption(f"Transcript: `{st.session_state['transcript_path'].relative_to(ROOT)}` · {artifact_version.artifact_version}")
