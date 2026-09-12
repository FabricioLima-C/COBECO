from typing import Annotated

from fastapi import APIRouter, Depends, Query, Request, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.adapters.responses import (
    CategoryResponse,
    ComparisonResponse,
    ComparisonRow,
    ConfigResponse,
    ListResponse,
    ListsResponse,
    ProductResponse,
    RecoveryResponse,
    RecoveryTokenResponse,
    SessionResponse,
    UserResponse,
)
from backend.adapters.schemas import (
    Availability,
    Comparison,
    Login,
    ProfileUpdate,
    Recovery,
    RecoveryVerify,
    Register,
    Reset,
    ShoppingList,
)

router = APIRouter(prefix="/api")
bearer = HTTPBearer(auto_error=False)


def services(request: Request):
    return request.app.state


def current_user(
    request: Request, credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]
):
    token = credentials.credentials if credentials else ""
    return services(request).auth.authenticate(token)


User = Annotated[dict, Depends(current_user)]


def client_ip(request):
    return request.client.host if request.client else "unknown"


def session_response(request, response, result):
    response.set_cookie(
        "refreshToken",
        result.pop("refresh_token"),
        max_age=7 * 86400,
        httponly=True,
        secure=services(request).settings.app_env == "production",
        samesite="strict",
        path="/api/auth",
    )
    response.headers["Cache-Control"] = "no-store"
    return result


@router.get("/config", tags=["Configuração"], response_model=ConfigResponse)
def config(request: Request):
    return {"recovery_mode": services(request).settings.recovery_mode}


@router.post("/auth/register", status_code=201, tags=["Autenticação"], response_model=UserResponse)
def register(data: Register, request: Request):
    services(request).limiter.request(f"register:{client_ip(request)}", 6, 900)
    return services(request).auth.register(data.model_dump())


@router.post("/auth/login", tags=["Autenticação"], response_model=SessionResponse)
def login(data: Login, request: Request, response: Response):
    result = services(request).auth.login(data.username, data.password, client_ip(request))
    return session_response(request, response, result)


@router.post("/auth/refresh", tags=["Autenticação"], response_model=SessionResponse)
def refresh(request: Request, response: Response):
    return session_response(
        request, response, services(request).auth.refresh(request.cookies.get("refreshToken", ""))
    )


@router.post("/auth/logout", status_code=204, tags=["Autenticação"])
def logout(request: Request, response: Response):
    services(request).auth.logout(request.cookies.get("refreshToken", ""))
    response.delete_cookie("refreshToken", path="/api/auth")


@router.post(
    "/auth/recovery", tags=["Autenticação"], response_model=RecoveryResponse, response_model_exclude_none=True
)
def recovery(data: Recovery, request: Request):
    return services(request).auth.recovery(data.username, client_ip(request))


@router.post("/auth/recovery/verify", tags=["Autenticação"], response_model=RecoveryTokenResponse)
def verify_recovery(data: RecoveryVerify, request: Request):
    return services(request).auth.verify_recovery(data.username, data.answer, client_ip(request))


@router.post("/auth/reset", status_code=204, tags=["Autenticação"])
def reset(data: Reset, request: Request):
    services(request).auth.reset(data.model_dump(), client_ip(request))


@router.get("/profile", tags=["Perfil"], response_model=UserResponse)
def profile(user: User):
    return user


@router.patch("/profile", tags=["Perfil"], response_model=UserResponse)
def update_profile(data: ProfileUpdate, request: Request, response: Response, user: User):
    services(request).limiter.request(f"profile:{user['id']}", 6, 900)
    result = services(request).auth.update_profile(user["id"], data.model_dump())
    if data.new_password:
        response.delete_cookie("refreshToken", path="/api/auth")
    return result


@router.get("/categories", tags=["Catálogo público"], response_model=list[CategoryResponse])
def categories(request: Request):
    return services(request).store.categories()


@router.get("/products", tags=["Catálogo público"], response_model=list[ProductResponse])
def products(request: Request, q: str = Query(min_length=2, max_length=100)):
    return services(request).store.products(q.strip()) if len(q.strip()) >= 2 else []


@router.post("/suppliers/availability", tags=["Comparação pública"], response_model=list[ComparisonRow])
def availability(data: Availability, request: Request):
    return services(request).shopping.availability(data.model_dump())


@router.post("/compare", tags=["Comparação pública"], response_model=ComparisonResponse)
def comparison(data: Comparison, request: Request):
    return services(request).shopping.comparison(data.model_dump())


@router.get("/lists", tags=["Listas privadas"], response_model=ListsResponse)
def lists(
    request: Request,
    user: User,
    page: int = Query(default=1, ge=1),
    q: str = Query(default="", max_length=100),
):
    return services(request).store.lists(user["id"], page, q)


@router.post("/lists", status_code=201, tags=["Listas privadas"], response_model=ListResponse)
def create_list(data: ShoppingList, request: Request, user: User):
    return services(request).shopping.save(user["id"], data.model_dump())


@router.get("/lists/{list_id}", tags=["Listas privadas"], response_model=ListResponse)
def get_list(list_id: int, request: Request, user: User):
    return services(request).store.get_list(user["id"], list_id)


@router.put("/lists/{list_id}", tags=["Listas privadas"], response_model=ListResponse)
def update_list(list_id: int, data: ShoppingList, request: Request, user: User):
    return services(request).shopping.save(user["id"], data.model_dump(), list_id)


@router.delete("/lists/{list_id}", status_code=204, tags=["Listas privadas"])
def delete_list(list_id: int, request: Request, user: User):
    services(request).store.delete_list(user["id"], list_id)
