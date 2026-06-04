"""End-to-end run API loop — zero tokens via fake LLM."""

INPUT = "给销售做个能看业绩的东西"
ANSWER = "目标是提升销售转化率，指标是月度达成率；作为销售经理我希望实时查看业绩，以便调整策略。"


def test_full_run_loop_via_api(client, fake_llm):
    mid = client.get("/api/methodologies", params={"q": "拆解"}).json()["methodologies"][0]["id"]

    detail = client.post("/api/runs", json={"methodology_id": mid, "raw_input": INPUT, "title": "t"}).json()
    run_id = detail["run"]["id"]
    assert detail["run"]["status"] == "in_progress"
    assert detail["methodology"]["slug"] == "requirement-decomposition"

    for _ in range(50):
        ask = client.post(f"/api/runs/{run_id}/ask").json()
        if ask.get("done"):
            break
        gid = ask["gate"]["id"]
        ans = client.post(f"/api/runs/{run_id}/answer", json={"gate_id": gid, "answer": ANSWER}).json()
        assert ans["resolved"] is True
        if ans["run_done"]:
            break

    syn = client.post(f"/api/runs/{run_id}/synthesize").json()
    assert syn["run"]["status"] == "completed"
    assert "验收标准" in syn["run"]["artifact_md"]
    assert syn["run"]["artifact_score"]["total"] > 0

    oc = client.post(f"/api/runs/{run_id}/outcome", json={"usefulness": 5, "adopted": True}).json()
    assert oc["outcome"]["usefulness"] == 5

    runs = client.get("/api/runs", params={"methodology_id": mid}).json()
    assert runs["total"] >= 1


def test_suggest_endpoint_keyword_fallback(client):
    res = client.post("/api/methodologies/suggest", json={"raw_input": INPUT, "top_k": 3}).json()
    assert res["suggestions"]
    assert any(s.get("slug") == "requirement-decomposition" for s in res["suggestions"])
