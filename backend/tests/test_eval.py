from __future__ import annotations

from pathlib import Path

from svarsa.eval import dataset as eval_dataset
from svarsa.eval import runner as eval_runner


def test_eval_runs_on_sample_dataset() -> None:
    samples = Path(__file__).parent.parent / "eval" / "sample.jsonl"
    dataset = eval_dataset.load_dataset(samples)
    assert len(dataset) >= 5
    report = eval_runner.run(dataset)
    assert report.total == len(dataset)
    assert report.intent_accuracy >= 0.6  # baseline; tighter threshold lives in CI


def test_format_slack_digest_includes_metrics() -> None:
    samples = Path(__file__).parent.parent / "eval" / "sample.jsonl"
    dataset = eval_dataset.load_dataset(samples)
    report = eval_runner.run(dataset)
    text = eval_runner.format_slack_digest(report)
    assert "Intent accuracy" in text
    assert "Emergency false negatives" in text
