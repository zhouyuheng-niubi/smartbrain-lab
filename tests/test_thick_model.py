"""Thick-asset fields, enriched library, and fork (本地化)."""


def test_thick_fields_persist_via_api(client):
    payload = {
        "name": "我的厚资产测试",
        "summary": "测试厚字段",
        "applicability": {"when_to_use": ["A"], "when_not_to_use": ["B", "C"]},
        "examples": [{"kind": "positive", "title": "正例", "content": "内容"}],
        "related": [{"slug": "musk-five-step", "relation": "complements", "note": "x"}],
        "tags": ["测试"],
    }
    created = client.post("/api/methodologies", json=payload).json()
    full = client.get(f"/api/methodologies/{created['id']}").json()
    assert full["applicability"]["when_not_to_use"] == ["B", "C"]
    assert full["examples"][0]["kind"] == "positive"
    assert full["related"][0]["slug"] == "musk-five-step"
    # custom-created provenance defaults to manual
    assert full["provenance"]["source_type"] == "manual"


def test_builtin_library_enriched(client):
    items = client.get("/api/methodologies").json()["methodologies"]
    slugs = {m["slug"] for m in items}
    assert {"first-principles", "five-whys-postmortem", "pre-mortem",
            "rice-prioritization", "adr-tech-decision", "code-review"} <= slugs
    cid = next(m["id"] for m in items if m["slug"] == "code-review")
    cr = client.get(f"/api/methodologies/{cid}").json()
    assert cr["applicability"]["when_not_to_use"]
    assert cr["provenance"]["origin"]
    assert cr["examples"]


def test_fork_builtin_to_company_version(client):
    items = client.get("/api/methodologies").json()["methodologies"]
    pid = next(m["id"] for m in items if m["slug"] == "musk-five-step")
    forked = client.post(f"/api/methodologies/{pid}/fork").json()
    assert forked["origin"] == "custom"
    assert forked["status"] == "draft"
    assert forked["provenance"]["forked_from"] == "musk-five-step"
    assert "我们公司版" in forked["name"]
    # forked carries the thick content over
    assert len(forked["steps"]) == 5


def test_agent_export_includes_when_not_to_use(client):
    items = client.get("/api/methodologies").json()["methodologies"]
    cid = next(m["id"] for m in items if m["slug"] == "code-review")
    content = client.get(f"/api/methodologies/{cid}/export", params={"format": "agent_md"}).json()["content"]
    assert "不适用" in content
