from __future__ import annotations

from datetime import timedelta
from pathlib import Path

from svarsa.integrations.storage import LocalStorage


def test_local_storage_round_trip(tmp_path: Path) -> None:
    s = LocalStorage(root=tmp_path)
    s.ensure_bucket("01J-firmaA")
    url = s.write("01J-firmaA", "rec/abc.mp3", b"audio bytes", "audio/mpeg")
    assert url.endswith("rec/abc.mp3")
    assert s.exists("01J-firmaA", "rec/abc.mp3")
    assert s.read("01J-firmaA", "rec/abc.mp3") == b"audio bytes"
    assert s.signed_url("01J-firmaA", "rec/abc.mp3", timedelta(hours=1)).startswith("file://")


def test_local_storage_tenant_isolation(tmp_path: Path) -> None:
    s = LocalStorage(root=tmp_path)
    s.write("01J-firmaA", "x.mp3", b"a", "audio/mpeg")
    assert not s.exists("01J-firmaB", "x.mp3")


def test_local_storage_rejects_path_traversal(tmp_path: Path) -> None:
    import pytest

    s = LocalStorage(root=tmp_path)
    with pytest.raises(ValueError):
        s.write("01J-firmaA", "../escape.mp3", b"a", "audio/mpeg")
    with pytest.raises(ValueError):
        s.write("01J-firmaA", "/etc/passwd", b"a", "audio/mpeg")


def test_local_storage_delete_tenant(tmp_path: Path) -> None:
    s = LocalStorage(root=tmp_path)
    s.write("01J-firmaA", "a.mp3", b"a", "audio/mpeg")
    s.write("01J-firmaA", "nested/b.mp3", b"b", "audio/mpeg")
    s.delete_tenant("01J-firmaA")
    assert not s.exists("01J-firmaA", "a.mp3")
