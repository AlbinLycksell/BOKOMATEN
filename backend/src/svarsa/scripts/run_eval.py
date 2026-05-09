"""Run the eval pipeline + post a Slack digest. Used by .github/workflows/eval-weekly.yml."""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from pathlib import Path
from typing import Sequence

from svarsa.eval import dataset as eval_dataset
from svarsa.eval import runner as eval_runner


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    dataset = eval_dataset.load_dataset(args.dataset)
    report = eval_runner.run(dataset)

    digest = eval_runner.format_slack_digest(report)
    print(digest)

    if args.slack_webhook:
        try:
            req = urllib.request.Request(
                args.slack_webhook,
                data=json.dumps({"text": digest}).encode(),
                headers={"Content-Type": "application/json"},
            )
            urllib.request.urlopen(req, timeout=10)
        except Exception as exc:  # noqa: BLE001
            print(f"slack post failed: {exc}", file=sys.stderr)

    if args.fail_below and report.intent_accuracy < args.fail_below:
        print(
            f"FAIL: intent accuracy {report.intent_accuracy:.1%} below threshold {args.fail_below:.1%}",
            file=sys.stderr,
        )
        return 1

    if args.fail_emergency_fn and report.emergency_false_negatives > args.fail_emergency_fn:
        print(
            f"FAIL: {report.emergency_false_negatives} emergency false negatives "
            f"exceeds {args.fail_emergency_fn}",
            file=sys.stderr,
        )
        return 1

    return 0


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Svarsa eval runner")
    p.add_argument("dataset", type=Path)
    p.add_argument(
        "--slack-webhook",
        default=os.environ.get("SVARSA_EVAL_SLACK_WEBHOOK", ""),
    )
    p.add_argument("--fail-below", type=float, default=0.85)
    p.add_argument("--fail-emergency-fn", type=int, default=0)
    return p.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(main())
