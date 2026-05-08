from __future__ import annotations

from sqlmodel import Session

from svarsa.agents.post_call_summary import summarize_call, summarize_transcript
from svarsa.core.ids import new_id
from svarsa.db.seed import DEMO_FIRMA_ID, seed_dev_data
from svarsa.db.session import get_engine, init_db
from svarsa.models import Call, CallStatus, Intent, TranscriptRole, TranscriptSegment


def test_heuristic_summarizer_on_emergency_keywords() -> None:
    summary = summarize_transcript(
        "[0s caller] Hej det är vattenläcka under diskbänken det rinner överallt"
    )
    assert "läcka" in summary.short_sv.lower() or "vatten" in summary.short_sv.lower()
    assert summary.owner_action_required is False


def test_heuristic_summarizer_on_offert_keywords() -> None:
    summary = summarize_transcript(
        "[0s caller] Jag vill ha offert på en badrumsrenovering"
    )
    assert "offert" in summary.short_sv.lower()
    assert summary.owner_action_required is True


def test_summarize_call_writes_summary_to_db() -> None:
    init_db()
    seed_dev_data()
    with Session(get_engine()) as s:
        call = Call(
            id=new_id(),
            firma_id=DEMO_FIRMA_ID,
            status=CallStatus.COMPLETED,
        )
        s.add(call)
        s.flush()
        s.add(
            TranscriptSegment(
                call_id=call.id,
                role=TranscriptRole.CALLER,
                text="Vattenläcka, det rinner",
                ts_ms_offset=0,
            )
        )
        s.commit()
        cid = call.id

    summary = summarize_call(cid)
    assert summary is not None

    with Session(get_engine()) as s2:
        reloaded = s2.get(Call, cid)
        assert reloaded is not None
        assert reloaded.summary is not None
        assert reloaded.intent is Intent.AKUT
