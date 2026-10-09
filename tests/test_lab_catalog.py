"""Durable catalog, idempotency, bounded pages, and online SQLite snapshots."""

import sqlite3

import pytest

from asquerix.lab.catalog import Catalog, Conflict
from asquerix.lab.config import Campaign


def test_idempotency_lifecycle_history_and_restart(tmp_path):
    catalog = Catalog(tmp_path)
    campaign = Campaign(name="Durable")
    first = catalog.submit(campaign, "unique-request-key")
    assert catalog.submit(campaign, "unique-request-key") == first
    assert catalog.campaigns()["total"] == 1
    with pytest.raises(Conflict):
        catalog.submit(Campaign(name="Different"), "unique-request-key")
    identifier = first["id"]
    assert catalog.command(identifier, "pause", "pause-request-key")["state"] == "PAUSED"
    assert catalog.command(identifier, "resume", "resume-request-key")["state"] == "QUEUED"
    page = catalog.history(identifier, limit=1)
    assert len(page["items"]) == 1
    assert isinstance(page["last_id"], str)
    rest = catalog.history(identifier, after=int(page["items"][0]["id"]))
    assert len(rest["items"]) == 2
    assert catalog.history(identifier, after=2**63 - 1)["cursor_reset"]
    catalog.close()
    restarted = Catalog(tmp_path)
    assert restarted.get(identifier)["spec"] == campaign.document()
    assert restarted.history(identifier)["total"] == 3
    restarted.close()


def test_online_backup_has_committed_wal_data_and_integrity(tmp_path):
    catalog = Catalog(tmp_path / "live")
    identifier = catalog.submit(Campaign(name="Backup"), "backup-request-key")["id"]
    snapshot = tmp_path / "snapshot/catalog.sqlite3"
    catalog.backup(snapshot)
    with sqlite3.connect(snapshot) as db:
        assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert db.execute("SELECT id FROM campaigns").fetchone()[0] == identifier
    catalog.close()


def test_unsupported_schema_rejected_on_temporary_snapshot(tmp_path):
    catalog = Catalog(tmp_path / "live")
    catalog.submit(Campaign(name="Original"), "snapshot-request-key")
    snapshot_root = tmp_path / "snapshot"
    catalog.backup(snapshot_root / "catalog.sqlite3")
    with sqlite3.connect(snapshot_root / "catalog.sqlite3") as db:
        db.execute("PRAGMA user_version=999")
        assert db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    with pytest.raises(ValueError, match="Unsupported"):
        Catalog(snapshot_root)
    assert catalog.campaigns()["total"] == 1
    catalog.close()
