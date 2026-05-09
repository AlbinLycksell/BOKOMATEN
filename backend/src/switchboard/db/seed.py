"""Dev seed data — deterministic fixtures used by the dashboard demo."""

from __future__ import annotations

from datetime import timedelta

from sqlmodel import Session, select

from switchboard.core.constants import DEFAULT_GEMINI_VOICE, DEMO_FIRMA_ID
from switchboard.core.logging import get_logger
from switchboard.core.time import utcnow
from switchboard.db.session import get_engine
from switchboard.models import (
    Call,
    CallStatus,
    Customer,
    CustomerType,
    Firma,
    FirmaSettings,
    Intent,
    PhoneNumber,
    PhoneNumberProvider,
    PhoneNumberStatus,
    Plan,
    Severity,
    ToolInvocation,
    ToolName,
    Trade,
    TranscriptRole,
    TranscriptSegment,
    User,
    UserRole,
)
from switchboard.models.enums import EmergencyIndicator

log = get_logger("switchboard.seed")


def seed_dev_data() -> None:
    engine = get_engine()
    with Session(engine) as s:
        existing = s.exec(select(Firma).where(Firma.id == DEMO_FIRMA_ID)).first()
        if existing is not None:
            log.info("seed.skipped", reason="already-seeded")
            return

        firma = Firma(
            id=DEMO_FIRMA_ID,
            name="Anderssons VVS AB",
            org_number="556789-1234",
            trade=Trade.VVS,
            plan=Plan.PROFESSIONAL,
            locality="Bromma",
            settings=FirmaSettings(
                greeting_text=(
                    "Hej, du har kommit till Anderssons VVS, "
                    "jag är deras digitala assistent. Hur kan jag hjälpa dig?"
                ),
                voice=DEFAULT_GEMINI_VOICE,
            ).model_dump(),
        )
        s.add(firma)

        s.add_all(
            [
                User(firma_id=DEMO_FIRMA_ID, role=UserRole.OWNER.value, name="Magnus Andersson",
                     phone="+46708111222", email="magnus@anderssonsvvs.se", on_call=True),
                User(firma_id=DEMO_FIRMA_ID, role=UserRole.BACK_OFFICE.value, name="Lena Andersson",
                     phone="+46708111223", email="lena@anderssonsvvs.se"),
                User(firma_id=DEMO_FIRMA_ID, role=UserRole.TECHNICIAN.value, name="Alex Berg",
                     phone="+46708111224", email="alex@anderssonsvvs.se", on_call=False),
            ]
        )
        s.add(
            PhoneNumber(
                firma_id=DEMO_FIRMA_ID,
                e164="+46812345678",
                provider=PhoneNumberProvider.ELKS.value,
                status=PhoneNumberStatus.ACTIVE.value,
            )
        )

        inger = Customer(
            firma_id=DEMO_FIRMA_ID,
            type=CustomerType.PRIVATE,
            name="Inger Svensson",
            phone="+46708557777",
            email="inger.svensson@example.se",
            address={"street": "Storgatan 14", "apartment": "lgh 3",
                     "postal_code": "168 31", "city": "Bromma"},
            notes_summary="Befintlig kund från 2024 — vattenkran-byte.",
        )
        karim = Customer(
            firma_id=DEMO_FIRMA_ID,
            type=CustomerType.COMPANY,
            name="Karim El-Sayed (Brf Vasaliljan)",
            phone="+46708558888",
            org_number="769612-3456",
            email="karim@vasaliljan.se",
            address={"street": "Vasagatan 8", "city": "Stockholm"},
            notes_summary="OVK-besiktningar, återkommande.",
        )
        ny = Customer(
            firma_id=DEMO_FIRMA_ID,
            type=CustomerType.PRIVATE,
            name="Pelle Lundgren",
            phone="+46708559999",
            email=None,
            address={"street": "Hökarängsplan 4", "city": "Stockholm"},
            notes_summary="Ny lead — badrumsrenovering offert.",
        )
        s.add_all([inger, karim, ny])
        s.flush()

        now = utcnow()

        akut = Call(
            firma_id=DEMO_FIRMA_ID,
            customer_id=inger.id,
            caller_phone=inger.phone,
            started_at=now - timedelta(hours=2, minutes=12),
            ended_at=now - timedelta(hours=2, minutes=11, seconds=22),
            intent=Intent.AKUT,
            severity=Severity.HIGH,
            status=CallStatus.HANDLED,
            summary={
                "short_sv": "Vattenläcka under diskbänken — Magnus eskalerad, ringer inom 15 min.",
                "long_sv": (
                    "Inger ringde om vattenläcka under diskbänken. "
                    "Hon stängde av huvudkranen. AI:n eskalerade till Magnus."
                ),
                "next_action_sv": "Magnus ringer Inger, kör akutbesök.",
                "owner_action_required": False,
            },
            billing_seconds=38,
        )
        s.add(akut)
        s.flush()
        s.add_all(
            [
                TranscriptSegment(call_id=akut.id, role=TranscriptRole.AI, ts_ms_offset=0,
                                  text="Hej, du har kommit till Anderssons VVS, jag är deras digitala assistent. Hur kan jag hjälpa dig?"),
                TranscriptSegment(call_id=akut.id, role=TranscriptRole.CALLER, ts_ms_offset=4200,
                                  text="Hej, jag har en vattenläcka under diskbänken, det rinner ner på golvet."),
                TranscriptSegment(call_id=akut.id, role=TranscriptRole.AI, ts_ms_offset=8500,
                                  text="Det låter akut. Är det mycket vatten — har du behövt stänga av vattnet?"),
                TranscriptSegment(call_id=akut.id, role=TranscriptRole.CALLER, ts_ms_offset=12200,
                                  text="Ja, jag stängde av huvudkranen. Men det är ändå vått."),
                TranscriptSegment(call_id=akut.id, role=TranscriptRole.AI, ts_ms_offset=15800,
                                  text="Bra att du stängt av. Vad är din adress?"),
                TranscriptSegment(call_id=akut.id, role=TranscriptRole.CALLER, ts_ms_offset=19000,
                                  text="Storgatan 14, lägenhet 3, Bromma."),
                TranscriptSegment(call_id=akut.id, role=TranscriptRole.AI, ts_ms_offset=22500,
                                  text="Tack Inger. Magnus är på ett jobb just nu men jag skickar honom ditt ärende direkt. Han ringer upp inom 15 minuter."),
            ]
        )
        s.add_all(
            [
                ToolInvocation(firma_id=DEMO_FIRMA_ID, call_id=akut.id, name=ToolName.LOOKUP_CUSTOMER.value,
                               args={"phone_number": inger.phone},
                               result={"found": True, "customer_id": inger.id, "name": inger.name},
                               latency_ms=42),
                ToolInvocation(firma_id=DEMO_FIRMA_ID, call_id=akut.id, name=ToolName.TRIAGE_EMERGENCY.value,
                               args={"problem_description": "vattenläcka, rinner",
                                     "trade": Trade.VVS.value,
                                     "indicators_present": [
                                         EmergencyIndicator.LACKA.value,
                                         EmergencyIndicator.RINNER.value,
                                     ]},
                               result={"is_emergency": True, "severity": Severity.HIGH.value,
                                       "recommended_action": "escalate_now"},
                               latency_ms=12),
                ToolInvocation(firma_id=DEMO_FIRMA_ID, call_id=akut.id, name=ToolName.ESCALATE_TO_OWNER.value,
                               args={"severity": Severity.HIGH.value, "reason": "vattenläcka",
                                     "customer_phone": inger.phone},
                               result={"escalation_id": "01J", "contacted": ["+46708111222"]},
                               latency_ms=180),
            ]
        )

        offert = Call(
            firma_id=DEMO_FIRMA_ID,
            customer_id=karim.id,
            caller_phone=karim.phone,
            started_at=now - timedelta(hours=4, minutes=2),
            ended_at=now - timedelta(hours=4, minutes=1, seconds=18),
            intent=Intent.BOKNING,
            severity=None,
            status=CallStatus.HANDLED,
            summary={
                "short_sv": "Karim på Brf Vasaliljan — bokade fyra OVK den 22 maj.",
                "long_sv": "Återkommande B2B-kund. Bokade in fyra adresser, hela dagen.",
                "next_action_sv": "Bekräftelse skickad. Inget mer.",
                "owner_action_required": False,
            },
            billing_seconds=62,
        )
        s.add(offert)

        ny_call = Call(
            firma_id=DEMO_FIRMA_ID,
            customer_id=ny.id,
            caller_phone=ny.phone,
            started_at=now - timedelta(minutes=18),
            ended_at=now - timedelta(minutes=17, seconds=4),
            intent=Intent.OFFERT,
            severity=None,
            status=CallStatus.NEEDS_FOLLOWUP,
            summary={
                "short_sv": "Pelle vill ha offert på badrumsrenovering — foton skickade.",
                "long_sv": "Ny lead. Hökarängsplan 4. Bad ~5 m². Önskar besök för uppmätning.",
                "next_action_sv": "Magnus ringer åter, bokar uppmätning denna vecka.",
                "owner_action_required": True,
            },
            billing_seconds=64,
        )
        s.add(ny_call)

        s.commit()
        log.info("seed.completed", firma=firma.name, calls=3)
