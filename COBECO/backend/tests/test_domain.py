from decimal import Decimal

import pytest
from pydantic import ValidationError

from backend.adapters.schemas import Comparison, Register, ShoppingList, strong_password
from backend.domain.comparison import compare
from backend.domain.errors import BusinessError, RateLimited
from backend.usecases.limiter import AttemptLimiter


def test_comparison_partial_zero_stock_ties_and_money():
    items = [
        {"product_id": 1, "name": "Arroz", "quantity": 3},
        {"product_id": 2, "name": "Leite", "quantity": 1},
    ]
    suppliers = [{"id": i, "name": f"Fornecedor {i}"} for i in range(1, 5)]
    offers = [
        {"supplier_id": sid, "product_id": pid, "price": Decimal(price), "stock": stock, "active": True}
        for sid, pid, price, stock in [
            (1, 1, "0.10", 3),
            (1, 2, "1.20", 1),
            (2, 1, "0.10", 3),
            (2, 2, "1.20", 1),
            (3, 1, "0.01", 2),
            (3, 2, "0.50", 1),
        ]
    ]
    result = compare(items, suppliers, offers)
    assert [r["supplier_id"] for r in result["rows"]] == [3, 1, 2, 4]
    assert result["best_supplier_ids"] == [1, 2]
    assert result["tied"]
    assert result["rows"][1]["total"] == "1.50"
    assert result["rows"][0]["missing_items"] == ["Arroz"]
    assert result["rows"][-1]["total"] is None


def test_empty_and_no_offers():
    with pytest.raises(BusinessError):
        compare([], [], [])
    result = compare([{"product_id": 1, "name": "A", "quantity": 1}], [{"id": 1, "name": "A"}], [])
    assert result["best_supplier_ids"] == []


def test_inactive_offer_is_not_available():
    result = compare(
        [{"product_id": 1, "name": "A", "quantity": 1}],
        [{"id": 1, "name": "A"}],
        [{"supplier_id": 1, "product_id": 1, "price": 1, "stock": 10, "active": False}],
    )
    assert result["rows"][0]["coverage"] == 0


def test_rate_limit_window_starts_on_sixth_failure():
    now = [0]
    limiter = AttemptLimiter(lambda: now[0])
    keys = ["ip", "username"]
    for index in range(6):
        now[0] = index * 10
        limiter.check(keys)
        limiter.fail(keys)
    with pytest.raises(RateLimited) as failure:
        limiter.check(keys)
    assert failure.value.seconds == 901
    limiter.clear("username")
    with pytest.raises(RateLimited):
        limiter.check(keys)
    now[0] = 951
    limiter.check(keys)
    limiter.request("request", 1)
    with pytest.raises(RateLimited):
        limiter.request("request", 1)


@pytest.mark.parametrize("quantity", [0, -1, 10000, 1.5, True, "1"])
def test_invalid_quantity(quantity):
    with pytest.raises(ValidationError):
        ShoppingList(name="Lista", items=[{"product_id": 1, "quantity": quantity}])


def test_duplicate_products_and_suppliers():
    item = {"product_id": 1, "quantity": 1}
    with pytest.raises(ValidationError):
        ShoppingList(name="Lista", items=[item, item])
    with pytest.raises(ValidationError):
        Comparison(items=[item], supplier_ids=[1, 1])
    with pytest.raises(ValidationError):
        ShoppingList(name="   ", items=[item])
    assert ShoppingList(name=" Lista ", items=[{**item, "quantity": 9999}]).name == "Lista"


@pytest.mark.parametrize("password", ["short", "abcdefgh123!", "ABCDEFGH!", "ABCDEFGH123", "Á" * 73])
def test_password_restrictions(password):
    with pytest.raises(ValueError):
        strong_password(password)


def test_registration_rejects_mismatch_and_underscore():
    data = dict(
        username="person",
        name="Pessoa",
        email="p@example.com",
        password="Password1!",
        confirm_password="wrong",
        security_question="Pergunta?",
        security_answer="answer",
    )
    with pytest.raises(ValidationError):
        Register(**data)
    data.update(confirm_password="Password1!", username="with_under")
    with pytest.raises(ValidationError):
        Register(**data)
