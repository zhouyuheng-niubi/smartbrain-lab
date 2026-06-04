"""OPC agent bindings — bind a methodology and export its injectable context."""


def test_binding_set_get_export(client):
    items = client.get("/api/methodologies").json()["methodologies"]
    mid = next(m["id"] for m in items if m["slug"] == "requirement-decomposition")

    # unbound → empty export
    assert client.get("/api/bindings/product_manager/export").json()["content"] == ""

    r = client.put("/api/bindings/product_manager", json={"methodology_id": mid}).json()
    assert r["methodology_id"] == mid

    assert client.get("/api/bindings/product_manager").json()["methodology_id"] == mid

    content = client.get("/api/bindings/product_manager/export").json()["content"]
    assert "方法论" in content and "决策闸门" in content


def test_binding_rejects_unknown_methodology(client):
    r = client.put("/api/bindings/product_manager", json={"methodology_id": "nope"})
    assert r.status_code == 404
