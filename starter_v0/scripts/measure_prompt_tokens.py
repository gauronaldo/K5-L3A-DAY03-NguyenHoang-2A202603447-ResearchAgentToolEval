"""Measure how many prompt tokens system_prompt + tools.yaml cost on a local Ollama model.

Ollama defaults to a 4096-token context. If system prompt + tool schemas exceed it, the
prompt is truncated silently and routing quality collapses, so check before each local run:

    python scripts/measure_prompt_tokens.py --model qwen2.5:7b
    python scripts/measure_prompt_tokens.py --system-prompt artifacts/system_prompt_local.md --tools artifacts/tools_local.yaml
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools import load_tool_declarations, to_openai_tools  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=os.getenv("OLLAMA_MODEL", "qwen2.5:7b"))
    parser.add_argument("--system-prompt", type=Path, default=ROOT / "artifacts" / "system_prompt.md")
    parser.add_argument("--tools", type=Path, default=ROOT / "artifacts" / "tools.yaml")
    parser.add_argument("--host", default="http://localhost:11434")
    args = parser.parse_args()

    body = {
        "model": args.model,
        "messages": [
            {"role": "system", "content": args.system_prompt.read_text(encoding="utf-8")},
            {"role": "user", "content": "Tweet mới nhất của Sam Altman là gì?"},
        ],
        "tools": to_openai_tools(load_tool_declarations(args.tools)),
        "stream": False,
        "options": {"num_predict": 1, "num_ctx": 32768},
    }
    data = requests.post(f"{args.host}/api/chat", json=body, timeout=900).json()
    print(f"model={args.model} prompt_tokens={data.get('prompt_eval_count')} "
          f"(prompt={args.system_prompt.name}, tools={args.tools.name})")


if __name__ == "__main__":
    main()
