from pathlib import Path

import pymysql
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.adapters.database import Database
from backend.adapters.repositories import MySQLStore
from backend.adapters.responses import ErrorResponse, HealthResponse
from backend.adapters.security import TokenSecurity
from backend.config import Settings
from backend.domain.errors import BusinessError, RateLimited
from backend.routers.api import router
from backend.usecases.auth import Auth
from backend.usecases.limiter import AttemptLimiter
from backend.usecases.shopping import Shopping


def create_app(settings=None, store=None, security=None):
    settings = settings or Settings()
    app = FastAPI(
        title="COBECO",
        version="3.1.0",
        description="Comparação de listas — MySQL/InnoDB",
        responses={code: {"model": ErrorResponse} for code in (401, 403, 404, 409, 422, 429, 503)},
    )
    db = Database(settings)
    app.state.settings = settings
    app.state.store = store or MySQLStore(db)
    app.state.limiter = AttemptLimiter()
    app.state.auth = Auth(
        app.state.store, security or TokenSecurity(settings.jwt_secret), app.state.limiter, settings
    )
    app.state.shopping = Shopping(app.state.store)

    @app.exception_handler(BusinessError)
    async def business_error(request, exc):
        headers = {"Retry-After": str(exc.seconds)} if isinstance(exc, RateLimited) else {}
        return JSONResponse(
            {"error": {"code": exc.code, "message": exc.message}}, exc.status, headers=headers
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        # Never return input payloads: password and security-answer fields may be present.
        messages = [str(e["msg"]).removeprefix("Value error, ") for e in exc.errors()]
        return JSONResponse({"error": {"code": "VALIDATION_ERROR", "message": " ".join(messages)}}, 422)

    @app.exception_handler(pymysql.IntegrityError)
    async def integrity_error(request, exc):
        return JSONResponse(
            {"error": {"code": "CONFLICT", "message": "Dados já cadastrados ou referência inválida."}}, 409
        )

    @app.exception_handler(pymysql.MySQLError)
    async def database_error(request, exc):
        return JSONResponse(
            {"error": {"code": "DATABASE_UNAVAILABLE", "message": "Banco indisponível. Tente novamente."}},
            503,
        )

    @app.middleware("http")
    async def controls(request: Request, call_next):
        origin = request.headers.get("origin")
        if request.method not in {"GET", "HEAD", "OPTIONS"} and origin and origin != settings.app_origin:
            return JSONResponse(
                {"error": {"code": "ORIGIN_REJECTED", "message": "Origem não autorizada."}}, 403
            )
        if request.headers.get("sec-fetch-site") == "cross-site" and request.method not in {"GET", "HEAD"}:
            return JSONResponse(
                {"error": {"code": "ORIGIN_REJECTED", "message": "Origem não autorizada."}}, 403
            )
        if request.url.path.startswith("/api/"):
            try:
                app.state.limiter.request(f"http:{request.client.host if request.client else 'unknown'}")
            except RateLimited as exc:
                return await business_error(request, exc)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "same-origin"
        if request.url.path not in {"/docs", "/redoc"}:
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
                "connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
            )
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/health", tags=["Saúde"], response_model=HealthResponse)
    def health():
        db.health()
        return {"status": "ok", "database": "mysql"}

    app.include_router(router)
    frontend = Path(__file__).parents[1] / "frontend"
    if frontend.exists():
        app.mount("/", StaticFiles(directory=frontend, html=True), name="frontend")
    return app
