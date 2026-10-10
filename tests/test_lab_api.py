"""Actual HTTP validation, isolation, authentication and catalog responses."""

from fastapi.testclient import TestClient

from asquerix.lab.api import create_app
from asquerix.lab.config import Campaign
from asquerix.lab.strategy import control_program

HEADERS = {"X-Asquerix-Client": "lab-v1", "Idempotency-Key": "api-test-request-key"}


def test_http_submission_idempotency_pagination_and_compilation(tmp_path):
    app = create_app(tmp_path, worker_enabled=False)
    with TestClient(app, base_url="http://127.0.0.1:8765") as client:
        assert client.get("/").status_code == 200
        assert client.get("/api/v1/capabilities").json()["square_count"] == [1, None]
        response = client.post("/api/v1/campaigns", json=Campaign(name="HTTP campaign").document(), headers=HEADERS)
        assert response.status_code == 202
        assert client.post("/api/v1/campaigns", json=Campaign(name="HTTP campaign").document(), headers=HEADERS).json() == response.json()
        identifier = response.json()["id"]
        assert client.get("/api/v1/campaigns?limit=1&offset=0").json()["total"] == 1
        assert client.get("/api/v1/campaigns?limit=0").status_code == 422
        assert client.get(f"/api/v1/campaigns/{identifier}").json()["state"] == "QUEUED"
        compiled = client.post("/api/v1/programs/validate", json={"program": control_program("legacy_compress")}, headers=HEADERS)
        assert compiled.status_code == 200
        assert compiled.json()["source_map"] == ["body[0]", "body[1]"]
        invalid = client.post("/api/v1/programs/validate", json={"program": {"schema": "asquerix-strategy-v1", "body": [{"op": "BAD"}]}}, headers=HEADERS)
        assert invalid.status_code == 422
        assert invalid.json()["node_path"] == "body[0].op"
        assert client.get(f"/api/v1/campaigns/{identifier}/history").json()["total"] == 1
        assert client.get(f"/api/v1/campaigns/{identifier}/history-state?index=0").json()["event"]["kind"] == "CAMPAIGN_QUEUED"
        assert client.get(f"/api/v1/campaigns/{identifier}/export").status_code == 409
    app.state.service.catalog.close()


def test_host_origin_client_header_body_bound_and_safe_artifacts(tmp_path):
    app = create_app(tmp_path, worker_enabled=False)
    with TestClient(app, base_url="http://127.0.0.1:8765") as client:
        spec = Campaign(name="Safety").document()
        assert client.post("/api/v1/campaigns", json=spec).status_code == 403
        assert client.post("/api/v1/campaigns", json=spec, headers={**HEADERS, "Origin": "http://evil.example"}).status_code == 403
        assert client.get("/api/v1/capabilities", headers={"Host": "evil.example"}).status_code == 400
        assert client.post("/api/v1/campaigns", content=b" " * (1024**2 + 1), headers=HEADERS).status_code == 413
        identifier = client.post("/api/v1/campaigns", json=spec, headers=HEADERS).json()["id"]
        artifact = app.state.service.catalog.artifact(identifier, {"path": "../../../AGENTS.md", "sha256": "a" * 64, "size_bytes": 1})
        assert client.get("/api/v1/artifacts/" + artifact).status_code == 403
        assert client.get("/api/v1/artifacts/unknown").status_code == 404
    app.state.service.catalog.close()


def test_authenticated_cookie_csrf_and_bearer_clients(tmp_path):
    token = "test-only-access-token-not-a-production-secret"
    app = create_app(tmp_path, token=token, worker_enabled=False)
    with TestClient(app, base_url="http://127.0.0.1:8765") as client:
        assert client.get("/api/v1/capabilities").status_code == 401
        login = client.post("/api/v1/session", json={"token": token}, headers=HEADERS)
        assert login.status_code == 200
        assert "HttpOnly" in login.headers["set-cookie"]
        assert client.get("/api/v1/capabilities").status_code == 200
        assert client.post("/api/v1/campaigns", json=Campaign(name="CSRF").document(), headers=HEADERS).status_code == 403
        assert client.post("/api/v1/campaigns", json=Campaign(name="CSRF").document(), headers={**HEADERS, "X-CSRF-Token": login.json()["csrf_token"]}).status_code == 202
    app.state.service.catalog.close()
    app = create_app(tmp_path / "bearer", token=token, worker_enabled=False)
    with TestClient(app, base_url="http://127.0.0.1:8765") as client:
        assert client.get("/api/v1/capabilities", headers={"Authorization": "Bearer " + token}).status_code == 200
    app.state.service.catalog.close()


def test_lan_requires_configured_authentication(tmp_path, monkeypatch):
    monkeypatch.delenv("ASQUERIX_LAB_TOKEN", raising=False)
    try:
        create_app(tmp_path, host="0.0.0.0")
    except ValueError as error:
        assert "LAN binding" in str(error)
    else:
        raise AssertionError("Unauthenticated LAN binding was accepted")


def test_best_known_upper_bounds_load_at_start_and_are_served(tmp_path):
    import json
    import pytest
    from asquerix.lab.api import BEST_KNOWN, load_best_known
    document = load_best_known()
    entries = {entry["n"]: entry for entry in document["entries"]}
    assert sorted(entries) == list(range(1, 101))
    assert entries[11]["printed"] == "3.8771" and entries[11]["author"] == "Trump" and not entries[11]["optimal_in_source"]
    assert abs(entries[10]["upper_bound"] - (3 + 2 ** -0.5)) < 1e-15 and entries[10]["optimal_in_source"]
    assert document["source"]["imported_sha256"] and document["source"]["revision_year"] == 2009
    broken = tmp_path / "broken.json"
    broken.write_text(json.dumps({**json.loads(BEST_KNOWN.read_text()), "schema": "other"}))
    with pytest.raises(ValueError, match="unsupported best-known schema"):
        load_best_known(broken)
    app = create_app(tmp_path / "lab", worker_enabled=False)
    with TestClient(app, base_url="http://127.0.0.1:8765") as client:
        assert client.get("/api/v1/references/best-known").json()["entries"][10]["n"] == 11
    app.state.service.catalog.close()
