"""Append one row to artifacts/version_log.csv using hashes + metrics taken from a run JSON.

    python scripts/log_version.py runs/v1_....json --changed system_prompt.md \
        --reason "..." --hypothesis "..." --before 0.30
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOG = ROOT / "artifacts" / "version_log.csv"
FIELDS = ["version", "author", "changed_artifact", "artifact_version", "prompt_hash", "tools_hash",
          "reason", "hypothesis", "metric_before", "metric_after", "run_file"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("run", type=Path)
    parser.add_argument("--changed", required=True)
    parser.add_argument("--reason", required=True)
    parser.add_argument("--hypothesis", required=True)
    parser.add_argument("--before", default="")
    parser.add_argument("--author", default="Hoang")
    args = parser.parse_args()

    run = json.loads(args.run.read_text(encoding="utf-8"))
    s = run["summary"]
    metric_after = (f"case={s['case_accuracy']};routing={s.get('tool_routing_accuracy')};"
                    f"args={s.get('argument_accuracy')};multiturn={s.get('multiturn_accuracy')}")
    run_file = args.run.resolve().relative_to(ROOT).as_posix()
    row = {
        "version": run["version"], "author": args.author, "changed_artifact": args.changed,
        "artifact_version": run["artifact_version"], "prompt_hash": run["prompt_hash"][:12],
        "tools_hash": run["tools_hash"][:12], "reason": f"[{run['provider']}:{run['model']}|{run['suite']}] {args.reason}",
        "hypothesis": args.hypothesis, "metric_before": args.before, "metric_after": metric_after, "run_file": run_file,
    }
    with LOG.open("a", encoding="utf-8", newline="") as fh:
        csv.DictWriter(fh, fieldnames=FIELDS).writerow(row)
    print(f"logged {row['version']}: {metric_after}")


if __name__ == "__main__":
    main()
