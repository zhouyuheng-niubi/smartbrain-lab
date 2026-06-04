"""Advisor (顾问陪练) API — multi-turn, zero tokens via fake LLM."""


def test_advisor_multi_turn(client, fake_llm):
    mid = client.get("/api/methodologies", params={"q": "第一性"}).json()["methodologies"][0]["id"]

    start = client.post("/api/advisor/start",
                        json={"methodology_id": mid, "topic": "要不要自研一套框架"}).json()["session"]
    sid = start["id"]
    assert start["methodology_name"]
    assert len(start["messages"]) == 1 and start["messages"][0]["role"] == "assistant"

    s2 = client.post(f"/api/advisor/{sid}/message", json={"content": "我觉得自研更可控"}).json()["session"]
    assert len(s2["messages"]) == 3  # assistant opening + user + assistant
    assert s2["messages"][1]["role"] == "user"
    assert s2["messages"][-1]["role"] == "assistant"

    got = client.get(f"/api/advisor/{sid}").json()["session"]
    assert got["id"] == sid
    assert len(got["messages"]) == 3


def test_advisor_unknown_methodology(client, fake_llm):
    r = client.post("/api/advisor/start", json={"methodology_id": "nope", "topic": "x"})
    assert r.status_code == 404
