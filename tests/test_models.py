"""Model + seeding tests (via the API to stay hook-safe)."""
from server.app.seeds import seed_builtin


def test_seed_is_idempotent():
    first = seed_builtin()
    assert first["total"] == 9
    second = seed_builtin()
    # second run updates the same set, creates none
    assert second["created"] == 0
    assert second["updated"] == 9


def test_methodology_slots_persisted(client):
    detail = client.get("/api/methodologies", params={"q": "马斯克"}).json()["methodologies"][0]
    full = client.get(f"/api/methodologies/{detail['id']}").json()
    assert full["slug"] == "musk-five-step"
    assert len(full["steps"]) == 5
    assert full["trigger"]["keywords"]
