import pytest
from fastapi.testclient import TestClient

from backend.config import Settings
from backend.main import create_app


@pytest.fixture
def schema_client():
    # Validation must fail before reaching a database, including on public routes.
    app = create_app(Settings(mysql_password="unused", jwt_secret="category-contract-only-secret-123456"))
    with TestClient(app) as client:
        yield client


@pytest.mark.parametrize(
    "category_ids", [[], [1, 1], [0], [-1], [True], ["1"], [1.5], None, list(range(1, 102))]
)
def test_category_contract_rejects_invalid_selections(schema_client, category_ids):
    response = schema_client.post("/api/suppliers/search", json={"category_ids": category_ids})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


@pytest.mark.parametrize("path", ["/api/suppliers/search", "/api/suppliers/availability", "/api/compare"])
def test_category_contract_requires_explicit_selection(schema_client, path):
    assert schema_client.post(path, json={}).status_code == 422


@pytest.mark.mysql
def test_category_union_without_items_and_invalid_supplier(client):
    first = client.post("/api/suppliers/search", json={"category_ids": [1]}).json()
    second = client.post("/api/suppliers/search", json={"category_ids": [2]}).json()
    result = client.post("/api/suppliers/search", json={"category_ids": [1, 2]})
    assert result.status_code == 200, result.text
    union = result.json()
    expected = {s["id"] for s in first + second}
    assert {s["id"] for s in union} == expected
    assert len(union) == len(expected) == 6
    assert all(s["categories"] for s in union)
    assert all("coverage" not in s for s in union)
    assert len(next(s for s in union if s["id"] == 1)["categories"]) == 2

    items = [{"product_id": 1, "quantity": 1}]
    available = client.post("/api/suppliers/availability", json={"items": items, "category_ids": [1, 2]})
    assert {s["supplier_id"] for s in available.json()} == expected
    assert all("coverage" in s and "categories" in s for s in available.json())
    compared = client.post(
        "/api/compare", json={"items": items, "category_ids": [1, 2], "supplier_ids": [1, 2]}
    )
    assert compared.status_code == 200
    assert len(compared.json()["rows"]) == 2
    outside = client.post("/api/compare", json={"items": items, "category_ids": [1], "supplier_ids": [1, 2]})
    assert outside.status_code == 422
    assert outside.json()["error"]["code"] == "INVALID_SUPPLIER"
    missing = client.post("/api/suppliers/search", json={"category_ids": [1, 999999]})
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "CATEGORY_NOT_FOUND"


@pytest.mark.mysql
def test_legacy_list_read_and_atomic_category_validation(client, logged, database, app):
    user = app.state.auth.authenticate(logged["Authorization"][7:])
    # Simulate an existing list from before the category contract; no schema change is needed.
    with database.transaction() as c:
        c.execute("INSERT INTO lists(user_id,name) VALUES (%s,%s)", (user["id"], "Lista anterior"))
        list_id = c.lastrowid
        c.execute("INSERT INTO list_items(list_id,product_id,quantity) VALUES (%s,1,2)", (list_id,))
    path = f"/api/lists/{list_id}"
    previous = client.get(path, headers=logged).json()
    assert previous["name"] == "Lista anterior"
    assert "category_ids" not in previous
    data = {"name": "Atualizada", "items": [{"product_id": 2, "quantity": 3}]}
    assert client.put(path, json=data, headers=logged).status_code == 422
    for method, url in [("PUT", path), ("POST", "/api/lists")]:
        response = client.request(method, url, json={**data, "category_ids": [999999]}, headers=logged)
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "CATEGORY_NOT_FOUND"
    assert client.get(path, headers=logged).json() == previous
    assert client.get("/api/lists", headers=logged).json()["total"] == 1
    # Product 2 need not belong to category 1: categories classify suppliers only.
    updated = client.put(path, json={**data, "category_ids": [1]}, headers=logged)
    assert updated.status_code == 200
    assert updated.json()["items"][0]["product_id"] == 2
    assert "category_ids" not in updated.json()


@pytest.mark.mysql
def test_empty_category_and_inactive_suppliers(client, database):
    with database.transaction() as c:
        c.execute("INSERT INTO categories(name) VALUES ('Categoria temporaria sem fornecedor')")
        category_id = c.lastrowid
        c.execute("UPDATE suppliers SET active=0 WHERE id=1")
    try:
        assert client.post("/api/suppliers/search", json={"category_ids": [category_id]}).json() == []
        rows = client.post("/api/suppliers/search", json={"category_ids": [1, 2]}).json()
        assert 1 not in {s["id"] for s in rows}
    finally:
        with database.transaction() as c:
            c.execute("UPDATE suppliers SET active=1 WHERE id=1")
            c.execute("DELETE FROM categories WHERE id=%s", (category_id,))
