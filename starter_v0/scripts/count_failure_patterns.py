"""Count small-model failure patterns in run JSON files (for REPORT B7).

    python scripts/count_failure_patterns.py runs/v3.2_B_base_*.json runs/v3-llama3b_*.json ...
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

DECLARED_CORE = None


def patterns(run: dict) -> dict[str, list[str]]:
    from tools import load_tool_declarations  # noqa: E402

    declared = {t["name"] for t in load_tool_declarations(Path(run["tools"]))}
    out: dict[str, list[str]] = {k: [] for k in [
        "hallucinated_or_wrong_tool", "invalid_json_args", "arg_type_or_enum_error",
        "no_tool_call_text", "missed_clarify", "tool_on_no_tool_case", "repeated_calls"]}
    for item in run["results"]:
        res, expect, cid = item["result"], item["expect"], item["id"]
        calls = res["actual_tool_calls"]
        if res["passed"]:
            continue
        names = [c["name"] for c in calls]
        expected = {c["name"] for c in expect.get("tool_calls", [])}
        if any(n not in declared for n in names) or (expected and names and not (set(names) & expected)):
            out["hallucinated_or_wrong_tool"].append(cid)
        if any("_invalid_json_arguments" in c["args"] for c in calls):
            out["invalid_json_args"].append(cid)
        if any(isinstance(v, str) and v.isdigit() for c in calls for v in c["args"].values()) or \
           any(c["args"].get("topic") not in (None, "news", "general") or
               c["args"].get("timeframe") not in (None, "day", "week", "month", "year") for c in calls):
            out["arg_type_or_enum_error"].append(cid)
        if not calls and not expect.get("no_tool"):
            out["no_tool_call_text"].append(cid)
        if "clarify" in expected and "clarify" not in names:
            out["missed_clarify"].append(cid)
        if expect.get("no_tool") and calls:
            out["tool_on_no_tool_case"].append(cid)
        if len(names) != len(set(names)):
            out["repeated_calls"].append(cid)
    return out


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    for path in sys.argv[1:]:
        run = json.loads(Path(path).read_text(encoding="utf-8"))
        print(f"\n{run['version']} ({run['model']}) case_accuracy={run['summary']['case_accuracy']}")
        for name, ids in patterns(run).items():
            print(f"  {name:28} {len(ids):2}  {', '.join(ids)}")


if __name__ == "__main__":
    main()
