"""Print failing cases of a run JSON compactly: expected vs actual tool calls.

    python scripts/show_failures.py runs/v0_B_base_ollama_*.json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    parser.add_argument("--all", action="store_true", help="also show passing cases")
    args = parser.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    run = json.loads(args.run.read_text(encoding="utf-8"))
    print(f"{run['version']} {run['model']} {run['summary']}")
    for item in run["results"]:
        res = item["result"]
        if res["passed"] and not args.all:
            continue
        expected = item["expect"].get("tool_calls") or "NO_TOOL"
        actual = [f"{c['name']}({json.dumps(c['args'], ensure_ascii=False)})" for c in res["actual_tool_calls"]]
        print(f"\n[{'PASS' if res['passed'] else 'FAIL'}] {item['id']} ({res.get('case_failure_type')} / {res.get('observed_mismatch')})")
        print(f"  expected: {json.dumps(expected, ensure_ascii=False)}")
        print(f"  actual:   {actual or (res.get('actual_text') or '')[:160]!r}")
        if res.get("failures"):
            print(f"  failures: {res['failures']}")


if __name__ == "__main__":
    main()
