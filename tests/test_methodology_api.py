"""API tests for methodology CRUD + export + suggest."""


def test_list_has_three_builtins(client):
    r = client.get("/api/methodologies")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] >= 3
    slugs = {m["slug"] for m in data["methodologies"]}
    assert {"requirement-decomposition", "musk-five-step", "amazon-working-backwards"} <= slugs


def test_get_detail_has_seven_slots(client):
    r = client.get("/api/methodologies", params={"q": "拆解"})
    mid = r.json()["methodologies"][0]["id"]
    detail = client.get(f"/api/methodologies/{mid}").json()
    for slot in ("trigger", "principles", "steps", "gates", "anti_patterns", "artifacts", "metrics"):
        assert slot in detail
    assert len(detail["gates"]) == 7


def test_create_custom_then_fetch(client):
    payload = {
        "name": "我的评审套路",
        "summary": "团队内部代码评审清单",
        "trigger": {"scenarios": ["代码评审"], "keywords": ["评审", "review"]},
        "principles": [{"title": "先看接口", "detail": "从对外契约看起"}],
        "steps": [{"id": "S1", "name": "看接口", "guidance": "..."}],
        "gates": [{"id": "G1", "step_id": "S1", "question": "接口是否稳定?", "pass_criteria": "稳定"}],
        "tags": ["评审"],
    }
    r = client.post("/api/methodologies", json=payload)
    assert r.status_code == 200
    created = r.json()
    assert created["origin"] == "custom"
    assert client.get(f"/api/methodologies/{created['id']}").json()["name"] == "我的评审套路"


def test_export_agent_md(client):
    mid = client.get("/api/methodologies", params={"q": "拆解"}).json()["methodologies"][0]["id"]
    r = client.get(f"/api/methodologies/{mid}/export", params={"format": "agent_md"})
    assert r.status_code == 200
    content = r.json()["content"]
    assert "方法论" in content and "决策闸门" in content


def test_suggest_keyword_finds_decomposition(client):
    r = client.post("/api/methodologies/suggest", json={"raw_input": "给销售做个能看业绩的东西", "top_k": 3})
    assert r.status_code == 200
    names = " ".join(s.get("slug", "") for s in r.json()["suggestions"])
    assert "requirement-decomposition" in names


def test_builtin_cannot_be_deleted(client):
    mid = client.get("/api/methodologies", params={"q": "拆解"}).json()["methodologies"][0]["id"]
    r = client.delete(f"/api/methodologies/{mid}")
    assert r.status_code == 400
