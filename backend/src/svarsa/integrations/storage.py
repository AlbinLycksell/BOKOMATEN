"""Per-tenant blob storage abstraction.

Production: per-firma GCS bucket with CMEK + 7-day default lifecycle TTL
(PRD §8.9, §9.6). Bucket name pattern: `{prefix}-{firma_id}-{region}`.

Dev: file-system fake under `backend/recordings/{firma_id}/...`.

Always tenant-scoped — every public method takes `firma_id` as the first
arg, and the `LocalStorage` and `GCSStorage` clients refuse cross-tenant
operations.
"""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from typing import Protocol, runtime_checkable

from svarsa.core.config import REPO_ROOT, Settings, get_settings
from svarsa.core.logging import get_logger

log = get_logger("svarsa.storage")


@runtime_checkable
class TenantBlobStore(Protocol):
    """Per-tenant blob store. Implementations must be tenant-scoped end-to-end."""

    def ensure_bucket(self, firma_id: str) -> str: ...

    def write(self, firma_id: str, key: str, data: bytes, content_type: str) -> str: ...

    def read(self, firma_id: str, key: str) -> bytes: ...

    def exists(self, firma_id: str, key: str) -> bool: ...

    def signed_url(self, firma_id: str, key: str, expires_in: timedelta) -> str: ...

    def delete_tenant(self, firma_id: str) -> None: ...


class LocalStorage:
    """File-system fake under `backend/recordings/{firma_id}/`. Dev only."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or (REPO_ROOT / "backend" / "recordings")

    def _firma_dir(self, firma_id: str) -> Path:
        return self.root / firma_id

    def ensure_bucket(self, firma_id: str) -> str:
        d = self._firma_dir(firma_id)
        d.mkdir(parents=True, exist_ok=True)
        return str(d)

    def _path(self, firma_id: str, key: str) -> Path:
        if ".." in key or key.startswith("/"):
            msg = f"unsafe key: {key}"
            raise ValueError(msg)
        return self._firma_dir(firma_id) / key

    def write(self, firma_id: str, key: str, data: bytes, content_type: str) -> str:
        path = self._path(firma_id, key)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        log.info("storage.local.write", firma_id=firma_id, key=key, bytes=len(data))
        return str(path)

    def read(self, firma_id: str, key: str) -> bytes:
        return self._path(firma_id, key).read_bytes()

    def exists(self, firma_id: str, key: str) -> bool:
        return self._path(firma_id, key).exists()

    def signed_url(self, firma_id: str, key: str, expires_in: timedelta) -> str:
        # Dev fakes a URL that the dashboard's <audio> tag in dev can
        # round-trip via a future /dev-recordings/ static mount.
        return f"file://{self._path(firma_id, key)}"

    def delete_tenant(self, firma_id: str) -> None:
        d = self._firma_dir(firma_id)
        if not d.exists():
            return
        for p in sorted(d.rglob("*"), reverse=True):
            if p.is_file():
                p.unlink()
            elif p.is_dir():
                p.rmdir()
        d.rmdir()
        log.info("storage.local.tenant_deleted", firma_id=firma_id)


class GCSStorage:
    """Per-tenant GCS buckets with CMEK + lifecycle TTL.

    Bucket creation is *eager* — call `ensure_bucket(firma_id)` from the
    onboarding flow so we fail fast on KMS / IAM misconfiguration. Once
    created, every write/read is tenant-scoped via the bucket name.
    """

    def __init__(
        self,
        project: str,
        prefix: str,
        region: str,
        retention_days: int,
        kms_keyring: str,
        kms_location: str,
    ) -> None:
        from google.cloud import storage  # type: ignore[attr-defined]

        self.project = project
        self.prefix = prefix
        self.region = region
        self.retention_days = retention_days
        self.kms_keyring = kms_keyring
        self.kms_location = kms_location
        self._client = storage.Client(project=project)

    def _bucket_name(self, firma_id: str) -> str:
        # Bucket names: lowercase, 3–63 chars. ULID is base32 (uppercase) — lower it.
        suffix = firma_id.lower().replace("_", "-")
        return f"{self.prefix}-{suffix}-{self.region}"[:63]

    def _kms_key_resource(self, firma_id: str) -> str:
        return (
            f"projects/{self.project}/locations/{self.kms_location}"
            f"/keyRings/{self.kms_keyring}/cryptoKeys/firma-{firma_id.lower()}"
        )

    def ensure_bucket(self, firma_id: str) -> str:
        from google.cloud import storage  # type: ignore[attr-defined]
        from google.api_core.exceptions import Conflict, NotFound

        name = self._bucket_name(firma_id)
        bucket = self._client.bucket(name)
        try:
            bucket.reload()
            log.info("storage.gcs.bucket_exists", firma_id=firma_id, bucket=name)
            return name
        except NotFound:
            pass

        bucket = storage.Bucket(self._client, name=name)
        bucket.location = self.region
        bucket.storage_class = "STANDARD"
        bucket.iam_configuration.uniform_bucket_level_access_enabled = True
        bucket.versioning_enabled = False
        bucket.default_kms_key_name = self._kms_key_resource(firma_id)
        bucket.lifecycle_rules = [
            {
                "action": {"type": "Delete"},
                "condition": {"age": self.retention_days},
            },
        ]
        try:
            bucket = self._client.create_bucket(bucket, location=self.region)
            log.info(
                "storage.gcs.bucket_created",
                firma_id=firma_id,
                bucket=name,
                kms=bucket.default_kms_key_name,
            )
        except Conflict:
            log.info("storage.gcs.bucket_race", firma_id=firma_id, bucket=name)
        return name

    def write(self, firma_id: str, key: str, data: bytes, content_type: str) -> str:
        bucket = self._client.bucket(self._bucket_name(firma_id))
        blob = bucket.blob(key)
        blob.upload_from_string(data, content_type=content_type)
        log.info("storage.gcs.write", firma_id=firma_id, key=key, bytes=len(data))
        return f"gs://{bucket.name}/{key}"

    def read(self, firma_id: str, key: str) -> bytes:
        bucket = self._client.bucket(self._bucket_name(firma_id))
        return bucket.blob(key).download_as_bytes()

    def exists(self, firma_id: str, key: str) -> bool:
        bucket = self._client.bucket(self._bucket_name(firma_id))
        return bucket.blob(key).exists()

    def signed_url(self, firma_id: str, key: str, expires_in: timedelta) -> str:
        bucket = self._client.bucket(self._bucket_name(firma_id))
        return bucket.blob(key).generate_signed_url(
            version="v4",
            expiration=expires_in,
            method="GET",
        )

    def delete_tenant(self, firma_id: str) -> None:
        from google.api_core.exceptions import NotFound

        bucket = self._client.bucket(self._bucket_name(firma_id))
        try:
            bucket.delete(force=True)
            log.info("storage.gcs.tenant_deleted", firma_id=firma_id, bucket=bucket.name)
        except NotFound:
            log.info("storage.gcs.tenant_already_gone", firma_id=firma_id)


def make_storage(settings: Settings | None = None) -> TenantBlobStore:
    s = settings or get_settings()
    if s.storage_mode == "gcs":
        return GCSStorage(
            project=s.gcp_project,
            prefix=s.gcs_bucket_prefix,
            region=s.region,
            retention_days=s.gcs_recording_retention_days,
            kms_keyring=s.kms_keyring,
            kms_location=s.kms_location,
        )
    return LocalStorage()
