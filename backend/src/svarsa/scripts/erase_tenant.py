"""GDPR Art. 17 tenant erasure — single-shot CLI.

Deletes every tenant-scoped row, the per-firma GCS bucket, and the
per-firma KMS key version. Audit-logs the erasure as the *last* operation
on the firma's data so there's a forensic trail before the row itself
goes away.

Usage:
  uv run erase-tenant FIRMA_ID
  uv run erase-tenant FIRMA_ID --dry-run
  uv run erase-tenant FIRMA_ID --operator alice@svarsa.se
"""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from sqlalchemy import text
from sqlmodel import Session, select

from svarsa.core.config import get_settings
from svarsa.core.logging import get_logger
from svarsa.core.tenant import firma_context
from svarsa.db.session import get_engine
from svarsa.integrations.storage import make_storage
from svarsa.models import Firma
from svarsa.services import audit_service

log = get_logger("svarsa.erase_tenant")


# Tables that carry firma_id directly. Topological order — children first.
DIRECT_TABLES: tuple[str, ...] = (
    "audit_log",
    "tool_invocation",
    "escalation",
    "job",
    "call",
    "customer",
    "integration",
    "escalation_chain",
    "phone_number",
    "user",
)

# Tables that don't carry firma_id but cascade through a parent. Each entry:
# (table, parent_table, parent_join_column).
INDIRECT_TABLES: tuple[tuple[str, str, str], ...] = (
    ("transcript_segment", "call", "call_id"),
    ("customer_note", "customer", "customer_id"),
    ("customer_photo", "customer", "customer_id"),
)


def _direct_count(session: Session, table: str, firma_id: str) -> int:
    return int(
        session.execute(
            text(f"SELECT COUNT(*) FROM {table} WHERE firma_id = :firma_id"),
            {"firma_id": firma_id},
        ).scalar()
        or 0
    )


def _indirect_count(
    session: Session, table: str, parent_table: str, join_col: str, firma_id: str
) -> int:
    sql = (
        f"SELECT COUNT(*) FROM {table} "
        f"WHERE {join_col} IN (SELECT id FROM {parent_table} WHERE firma_id = :firma_id)"
    )
    return int(session.execute(text(sql), {"firma_id": firma_id}).scalar() or 0)


def erase_tenant(
    firma_id: str,
    *,
    operator: str = "system",
    dry_run: bool = False,
) -> dict[str, int]:
    settings = get_settings()
    engine = get_engine()
    counts: dict[str, int] = {}

    with Session(engine) as session, firma_context(firma_id):
        firma = session.get(Firma, firma_id)
        if firma is None:
            msg = f"firma_not_found:{firma_id}"
            raise SystemExit(msg)

        log.warning("erase_tenant.start", firma_id=firma_id, dry_run=dry_run, operator=operator)

        for table, parent, col in INDIRECT_TABLES:
            counts[table] = _indirect_count(session, table, parent, col, firma_id)
        for table in DIRECT_TABLES:
            counts[table] = _direct_count(session, table, firma_id)

        # Final audit row before the firma itself is erased.
        audit_service.record(
            session,
            actor=operator,
            action="firma.erased" if not dry_run else "firma.erase_dry_run",
            target_type="firma",
            target_id=firma_id,
            payload={"counts": counts, "firma_name": firma.name},
        )

        if dry_run:
            log.info("erase_tenant.dry_run.complete", firma_id=firma_id, counts=counts)
            return counts

        # Indirect tables first so the parent's children are gone before we
        # delete the parents. Then direct-firma_id tables. Then firma itself.
        for table, parent, col in INDIRECT_TABLES:
            session.execute(
                text(
                    f"DELETE FROM {table} WHERE {col} IN "
                    f"(SELECT id FROM {parent} WHERE firma_id = :firma_id)"
                ),
                {"firma_id": firma_id},
            )
        for table in DIRECT_TABLES:
            session.execute(
                text(f"DELETE FROM {table} WHERE firma_id = :firma_id"),
                {"firma_id": firma_id},
            )
        session.execute(
            text("DELETE FROM firma WHERE id = :firma_id"),
            {"firma_id": firma_id},
        )
        session.commit()

    # Per-tenant blob storage.
    try:
        store = make_storage(settings)
        store.delete_tenant(firma_id)
    except Exception:  # noqa: BLE001
        log.exception("erase_tenant.storage_delete_failed", firma_id=firma_id)

    # Per-tenant KMS key destruction (production only; best-effort).
    if settings.storage_mode == "gcs" and settings.gcp_project:
        try:
            from google.cloud import kms  # type: ignore[attr-defined]

            client = kms.KeyManagementServiceClient()
            key_name = (
                f"projects/{settings.gcp_project}/locations/{settings.kms_location}"
                f"/keyRings/{settings.kms_keyring}/cryptoKeys/firma-{firma_id.lower()}"
            )
            for version in client.list_crypto_key_versions(parent=key_name):
                if version.state.name == "ENABLED":
                    client.destroy_crypto_key_version(name=version.name)
            log.info("erase_tenant.kms_destroyed", firma_id=firma_id, key=key_name)
        except Exception:  # noqa: BLE001
            log.exception("erase_tenant.kms_failed", firma_id=firma_id)

    log.warning("erase_tenant.complete", firma_id=firma_id, counts=counts)
    return counts


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    counts = erase_tenant(
        args.firma_id,
        operator=args.operator,
        dry_run=args.dry_run,
    )
    print(f"firma_id={args.firma_id} dry_run={args.dry_run}")
    for table, n in counts.items():
        print(f"  {table:<24} {n:>6} rows")
    return 0


def _parse_args(argv: Sequence[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="GDPR Art. 17 tenant erasure")
    p.add_argument("firma_id")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--operator", default="system")
    return p.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(main())
