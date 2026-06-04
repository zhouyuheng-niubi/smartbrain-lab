"""Lens (透镜诊断) API — zero tokens via fake LLM."""


def test_lens_diagnose_and_history(client, fake_llm):
    mid = client.get("/api/methodologies", params={"q": "拆解"}).json()["methodologies"][0]["id"]
    r = client.post("/api/lens", json={
        "methodology_id": mid,
        "material": "给销售做个看业绩的仪表盘，要实时，加点AI预测和聊天功能。",
        "title": "销售看板方案",
    }).json()["review"]

    assert r["methodology_id"] == mid
    assert r["methodology_name"]
    diag = r["diagnosis"]
    assert diag["gate_findings"] and diag["top_fixes"]
    assert r["score"]["total"] > 0

    hist = client.get("/api/lens", params={"methodology_id": mid}).json()
    assert hist["total"] >= 1

    got = client.get(f"/api/lens/{r['id']}").json()["review"]
    assert got["id"] == r["id"]


def test_lens_unknown_methodology(client, fake_llm):
    r = client.post("/api/lens", json={"methodology_id": "nope", "material": "x"})
    assert r.status_code == 404
