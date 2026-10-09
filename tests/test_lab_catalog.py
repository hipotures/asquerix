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


def test_version_one_catalog_migrates_candidates_to_campaign_scoped_keys(tmp_path):
    import sqlite3
    from asquerix.lab import catalog as module
    old_schema = module.SCHEMA.replace("id TEXT NOT NULL, campaign_id", "id TEXT PRIMARY KEY, campaign_id").replace(
        "document TEXT NOT NULL, PRIMARY KEY(campaign_id, id), UNIQUE(campaign_id, arm, position)",
        "document TEXT NOT NULL, UNIQUE(campaign_id, arm, position)").replace("PRAGMA user_version=2", "PRAGMA user_version=1")
    db = sqlite3.connect(tmp_path / "catalog.sqlite3")
    db.executescript(old_schema)
    db.execute("INSERT INTO campaigns(id,state,spec,created,updated) VALUES('p','COMPLETED','{}',0,0)")
    db.execute("INSERT INTO campaigns(id,state,spec,created,updated) VALUES('c','QUEUED','{}',0,0)")
    db.execute("INSERT INTO programs VALUES('h','{}')")
    db.execute("INSERT INTO candidates VALUES('p:arm:0','p','arm','h',0,0,'{\"id\":\"p:arm:0\"}')")
    db.commit()
    db.close()
    catalog = module.Catalog(tmp_path)
    assert catalog.db.execute("PRAGMA user_version").fetchone()[0] == 2
    assert catalog.db.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
    candidate = {"id": "p:arm:0", "arm": "arm", "position": 0, "program": {"hash": "h"}, "score": {"inherited": True}}
    catalog.candidate("c", candidate)  # a continuation stores its own copy; the parent's record is untouched
    assert catalog.get_candidate("p", "p:arm:0") == {"id": "p:arm:0"}
    assert catalog.get_candidate("c", "p:arm:0")["score"] == {"inherited": True}
    catalog.close()


def test_candidates_sort_by_mean_rank_best_start_or_generation_order(tmp_path):
    from asquerix.lab.catalog import Catalog
    catalog = Catalog(tmp_path)
    catalog.db.execute("INSERT INTO campaigns(id,state,spec,created,updated) VALUES('c','COMPLETED','{}',0,0)")
    catalog.db.commit()
    for arm, position, mean, best, eligible in (("a", 0, 4.3, 4.0, True), ("a", 1, 9.1, 9.1, True),
                                                 ("b", 0, 4.2, 4.1, True), ("b", 1, 4.0, 4.0, False)):
        catalog.candidate("c", {"id": f"{arm}{position}", "arm": arm, "position": position, "program": {"hash": f"h{arm}{position}"},
                                "score": {"mean_best_L": mean, "best_L": best, "eligible": eligible}})
    ids = lambda sort: [item["id"] for item in catalog.candidates("c", sort=sort)["items"]]
    assert ids("rank") == ["b0", "a0", "a1", "b1"]
    assert ids("best") == ["a0", "b0", "a1", "b1"]
    assert ids("order") == ["a0", "a1", "b0", "b1"]
    catalog.close()
