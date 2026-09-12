import re
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

PositiveId = Annotated[int, Field(gt=0, strict=True)]


def strong_password(value: str) -> str:
    if len(value) < 8 or len(value.encode("utf-8")) > 72:
        raise ValueError("Senha deve ter 8 caracteres ou mais e no máximo 72 bytes UTF-8.")
    if not all(re.search(pattern, value) for pattern in (r"[A-Z]", r"[0-9]", r"[^A-Za-z0-9]")):
        raise ValueError("Inclua uma letra maiúscula, um número e um caractere especial.")
    return value


class Input(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Register(Input):
    username: str = Field(pattern=r"^[A-Za-z0-9]{3,30}$")
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str
    confirm_password: str
    security_question: str = Field(min_length=5, max_length=200)
    security_answer: str = Field(min_length=2, max_length=100)

    @field_validator("password")
    @classmethod
    def password_rules(cls, value):
        return strong_password(value)

    @field_validator("name", "security_question", "security_answer")
    @classmethod
    def non_blank(cls, value):
        if len(value.strip()) < 2:
            raise ValueError("Preencha o campo.")
        return value.strip()

    @model_validator(mode="after")
    def matching(self):
        if self.password != self.confirm_password:
            raise ValueError("As senhas não coincidem.")
        return self


class Login(Input):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=200)


class Recovery(Input):
    username: str = Field(min_length=1, max_length=100)


class RecoveryVerify(Recovery):
    answer: str = Field(min_length=1, max_length=100)


class Reset(Recovery):
    answer: str | None = Field(default=None, max_length=100)
    token: str | None = Field(default=None, max_length=200)
    new_password: str
    confirm_password: str

    @field_validator("new_password")
    @classmethod
    def password_rules(cls, value):
        return strong_password(value)

    @model_validator(mode="after")
    def matching(self):
        if self.new_password != self.confirm_password:
            raise ValueError("As senhas não coincidem.")
        return self


class ProfileUpdate(Input):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    current_password: str = Field(min_length=1, max_length=200)
    new_password: str | None = None

    @field_validator("name")
    @classmethod
    def non_blank(cls, value):
        if len(value.strip()) < 2:
            raise ValueError("Informe seu nome.")
        return value.strip()

    @field_validator("new_password")
    @classmethod
    def password_rules(cls, value):
        return strong_password(value) if value is not None else value


class Item(Input):
    product_id: PositiveId
    quantity: int = Field(ge=1, le=9999, strict=True)


class Items(Input):
    items: list[Item] = Field(min_length=1, max_length=100)

    @field_validator("items")
    @classmethod
    def unique_products(cls, value):
        if len({i.product_id for i in value}) != len(value):
            raise ValueError("Cada produto deve aparecer apenas uma vez.")
        return value


class Availability(Items):
    category_id: PositiveId | None = None


class Comparison(Items):
    supplier_ids: list[PositiveId] = Field(min_length=2, max_length=10)

    @field_validator("supplier_ids")
    @classmethod
    def unique_suppliers(cls, value):
        if len(set(value)) != len(value):
            raise ValueError("Selecione fornecedores diferentes.")
        return value


class ShoppingList(Items):
    name: str = Field(min_length=1, max_length=100)

    @field_validator("name")
    @classmethod
    def non_blank(cls, value):
        if not value.strip():
            raise ValueError("Informe um nome para a lista.")
        return value.strip()
