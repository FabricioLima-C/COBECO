from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


class UserResponse(BaseModel):
    id: int
    username: str
    name: str
    email: str
    created_at: datetime


class SessionResponse(BaseModel):
    access_token: str
    user: UserResponse


class ConfigResponse(BaseModel):
    recovery_mode: Literal["question", "log"]


class RecoveryResponse(BaseModel):
    mode: Literal["question", "log"]
    question: str | None = None
    message: str | None = None


class RecoveryTokenResponse(BaseModel):
    token: str


class CategoryResponse(BaseModel):
    id: int
    name: str
    description: str | None = None


class ProductResponse(BaseModel):
    id: int
    name: str
    unit: str


class ComparisonRow(BaseModel):
    supplier_id: int
    supplier_name: str
    available_items: list[str]
    missing_items: list[str]
    coverage: float = Field(ge=0, le=100)
    total: str | None = Field(pattern=r"^\d+\.\d{2}$")
    partial: bool


class ComparisonResponse(BaseModel):
    rows: list[ComparisonRow]
    best_supplier_ids: list[int]
    tied: bool


class ListSummary(BaseModel):
    id: int
    name: str
    created_at: datetime
    updated_at: datetime
    item_count: int = 0


class ListItemResponse(BaseModel):
    product_id: int
    quantity: int
    name: str
    unit: str
    active: bool


class ListResponse(ListSummary):
    items: list[ListItemResponse]


class ListsResponse(BaseModel):
    items: list[ListSummary]
    total: int
    page: int
    page_size: int


class HealthResponse(BaseModel):
    status: Literal["ok"]
    database: Literal["mysql"]
