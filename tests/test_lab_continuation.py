"""Continuation rules: only comparability-preserving settings change; finished parents only."""

from fastapi.testclient import TestClient
import pytest

from asquerix.lab.api import create_app
from asquerix.lab.config import Campaign
from asquerix.lab.continuation import continuation_spec

HEADERS = {"X-Asquerix-Client": "lab-v1", "Idempotency-Key": "continuation-test-key"}


def parent(**changes):
    return {"id": "a" * 32, "spec": Campaign(name="Parent", **changes).document()}


def test_budget_grows_and_editable_settings_apply():
    child = continuation_spec(parent(), 8, {"batch_capacity": 512, "limits": {"max_seconds": 30.0}, "name": "Child"})
    assert child.search.candidate_budget_per_method == 32 + 8
    assert child.batch_capacity == 512 and child.limits.max_seconds == 30.0 and child.limits.max_artifact_mib == 256.0
    assert child.continuation_of == "a" * 32 and child.document()["continuation_of"] == "a" * 32
    assert child.profile() == Campaign.model_validate(parent()["spec"]).profile()


@pytest.mark.parametrize("field", ["n", "initial_side", "datasets", "operator_seed", "search", "generation", "work_limits", "controls"])
def test_comparability_settings_are_locked(field):
    with pytest.raises(ValueError, match="cannot change"):
        continuation_spec(parent(), 1, {field: None})


def test_needs_search_methods_and_a_positive_budget():
    with pytest.raises(ValueError, match="no search method"):
        continuation_spec(parent(search={"methods": []}), 1, {})
    with pytest.raises(ValueError, match="between 1 and 1,000,000"):
        continuation_spec(parent(), 0, {})


def test_ordinary_manifests_do_not_gain_a_continuation_field():
    assert "continuation_of" not in Campaign(name="Ordinary").document()


def test_api_refuses_unfinished_parent(tmp_path):
    app = create_app(tmp_path, worker_enabled=False)
    with TestClient(app, base_url="http://127.0.0.1:8765") as client:
        queued = client.post("/api/v1/campaigns", json=Campaign(name="Queued").document(), headers=HEADERS).json()["id"]
        response = client.post(f"/api/v1/campaigns/{queued}/continue", json={"additional_candidates_per_method": 4},
                               headers={**HEADERS, "Idempotency-Key": "continuation-test-key-2"})
        assert response.status_code == 409 and "completed or partial" in response.json()["detail"]
        assert client.post(f"/api/v1/campaigns/{queued}/continue", json={"additional_candidates_per_method": 4, "n": 12},
                           headers={**HEADERS, "Idempotency-Key": "continuation-test-key-3"}).status_code == 422
    app.state.service.catalog.close()
