"""Distillation API — both intake modes, zero tokens via fake LLM."""


def test_distill_from_materials(client, fake_llm):
    body = {
        "materials": ["老张的评审记录1：先看接口稳定性…", "评审记录2：关注空指针与边界…"],
        "topic": "代码评审",
        "hint": "提炼老张的评审套路",
    }
    m = client.post("/api/distill/materials", json=body).json()["methodology"]
    assert m["origin"] == "custom"
    assert m["status"] == "draft"
    assert m["provenance"]["source_type"] == "distilled"
    assert len(m["steps"]) >= 1 and len(m["gates"]) >= 1
    assert m["applicability"]["when_not_to_use"]
    # appears in the library as a draft
    drafts = client.get("/api/methodologies", params={"origin": "custom"}).json()["methodologies"]
    assert any(x["id"] == m["id"] and x["status"] == "draft" for x in drafts)


def test_distill_interview_flow(client, fake_llm):
    start = client.post("/api/distill/interview/start",
                        json={"topic": "需求评审", "expert_name": "张三"}).json()
    sid = start["session"]["id"]
    assert start["question"]
    assert start["session"]["mode"] == "interview"

    for _ in range(10):
        r = client.post(f"/api/distill/interview/{sid}/answer",
                        json={"answer": "我会先确认业务目标，再分层拆解，最后定验收标准。"}).json()
        if r["done"]:
            break

    m = client.post(f"/api/distill/interview/{sid}/synthesize").json()["methodology"]
    assert m["status"] == "draft"
    assert m["provenance"]["source_type"] == "distilled"
    assert "内部:张三" in m["provenance"]["origin"]
    assert len(m["steps"]) >= 1
