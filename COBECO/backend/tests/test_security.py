import asyncio
import secrets
import uuid
from threading import Event, Thread

import pytest
from pydantic import ValidationError
from starlette.responses import Response

from backend.adapters.request_limits import RequestLimits
from backend.config import Settings
from backend.domain.errors import RateLimited
from backend.seed import seed
from backend.usecases.limiter import AttemptLimiter


@pytest.mark.parametrize(
    "values",
    [
        {"app_env": "prodution"},
        {"jwt_secret": "change-this-to-a-random-secret-of-at-least-32-characters"},
        {"jwt_secret": "a" * 64},
        {"app_origin": "https://example.com/path"},
        {"app_origin": "https://user:pass@example.com"},
        {"app_origin": "https://example.com?query=1"},
        {"app_env": "production", "app_origin": "http://example.com"},
        {"app_env": "production", "app_origin": "https://example.com", "recovery_mode": "question"},
        {"app_env": "production", "app_origin": "https://example.com", "recovery_mode": "log"},
        {
            "app_env": "production",
            "app_origin": "https://example.com",
            "seed_demo_password": "Strong-demo-123!",
        },
        {"app_env": "production", "app_origin": "https://example.com", "mysql_password": ""},
    ],
)
def test_unsafe_configuration_is_rejected(values):
    with pytest.raises(ValidationError):
        Settings(**{"mysql_password": "test-db-password", "jwt_secret": secrets.token_urlsafe(48), **values})


def test_safe_production_configuration():
    config = Settings(
        mysql_password="test-db-password",
        jwt_secret=secrets.token_urlsafe(48),
        app_env="production",
        app_origin="https://example.com",
    )
    assert config.recovery_mode == "code"


def test_pending_attempts_are_bounded_without_blocking_unrelated_requests():
    limiter = AttemptLimiter()
    entered, release, completed = Event(), Event(), Event()

    def slow_authentication():
        with limiter.attempt(["user:a"], maximum=1):
            entered.set()
            release.wait(3)

    thread = Thread(target=slow_authentication)
    thread.start()
    assert entered.wait(1)
    try:
        with pytest.raises(RateLimited):
            with limiter.attempt(["user:a"], maximum=1):
                pytest.fail("Concurrent attempt must not bypass reservation")

        def other_request():
            limiter.request("http:another-user")
            completed.set()

        other = Thread(target=other_request)
        other.start()
        assert completed.wait(1), "Unrelated HTTP request blocked by password operation"
        other.join(1)
    finally:
        release.set()
        thread.join(2)
    assert limiter.pending == {}
    with limiter.attempt(["user:a"], maximum=1):
        pass


@pytest.mark.parametrize(
    "headers,chunks,status",
    [
        ([(b"content-length", b"33")], [b"x"], 413),
        ([], [b"x" * 17, b"y" * 16], 413),
        ([(b"content-length", b"1")], [b"x" * 33], 413),
        ([(b"content-length", b"invalid")], [b""], 400),
        ([(b"content-length", b"-1")], [b""], 400),
        ([], [b"x" * 16, b"y" * 16], 200),
    ],
)
def test_body_limit_handles_streaming_and_untrusted_content_length(headers, chunks, status):
    async def run():
        messages = []
        queue = [
            {"type": "http.request", "body": chunk, "more_body": i < len(chunks) - 1}
            for i, chunk in enumerate(chunks)
        ]

        async def receive():
            return queue.pop(0)

        async def send(message):
            messages.append(message)

        async def app(scope, receive, send):
            message = await receive()
            assert message["body"] == b"".join(chunks)
            await Response("ok")(scope, receive, send)

        await RequestLimits(app, maximum=32)({"type": "http", "headers": headers}, receive, send)
        assert messages[0]["status"] == status

    asyncio.run(run())


def test_body_limit_times_out_and_handles_disconnect():
    async def run():
        messages = []

        async def send(message):
            messages.append(message)

        async def slow():
            await asyncio.sleep(0.1)

        async def disconnected():
            return {"type": "http.disconnect"}

        async def unused(*args):
            pytest.fail("Application must not run")

        middleware = RequestLimits(unused, timeout=0.01)
        await middleware({"type": "http"}, slow, send)
        assert messages[0]["status"] == 408
        messages.clear()
        await middleware({"type": "http"}, disconnected, send)
        assert messages == []

    asyncio.run(run())


def test_reset_requires_token_even_in_question_mode(client, account):
    response = client.post(
        "/api/auth/reset",
        json={
            "username": account["username"],
            "answer": account["security_answer"],
            "new_password": "New-password-123!",
            "confirm_password": "New-password-123!",
        },
    )
    assert response.status_code == 422
    assert (
        client.post("/api/auth/login", json={k: account[k] for k in ("username", "password")}).status_code
        == 200
    )


def test_recovery_start_never_reveals_account(client, account, app):
    for mode in ("code", "question"):
        app.state.auth.settings = app.state.settings.model_copy(update={"recovery_mode": mode})
        known = client.post("/api/auth/recovery", json={"username": account["username"]})
        unknown = client.post("/api/auth/recovery", json={"username": "missingaccount"})
        assert known.status_code == unknown.status_code == 200
        assert known.json() == unknown.json()
        assert account["security_question"] not in known.text


def test_code_rotation_reset_and_replay(client, account, logged, app, database):
    app.state.auth.settings = app.state.settings.model_copy(update={"recovery_mode": "code"})
    endpoint = "/api/profile/recovery-code"
    assert client.post(endpoint, json={"current_password": account["password"]}).status_code == 401
    assert client.post(endpoint, headers=logged, json={"current_password": "wrong"}).status_code == 401
    first = client.post(endpoint, headers=logged, json={"current_password": account["password"]}).json()[
        "recovery_code"
    ]
    second = client.post(endpoint, headers=logged, json={"current_password": account["password"]}).json()[
        "recovery_code"
    ]
    assert first != second and len(second) >= 43
    with database.transaction() as c:
        c.execute(
            "SELECT code_hash FROM recovery_codes JOIN users ON users.id=user_id WHERE username=%s",
            (account["username"],),
        )
        stored = c.fetchone()["code_hash"]
        assert stored == app.state.auth.security.digest(second) and stored != second
    assert (
        client.post(
            "/api/auth/recovery/verify", json={"username": account["username"], "answer": first}
        ).status_code
        == 422
    )
    verified = client.post(
        "/api/auth/recovery/verify", json={"username": account["username"], "answer": second}
    )
    assert verified.status_code == 200
    data = {
        "username": account["username"],
        "token": verified.json()["token"],
        "new_password": "New-password-123!",
        "confirm_password": "New-password-123!",
    }
    assert client.post("/api/auth/reset", json=data).status_code == 204
    assert client.get("/api/profile", headers=logged).status_code == 401
    assert client.post("/api/auth/reset", json=data).status_code == 422
    assert (
        client.post(
            "/api/auth/recovery/verify", json={"username": account["username"], "answer": second}
        ).status_code
        == 422
    )


def test_demo_cannot_be_recovered_or_used_in_production(client, app, database, settings):
    demo_settings = settings.model_copy(update={"seed_demo_password": "Test-demo-password-123!"})
    seed(database, demo_settings)
    assert (
        client.post("/api/auth/recovery/verify", json={"username": "demo", "answer": "cobeco"}).status_code
        == 422
    )
    app.state.auth.settings = settings.model_copy(update={"app_env": "production", "recovery_mode": "code"})
    assert (
        client.post(
            "/api/auth/login", json={"username": "demo", "password": demo_settings.seed_demo_password}
        ).status_code
        == 401
    )
    with pytest.raises(ValueError):
        seed(database, demo_settings.model_copy(update={"app_env": "production"}))


def test_existing_reset_token_is_invalidated_by_rotating_code(client, account, logged, app):
    app.state.auth.settings = app.state.settings.model_copy(update={"recovery_mode": "code"})
    code = client.post(
        "/api/profile/recovery-code", headers=logged, json={"current_password": account["password"]}
    ).json()["recovery_code"]
    token = client.post(
        "/api/auth/recovery/verify", json={"username": account["username"], "answer": code}
    ).json()["token"]
    client.post("/api/profile/recovery-code", headers=logged, json={"current_password": account["password"]})
    assert (
        client.post(
            "/api/auth/reset",
            json={
                "username": account["username"],
                "token": token,
                "new_password": "New-password-123!",
                "confirm_password": "New-password-123!",
            },
        ).status_code
        == 422
    )


def test_actual_application_rejects_large_request(client):
    response = client.post("/api/compare", content=b"x" * 65537, headers={"Content-Type": "application/json"})
    assert response.status_code == 413


def test_registration_code_is_only_returned_once(client, app, account):
    app.state.auth.settings = app.state.settings.model_copy(update={"recovery_mode": "code"})
    name = "secure" + uuid.uuid4().hex[:12]
    data = {k: v for k, v in account.items() if not k.startswith("security_")}
    data.update(username=name, email=name + "@example.com")
    result = client.post("/api/auth/register", json=data)
    assert result.status_code == 201
    code = result.json()["recovery_code"]
    assert len(code) == 43 and result.headers["cache-control"] == "no-store"
    session = client.post("/api/auth/login", json={"username": name, "password": data["password"]})
    assert "recovery_code" not in session.json()
    profile = client.get(
        "/api/profile", headers={"Authorization": "Bearer " + session.json()["access_token"]}
    )
    assert code not in profile.text and "recovery_code" not in profile.json()
    assert (
        client.post("/api/auth/recovery/verify", json={"username": name, "answer": code}).status_code == 200
    )
    app.state.auth.settings = app.state.settings.model_copy(update={"recovery_mode": "question"})
    assert (
        client.post(
            "/api/auth/recovery/verify", json={"username": name, "answer": "Não utilizado"}
        ).status_code
        == 422
    )


def test_reserved_username_and_missing_legacy_answer(client, account):
    assert client.post("/api/auth/register", json={**account, "username": "demo"}).status_code == 422
    data = {k: v for k, v in account.items() if not k.startswith("security_")}
    assert client.post("/api/auth/register", json=data).status_code == 422


def test_production_cookie_is_secure(client, account, app):
    app.state.settings = app.state.settings.model_copy(update={"app_env": "production"})
    result = client.post("/api/auth/login", json={k: account[k] for k in ("username", "password")})
    assert result.status_code == 200
    assert "Secure" in result.headers["set-cookie"]
