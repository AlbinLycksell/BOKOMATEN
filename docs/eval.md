# Eval pipeline

Weekly automated eval over a labeled Swedish call dataset reports triage accuracy, severity match, and emergency false-negative rate. CI fails the run if intent accuracy drops below 85% or any emergency is missed (PRD §11.2 / §3.1).

## Dataset format

JSONL, one labeled call per row:

```jsonl
{"call_id":"...","transcript":[{"role":"caller","text":"..."},{"role":"ai","text":"..."}],"expected_intent":"akut","expected_severity":"high","expected_tools":["lookup_customer","triage_emergency","escalate_to_owner"],"expected_recommended_action":"escalate_now","trade":"vvs","notes":"..."}
```

Storage: `gs://switchboard-eval-dataset/v1/calls.jsonl`. Annotated by Founders + a Swedish-speaking VA. Sample shipped with the foundation: `backend/eval/sample.jsonl`.

## Running locally

```bash
cd backend
uv run run-eval eval/sample.jsonl
uv run run-eval eval/sample.jsonl --fail-below 0.85 --fail-emergency-fn 0
uv run run-eval eval/sample.jsonl --slack-webhook "$SLACK_WEBHOOK"
```

## Weekly Slack digest

GitHub Actions workflow `eval-weekly.yml` runs Sunday 06:00 UTC. Posts a summary to `#switchboard-eval`:

```
*Switchboard eval — n=523*
  Intent accuracy: 91.2%
  Severity accuracy: 88.7%
  Emergency false negatives: 0/47
  Distribution:
    bokning: 198
    offertforfragan: 142
    akut: 47
    befintlig_kund_fraga: 88
    ovrigt: 48
  Failures (3, first 5):
    • call-024: intent=offertforfragan, severity=low
    • …
```

## Adding a labeled call

1. Pull a real call from the dashboard or pilot recording.
2. Annotate with `expected_intent` (5 enum), `expected_severity` (4 enum + null), `expected_tools` (list of canonical names), `expected_recommended_action`, `trade`, free-text `notes`.
3. Append to the dataset JSONL. Re-run the eval to ensure your new row classifies sensibly.

## Investigating regressions

When CI fails:

1. Open the workflow log → find the "Failures" section.
2. Each failing call's id maps back to the dashboard (or to the eval-recordings bucket if not from a real call).
3. Replay the transcript through the bridge in dev:
   ```bash
   uv run python -m switchboard.eval.runner_cli --replay <call-id>
   ```
   (Helper to be added if needed; for MVP the failure list + transcript inspection is sufficient.)
4. If the failure is a model regression, check recent prompt changes (`bridge/system_prompt.py`) or persona corrections (`Firma.settings.persona_corrections`).
5. If it's a triage rule gap, update `services/triage_service.py` and add the failing call to the dataset.

## Per-tool latency SLO

A separate metric stream from Eval — but related. PRD §8.4 budget: p95 < 200 ms per tool.

`GET /api/metrics/tools/latency?hours=24` returns per-tool stats over the last N hours. The dashboard pings this hourly; SLA breaches surface as Sentry alerts via `services.sla_service.detect_breaches`.

Source: `backend/src/switchboard/services/sla_service.py`, `backend/src/switchboard/api/routes_metrics.py`.
