import re
from datetime import UTC, datetime, timedelta

import jwt
import pytest

from backend.adapters.repositories import MySQLStore
from backend.domain.errors import BusinessError
from backend.seed import seed

pytestmark = pytest.mark.mysql
LIST = {"name": "Compras", "items": [{"product_id": 1, "quantity": 2}, {"product_id": 2, "quantity": 1}]}


def test_public_catalog_comparison_and_private_boundary(client):
    assert client.get("/").status_code == 200
    assert client.get("/docs").status_code == 200
    assert client.get("/health").json()["database"] == "mysql"
    assert len(client.get("/api/categories").json()) == 5
    assert client.get("/api/products?q=ar").json()
    assert client.get("/api/products?q=a").status_code == 422
    assert client.get("/api/products?q=  ").json() == []
    assert client.get("/api/products?q=%25%25").json() == []
    assert client.get("/api/lists").status_code == 401
    rows = client.post("/api/suppliers/availability", json={"items": LIST["items"]}).json()
    assert len(rows) == 10
    assert (
        len(
            client.post("/api/suppliers/availability", json={"items": LIST["items"], "category_id": 1}).json()
        )
        == 4
    )
    assert (
        client.post(
            "/api/suppliers/availability", json={"items": LIST["items"], "category_id": 999}
        ).status_code
        == 404
    )
    result = client.post("/api/compare", json={"items": LIST["items"], "supplier_ids": [1, 2]}).json()
    assert len(result["rows"]) == 2
    assert (
        client.post("/api/compare", json={"items": LIST["items"], "supplier_ids": [1, 999]}).status_code
        == 422
    )
    assert client.post("/api/compare", json={"items": LIST["items"], "supplier_ids": [1]}).status_code == 422


def test_registration_duplicate_validation_no_secret_echo(client, account):
    assert client.post("/api/auth/register", json=account).status_code == 409
    response = client.post("/api/auth/register", json={**account, "password": "SECRET"})
    assert response.status_code == 422
    assert "SECRET" not in response.text
    assert "hash" not in client.post("/api/auth/register", json=account).text


def test_session_rotation_replay_logout_and_cookie(client, account, logged, security):
    assert client.get("/api/profile", headers=logged).json()["username"] == account["username"]
    old_refresh = client.cookies.get("refreshToken")
    rotated = client.post("/api/auth/refresh")
    assert rotated.status_code == 200
    assert "HttpOnly" in rotated.headers["set-cookie"]
    assert "SameSite=strict" in rotated.headers["set-cookie"]
    assert "Max-Age=604800" in rotated.headers["set-cookie"]
    new_refresh = client.cookies.get("refreshToken")
    assert new_refresh != old_refresh
    with pytest.raises(BusinessError):
        client.app.state.auth.refresh(old_refresh)
    response = client.post("/api/auth/logout")
    assert response.status_code == 204
    assert client.get("/api/profile", headers=logged).status_code == 401
    assert client.post("/api/auth/refresh").status_code == 401
    assert client.post("/api/auth/logout").status_code == 204
    with pytest.raises(BusinessError):
        security.decode(rotated.json()["access_token"], "refresh")


def test_six_bad_logins_block_and_success_resets_account(client, account, app):
    for _ in range(5):
        assert (
            client.post(
                "/api/auth/login", json={"username": account["username"], "password": "wrong"}
            ).status_code
            == 401
        )
    good = client.post("/api/auth/login", json={k: account[k] for k in ("username", "password")})
    assert good.status_code == 200
    assert f"login:user:{account['username']}" not in app.state.limiter.entries
    assert (
        client.post(
            "/api/auth/login", json={"username": account["username"], "password": "wrong"}
        ).status_code
        == 401
    )
    blocked = client.post("/api/auth/login", json={k: account[k] for k in ("username", "password")})
    assert blocked.status_code == 429
    assert int(blocked.headers["retry-after"]) > 0


def test_unknown_login_and_expired_token(client, security, settings):
    assert (
        client.post("/api/auth/login", json={"username": "unknown", "password": "wrong"}).status_code == 401
    )
    expired = jwt.encode(
        {
            "sub": "1",
            "version": 0,
            "type": "access",
            "iss": "cobeco",
            "aud": "cobeco",
            "iat": datetime.now(UTC) - timedelta(hours=1),
            "exp": datetime.now(UTC) - timedelta(minutes=1),
        },
        settings.jwt_secret,
    )
    assert client.get("/api/profile", headers={"Authorization": f"Bearer {expired}"}).status_code == 401


def test_question_reset_revokes_session(client, account, logged):
    result = client.post("/api/auth/recovery", json={"username": account["username"]})
    assert result.json()["question"] == account["security_question"]
    new_password = "New-password-456!"
    data = {
        "username": account["username"],
        "answer": "  Cobeco  ",
        "new_password": new_password,
        "confirm_password": new_password,
    }
    assert client.post("/api/auth/reset", json=data).status_code == 204
    assert client.get("/api/profile", headers=logged).status_code == 401
    assert (
        client.post(
            "/api/auth/login", json={"username": account["username"], "password": new_password}
        ).status_code
        == 200
    )


def test_reset_three_failures_and_unknown_account(client, account):
    assert client.post("/api/auth/recovery", json={"username": "unknown"}).status_code == 200
    data = {
        "username": account["username"],
        "answer": "wrong",
        "new_password": "Password2!",
        "confirm_password": "Password2!",
    }
    for _ in range(3):
        assert client.post("/api/auth/reset", json=data).status_code == 422
    assert client.post("/api/auth/reset", json=data).status_code == 429


def test_log_reset_single_use_and_expiry(client, app, account, caplog, database):
    from copy import copy

    app.state.auth.settings = copy(app.state.settings)
    app.state.auth.settings.recovery_mode = "log"
    response = client.post("/api/auth/recovery", json={"username": account["username"]})
    assert response.json()["mode"] == "log"
    assert "token=" not in response.text
    token = re.search(r"token=([\w-]+)", caplog.text).group(1)
    data = {
        "username": account["username"],
        "token": token,
        "new_password": "Password2!",
        "confirm_password": "Password2!",
    }
    assert client.post("/api/auth/reset", json=data).status_code == 204
    assert client.post("/api/auth/reset", json=data).status_code == 422
    caplog.clear()
    client.post("/api/auth/recovery", json={"username": account["username"]})
    data["token"] = re.search(r"token=([\w-]+)", caplog.text).group(1)
    with database.transaction() as c:
        c.execute(
            "UPDATE users SET reset_expires_at=UTC_TIMESTAMP()-INTERVAL 1 MINUTE WHERE username=%s",
            (account["username"],),
        )
    assert client.post("/api/auth/reset", json=data).status_code == 422


def test_profile_password_and_email(client, account, logged):
    data = {"name": "Nome Atualizado", "email": account["email"], "current_password": "wrong"}
    assert client.patch("/api/profile", headers=logged, json=data).status_code == 401
    data["current_password"] = account["password"]
    assert client.patch("/api/profile", headers=logged, json=data).json()["name"] == "Nome Atualizado"
    assert (
        client.patch(
            "/api/profile", headers=logged, json={**data, "new_password": account["password"]}
        ).status_code
        == 422
    )
    assert (
        client.patch(
            "/api/profile", headers=logged, json={**data, "new_password": "New-password-456!"}
        ).status_code
        == 200
    )
    assert client.get("/api/profile", headers=logged).status_code == 401


def test_lists_atomic_ownership_pagination_search_and_delete(client, logged, database, app):
    created = client.post("/api/lists", headers=logged, json=LIST)
    assert created.status_code == 201, created.text
    saved = created.json()
    assert len(saved["items"]) == 2
    assert (
        client.put(
            f"/api/lists/{saved['id']}", headers=logged, json={**LIST, "name": "Atualizada"}
        ).status_code
        == 200
    )
    assert client.get("/api/lists?q=atualizada", headers=logged).json()["total"] == 1
    user = app.state.auth.authenticate(logged["Authorization"][7:])
    with pytest.raises(BusinessError):
        app.state.store.get_list(user["id"] + 999999, saved["id"])
    with pytest.raises(BusinessError):
        app.state.store.save_list(user["id"] + 999999, LIST, saved["id"])
    with pytest.raises(BusinessError):
        app.state.store.delete_list(user["id"] + 999999, saved["id"])
    for index in range(22):
        app.state.store.save_list(user["id"], {**LIST, "name": f"Página {index}"})
    first = client.get("/api/lists", headers=logged).json()
    assert len(first["items"]) == 20
    assert first["total"] == 23
    assert client.get("/api/lists?page=2", headers=logged).json()["page"] == 2
    assert client.get("/api/lists?page=999", headers=logged).json()["page"] == 2
    assert client.get("/api/lists?q=%25%25", headers=logged).json()["total"] == 0
    assert client.delete(f"/api/lists/{saved['id']}", headers=logged).status_code == 204
    assert client.get(f"/api/lists/{saved['id']}", headers=logged).status_code == 404
    with database.transaction() as c:
        c.execute("SELECT deleted_at FROM lists WHERE id=%s", (saved["id"],))
        assert c.fetchone()["deleted_at"] is not None


def test_invalid_product_and_rollback(client, logged, app, database, monkeypatch):
    user = app.state.auth.authenticate(logged["Authorization"][7:])
    bad = {"name": "Não salvar", "items": [{"product_id": 999999, "quantity": 1}]}
    assert client.post("/api/lists", headers=logged, json=bad).status_code == 422
    assert client.get("/api/lists", headers=logged).json()["total"] == 0
    original = MySQLStore.read_list

    def fail_after_insert(*args, **kwargs):
        raise RuntimeError("simulated connection failure before commit")

    monkeypatch.setattr(MySQLStore, "read_list", staticmethod(fail_after_insert))
    with pytest.raises(RuntimeError):
        app.state.store.save_list(user["id"], LIST)
    monkeypatch.setattr(MySQLStore, "read_list", staticmethod(original))
    assert client.get("/api/lists", headers=logged).json()["total"] == 0


def test_seed_idempotent_and_constraints(database, settings):
    seed(database, settings)
    seed(database, settings)
    with database.transaction() as c:
        for table, count in [
            ("categories", 5),
            ("suppliers", 10),
            ("products", 50),
            ("supplier_categories", 20),
            ("supplier_products", 294),
        ]:
            c.execute(f"SELECT COUNT(*) AS total FROM {table}")
            assert c.fetchone()["total"] == count
    import pymysql

    with pytest.raises(pymysql.IntegrityError):
        with database.transaction() as c:
            c.execute(
                "INSERT INTO supplier_products(supplier_id,product_id,price,stock) VALUES(1,999999,1,1)"
            )
    with pytest.raises(pymysql.OperationalError):
        with database.transaction() as c:
            c.execute("UPDATE supplier_products SET stock=-1 WHERE supplier_id=1")


def test_origin_and_global_limit(client, app):
    assert client.post("/api/auth/logout", headers={"Origin": "https://evil.invalid"}).status_code == 403
    assert client.post("/api/auth/logout", headers={"Sec-Fetch-Site": "cross-site"}).status_code == 403
    for _ in range(100):
        app.state.limiter.request("http:testclient")
    assert client.get("/api/config").status_code == 429


def test_three_stage_recovery_token_is_single_use(client, account):
    response = client.post(
        "/api/auth/recovery/verify", json={"username": account["username"], "answer": "wrong"}
    )
    assert response.status_code == 422
    response = client.post(
        "/api/auth/recovery/verify", json={"username": account["username"], "answer": "COBECO"}
    )
    assert response.status_code == 200
    data = {
        "username": account["username"],
        "token": response.json()["token"],
        "new_password": "Updated-password-123!",
        "confirm_password": "Updated-password-123!",
    }
    assert client.post("/api/auth/reset", json=data).status_code == 204
    assert client.post("/api/auth/reset", json=data).status_code == 422
