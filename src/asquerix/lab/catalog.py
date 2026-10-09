"""Short, serialized SQLite writes and durable semantic history/ownership."""

from __future__ import annotations

from contextlib import contextmanager
import json
from pathlib import Path
import sqlite3
from threading import RLock
import time
from uuid import uuid4

from .config import Campaign, digest

SCHEMA = """
CREATE TABLE IF NOT EXISTS campaigns (
 id TEXT PRIMARY KEY, state TEXT NOT NULL, spec TEXT NOT NULL,
 created REAL NOT NULL, updated REAL NOT NULL, summary TEXT NOT NULL DEFAULT '{}',
 worker_token TEXT, device_uuid TEXT, publication TEXT NOT NULL DEFAULT '{}');
CREATE TABLE IF NOT EXISTS programs (hash TEXT PRIMARY KEY, document TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS candidates (
 id TEXT NOT NULL, campaign_id TEXT NOT NULL REFERENCES campaigns(id), arm TEXT NOT NULL,
 program_hash TEXT NOT NULL REFERENCES programs(hash), position INTEGER NOT NULL, generation INTEGER NOT NULL,
 document TEXT NOT NULL, PRIMARY KEY(campaign_id, id), UNIQUE(campaign_id, arm, position));
CREATE TABLE IF NOT EXISTS episodes (
 task_id TEXT PRIMARY KEY, campaign_id TEXT NOT NULL REFERENCES campaigns(id), candidate_id TEXT NOT NULL,
 episode_key TEXT NOT NULL, bank TEXT NOT NULL, initial_id TEXT NOT NULL, document TEXT NOT NULL,
 UNIQUE(campaign_id,candidate_id,episode_key));
CREATE TABLE IF NOT EXISTS events (
 id INTEGER PRIMARY KEY AUTOINCREMENT, campaign_id TEXT NOT NULL REFERENCES campaigns(id),
 kind TEXT NOT NULL, created REAL NOT NULL, payload TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS events_campaign ON events(campaign_id,id);
CREATE INDEX IF NOT EXISTS episodes_campaign ON episodes(campaign_id,candidate_id,bank);
CREATE TABLE IF NOT EXISTS artifacts (
 id TEXT PRIMARY KEY, campaign_id TEXT NOT NULL REFERENCES campaigns(id), path TEXT NOT NULL,
 sha256 TEXT NOT NULL, size INTEGER NOT NULL, UNIQUE(campaign_id,path));
CREATE TABLE IF NOT EXISTS replays (
 id TEXT PRIMARY KEY, campaign_id TEXT NOT NULL REFERENCES campaigns(id), episode_key TEXT NOT NULL,
 state TEXT NOT NULL, document TEXT NOT NULL, UNIQUE(campaign_id,episode_key));
CREATE TABLE IF NOT EXISTS workers (
 token TEXT PRIMARY KEY, pid INTEGER NOT NULL, process_start TEXT NOT NULL, device_uuid TEXT,
 campaign_id TEXT, heartbeat REAL NOT NULL, state TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS requests (
 key TEXT PRIMARY KEY, route TEXT NOT NULL, body_hash TEXT NOT NULL, response TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS checkpoints (
 campaign_id TEXT PRIMARY KEY REFERENCES campaigns(id), document TEXT NOT NULL);
PRAGMA user_version=2;
"""

# Version 2 keys candidates by campaign: a continuation lists the candidates it inherited
# under their original identities without touching the parent campaign's records.
MIGRATE_1_TO_2 = """
BEGIN;
CREATE TABLE candidates_v2 (
 id TEXT NOT NULL, campaign_id TEXT NOT NULL REFERENCES campaigns(id), arm TEXT NOT NULL,
 program_hash TEXT NOT NULL REFERENCES programs(hash), position INTEGER NOT NULL, generation INTEGER NOT NULL,
 document TEXT NOT NULL, PRIMARY KEY(campaign_id, id), UNIQUE(campaign_id, arm, position));
INSERT INTO candidates_v2 (id, campaign_id, arm, program_hash, position, generation, document)
 SELECT id, campaign_id, arm, program_hash, position, generation, document FROM candidates;
DROP TABLE candidates;
ALTER TABLE candidates_v2 RENAME TO candidates;
PRAGMA user_version=2;
COMMIT;
"""


def dumps(value) -> str:
    return json.dumps(value, sort_keys=True, allow_nan=False, separators=(",", ":"))


class Conflict(ValueError):
    pass


class Catalog:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.path = self.root / "catalog.sqlite3"
        self.lock = RLock()
        self.db = sqlite3.connect(self.path, timeout=5, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA busy_timeout=5000")
        version = self.db.execute("PRAGMA user_version").fetchone()[0]
        if version not in (0, 1, 2):
            self.db.close()
            raise ValueError("Unsupported catalog schema; no implicit migrations are performed")
        self.db.execute("PRAGMA journal_mode=WAL")
        with self.lock:
            if version == 1:
                self.db.executescript(MIGRATE_1_TO_2)
            self.db.executescript(SCHEMA)

    def close(self):
        with self.lock:
            self.db.close()

    @contextmanager
    def transaction(self):
        with self.lock:
            try:
                self.db.execute("BEGIN IMMEDIATE")
                yield self.db
                self.db.commit()
            except BaseException:
                self.db.rollback()
                raise

    def backup(self, destination: Path):
        destination.parent.mkdir(parents=True, exist_ok=True)
        with self.lock, sqlite3.connect(destination) as target:
            self.db.backup(target)
            if target.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("Catalog snapshot failed integrity_check")

    def _event(self, db, campaign_id, kind, payload):
        cursor = db.execute("INSERT INTO events(campaign_id,kind,created,payload) VALUES(?,?,?,?)",
                            (campaign_id, kind, time.time(), dumps(payload)))
        return str(cursor.lastrowid)

    def event(self, campaign_id: str, kind: str, payload: dict):
        with self.transaction() as db:
            return self._event(db, campaign_id, kind, payload)

    def idempotent(self, key: str, route: str, body, action):
        if not 8 <= len(key) <= 128 or not all(char.isalnum() or char in "-_:" for char in key):
            raise ValueError("Provide an idempotency key of 8-128 safe characters")
        body_hash = digest(body)
        with self.transaction() as db:
            existing = db.execute("SELECT * FROM requests WHERE key=?", (key,)).fetchone()
            if existing:
                if (existing["route"], existing["body_hash"]) != (route, body_hash):
                    raise Conflict("Idempotency key is already bound to another request")
                return json.loads(existing["response"])
            result = action(db)
            db.execute("INSERT INTO requests VALUES(?,?,?,?)", (key, route, body_hash, dumps(result)))
            return result

    def submit(self, campaign: Campaign, key: str, *, state="QUEUED") -> dict:
        spec = campaign.document()

        def action(db):
            identifier = uuid4().hex
            now = time.time()
            db.execute("INSERT INTO campaigns(id,state,spec,created,updated) VALUES(?,?,?,?,?)",
                       (identifier, state, dumps(spec), now, now))
            self._event(db, identifier, "CAMPAIGN_" + state, {"plan": campaign.plan(), "manifest_hash": digest(spec)})
            return {"id": identifier, "state": state, "plan": campaign.plan()}

        return self.idempotent(key, "submit:" + state, spec, action)

    def get(self, identifier: str) -> dict:
        with self.lock:
            row = self.db.execute("SELECT * FROM campaigns WHERE id=?", (identifier,)).fetchone()
        if row is None:
            raise KeyError("Unknown campaign")
        result = dict(row)
        for field in ("spec", "summary", "publication"):
            result[field] = json.loads(result[field])
        result["manifest_hash"] = digest(result["spec"])
        return result

    def campaigns(self, *, limit=30, offset=0, state=None, query="") -> dict:
        conditions, values = ["spec LIKE ?"], ["%" + query + "%"]
        if state:
            conditions.append("state=?")
            values.append(state)
        where = " AND ".join(conditions)
        with self.lock:
            total = self.db.execute("SELECT count(*) FROM campaigns WHERE " + where, values).fetchone()[0]
            rows = self.db.execute("SELECT id FROM campaigns WHERE " + where + " ORDER BY created DESC LIMIT ? OFFSET ?",
                                   (*values, limit, offset)).fetchall()
        return {"items": [self.get(row["id"]) for row in rows], "total": total, "offset": offset, "limit": limit}

    def set_state(self, identifier: str, state: str, *, summary=None, token=None, uuid=None, publication=None):
        with self.transaction() as db:
            row = db.execute("SELECT summary,publication FROM campaigns WHERE id=?", (identifier,)).fetchone()
            if row is None:
                raise KeyError("Unknown campaign")
            current_summary = json.loads(row["summary"])
            if summary:
                current_summary.update(summary)
            db.execute("UPDATE campaigns SET state=?,updated=?,summary=?,worker_token=coalesce(?,worker_token),device_uuid=coalesce(?,device_uuid),publication=? WHERE id=?",
                       (state, time.time(), dumps(current_summary), token, uuid,
                        dumps(publication) if publication is not None else row["publication"], identifier))
            self._event(db, identifier, "STATE", {"state": state, "summary": current_summary})

    def command(self, identifier: str, command: str, key: str):
        transitions = {
            "pause": {"QUEUED": "PAUSED", "PREPARING": "PAUSE_REQUESTED", "RUNNING": "PAUSE_REQUESTED", "PAUSE_REQUESTED": "PAUSE_REQUESTED", "PAUSED": "PAUSED"},
            "resume": {"PAUSED": "QUEUED", "INTERRUPTED": "QUEUED", "QUEUED": "QUEUED"},
            "stop": {"QUEUED": "STOP_REQUESTED", "PREPARING": "STOP_REQUESTED", "RUNNING": "STOP_REQUESTED", "PAUSE_REQUESTED": "STOP_REQUESTED", "PAUSED": "STOP_REQUESTED", "STOP_REQUESTED": "STOP_REQUESTED"}}
        if command not in transitions:
            raise ValueError("Unknown lifecycle command")

        def action(db):
            row = db.execute("SELECT state FROM campaigns WHERE id=?", (identifier,)).fetchone()
            if row is None:
                raise KeyError("Unknown campaign")
            if row["state"] not in transitions[command]:
                raise Conflict(f"Cannot {command} a campaign in {row['state']}")
            state = transitions[command][row["state"]]
            db.execute("UPDATE campaigns SET state=?,updated=? WHERE id=?", (state, time.time(), identifier))
            self._event(db, identifier, "COMMAND", {"command": command, "state": state})
            return {"id": identifier, "state": state}

        return self.idempotent(key, command + ":" + identifier, {}, action)

    def history(self, identifier: str, *, after=0, limit=100) -> dict:
        self.get(identifier)
        with self.lock:
            rows = self.db.execute("SELECT * FROM events WHERE campaign_id=? AND id>? ORDER BY id LIMIT ?", (identifier, after, limit)).fetchall()
            bounds = self.db.execute("SELECT min(id),max(id),count(*) FROM events WHERE campaign_id=?", (identifier,)).fetchone()
        return {"items": [{"id": str(row["id"]), "kind": row["kind"], "created": row["created"], "payload": json.loads(row["payload"])} for row in rows],
                "first_id": str(bounds[0] or 0), "last_id": str(bounds[1] or 0), "total": bounds[2],
                "cursor_reset": after > (bounds[1] or 0)}

    def candidate(self, campaign_id: str, candidate: dict):
        program = candidate["program"]
        with self.transaction() as db:
            db.execute("INSERT INTO programs VALUES(?,?) ON CONFLICT(hash) DO NOTHING", (program["hash"], dumps(program)))
            db.execute("INSERT INTO candidates VALUES(?,?,?,?,?,?,?) ON CONFLICT(campaign_id, id) DO UPDATE SET document=excluded.document",
                       (candidate["id"], campaign_id, candidate["arm"], program["hash"], candidate["position"], candidate.get("generation", 0), dumps(candidate)))

    def program(self, program_hash: str) -> dict:
        with self.lock:
            row = self.db.execute("SELECT document FROM programs WHERE hash=?", (program_hash,)).fetchone()
        if row is None:
            raise KeyError("Unknown program")
        return json.loads(row[0])

    def get_candidate(self, campaign_id: str, identifier: str) -> dict:
        with self.lock:
            row = self.db.execute("SELECT document FROM candidates WHERE campaign_id=? AND id=?", (campaign_id, identifier)).fetchone()
        if row is None:
            raise KeyError("Unknown candidate")
        return json.loads(row[0])

    def comparison(self, campaign_id: str) -> dict:
        self.get(campaign_id)
        with self.lock:
            rows = self.db.execute("SELECT document FROM candidates WHERE campaign_id=?", (campaign_id,)).fetchall()
        candidates = [json.loads(row[0]) for row in rows]
        fields = ("id", "arm", "position", "score", "holdout_score", "completed_at", "execution_elapsed_seconds", "arm_execution_elapsed_seconds")
        return {"candidates": [{key: candidate.get(key, {} if key.endswith("score") else 0) for key in fields}
                               for candidate in sorted(candidates, key=lambda item: (item.get("completed_at", 0), item["arm"], item["position"]))],
                "warning": "Equal candidate counts do not imply equal work. Mixed batch GPU times are not isolated program costs."}

    def history_state(self, campaign_id: str, index: int) -> dict:
        self.get(campaign_id)
        with self.lock:
            selected = self.db.execute("SELECT * FROM events WHERE campaign_id=? ORDER BY id LIMIT 1 OFFSET ?", (campaign_id, index)).fetchone()
            if selected is None:
                raise KeyError("Unknown history index")
            cursor = self.db.execute("SELECT * FROM events WHERE campaign_id=? AND id<=? ORDER BY id", (campaign_id, selected["id"]))
            candidates, parent_id = {}, None
            while True:
                page = cursor.fetchmany(100)
                if not page:
                    break
                for row in page:
                    payload = json.loads(row["payload"])
                    if row["kind"] == "CANDIDATE_GENERATED":
                        candidates[payload["id"]] = payload
                    elif row["kind"] in ("CANDIDATE_RESULT", "HOLDOUT_RESULT") and payload["candidate_id"] in candidates:
                        candidate = candidates[payload["candidate_id"]]
                        candidate["score" if payload["bank"] == "training" else "holdout_score"] = payload["score"]
                        candidate["state"] = "EVALUATED" if payload["score"]["complete"] else "INCOMPLETE"
                    elif row["kind"] in ("PARENT_SELECTION", "INCUMBENT_SELECTION"):
                        parent_id = payload["parent_id"]
        event = {"id": str(selected["id"]), "kind": selected["kind"], "created": selected["created"], "payload": json.loads(selected["payload"])}
        payload = event["payload"]
        candidate_id = payload.get("candidate_id") or payload.get("parent_id") or (payload.get("id") if event["kind"] == "CANDIDATE_GENERATED" else parent_id)
        candidate = candidates.get(candidate_id)
        related = [candidate] if candidate else []
        if candidate and candidate.get("parent_id") in candidates:
            related.append(candidates[candidate["parent_id"]])
        return {"event": event, "candidate": candidate, "candidates": related, "parent_id": parent_id,
                "completed_candidates": sum(bool(item.get("score", {}).get("complete")) for item in candidates.values())}

    def candidates(self, campaign_id: str, *, limit=50, offset=0, arm=None) -> dict:
        self.get(campaign_id)
        condition, values = "campaign_id=?", [campaign_id]
        if arm:
            condition += " AND arm=?"
            values.append(arm)
        with self.lock:
            rows = self.db.execute("SELECT document FROM candidates WHERE " + condition + " ORDER BY arm,position LIMIT ? OFFSET ?", (*values, limit, offset)).fetchall()
            total = self.db.execute("SELECT count(*) FROM candidates WHERE " + condition, values).fetchone()[0]
        return {"items": [json.loads(row[0]) for row in rows], "total": total, "offset": offset, "limit": limit}

    def admit_episodes(self, campaign_id: str, rows: list[dict]):
        with self.transaction() as db:
            for row in rows:
                db.execute("INSERT INTO episodes VALUES(?,?,?,?,?,?,?) ON CONFLICT(task_id) DO NOTHING",
                           (row["task_id"], campaign_id, row["candidate_id"], row["episode_key"], row["bank"], row["initial_id"], dumps(row)))

    def episodes(self, campaign_id: str, *, limit=50, offset=0, candidate_id=None, bank=None) -> dict:
        self.get(campaign_id)
        condition, values = "campaign_id=?", [campaign_id]
        for field, value in (("candidate_id", candidate_id), ("bank", bank)):
            if value:
                condition += " AND " + field + "=?"
                values.append(value)
        with self.lock:
            rows = self.db.execute("SELECT document FROM episodes WHERE " + condition + " ORDER BY initial_id,episode_key LIMIT ? OFFSET ?", (*values, limit, offset)).fetchall()
            total = self.db.execute("SELECT count(*) FROM episodes WHERE " + condition, values).fetchone()[0]
        return {"items": [json.loads(row[0]) for row in rows], "total": total, "offset": offset, "limit": limit}

    def artifact(self, campaign_id: str, document: dict) -> str:
        identifier = digest({"campaign": campaign_id, "path": document["path"]})[:32]
        with self.transaction() as db:
            db.execute("INSERT INTO artifacts VALUES(?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET sha256=excluded.sha256,size=excluded.size",
                       (identifier, campaign_id, document["path"], document["sha256"], document["size_bytes"]))
        return identifier

    def get_artifact(self, identifier: str) -> dict:
        with self.lock:
            row = self.db.execute("SELECT * FROM artifacts WHERE id=?", (identifier,)).fetchone()
        if row is None:
            raise KeyError("Unknown artifact")
        return dict(row)

    def replay(self, campaign_id: str, episode_key: str, document: dict, state="QUEUED") -> str:
        identifier = digest({"campaign": campaign_id, "episode": episode_key})[:32]
        with self.transaction() as db:
            db.execute("INSERT INTO replays VALUES(?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET state=excluded.state,document=excluded.document",
                       (identifier, campaign_id, episode_key, state, dumps(document)))
        return identifier

    def get_replay(self, identifier: str) -> dict:
        with self.lock:
            row = self.db.execute("SELECT * FROM replays WHERE id=?", (identifier,)).fetchone()
        if row is None:
            raise KeyError("Unknown replay")
        return {**dict(row), "document": json.loads(row["document"])}

    def replays(self, campaign_id: str) -> list[dict]:
        with self.lock:
            rows = self.db.execute("SELECT id FROM replays WHERE campaign_id=? ORDER BY id", (campaign_id,)).fetchall()
        return [self.get_replay(row[0]) for row in rows]

    def pending_replays(self) -> list[dict]:
        with self.lock:
            rows = self.db.execute("SELECT id FROM replays WHERE state='QUEUED' ORDER BY rowid LIMIT 1").fetchall()
        return [self.get_replay(row[0]) for row in rows]

    def worker(self, token: str, pid: int, process_start: str, *, campaign_id=None, device_uuid=None, state="IDLE"):
        with self.transaction() as db:
            db.execute("INSERT INTO workers VALUES(?,?,?,?,?,?,?) ON CONFLICT(token) DO UPDATE SET heartbeat=excluded.heartbeat,campaign_id=excluded.campaign_id,device_uuid=excluded.device_uuid,state=excluded.state",
                       (token, pid, process_start, device_uuid, campaign_id, time.time(), state))

    def workers(self) -> list[dict]:
        with self.lock:
            return [dict(row) for row in self.db.execute("SELECT * FROM workers WHERE state != 'DEAD'").fetchall()]
